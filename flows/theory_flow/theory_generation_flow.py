import json
import re
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from cognition.evaluation.llm_theory_evaluator import LLMTheoryEvaluator
from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.theory.theory import Branch  # Import new schemas
from cognition.schemas.theory.theory import Theory, TheoryStructured
from interfaces.ollama_client import OllamaClient


class TheoryGenerationFlow:

    def __init__(self):
        # Stability tuning: Deterministic output for cognitive consistency
        self.client = OllamaClient(temperature=0.0, seed=42)
        self.evaluator = LLMTheoryEvaluator()
        self.debug = False

    def process(
        self,
        abstraction,
        historical_context: str = "",
        market_memory_context: str = "",
        current_market_observation: str = "",
        reflective_memory_summary: str = "",
        regime_subtype: str = "neutral",
        falsifiability_conditions: list = None,
        analog_divergence_claim: str = None,
        regime_history: dict = None,
        dialectical_synthesis: str = None,
        relevant_lessons: list = None,
        prior_theory: Optional[Theory] = None,
        prior_attribution: Optional[Any] = None,
        retrieved_theory: Optional[Theory] = None,
    ) -> tuple[Theory, dict]:

        if not regime_subtype:
            regime_subtype = "neutral"

        if falsifiability_conditions is None:
            falsifiability_conditions = []

        if self.debug:
            print("[Regime History Debug]", regime_history)

        falsifiability_text = ""
        if falsifiability_conditions:
            falsifiability_text = (
                f"\n\nThe theory is falsified if any of these conditions occur:\n- "
                + "\n- ".join(falsifiability_conditions)
            )

        # v3.1 Tuning Correction: Reduced history burden
        seen_count = regime_history.get("seen_count", 0) if regime_history else 0
        if seen_count < 2:
            history_text_for_prompt = "No prior subtype history."
        else:
            res = regime_history.get("historical_resolution", {})
            dominant_res = max(res, key=res.get) if res else "uncertain"
            history_text_for_prompt = f"""
Historical subtype memory:
Subtype: {regime_history.get('subtype', 'neutral')}
Seen: {seen_count}
Dominant resolution: {dominant_res}
Avg usefulness: {regime_history.get('avg_usefulness', 0.0):.2f}

Use subtype history only if materially relevant. Primary focus remains: 1 observation, 2 subtype, 3 falsifiability. History is secondary context. Do not force theory to explain history.
"""
        if self.debug:
            print(
                f"[Theory History Debug] seen_count: {seen_count}, context: {history_text_for_prompt}"
            )

        synthesis_context = ""
        if dialectical_synthesis:
            synthesis_context = f"""
MANDATORY Dialectical Synthesis Anchor:
{dialectical_synthesis}
You MUST incorporate the logic of this synthesis into your new theory. If current observations contradict this synthesis, explicitly explain the divergence.
"""

        lessons_context = ""
        if relevant_lessons:
            lessons_context = "Historical Lessons for this Regime:\n- " + "\n- ".join(
                relevant_lessons
            )
        else:
            lessons_context = "No validated historical lessons for this regime yet."

        attribution_context = ""
        if (
            prior_theory
            and prior_attribution
            and getattr(prior_attribution, "components_failed", None)
        ):
            failed_comps = prior_attribution.components_failed
            passed_comps = getattr(prior_attribution, "components_passed", [])
            root_cause = getattr(prior_attribution, "root_cause_component", "Unknown")
            guidance = prior_attribution.get_mutation_guidance()
            prior_claim = (
                prior_theory.summary_structured.claim
                if prior_theory.summary_structured
                else prior_theory.summary
            )

            attribution_context = f"""
MANDATORY MUTATION GUIDANCE FOR EXISTING THEORY:
You are mutating the existing active theory to fix its failures:
Claim: {prior_claim}

Causal Attribution Analysis of the prior theory:
- Failed Components: {', '.join(failed_comps)}
- Passed Components: {', '.join(passed_comps) if passed_comps else 'None'}
- Root Cause of Failure: {root_cause}
- Guidance: {guidance}

INSTRUCTIONS:
1. Mutate the existing theory to resolve the failures in the components that failed: {', '.join(failed_comps)}.
2. Keep the components that passed unchanged: {', '.join(passed_comps) if passed_comps else 'None'}.
3. Ensure the mutated theory is structurally coherent and directly addresses the root cause: {root_cause}.
"""

        retrieved_theory_context = ""
        if retrieved_theory:
            ret_claim = (
                retrieved_theory.summary_structured.claim
                if retrieved_theory.summary_structured
                else retrieved_theory.summary
            )
            ret_falsified = (
                retrieved_theory.summary_structured.falsified_if
                if retrieved_theory.summary_structured
                else "unknown"
            )
            retrieved_theory_context = f"""
MANDATORY MEMORY COMPARISON TASK:
Historical theory from similar regime:
- Claim: {ret_claim}
- Falsified if: {ret_falsified}

Evaluate whether this historical theory remains valid under current observations.
You may:
1. reuse (set "reuse_decision" to "REUSED", keep the "claim", "if_branch", "else_branch", "unless", and "falsified_if" identical to the historical theory)
2. modify (set "reuse_decision" to "MODIFIED", adapt the historical theory slightly to fit the current situation)
3. reject (set "reuse_decision" to "REJECTED", write a completely new theory from scratch)

You MUST select one of these decisions and populate the "reuse_decision" field with exactly one of: "REUSED", "MODIFIED", or "REJECTED".
"""
        else:
            retrieved_theory_context = """
No historical retrieved theory is available. Populate the "reuse_decision" field with "REJECTED".
"""

        prompt = f"""
Market Memory:
{market_memory_context}

Current Market Observation:
{current_market_observation}

The current market regime subtype is: {regime_subtype}.
Analog Divergence: {analog_divergence_claim or "None"}
{falsifiability_text}

{history_text_for_prompt}

{synthesis_context}

{lessons_context}

{attribution_context}

{retrieved_theory_context}

Reflective Memory Summary:
{reflective_memory_summary}

Historical Cognition:
{historical_context}

Current Abstraction:
{abstraction.abstraction_summary}

MANDATORY COGNITIVE TASK:
1. Identify the hidden causal MECHANISM (e.g., Absorption, Exhaustion, Front-running).
2. Define what the market is FORBIDDEN to do if your mechanism is correct.
3. Decompose your mechanism into independently testable sub-components.

MECHANISM COMPONENT REQUIREMENTS:

You must decompose your mechanism into independently testable sub-components.
Each component must be verifiable against specific market data.

Add these fields to your output:
- "mechanism_components": A JSON array of objects, each with:
  - "component_id": Short snake_case name (e.g., "price_structure", "volume_confirm")
  - "description": What this component claims about the market
  - "observable": What specific market data validates this (e.g., "price_action.daily_structure")
  - "expected_behavior": What we should observe if component holds
  - "dependency": null or component_id this depends on

- "falsification_conditions": A JSON array of strings like:
  "component_id: specific condition that would falsify this component"

Example:
{{
  "mechanism_components": [
    {{
      "component_id": "price_structure",
      "description": "Price maintains sequence of higher highs and higher lows",
      "observable": "price_action.daily_structure",
      "expected_behavior": "Each day's high > previous high, each low > previous low",
      "dependency": null
    }},
    {{
      "component_id": "volume_confirmation",
      "description": "Volume expands on up days relative to down days",
      "observable": "volume.daily_ratio",
      "expected_behavior": "Average volume on up days exceeds average volume on down days",
      "dependency": null
    }}
  ],
  "falsification_conditions": [
    "price_structure: lower low formed breaking HH/HL sequence",
    "volume_confirmation: down-day volume exceeds up-day volume for 3 consecutive sessions"
  ]
}}

Return exactly a JSON object conforming to this schema:
{{
  "claim": "string",
  "mechanism": "string",
  "if_branch": {{"condition": "string", "action": "string"}},
  "else_branch": {{"condition": "string", "action": "string"}},
  "unless": "string",
  "falsified_if": "string",
  "mechanism_components": [
    {{
      "component_id": "string",
      "description": "string",
      "observable": "string",
      "expected_behavior": "string",
      "dependency": "string or null"
    }}
  ],
  "falsification_conditions": ["string"],
  "reuse_decision": "REUSED | MODIFIED | REJECTED"
}}

Constraint Checklist:
- Start claim with the causal mechanism (e.g., "Regime is driven by [Mechanism]...")
- Define a FORBIDDEN STATE in 'falsified_if'.
- Logic branches must be conditional ('if... then...') and specific.
- Prioritize Dialectical Synthesis logic if provided.
- Start the claim by stating the regime subtype (unless 'neutral').
- explicitly name unresolved tension if the evidence contains tension.
- focus on market structure, coherence, uncertainty, volatility, breadth, participation, liquidity, and regime evolution.
- do not produce trading recommendations or advice.
- No macro filler, no headings, no markdown.
- Populate "reuse_decision" field exactly with one of: "REUSED", "MODIFIED", or "REJECTED".

Example:
{{
  "claim": "Compression regime is driven by passive absorption; price remains range-bound despite volume expansion.",
  "if_branch": {{"condition": "participation widens above average", "action": "favor breakout higher"}},
  "else_branch": {{"condition": "volatility remains compressed", "action": "favor range persistence"}},
  "unless": "liquidity evaporates entirely",
  "falsified_if": "decisive close below the prior support floor",
  "reuse_decision": "REJECTED"
}}
"""

        # Strongly prefer a JSON-only response. Add an explicit output format
        # requirement to the prompt to reduce free-text responses.
        # The prompt above already includes the detailed output format.

        result = self.client.generate(prompt, json_format=True)

        # Attempt to parse JSON output, with more robust retries.
        parsed_theory_data = None
        # First, allow a few normal regenerations with the strict prompt
        for attempt in range(3):
            try:
                # Extract JSON using a more targeted approach to avoid greedy capture of multiple blocks
                # We search for the first '{' and the last '}' in the string
                start = result.find("{")
                end = result.rfind("}") + 1
                json_text = result[start:end] if start != -1 and end > start else result
                parsed_theory_data = json.loads(json_text)
                break
            except (json.JSONDecodeError, AttributeError):
                if self.debug:
                    print(
                        f"[Theory JSON Parse Error] Attempt {attempt+1}/3. Retrying generation..."
                    )
                result = self.client.generate(prompt, json_format=True)

        # If still not parsed, attempt one final targeted JSON-only repair prompt
        if parsed_theory_data is None:
            repair_prompt = (
                "The previous response could not be parsed as JSON.\n"
                "Extract the core theory content from the last message and return ONLY a JSON object with keys:"
                " claim, mechanism, if_branch, else_branch, unless, falsified_if,"
                " mechanism_components, falsification_conditions, reuse_decision.\n"
                "Here is the original output:\n"
                + result
                + "\n\nRespond ONLY with the JSON object. No commentary."
            )
            try:
                repair_result = self.client.generate(repair_prompt, json_format=True)
                # Extract JSON from repair result
                start = repair_result.find("{")
                end = repair_result.rfind("}") + 1
                json_text = (
                    repair_result[start:end]
                    if start != -1 and end > start
                    else repair_result
                )
                parsed_theory_data = json.loads(json_text)
                result = repair_result
            except Exception:
                # Leave parsed_theory_data as None and fall back to text cleaning below
                parsed_theory_data = None

        # v3.7 Logic: Convert dict to Pydantic object to support attribute access in downstream logic
        if parsed_theory_data and isinstance(parsed_theory_data, dict):
            # Pre-sanitize to prevent validation noise
            if "if_branch" in parsed_theory_data and isinstance(
                parsed_theory_data["if_branch"], str
            ):
                parsed_theory_data["if_branch"] = {
                    "condition": parsed_theory_data["if_branch"],
                    "action": "behavior continues",
                }
            if "else_branch" in parsed_theory_data and isinstance(
                parsed_theory_data["else_branch"], str
            ):
                parsed_theory_data["else_branch"] = {
                    "condition": parsed_theory_data["else_branch"],
                    "action": "behavior persists",
                }
            if parsed_theory_data.get("unless") is None:
                parsed_theory_data["unless"] = "no contrary evidence emerges"

            try:
                parsed_theory_data = TheoryStructured(**parsed_theory_data)
            except Exception as e:
                if self.debug:
                    print(f"[Theory Structure Validation Error] {e}")
                parsed_theory_data = None

        # Phase 1: Attach structured data to object for the evaluator
        # This ensures the evaluator has access to the clean JSON even if persistence hasn't happened yet

        theory_text, branches_generated, branches_retained = self._clean_theory(
            result,
            parsed_theory_data,
            regime_subtype=regime_subtype,
            dialectical_synthesis=dialectical_synthesis,
        )

        if self.debug:
            print("[Theory Summary Debug]", theory_text)

        theory = Theory(
            lineage_id=str(uuid4()),
            thesis=theory_text,
            summary=theory_text,
            assumptions=[],
            summary_structured=parsed_theory_data,
            confidence_state=ConfidenceState(),
            # v3.0 Regime-based continuity
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
        )

        object.__setattr__(theory, "llm_evaluation", self.evaluator.evaluate(theory))

        branch_stats = {"generated": branches_generated, "retained": branches_retained}
        return theory, branch_stats

    def _clean_theory(
        self,
        raw_llm_output: str,
        parsed_theory_data: Optional[TheoryStructured],
        regime_subtype: str = "neutral",
        dialectical_synthesis: str = None,
    ) -> Tuple[str, int, int]:

        replacements = {
            "I've generated the requested outputs:": "",
            "I've reformatted the text into a more readable format and generated the requested outputs.": "",
            "Here they are:": "",
            "Here are the requested outputs:": "",
            "Here's a generated text that meets the requirements:": "",
            "generate strong returns": "sustain directional movement",
            "leading to stronger expected returns": (
                "indicating stronger market structure"
            ),
            "investors": "market participants",
            "trading recommendations": "market conclusions",
            "profit": "market outcome",
            "returns": "market behavior",
            "momentum strategies": "momentum behavior",
            "momentum-based approaches": "momentum behavior",
            "are likely to excel": "may become more persistent",
            "generating strong market behavior for market participants": (
                "reinforcing directional market behavior"
            ),
            "actively buying and selling securities": (
                "participating across index constituents"
            ),
            "capitalize on": "reflect",
            "tend to excel": "can become more persistent",
            "tends to excel": "can become more persistent",
            "particularly effective": "more structurally coherent",
        }
        blocked_phrases = [
            "i'd be happy",
            "here are",
            "here is",
            "here's",
            "concise theory",
            "epistemically grounded theory",
            "market-grounded theory",
            "uncertainty-aware theory",
            "contradiction-sensitive theory",
        ]
        lines = []

        if parsed_theory_data:
            # v3.7 Structured Theory Output: Prioritize JSON parsing
            # With the new TheoryStructured Pydantic model, parsed_theory_data is guaranteed to be valid.
            # We will now generate the 'summary' (legacy text) from the structured data.

            # Generate a concise text summary from the structured data for legacy 'summary' field
            # This is a temporary step to maintain compatibility with existing print statements
            # and logging that might still rely on theory.summary as a string.
            theory_text = f"{parsed_theory_data.claim}. If {parsed_theory_data.if_branch.condition}: {parsed_theory_data.if_branch.action}. Else {parsed_theory_data.else_branch.condition}: {parsed_theory_data.else_branch.action}."
            if parsed_theory_data.unless:
                theory_text += f" Unless {parsed_theory_data.unless}."
            theory_text += f" Falsified if: {parsed_theory_data.falsified_if}."
        else:
            theory_text = raw_llm_output

        for line in theory_text.splitlines():
            cleaned_line = line.strip().strip("*").strip("#").strip()

            if not cleaned_line:
                continue

            lower_line = cleaned_line.lower().rstrip(":")

            if any(phrase in lower_line for phrase in blocked_phrases):
                continue

            lines.append(cleaned_line)

        cleaned = "\n".join(lines)

        for source, replacement in replacements.items():
            cleaned = re.sub(
                re.escape(source), replacement, cleaned, flags=re.IGNORECASE
            )

        cleaned = re.sub(r"\*\*[^*]+:\*\*", "", cleaned)
        cleaned = re.sub(
            r"\b(Concise Reflection|Momentum Behavior Theory|Note):", "", cleaned
        )
        cleaned = cleaned.replace("**", "")

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
            if sentence.strip()
        ]
        grounded_sentences = []
        allowed_terms = [
            "nifty",
            "market",
            "liquidity",
            "breadth",
            "volatility",
            "regime",
            "contradiction",
            "trend",
            "participation",
            "coherence",
            "uncertainty",
            "momentum",
            "subtype",
            "expansion",
            "compression",
            "fatigue",
            "breakout",
            "rejection",
            "support",
            "divergence",
            "synthesis",
            "conflict",
            "reconciliation",
            "reconcil",
            "premise",
            "boundary",
            "reconciled",
            "reconciling",
            "if",
            "else",
            "favor",
            "logic",
            "conditional",
            "then",
            "price",
            "high",
            "low",
            "close",
            "level",
            "uncertain",
            "scenario",
            "gate",
        ]
        blocked_terms = [
            "i've",
            "i have",
            "requested outputs",
            "here they are",
            "adopt",
            "recommend",
            "advice",
        ]
        generic_patterns = [
            r"\bthe market is characterized by\b",
            r"\binvestor confidence suggests\b",
            r"\bstable upward trajectory\b",
            r"\bthis indicates that\b",
            r"\bthe market demonstrates\b",
            r"\bparticipants are optimistic\b",
            r"\bstable growth due to\b",
        ]
        broad_causal_patterns = [
            r"\bdue to investor confidence\b",
            r"\battributed to .*confidence\b",
            r"\bcaused by .*confidence\b",
            r"\bdemonstrates stable growth\b",
        ]

        for sentence in sentences:
            lower_sentence = sentence.lower()

            # v3.4 bypass for regime and synthesis logic
            if regime_subtype != "neutral" and regime_subtype.lower() in lower_sentence:
                grounded_sentences.append(sentence)
                continue

            if dialectical_synthesis:
                # Preserve sentences that explicitly address the mandatory anchor
                if any(
                    term in lower_sentence
                    for term in [
                        "synthesis",
                        "conflict",
                        "reconciliation",
                        "reconcil",
                        "premise",
                        "boundary",
                    ]
                ):
                    grounded_sentences.append(sentence)
                    continue

            if any(term in lower_sentence for term in blocked_terms):
                continue

            if any(
                re.search(pattern, lower_sentence)
                for pattern in generic_patterns + broad_causal_patterns
            ):
                continue

            if not any(term in lower_sentence for term in allowed_terms):
                continue

            grounded_sentences.append(sentence)

        if parsed_theory_data:
            branches_generated = self._count_branches_from_structured(
                parsed_theory_data
            )
            branches_retained = branches_generated
        else:
            branches_generated = self._count_branches(raw_llm_output)
            branches_retained = self._count_branches(theory_text)

        if grounded_sentences:
            return theory_text, branches_generated, branches_retained

        # If no grounded sentences, try a more minimal cleaning
        compressed = self._remove_generic_phrases(cleaned).strip()
        if not compressed:
            compressed = "Evidence remains insufficient for a compressed market theory."

        branches_generated = self._count_branches(raw_llm_output)
        branches_retained = self._count_branches(compressed)
        return (
            theory_text,
            branches_generated,
            branches_retained,
        )  # Return the generated theory_text

    def _remove_generic_phrases(self, text: str) -> str:
        """Minimally remove known filler openings without rewriting claims."""
        generic_openings = [
            "The market is characterized by",
            "Investor confidence suggests",
            "Stable upward trajectory",
            "This indicates that",
        ]
        cleaned = text
        for phrase in generic_openings:
            cleaned = re.sub(
                rf"^\s*{re.escape(phrase)}[:,]?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
        return cleaned

    def _count_branches(self, text: str) -> int:
        """Lightweight count of If/Else logic branches."""
        if not text:
            return 0
        count = 0
        # v3.7 Loosen anchors to catch branches in joined or formatted text
        patterns = [
            r"(?:^|\n|\. |; )\s*if\b",
            r"(?:^|\n|\. |; )\s*else\s+if\b",
            r"(?:^|\n|\. |; )\s*else\b",
        ]

        for line in text.splitlines():
            cleaned = line.strip().strip("*").strip("#").strip().lower()
            if any(re.search(p, cleaned) for p in patterns):
                count += 1

        if count == 0:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for s in sentences:
                cleaned = s.strip().lower()
                if any(re.search(p, cleaned) for p in patterns):
                    count += 1
        return count

    def _count_branches_from_structured(
        self, theory_structured: TheoryStructured
    ) -> int:
        """Count branches from a structured theory dictionary."""
        count = 0
        if theory_structured.if_branch:
            count += 1
        if theory_structured.else_branch:
            count += 1
        if theory_structured.unless:
            count += 1
        return count
