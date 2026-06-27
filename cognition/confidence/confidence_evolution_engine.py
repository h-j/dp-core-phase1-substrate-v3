from statistics import mean
from typing import Any, Dict, List, Optional


class ConfidenceEvolutionEngine:
    def evolve(
        self,
        confidence_state,
        validation,
        reflection,
        contradiction_result,
        market_observation=None,
        recent_validations=None,
        outcome_validation_result=None,
        lineage_event=None,
        theory_usefulness: Optional[Dict[str, Any]] = None,
        regime_matches: Optional[List[Any]] = None,
        rolling_accuracy: float = 0.5,   # Recent 15-day accuracy
        regime_accuracy: float = 0.5,    # Regime-specific rolling accuracy
        lifetime_accuracy: float = 0.5,  # Lifetime overall accuracy
    ):

        recent_validations = recent_validations or []
        lineage_event = lineage_event or {}

        empirical_delta = 0.0
        regime_delta = 0.0
        reflection_delta = 0.0
        coherence_delta = 0.0
        pressure_delta = 0.0

        new_contradictions = int(contradiction_result.get("new_contradictions", 0))
        resolved_contradictions = int(
            contradiction_result.get("resolved_contradictions", 0)
        )
        active_contradictions = int(
            contradiction_result.get("active_contradictions", 0)
        )
        mutated = int(lineage_event.get("mutated", 0))
        merged = int(lineage_event.get("merged", 0))

        if outcome_validation_result:
            outcome_alignment = outcome_validation_result.get("validation_score", 0.5)
            if outcome_alignment > 0.7:
                empirical_delta += 0.08
                regime_delta += 0.04
                coherence_delta += 0.03
            elif outcome_alignment > 0.4:
                empirical_delta += 0.02
                regime_delta += 0.01
            else:
                empirical_delta -= 0.09
                coherence_delta -= 0.06
                pressure_delta += 0.08

            outcome_contradictions = outcome_validation_result.get(
                "contradictions_detected", []
            )
            if outcome_contradictions:
                pressure_delta += len(outcome_contradictions) * 0.06
                coherence_delta -= len(outcome_contradictions) * 0.03

            regime_mismatch = outcome_validation_result.get("regime_mismatch", 0.0)
            if regime_mismatch > 0.5:
                regime_delta -= 0.04
                coherence_delta -= 0.03

        # v2.7: Weighting Theory Usefulness and Regime Stability (Target: corr > 0.2)
        if theory_usefulness:
            use_score = theory_usefulness.get("score", 0.0)
            if use_score > 0.6:
                empirical_delta += 0.08
                coherence_delta += 0.05
            elif use_score < 0.3:
                empirical_delta -= 0.12
                coherence_delta -= 0.10

        if regime_matches:
            try:
                sims = [
                    m.similarity if hasattr(m, "similarity") else m.get("similarity", 0)
                    for m in regime_matches
                ]
                avg_sim = mean(sims) if sims else 0.0
                if avg_sim > 0.75:
                    regime_delta += 0.06
                elif avg_sim < 0.4:
                    regime_delta -= 0.04
            except Exception:
                pass

        if self._validation_aligns(validation):
            # v2.7: Dampened narrative-only validation (0.06 -> 0.03)
            empirical_delta += 0.03
        else:
            empirical_delta -= 0.08
            coherence_delta -= 0.05
            pressure_delta += 0.10

        if self._repeated_support(validation, recent_validations):
            empirical_delta += 0.05
            regime_delta += 0.03

        reflection_text = reflection.reflection_summary.lower()
        if self._contains_any(
            reflection_text,
            [
                "strengthen",
                "support",
                "supported",
                "evidence",
                "align",
                "consistent",
            ],
        ):
            # v2.7: Dampened reflection keyword weight (0.05 -> 0.02)
            reflection_delta += 0.02

        if self._contains_any(
            reflection_text,
            [
                "uncertain",
                "uncertainty",
                "caution",
                "mixed",
                "limited",
                "contradict",
                "conflict",
                "overconfidence",
            ],
        ):
            reflection_delta -= 0.03
            pressure_delta += 0.08

        if new_contradictions > 0:
            pressure_delta += 0.14 * new_contradictions

        if active_contradictions > 0:
            pressure_delta += 0.09 * active_contradictions

        if resolved_contradictions > 0:
            empirical_delta += 0.08 * resolved_contradictions
            pressure_delta -= 0.07 * resolved_contradictions

        if market_observation is not None:
            candle_type = getattr(market_observation, "candle_type", "")
            participation_confirmation = getattr(
                market_observation, "participation_confirmation", ""
            )
            participation_strength = getattr(
                market_observation, "participation_strength", ""
            )
            contradiction_markers = getattr(
                market_observation, "contradiction_markers", []
            )

            if candle_type in [
                "strong_bull",
                "strong_bear",
            ] and participation_confirmation in [
                "bullish_confirmed",
                "bearish_confirmed",
            ]:
                empirical_delta += 0.04
                regime_delta += 0.02

            if participation_confirmation == "divergence":
                empirical_delta -= 0.05
                pressure_delta += 0.06

            if candle_type == "indecision":
                reflection_delta -= 0.04
                pressure_delta += 0.05

            if participation_strength == "weak":
                pressure_delta += 0.03

            if "price_participation_divergence" in contradiction_markers:
                pressure_delta += 0.04

        if mutated > 0:
            empirical_delta -= 0.05 * mutated
            pressure_delta += 0.08 * mutated

        if merged > 0:
            empirical_delta += 0.03 * merged

        contradiction_score = contradiction_result.get("score", 0.0)
        if contradiction_score > 0:
            pressure_delta += contradiction_score * 0.10
        # 1. Three-Window Confidence: blend regime-specific, recent, and lifetime accuracies
        # (Weighting: 50% regime, 30% recent, 20% lifetime)
        weighted_accuracy = 0.5 * regime_accuracy + 0.3 * rolling_accuracy + 0.2 * lifetime_accuracy

        # 2. Rich Prior probability P(Theory): Theory prior confidence + Lineage usefulness + Regime matches
        lineage_usefulness_val = theory_usefulness.get("score", 0.5) if theory_usefulness else 0.5
        regime_sim = 0.5
        if regime_matches:
            try:
                sims = [
                    m.similarity if hasattr(m, "similarity") else m.get("similarity", 0)
                    for m in regime_matches
                ]
                regime_sim = mean(sims) if sims else 0.5
            except Exception:
                pass
        
        prior_probability = 0.5 * confidence_state.empirical_confidence + 0.3 * lineage_usefulness_val + 0.2 * regime_sim

        # 3. Bayesian calibration multipliers
        # Normalizes pos_mult and neg_mult around a baseline of 0.25 (which is 0.5 * 0.5)
        pos_mult = (weighted_accuracy * prior_probability) / 0.25
        neg_mult = ((1.0 - weighted_accuracy) * (1.0 - prior_probability)) / 0.25

        # Clamp multipliers to a safe range [0.1, 3.0] to prevent underflow/overflow
        pos_mult = max(0.1, min(3.0, pos_mult))
        neg_mult = max(0.1, min(3.0, neg_mult))
        if empirical_delta > 0:
            empirical_delta *= pos_mult
        else:
            empirical_delta *= neg_mult

        if regime_delta > 0:
            regime_delta *= pos_mult
        else:
            regime_delta *= neg_mult

        if reflection_delta > 0:
            reflection_delta *= pos_mult
        else:
            reflection_delta *= neg_mult

        if coherence_delta > 0:
            coherence_delta *= pos_mult
        else:
            coherence_delta *= neg_mult

        if pressure_delta > 0:
            pressure_delta *= neg_mult
        else:
            pressure_delta *= pos_mult

        confidence_state.empirical_confidence = self._clamp(
            confidence_state.empirical_confidence + empirical_delta
        )
        confidence_state.regime_confidence = self._clamp(
            confidence_state.regime_confidence + regime_delta
        )
        confidence_state.reflection_confidence = self._clamp(
            confidence_state.reflection_confidence + reflection_delta
        )
        confidence_state.contradiction_pressure = self._clamp(
            confidence_state.contradiction_pressure + pressure_delta
        )
        confidence_state.theoretical_coherence = self._clamp(
            confidence_state.theoretical_coherence
            + coherence_delta
            - confidence_state.contradiction_pressure * 0.04
        )

        return confidence_state

    def _validation_aligns(self, validation) -> bool:

        observed = validation.observed_behavior.lower()
        expected = validation.expected_behavior.lower()

        if self._contains_any(
            observed, ["failed", "weakened", "declined", "opposite", "did not"]
        ):
            return False

        if "strengthen" in expected and "increased" in observed:
            return True

        if "increase" in expected and "increased" in observed:
            return True

        if "weaken" in expected and "decreased" in observed:
            return True

        return self._contains_any(
            validation.validation_summary.lower(),
            ["showed", "supported", "aligned", "confirmed"],
        )

    def _repeated_support(self, validation, recent_validations) -> bool:

        current_summary = validation.validation_summary.lower()
        support_count = 0

        for recent_validation in recent_validations:
            recent_summary = recent_validation.validation_summary.lower()

            if recent_validation.id == validation.id:
                continue

            if current_summary == recent_summary:
                support_count += 1
                continue

            if "liquidity" in current_summary and "liquidity" in recent_summary:
                if "momentum" in current_summary or "trend" in current_summary:
                    support_count += 1

        return support_count >= 1

    def _contains_any(self, text: str, phrases: List[str]) -> bool:

        return any(phrase in text for phrase in phrases)

    def _clamp(self, value: float) -> float:

        return max(0.0, min(1.0, round(value, 4)))
