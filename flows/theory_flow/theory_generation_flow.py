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
    ) -> Theory:

        prompt = f"""
Market Memory:
{market_memory_context}

Current Market Observation:
{current_market_observation}

Reflective Memory Summary:
{reflective_memory_summary}

Historical Cognition:
{historical_context}

Current Abstraction:
{abstraction.abstraction_summary}

Generate:
- one compressed theory, 1-3 sentences
- direct grounding in the observation and abstraction above
- narrow claim over broad narrative
- falsifiable interpretation that future observations could contradict
- preserve ambiguity where evidence is weak
- explicitly name unresolved tension if the evidence contains tension
- focus on market structure, coherence, uncertainty, volatility, breadth, participation, liquidity, and regime evolution
- avoid broad macro explanations, generic financial commentary, and smooth storytelling
- avoid causal certainty unless the supplied evidence directly supports it
- avoid semantic filler and opening phrases
- avoid repeating prior theories blindly; use prior validations/reflections only as constraints
- do not produce trading recommendations
- do not mention buy, sell, returns, profit, trading signals, or investment advice
- do not use headings
- no markdown

Good style:
Continuation remains weakly supported under compressed volatility.
Observed stability may weaken if participation deteriorates.

Bad style:
The market demonstrates stable growth due to investor confidence.
Participants are optimistic and stability is likely to continue.
"""

        result = self.client.generate(prompt)
        theory_text = self._clean_theory(result)

        return Theory(
            lineage_id=str(uuid4()),
            thesis=theory_text,
            summary=theory_text,
            assumptions=[],
            confidence_state=ConfidenceState(),
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
            return " ".join(grounded_sentences[:3]).strip()

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
