from typing import Any, List, Optional


class CognitionPipeline:
    """Encapsulates the sequential execution of LLM-based cognition flows."""

    def __init__(self, flows: dict):
        self.abstraction_flow = flows["abstraction"]
        self.theory_flow = flows["theory"]
        self.reflection_flow = flows["reflection"]
        self.contradiction_detector = flows["contradiction"]

    def process(
        self,
        obs_event: Any,
        market_obs: Any,
        historical_context: str,
        regime_context: str,
        horizon_context: str,
        regime_subtype: str,
        falsifiability_conditions: List[str],
        regime_history: Any,
        active_synthesis: Optional[str],
        recent_theories: List[Any],
        recent_validations: List[Any],
        recent_reflections: List[Any],
        prior_market_obs: List[Any],
        relevant_lessons: List[str] = None,
    ):
        # 1. Abstraction
        abstraction = self.abstraction_flow.process(obs_event)

        # 2. Theory
        theory, branch_stats = self.theory_flow.process(
            abstraction,
            historical_context=historical_context,
            market_memory_context=regime_context,
            current_market_observation=market_obs.observation_text,
            reflective_memory_summary=horizon_context,
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
            analog_divergence_claim=getattr(market_obs, "analog_divergence_claim", ""),
            regime_history=regime_history,
            dialectical_synthesis=active_synthesis,
            relevant_lessons=relevant_lessons,
        )

        # 3. Contradiction
        contradiction_result = self.contradiction_detector.detect(
            current_theory=theory,
            historical_theories=recent_theories,
            validations=recent_validations,
            reflections=recent_reflections,
            current_observation=market_obs,
            historical_observations=prior_market_obs,
        )

        return abstraction, theory, contradiction_result, branch_stats
