from typing import List
class ContradictionDetector:

    def detect(
        self,
        current_theory,
        historical_theories,
        validations,
        reflections,
        current_observation=None,
        historical_observations=None,
    ):

        indicators = []
        severity_weights = []

        current_text = current_theory.summary.lower()
        historical_texts = [
            theory.summary.lower()
            for theory in historical_theories
            if theory.id != current_theory.id
        ]
        historical_observations = historical_observations or []
        validation_texts = [
            self._validation_text(validation) for validation in validations
        ]
        reflection_texts = [
            reflection.reflection_summary.lower() for reflection in reflections
        ]

        self._detect_directional_conflicts(
            current_text, historical_texts, indicators, severity_weights
        )
        self._detect_observation_transitions(
            current_observation,
            historical_observations,
            indicators,
            severity_weights,
        )
        self._detect_validation_failures(validation_texts, indicators, severity_weights)
        self._detect_uncertainty(reflection_texts, indicators, severity_weights)
        self._detect_momentum_liquidity_conflicts(
            current_text, historical_texts, indicators, severity_weights
        )

        score = min(1.0, round(sum(severity_weights), 4))

        if indicators:
            summary = "; ".join(indicators)
        else:
            summary = "No explicit contradictions detected."

        return {
            "score": score,
            "summary": summary,
            "indicators": indicators,
            "contradictions": indicators,
        }

    def _detect_directional_conflicts(
        self, current_text, historical_texts, indicators, severity_weights
    ):

        current_positive = self._contains_any(
            current_text, ["strengthen", "increased", "stronger", "excel", "thrive"]
        )
        current_negative = self._contains_any(
            current_text, ["weaken", "decreased", "weaker", "struggle", "underperform"]
        )

        for historical_text in historical_texts:
            historical_positive = self._contains_any(
                historical_text,
                ["strengthen", "increased", "stronger", "excel", "thrive"],
            )
            historical_negative = self._contains_any(
                historical_text,
                ["weaken", "decreased", "weaker", "struggle", "underperform"],
            )

            if current_positive and historical_negative:
                indicators.append(
                    "Current theory strengthens a relationship that prior "
                    "theory weakened."
                )
                severity_weights.append(0.31)
                return

            if current_negative and historical_positive:
                indicators.append(
                    "Current theory weakens a relationship that prior "
                    "theory strengthened."
                )
                severity_weights.append(0.31)
                return

    def _detect_observation_transitions(
        self,
        current_observation,
        historical_observations,
        indicators,
        severity_weights,
    ):
        if not current_observation or not historical_observations:
            return

        prior_observation = historical_observations[-1]
        current_trend = getattr(current_observation, "trend_state", "")
        prior_trend = getattr(prior_observation, "trend_state", "")
        current_breadth = getattr(current_observation, "breadth_state", "")
        prior_breadth = getattr(prior_observation, "breadth_state", "")

        if prior_trend == "closed_lower" and current_trend == "range_bound":
            indicators.append("Trend contradiction: closed_lower moved to range_bound.")
            severity_weights.append(0.18)

        if prior_trend == "range_bound" and current_trend == "extended_higher":
            indicators.append(
                "Trend contradiction: range_bound moved to extended_higher."
            )
            severity_weights.append(0.42)

        if prior_breadth in {
            "strengthened",
            "strongly_participatory",
        } and current_breadth in {"weakened", "deteriorated"}:
            indicators.append("Breadth contradiction: prior strength weakened.")
            severity_weights.append(0.31)

    def _detect_validation_failures(
        self, validation_texts, indicators, severity_weights
    ):

        failure_phrases = [
            "failed",
            "did not",
            "opposite",
            "weakened",
            "decreased",
            "invalidated",
            "conflicted",
        ]

        for validation_text in validation_texts:
            if self._contains_any(validation_text, failure_phrases):
                indicators.append("Recent validation contains failure signal.")
                severity_weights.append(0.18)
                return

    def _detect_uncertainty(self, reflection_texts, indicators, severity_weights):

        uncertainty_phrases = [
            "uncertain",
            "uncertainty",
            "mixed",
            "limited",
            "caution",
            "overconfidence",
            "contradictory",
        ]

        for reflection_text in reflection_texts:
            if self._contains_any(reflection_text, uncertainty_phrases):
                indicators.append(
                    "Recent reflection contains uncertainty or caution signal."
                )
                severity_weights.append(0.18)
                return

    def _detect_momentum_liquidity_conflicts(
        self, current_text, historical_texts, indicators, severity_weights
    ):

        if "momentum" not in current_text or "liquidity" not in current_text:
            return

        current_supports = self._contains_any(
            current_text, ["strengthen", "stronger", "excel", "thrive", "persistence"]
        )
        current_rejects = self._contains_any(
            current_text, ["weaken", "weaker", "struggle", "underperform", "breakdown"]
        )

        for historical_text in historical_texts:
            if "momentum" not in historical_text:
                continue

            if "liquidity" not in historical_text:
                continue

            historical_supports = self._contains_any(
                historical_text,
                ["strengthen", "stronger", "excel", "thrive", "persistence"],
            )
            historical_rejects = self._contains_any(
                historical_text,
                ["weaken", "weaker", "struggle", "underperform", "breakdown"],
            )

            if current_supports and historical_rejects:
                indicators.append(
                    "Momentum/liquidity conclusion conflicts with prior "
                    "negative conclusion."
                )
                severity_weights.append(0.31)
                return

            if current_rejects and historical_supports:
                indicators.append(
                    "Momentum/liquidity conclusion conflicts with prior "
                    "positive conclusion."
                )
                severity_weights.append(0.31)
                return

    def _validation_text(self, validation) -> str:

        return " ".join(
            [
                validation.validation_summary,
                validation.observed_behavior,
                validation.expected_behavior,
            ]
        ).lower()

    def _contains_any(self, text: str, phrases: List[str]) -> bool:

        return any(phrase in text for phrase in phrases)
