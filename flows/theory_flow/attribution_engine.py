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

        # Determine actual direction from observation
        trend = ""
        if hasattr(observation, "trend_state") and getattr(observation, "trend_state"):
            trend = getattr(observation, "trend_state", "").lower()
        else:
            trend = obs_text

        actual_direction = "uncertain"
        if "range_bound" in trend:
            actual_direction = "range_bound"
        elif any(word in trend for word in ["higher", "up", "extended_higher", "recovered_intraday"]):
            actual_direction = "higher"
        elif any(word in trend for word in ["lower", "down", "closed_lower"]):
            actual_direction = "lower"

        OPPOSITES = [
            ("higher", "lower"),
            ("up", "down"),
            ("increase", "decrease"),
            ("expansion", "contraction"),
            ("bullish", "bearish"),
            ("above", "below"),
            ("exceed", "below"),
            ("growth", "decline"),
            ("rising", "falling"),
            ("gains", "losses"),
            ("expansion", "compression"),
            ("expansion", "flat"),
        ]

        for c in components:
            if c.dependency and c.dependency in failed:
                failed.append(c.component_id)
                continue

            exp_lowered = c.expected_behavior.lower()
            is_failed = False

            # 1. Opposites heuristic (only triggers if one opposite is present in expected, but not both)
            for word_a, word_b in OPPOSITES:
                if (word_a in exp_lowered) != (word_b in exp_lowered):
                    if word_a in exp_lowered and word_b in obs_text:
                        is_failed = True
                        break
                    if word_b in exp_lowered and word_a in obs_text:
                        is_failed = True
                        break

            # 2. Prediction failure alignment
            if not is_failed and actual_direction != "uncertain" and prediction != "uncertain" and actual_direction != prediction:
                if prediction == "higher" and any(w in exp_lowered for w in ["higher", "up", "bullish", "expansion", "increase"]):
                    is_failed = True
                elif prediction == "lower" and any(w in exp_lowered for w in ["lower", "down", "bearish", "contraction", "decrease"]):
                    is_failed = True
                elif prediction == "range_bound" and any(w in exp_lowered for w in ["range", "flat", "compress", "absorb", "limit"]):
                    is_failed = True

            if is_failed:
                failed.append(c.component_id)
            else:
                passed.append(c.component_id)

        # 3. Fallback when prediction failed but no component flagged
        if not failed and actual_direction != "uncertain" and prediction != "uncertain" and actual_direction != prediction and components:
            fallback_idx = 0
            for i, c in enumerate(components):
                c_id_lower = c.component_id.lower()
                if any(w in c_id_lower for w in ["price", "trend", "momentum", "direction", "move"]):
                    fallback_idx = i
                    break
            failed.append(components[fallback_idx].component_id)

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
