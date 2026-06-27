import json

from cognition.schemas.theory.theory import \
    Theory  # Import Theory Pydantic model
from interfaces.ollama_client import OllamaClient


class LLMContradictionAuditor:
    """Probabilistic Auditor to resolve semantic synonym conflicts."""

    def __init__(self):
        self.client = OllamaClient()

    def audit_conflict(self, theory_a, theory_b):
        """
        Inputs: Two theory objects.
        Logic: Asks LLM if the mechanisms are mutually exclusive or just using different language.
        """
        summary_a = (
            theory_a.summary_structured.claim
            if theory_a.summary_structured
            else theory_a.summary
        )
        summary_b = (
            theory_b.summary_structured.claim
            if theory_b.summary_structured
            else theory_b.summary
        )

        prompt = f"""
        Audit the logical relationship between these two market theories:
        
        Theory A: {summary_a}
        Theory B: {summary_b}

        Are these compatible (can both be true), competing (different paths to same outcome), or contradictory (mutually exclusive mechanisms)?

        Return ONLY JSON:
        {{
            "relationship": "compatible" | "competing" | "contradictory",
            "confidence": 0.0-1.0,
            "reasoning": "..."
        }}
        """

        result = self.client.generate(prompt, json_format=True)
        try:
            cleaned = result.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except Exception:
            return {
                "relationship": "unknown",
                "confidence": 0.0,
                "reasoning": result[:200],
            }
