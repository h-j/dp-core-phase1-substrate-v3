import re

from cognition.schemas.reflection.reflection_event import ReflectionEvent
from interfaces.ollama_client import OllamaClient


class ReflectionFlow:

    def __init__(self):

        self.client = OllamaClient()

    def process(self, theory, validation, contradiction_result=None) -> ReflectionEvent:
        contradiction_result = contradiction_result or {}
        contradiction_summary = contradiction_result.get(
            "summary", "No explicit contradiction detected."
        )
        contradiction_indicators = contradiction_result.get("indicators", [])

        prompt = f"""
Reflect on the following theory validation.

Theory:
{theory.summary}

Contradiction:
{contradiction_summary}
{'; '.join(contradiction_indicators)}

Validation:
{validation.validation_summary}

Return:
- compressed critique, 1-3 sentences
- reference the actual theory
- reference the actual contradiction
- identify one unresolved tension
- identify what remains weak, untested, ambiguous, or contradicted
- preserve unresolved tension instead of resolving it rhetorically
- evaluate uncertainty and confidence pressure directly
- avoid overconfidence, reinforcement bias, and self-congratulation
- avoid generic philosophical language or broad market commentary
- prefer falsifiable weakness statements over praise
- maximum 3 sentences
- do not praise the theory, prompt, or validation process
- do not use headings or numbered sections
- no markdown

Good style:
Observed continuation remains insufficiently tested under volatility expansion.

Bad style:
This theory appears insightful and coherent.
"""

        result = self.client.generate(prompt)
        reflection_summary = self._clean_reflection(
            result,
            theory_text=theory.summary,
            contradiction_summary=contradiction_summary,
        )

        return ReflectionEvent(
            related_theory_id=theory.id,
            reflection_summary=reflection_summary,
            confidence_impact="moderate",
        )

    def _clean_reflection(
        self,
        reflection: str,
        theory_text: str = "",
        contradiction_summary: str = "",
    ) -> str:

        blocked_phrases = [
            "well-crafted",
            "well done",
            "what a",
            "strengths",
            "suggestions",
            "overall",
            "here's",
            "here is",
            "well-executed",
            "insightful and coherent",
            "viable framework",
            "epistemic humility",
            "market dynamics are inherently complex",
            "embracing uncertainty",
            "provided validation",
            "validation attempt",
            "good-style critique",
            "good style",
            "bad style",
            "requested",
            "prompt",
            "this approach",
            "a more effective approach",
        ]
        generic_patterns = [
            r"\bthis theory appears\b",
            r"\bthis indicates that\b",
            r"\bthe validation suggests that it may be\b",
            r"\bfinancial markets\b",
            r"\bthe provided validation\b",
            r"\bthe critique should\b",
            r"\ba good-style critique\b",
        ]
        lines = []

        for line in reflection.splitlines():
            cleaned_line = line.strip().strip("*").strip("#").strip()

            if not cleaned_line:
                continue

            lower_line = cleaned_line.lower()

            if any(phrase in lower_line for phrase in blocked_phrases):
                continue

            if any(re.search(pattern, lower_line) for pattern in generic_patterns):
                continue

            if lower_line[:2] in ["1.", "2.", "3.", "4."]:
                continue

            lines.append(cleaned_line)

        cleaned = " ".join(lines)
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
            if sentence.strip()
        ]

        if not sentences:
            return self._fallback_reflection(theory_text, contradiction_summary)

        compressed = " ".join(sentences[:3])
        if compressed[-1:] not in [".", "!", "?"]:
            compressed = compressed + "."
        if not self._is_grounded_reflection(
            compressed,
            theory_text=theory_text,
            contradiction_summary=contradiction_summary,
        ):
            return self._fallback_reflection(theory_text, contradiction_summary)
        return compressed

    def _is_grounded_reflection(
        self,
        reflection: str,
        theory_text: str,
        contradiction_summary: str,
    ) -> bool:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", reflection)
            if sentence.strip()
        ]
        if not 1 <= len(sentences) <= 3:
            return False

        lower_reflection = reflection.lower()
        meta_terms = [
            "prompt",
            "validation process",
            "provided validation",
            "good-style",
            "this critique",
            "the critique",
        ]
        if any(term in lower_reflection for term in meta_terms):
            return False

        theory_terms = self._salient_terms(theory_text)
        contradiction_terms = self._salient_terms(contradiction_summary)
        tension_terms = {
            "weak",
            "unresolved",
            "tension",
            "fragile",
            "fragility",
            "limited",
            "insufficient",
            "untested",
            "contradiction",
            "contradicted",
            "masks",
        }
        theory_grounded = any(term in lower_reflection for term in theory_terms)
        contradiction_grounded = (
            contradiction_summary.lower().startswith("no explicit")
            or any(term in lower_reflection for term in contradiction_terms)
            or "contradiction" in lower_reflection
        )
        tension_grounded = any(term in lower_reflection for term in tension_terms)
        return theory_grounded and contradiction_grounded and tension_grounded

    def _fallback_reflection(self, theory_text: str, contradiction_summary: str) -> str:
        lower_theory = theory_text.lower()
        lower_contradiction = contradiction_summary.lower()

        if "breadth" in lower_theory or "breadth" in lower_contradiction:
            return "Breadth weakness remains unresolved under contradiction pressure."
        if "volatility" in lower_theory or "volatility" in lower_contradiction:
            return "Compressed volatility masks fragility under contradiction pressure."
        if "continuation" in lower_theory:
            return "Continuation remains weakly evidenced against caution signals."
        if "participation" in lower_theory:
            return "Participation tension remains weakly evidenced against caution signals."
        if "liquidity" in lower_theory:
            return "Liquidity support remains weakly tested against contradiction pressure."
        return "Theory contradiction remains unresolved."

    def _salient_terms(self, text: str) -> set[str]:
        blocked_terms = {
            "the",
            "and",
            "that",
            "this",
            "with",
            "from",
            "current",
            "recent",
            "theory",
            "contains",
            "signal",
            "market",
        }
        return {
            term
            for term in re.findall(r"[a-z][a-z-]{4,}", text.lower())
            if term not in blocked_terms
        }
