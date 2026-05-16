from cognition.schemas.reflection.reflection_event import ReflectionEvent
from interfaces.ollama_client import OllamaClient


class ReflectionFlow:

    def __init__(self):

        self.client = OllamaClient()

    def process(self, theory, validation) -> ReflectionEvent:

        prompt = f'''
Reflect on the following theory validation.

Theory:
{theory.summary}

Validation:
{validation.validation_summary}

Return:
- short grounded reflection
- confidence implication with epistemic humility
- acknowledge uncertainty or contradictory evidence when present
- avoid overconfidence and reinforcement bias
- maximum 3 sentences
- do not praise the theory, prompt, or validation process
- do not use headings or numbered sections
- no markdown
'''

        result = self.client.generate(prompt)

        return ReflectionEvent(
            related_theory_id=theory.id,
            reflection_summary=self._clean_reflection(result),
            confidence_impact="moderate"
        )

    def _clean_reflection(self, reflection: str) -> str:

        blocked_phrases = [
            "well-crafted",
            "well done",
            "what a",
            "strengths",
            "suggestions",
            "overall",
            "here's",
            "here is",
            "well-executed"
        ]
        lines = []

        for line in reflection.splitlines():
            cleaned_line = line.strip().strip("*").strip("#").strip()

            if not cleaned_line:
                continue

            lower_line = cleaned_line.lower()

            if any(phrase in lower_line for phrase in blocked_phrases):
                continue

            if lower_line[:2] in ["1.", "2.", "3.", "4."]:
                continue

            lines.append(cleaned_line)

        cleaned = " ".join(lines)
        sentences = [
            sentence.strip()
            for sentence in cleaned.split(".")
            if sentence.strip()
        ]

        if not sentences:
            return reflection.strip()

        return ". ".join(sentences[:3]) + "."
