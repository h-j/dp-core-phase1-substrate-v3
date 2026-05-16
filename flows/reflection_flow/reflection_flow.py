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
- concise reflection
- confidence implication
- no markdown
'''

        result = self.client.generate(prompt)

        return ReflectionEvent(
            related_theory_id=theory.id,
            reflection_summary=result.strip(),
            confidence_impact="moderate"
        )
