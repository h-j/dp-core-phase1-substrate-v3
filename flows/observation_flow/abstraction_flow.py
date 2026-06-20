from cognition.schemas.abstraction.abstraction_unit import AbstractionUnit
from interfaces.ollama_client import OllamaClient


class AbstractionFlow:

    def __init__(self):

        self.client = OllamaClient()

    def process(self, observation) -> AbstractionUnit:

        prompt = f"""
Convert the market observation into a concise abstraction.

Observation:
{observation.raw_content}

Return:
- concise abstraction
- no markdown
"""

        result = self.client.generate(prompt)

        return AbstractionUnit(
            source_observation_id=observation.id,
            abstraction_summary=result.strip(),
            concepts=[],
        )
