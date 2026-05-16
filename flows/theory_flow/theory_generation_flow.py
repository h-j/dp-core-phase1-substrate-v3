from uuid import uuid4

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.theory.theory import Theory
from interfaces.ollama_client import OllamaClient


class TheoryGenerationFlow:

    def __init__(self):

        self.client = OllamaClient()

    def process(self, abstraction, historical_context: str = "") -> Theory:

        prompt = f'''
Historical Cognition:
{historical_context}

Current Abstraction:
{abstraction.abstraction_summary}

Generate:
- concise theory
- epistemically grounded theory
- avoid repeating prior theories blindly
- consider prior validations/reflections
- no markdown
'''

        result = self.client.generate(prompt)

        return Theory(
            lineage_id=str(uuid4()),
            thesis=result.strip(),
            summary=result.strip(),
            assumptions=[],
            confidence_state=ConfidenceState()
        )
