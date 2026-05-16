from uuid import uuid4

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.theory.theory import Theory
from interfaces.ollama_client import OllamaClient


class TheoryGenerationFlow:

    def __init__(self):

        self.client = OllamaClient()

    def process(self, abstraction) -> Theory:

        prompt = f'''
Generate a concise market theory.

Abstraction:
{abstraction.abstraction_summary}

Return:
- coherent market theory
- concise explanation
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
