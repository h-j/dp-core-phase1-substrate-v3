"""
Attribution Engine: Determines WHY a theory succeeded or failed.
"""

from typing import Any, Dict, List, Optional
from flows.theory_flow.attribution import AttributionResult, MechanismComponent


class AttributionEngine:
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def attribute(
        self,
        theory: Any,
        prediction: str,
        observation: Any,
        market_context: Optional[Dict[str, Any]] = None,
    ) -> AttributionResult:
        theory_dict = (
            theory.summary_structured.model_dump()
            if hasattr(theory, "summary_structured") and theory.summary_structured
            else {}
        )
        components = [
            MechanismComponent.from_dict(c)
            for c in theory_dict.get("mechanism_components", [])
        ]

        passed, failed = [], []
        obs_text = getattr(observation, "observation_text", "").lower()
        for c in components:
            if c.dependency and c.dependency in failed:
                failed.append(c.component_id)
                continue
            # Basic heuristic: check if expected behavior is contradicted in text
            if "higher" in c.expected_behavior.lower() and "lower" in obs_text:
                failed.append(c.component_id)
            else:
                passed.append(c.component_id)

        outcome = (
            "falsified"
            if (failed and len(failed) == len(components))
            else "validated" if not failed else "partial"
        )

        attribution = AttributionResult(
            theory_id=str(getattr(theory, "id", "unknown")),
            theory_claim=theory_dict.get("claim", ""),
            outcome=outcome,
            components_tested=[c.component_id for c in components],
            components_passed=passed,
            components_failed=failed,
            expected_outcome=prediction,
            actual_outcome=obs_text,
            root_cause_component=failed[0] if failed else None,
            attribution_confidence=0.7,
        )

        if failed and self.llm:
            prompt = f"Explain why theory '{attribution.theory_claim}' failed given obs: {attribution.actual_outcome}. Failed: {failed}."
            try:
                attribution.attribution_reasoning = self.llm.generate(prompt)
            except:
                attribution.attribution_reasoning = "Causal narrative unavailable."

        return attribution
