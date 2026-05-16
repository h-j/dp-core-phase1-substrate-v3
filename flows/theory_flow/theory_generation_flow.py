from uuid import uuid4
import re

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
        reflective_memory_summary: str = ""
    ) -> Theory:

        prompt = f'''
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
- concise theory
- epistemically grounded theory
- market-grounded theory
- uncertainty-aware theory
- contradiction-sensitive theory
- focus on market structure, coherence, uncertainty, and regime evolution
- avoid repeating prior theories blindly
- consider prior validations/reflections
- do not produce trading recommendations
- do not mention buy, sell, returns, profit, trading signals, or investment advice
- do not use headings
- no markdown
'''

        result = self.client.generate(prompt)
        theory_text = self._clean_theory(result)

        return Theory(
            lineage_id=str(uuid4()),
            thesis=theory_text,
            summary=theory_text,
            assumptions=[],
            confidence_state=ConfidenceState()
        )

    def _clean_theory(self, theory_text: str) -> str:

        replacements = {
            "I've generated the requested outputs:": "",
            "I've reformatted the text into a more readable format and generated the requested outputs.": "",
            "Here they are:": "",
            "Here are the requested outputs:": "",
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
            "particularly effective": "more structurally coherent"
        }
        blocked_phrases = [
            "i'd be happy",
            "here are",
            "here is",
            "concise theory",
            "epistemically grounded theory",
            "market-grounded theory",
            "uncertainty-aware theory",
            "contradiction-sensitive theory"
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
                re.escape(source),
                replacement,
                cleaned,
                flags=re.IGNORECASE
            )

        cleaned = re.sub(
            r"\*\*[^*]+:\*\*",
            "",
            cleaned
        )
        cleaned = re.sub(
            r"\b(Concise Reflection|Momentum Behavior Theory|Note):",
            "",
            cleaned
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
            "momentum"
        ]
        blocked_terms = [
            "i've",
            "i have",
            "requested outputs",
            "here they are",
            "adopt",
            "recommend",
            "advice"
        ]

        for sentence in sentences:
            lower_sentence = sentence.lower()

            if any(term in lower_sentence for term in blocked_terms):
                continue

            if not any(term in lower_sentence for term in allowed_terms):
                continue

            grounded_sentences.append(sentence)

        if grounded_sentences:
            return " ".join(grounded_sentences[:4]).strip()

        return cleaned.strip()
