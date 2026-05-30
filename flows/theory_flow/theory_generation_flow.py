import re
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
    ) -> Theory:

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

        prompt = f"""
Market Memory:
{market_memory_context}

Current Market Observation:
{current_market_observation}

The current market regime subtype is: {regime_subtype}.
Analog Divergence: {analog_divergence_claim or "None"}
{falsifiability_text}

{history_text_for_prompt}

Reflective Memory Summary:
{reflective_memory_summary}

Historical Cognition:
{historical_context}

Current Abstraction:
{abstraction.abstraction_summary}

Generate:
- one compressed theory, 2-4 sentences
- direct grounding in the observation and abstraction above
- narrow claim over broad narrative
- falsifiable interpretation that future observations could contradict
- preserve ambiguity where evidence is weak
- explicitly name unresolved tension if the evidence contains tension
- focus on market structure, coherence, uncertainty, volatility, breadth, participation, liquidity, and regime evolution
- if generating theory for same regime subtype as prior theories, explicitly reference continuity or divergence
- anchor claims to the specific falsifiability conditions above
- start the theory by explicitly stating the current regime subtype, unless it is 'neutral'
- avoid broad macro explanations, generic financial commentary, and smooth storytelling
- avoid causal certainty unless the supplied evidence directly supports it
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

Bad style:
The market demonstrates stable growth due to investor confidence.
Participants are optimistic and stability is likely to continue.
"""

        result = self.client.generate(prompt)
        theory_text = self._clean_theory(result)

        print("[Theory Summary Debug]", theory_text)

        return Theory(
            lineage_id=str(uuid4()),
            thesis=theory_text,
            summary=theory_text,
            assumptions=[],
            confidence_state=ConfidenceState(),
            # v3.0 Regime-based continuity
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
        )

    def _clean_theory(self, theory_text: str) -> str:

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

        for line in theory_text.splitlines():
            cleaned_line = line.strip().strip("*").strip("#").strip()

            if not cleaned_line:
                continue

            lower_line = cleaned_line.lower().rstrip(":")

            if any(phrase in lower_line for phrase in blocked_phrases):
                continue

            lines.append(cleaned_line)

        cleaned = " ".join(lines)

        for source, replacement in replacements.items():
            cleaned = re.sub(
                re.escape(source), replacement, cleaned, flags=re.IGNORECASE
            )

        cleaned = re.sub(r"\*\*[^*]+:\*\*", "", cleaned)
        cleaned = re.sub(
            r"\b(Concise Reflection|Momentum Behavior Theory|Note):", "", cleaned
        )
        cleaned = cleaned.replace("**", "")
        cleaned = re.sub(r"\s+", " ", cleaned)

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

        if grounded_sentences:
            return " ".join(grounded_sentences[:4]).strip()

        compressed = self._remove_generic_phrases(cleaned).strip()
        if not compressed:
            return "Evidence remains insufficient for a compressed market theory."
        return compressed

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
