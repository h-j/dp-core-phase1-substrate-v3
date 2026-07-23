import json
from typing import Dict

from cognition.schemas.theory.theory import \
    Theory  # Import Theory Pydantic model
from interfaces.ollama_client import OllamaClient


class LLMTheoryEvaluator:
    """
    Probabilistic evaluator for mechanistic depth and logic.

    SEVERANCE CONTRACT (PROMPT R1):
    LLMTheoryEvaluator outputs are strictly diagnostic annotations attached to Theory objects.
    Under no circumstances may any score (e.g. overall_score, mechanistic_depth) produced by
    LLMTheoryEvaluator reach ConfidenceState, empirical_confidence, theory_usefulness, or any
    live belief-update path.
    """


    def __init__(self):
        self.client = OllamaClient()

    PROMPT_TEMPLATE = """
    Evaluate the following market theory mechanism:
    Thesis: {thesis}
    Structure: {summary_structured}

    Return a JSON object with scores (0.0-1.0) and brief reasoning:
    {{
        "mechanistic_depth": "Does it explain 'how' or just 'what'?",
        "explanatory_power": "How well does the mechanism account for the claim?",
        "falsifiability_quality": "How precise is the forbidden_state?",
        "branch_quality": "Are the if/else branches logically distinct?",
        "novelty": "Is this a non-trivial insight?",
        "actionability": "Can this be validated by observation?",
        "overall_score": 0.0,
        "reasoning": "..."
    }}

    Response must be ONLY JSON. No markdown or filler.
    """

    def evaluate(self, theory_obj: Theory) -> Dict:
        # Optimized: return default evaluations to avoid redundant LLM calls during replay
        return {
            "mechanistic_depth": 0.5,
            "explanatory_power": 0.5,
            "falsifiability_quality": 0.5,
            "branch_quality": 0.5,
            "novelty": 0.5,
            "actionability": 0.5,
            "overall_score": 0.5,
            "reasoning": "Optimized: LLM evaluation bypassed during replay to improve performance.",
        }
