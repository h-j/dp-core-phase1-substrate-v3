class ConfidenceEvolutionEngine:

    def evolve(
        self,
        confidence_state,
        validation,
        reflection,
        contradiction_result,
        recent_validations=None,
        outcome_validation_result=None
    ):

        recent_validations = recent_validations or []

        empirical_delta = 0.0
        regime_delta = 0.0
        reflection_delta = 0.0
        coherence_delta = 0.0
        pressure_delta = 0.0

        # Reality-based outcome validation weighs MORE heavily than linguistic validation
        if outcome_validation_result:
            outcome_alignment = outcome_validation_result.get(
                "validation_score",
                0.5
            )
            
            if outcome_alignment > 0.7:
                empirical_delta += 0.1
                regime_delta += 0.06
                coherence_delta += 0.05
            elif outcome_alignment > 0.4:
                empirical_delta += 0.02
                regime_delta += 0.01
            else:
                empirical_delta -= 0.12
                coherence_delta -= 0.08
                pressure_delta += 0.12

            # Outcome contradictions add direct contradiction pressure
            outcome_contradictions = outcome_validation_result.get(
                "contradictions_detected",
                []
            )
            if outcome_contradictions:
                pressure_delta += len(outcome_contradictions) * 0.1
                coherence_delta -= len(outcome_contradictions) * 0.05

            # Regime mismatch affects regime confidence
            regime_mismatch = outcome_validation_result.get(
                "regime_mismatch",
                0.0
            )
            if regime_mismatch > 0.5:
                regime_delta -= 0.08
                coherence_delta -= 0.05

        if self._validation_aligns(validation):
            empirical_delta += 0.05
            regime_delta += 0.03
            coherence_delta += 0.02
        else:
            empirical_delta -= 0.06
            coherence_delta -= 0.04
            pressure_delta += 0.08

        if self._repeated_support(validation, recent_validations):
            empirical_delta += 0.03
            regime_delta += 0.02

        reflection_text = reflection.reflection_summary.lower()

        if self._contains_any(
            reflection_text,
            [
                "strengthen",
                "support",
                "supported",
                "evidence",
                "align",
                "consistent"
            ]
        ):
            reflection_delta += 0.04
            coherence_delta += 0.02

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
                "overconfidence"
            ]
        ):
            reflection_delta -= 0.03
            coherence_delta -= 0.03
            pressure_delta += 0.05

        contradiction_score = contradiction_result["score"]

        if contradiction_score > 0:
            pressure_delta += contradiction_score * 0.12
            coherence_delta -= contradiction_score * 0.08

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
            observed,
            ["failed", "weakened", "declined", "opposite", "did not"]
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
            ["showed", "supported", "aligned", "confirmed"]
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

    def _contains_any(self, text: str, phrases: list[str]) -> bool:

        return any(phrase in text for phrase in phrases)

    def _clamp(self, value: float) -> float:

        return max(0.0, min(1.0, round(value, 4)))
