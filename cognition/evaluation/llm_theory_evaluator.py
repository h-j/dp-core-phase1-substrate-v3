import json
from typing import Dict
from cognition.schemas.theory.theory import Theory # Import Theory Pydantic model
from interfaces.ollama_client import OllamaClient

class LLMTheoryEvaluator:
    """Probabilistic evaluator for mechanistic depth and logic."""
    
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
        thesis = theory_obj.thesis # Always available
        
        # Handle cases where summary_structured might be None due to validation errors
        if theory_obj.summary_structured:
            summary_structured_json = theory_obj.summary_structured.model_dump_json()
        else:
            # If structured data is missing, provide a placeholder or indicate it's unstructured
            # This allows the LLM to still provide some evaluation based on the thesis
            summary_structured_json = json.dumps({"error": "Structured summary missing or invalid", "claim": theory_obj.summary})
            
        
        prompt = self.PROMPT_TEMPLATE.format(
            thesis=thesis,
            summary_structured=summary_structured_json
        )
        
        result = self.client.generate(prompt)
        try:
            # Robust JSON extraction
            json_start = result.find('{')
            json_end = result.rfind('}')
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON object found in LLM response")
            
            cleaned = result[json_start:json_end+1]
            # Remove potential markdown block markers if they were inside the extract
            cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned)
        except Exception as e:
            return {
                "overall_score": 0.0,
                "error": str(e),
                "raw": result[:100]
            }