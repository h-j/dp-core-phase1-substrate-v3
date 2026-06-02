import json
import re
from typing import Dict, Optional, Tuple
from uuid import uuid4

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.theory.theory import Theory
from interfaces.ollama_client import OllamaClient


class TheoryGenerationFlow:

    def __init__(self):

        self.client = OllamaClient()

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
    ) -> tuple[Theory, dict]:

        if not regime_subtype:
            regime_subtype = "neutral"

        if falsifiability_conditions is None:
            falsifiability_conditions = []

        print("[Regime History Debug]", regime_history)

        falsifiability_text = ""
        if falsifiability_conditions:
            falsifiability_text = f"\n\nThe theory is falsified if any of these conditions occur:\n- " + "\n- ".join(falsifiability_conditions)

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
        print(f"[Theory History Debug] seen_count: {seen_count}, context: {history_text_for_prompt}")

        synthesis_context = ""
        if dialectical_synthesis:
            synthesis_context = f"""
MANDATORY Dialectical Synthesis Anchor:
{dialectical_synthesis}
You MUST incorporate the logic of this synthesis into your new theory. If current observations contradict this synthesis, explicitly explain the divergence.
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

Reflective Memory Summary:
{reflective_memory_summary}

Historical Cognition:
{historical_context}

Current Abstraction:
{abstraction.abstraction_summary}

MANDATORY COGNITIVE TASK:
1. Identify the hidden causal MECHANISM (e.g., Absorption, Exhaustion, Front-running).
2. Define what the market is FORBIDDEN to do if your mechanism is correct.

Generate:
- one compressed theory, 2-4 sentences
- Start with the hidden causal mechanism (e.g., "Regime is driven by [Mechanism]...")
- direct grounding in the observation and abstraction above
- Define a FORBIDDEN STATE: a specific market behavior that would instantly invalidate your mechanism.
- Falsification must be an event that proves your mechanism (the 'Why') is wrong, not just that the price moved.
- explicitly name unresolved tension if the evidence contains tension
- The provided Dialectical Synthesis is a MANDATORY cognitive anchor.
- Prioritize the reconciliation logic found in the synthesis over generic observation.
- avoid causal certainty; emphasize the conditional nature of the trend.
- ensure logic branches explicitly reference the provided falsifiability boundary conditions.
- focus on market structure, coherence, uncertainty, volatility, breadth, participation, liquidity, and regime evolution
- if generating theory for same regime subtype as prior theories, explicitly reference continuity or divergence
- anchor claims to the specific falsifiability conditions above
- start the theory by explicitly stating the current regime subtype, unless it is 'neutral'
- avoid broad macro explanations, generic financial commentary, and smooth storytelling
- avoid semantic filler and opening phrases
- avoid repeating prior theories blindly; use prior validations/reflections only as constraints
- do not produce trading recommendations
- do not mention buy, sell, returns, profit, trading signals, or investment advice
- avoid generic "additional confirmation needed" or "requires additional confirmation" phrasing
- do not use headings
- no markdown

Good style:
Continuation remains weakly supported under compressed volatility; would falsify if volume normalizes.
Observed stability may weaken if participation deteriorates; consistent with prior liquidity-constrained patterns.

Decision Branch Style (Preferred):
If price closes above rejection high with stable volume:
favor continuation higher (confidence medium)
Else if participation weakens below average:
favor range persistence
Else:
remain uncertain

Bad style:
The market demonstrates stable growth due to investor confidence.
Participants are optimistic and stability is likely to continue.
"""

        # Strongly prefer a JSON-only response. Add an explicit output format
        # requirement to the prompt to reduce free-text responses.
        prompt = prompt + "\n\nOUTPUT FORMAT (REQUIRED): Respond ONLY with a single JSON object with the following keys: \"claim\", \"if_branch\", \"else_branch\", \"unless\", \"falsified_if\". Do not include any additional text, explanation, or markdown."

        result = self.client.generate(prompt)

        # Attempt to parse JSON output, with more robust retries.
        parsed_theory_data = None
        # First, allow a few normal regenerations with the strict prompt
        for attempt in range(3):
            try:
                parsed_theory_data = json.loads(result)
                break
            except json.JSONDecodeError:
                print(f"[Theory JSON Parse Error] Attempt {attempt+1}/3. Retrying generation (strict JSON prompt)...")
                result = self.client.generate(prompt)

        # If still not parsed, attempt one final targeted JSON-only repair prompt
        if parsed_theory_data is None:
            repair_prompt = (
                "The previous response could not be parsed as JSON.\n"
                "Extract the core theory content from the last message and return ONLY a JSON object with keys:"
                " claim, if_branch, else_branch, unless, falsified_if.\n"
                "Here is the original output:\n" + result + "\n\nRespond ONLY with the JSON object. No commentary."
            )
            try:
                repair_result = self.client.generate(repair_prompt)
                parsed_theory_data = json.loads(repair_result)
                result = repair_result
            except Exception:
                # Leave parsed_theory_data as None and fall back to text cleaning below
                parsed_theory_data = None
        
        theory_text, branches_generated, branches_retained = self._clean_theory(result, parsed_theory_data, regime_subtype=regime_subtype, dialectical_synthesis=dialectical_synthesis)

        print("[Theory Summary Debug]", theory_text)

        theory = Theory(
            lineage_id=str(uuid4()),
            thesis=theory_text,
            summary=theory_text,
            assumptions=[],
            confidence_state=ConfidenceState(),
            # v3.0 Regime-based continuity
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
        )
        branch_stats = {"generated": branches_generated, "retained": branches_retained}
        return theory, branch_stats

    def _clean_theory(self, raw_llm_output: str, parsed_theory_data: Optional[Dict[str, str]], regime_subtype: str = "neutral", dialectical_synthesis: str = None) -> Tuple[str, int, int]:

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
        
        # v3.7 Structured Theory Output: Prioritize JSON parsing
        if parsed_theory_data:
            # Validate schema
            required_fields = ["claim", "if_branch", "else_branch", "unless", "falsified_if"]
            if all(field in parsed_theory_data for field in required_fields):
                # Perform field normalization, safely stripping only string values
                cleaned_theory = {k: v.strip() if isinstance(v, str) else v for k, v in parsed_theory_data.items()}
                
                # Count branches from the structured data
                branches_generated = self._count_branches_from_dict(cleaned_theory)
                branches_retained = branches_generated # All generated branches are retained in structured output
                
                # Store as JSON string in summary
                return json.dumps(cleaned_theory), branches_generated, branches_retained
            else:
                print(f"[Theory JSON Schema Error] Invalid schema, falling back: {parsed_theory_data}")
                # Fallback to text cleaning if schema is invalid
                theory_text = raw_llm_output
        else:
            # If JSON parsing failed, use raw LLM output for text cleaning
            theory_text = raw_llm_output

        # Fallback to old text-based cleaning if JSON is invalid or not produced
        # This path should ideally be removed once LLM reliably produces JSON
        
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
            "gate"
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
                if any(term in lower_sentence for term in ["synthesis", "conflict", "reconciliation", "reconcil", "premise", "boundary"]):
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
        
        branches_generated = self._count_branches(raw_llm_output) # Count from raw output
        branches_retained = self._count_branches("\n".join(grounded_sentences).strip()) # Count from cleaned text
        
        if grounded_sentences:
            return " ".join(grounded_sentences).strip(), branches_generated, branches_retained

        # If no grounded sentences, try a more minimal cleaning
        compressed = self._remove_generic_phrases(cleaned).strip()
        if not compressed:
            compressed = "Evidence remains insufficient for a compressed market theory."
        
        branches_generated = self._count_branches(raw_llm_output)
        branches_retained = self._count_branches(compressed)
        return compressed, branches_generated, branches_retained

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
        patterns = [r"(?:^|\n|\. |; )\s*if\b", r"(?:^|\n|\. |; )\s*else\s+if\b", r"(?:^|\n|\. |; )\s*else\b"]

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

    def _count_branches_from_dict(self, theory_dict: Dict[str, str]) -> int:
        """Count branches from a structured theory dictionary."""
        count = 0
        if theory_dict.get("if_branch"): count += 1
        if theory_dict.get("else_branch"): count += 1
        if theory_dict.get("unless"): count += 1
        return count
