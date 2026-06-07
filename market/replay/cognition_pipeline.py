from typing import List, Dict, Any, Optional
from cognition.schemas.observation.observation_event import ObservationEvent
from cognition.schemas.validation.validation_event import ValidationEvent

class CognitionPipeline:
    """Encapsulates the sequence: Obs -> Abs -> Theory -> Contra -> Reflection."""
    
    def __init__(self, abstraction_flow, theory_flow, reflection_flow, contradiction_detector, dialectical_synthesizer):
        self.abstraction_flow = abstraction_flow
        self.theory_flow = theory_flow
        self.reflection_flow = reflection_flow
        self.contradiction_detector = contradiction_detector
        self.dialectical_synthesizer = dialectical_synthesizer

    def _format_historical_context(self, validations: list, reflections: list) -> str:
        validation_bits = [getattr(item, "validation_summary", "")[:120] for item in validations[:3]]
        reflection_bits = [getattr(item, "reflection_summary", "")[:120] for item in reflections[:3]]
        bits = [bit for bit in validation_bits + reflection_bits if bit]
        return " | ".join(bits)

    def _format_regime_context(self, matches: list) -> str:
        if not matches: return "Regime memory: no prior match."
        parts = []
        for match in matches[:3]:
            contradiction = f", recurring contradiction {match.recurring_contradiction}" if match.recurring_contradiction else ""
            parts.append(f"{match.date} similarity {match.similarity:.2f}, confidence {match.confidence:.2f}{contradiction}")
        return "Regime memory: " + " | ".join(parts)

    def run_cognition(
        self,
        day_idx: int,
        market_obs: Any,
        recent_theories: List[Any],
        recent_validations: List[Any],
        recent_reflections: List[Any],
        horizon_context: str,
        regime_matches: List[Any],
        prior_dialectical_synthesis: Optional[str],
        prior_dialectical_subtype: Optional[str],
        regime_history_prompt: str,
        regime_subtype: str,
        falsifiability_conditions: List[str],
        debug: bool = False
    ) -> Dict:
        """Executes the sequential cognition loop."""
        
        # 1. Observe & Abstract
        obs_event = ObservationEvent(
            source_type="replay",
            raw_content=f"{market_obs.observation_text}\n{horizon_context}"
        )
        abstraction = self.abstraction_flow.process(obs_event)

        # 2. Contextualize
        regime_context = self._format_regime_context(regime_matches)
        historical_context = self._format_historical_context(recent_validations, recent_reflections)

        # 3. Dialectical Gate
        active_synthesis = None
        if prior_dialectical_synthesis:
            max_sim = max([getattr(m, "similarity", 0.0) for m in regime_matches] + [0.0])
            if regime_subtype == prior_dialectical_subtype or max_sim > 0.8:
                active_synthesis = prior_dialectical_synthesis

        # 4. Generate Theory
        theory, branch_stats = self.theory_flow.process(
            abstraction,
            historical_context=historical_context,
            market_memory_context=regime_context,
            current_market_observation=market_obs.observation_text,
            reflective_memory_summary=horizon_context,
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
            analog_divergence_claim=getattr(market_obs, "analog_divergence_claim", ""),
            regime_history=regime_history_prompt,
            dialectical_synthesis=active_synthesis,
        )

        # 5. Detect Contradiction
        contradiction_result = self.contradiction_detector.detect(
            current_theory=theory,
            historical_theories=recent_theories,
            validations=recent_validations,
            reflections=recent_reflections,
            current_observation=market_obs,
            historical_observations=recent_theories, # Placeholder for historical market obs
        )

        # 6. Reflect
        validation = ValidationEvent(
            theory_id=theory.id,
            validation_summary=f"Replay validation. {horizon_context}. {regime_context}",
            observed_behavior=market_obs.observation_text,
            expected_behavior="Market-grounded theory",
        )
        reflection = self.reflection_flow.process(
            theory, validation, contradiction_result=contradiction_result,
            market_observation=market_obs, regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
            analog_divergence_claim=getattr(market_obs, "analog_divergence_claim", ""),
            regime_history=regime_history_prompt,
            dialectical_synthesis=self.dialectical_synthesizer.format_for_reflection(active_synthesis) if active_synthesis else None
        )

        return {"abstraction": abstraction, "theory": theory, "contradiction": contradiction_result, "reflection": reflection, "validation": validation, "branch_stats": branch_stats}