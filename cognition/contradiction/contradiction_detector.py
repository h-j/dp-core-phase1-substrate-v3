class ContradictionDetector:

    def detect(
        self,
        current_theory,
        historical_theories,
        validations,
        reflections
    ):

        indicators = []

        current_text = current_theory.summary.lower()
        historical_texts = [
            theory.summary.lower()
            for theory in historical_theories
            if theory.id != current_theory.id
        ]
        validation_texts = [
            self._validation_text(validation)
            for validation in validations
        ]
        reflection_texts = [
            reflection.reflection_summary.lower()
            for reflection in reflections
        ]

        self._detect_directional_conflicts(
            current_text,
            historical_texts,
            indicators
        )
        self._detect_validation_failures(validation_texts, indicators)
        self._detect_uncertainty(reflection_texts, indicators)
        self._detect_momentum_liquidity_conflicts(
            current_text,
            historical_texts,
            indicators
        )

        score = min(1.0, round(len(indicators) * 0.2, 4))

        if indicators:
            summary = "; ".join(indicators)
        else:
            summary = "No explicit contradictions detected."

        return {
            "score": score,
            "summary": summary,
            "indicators": indicators
        }

    def _detect_directional_conflicts(
        self,
        current_text,
        historical_texts,
        indicators
    ):

        current_positive = self._contains_any(
            current_text,
            ["strengthen", "increased", "stronger", "excel", "thrive"]
        )
        current_negative = self._contains_any(
            current_text,
            ["weaken", "decreased", "weaker", "struggle", "underperform"]
        )

        for historical_text in historical_texts:
            historical_positive = self._contains_any(
                historical_text,
                ["strengthen", "increased", "stronger", "excel", "thrive"]
            )
            historical_negative = self._contains_any(
                historical_text,
                ["weaken", "decreased", "weaker", "struggle", "underperform"]
            )

            if current_positive and historical_negative:
                indicators.append(
                    "Current theory strengthens a relationship that prior "
                    "theory weakened."
                )
                return

            if current_negative and historical_positive:
                indicators.append(
                    "Current theory weakens a relationship that prior "
                    "theory strengthened."
                )
                return

    def _detect_validation_failures(self, validation_texts, indicators):

        failure_phrases = [
            "failed",
            "did not",
            "opposite",
            "weakened",
            "decreased",
            "invalidated",
            "conflicted"
        ]

        for validation_text in validation_texts:
            if self._contains_any(validation_text, failure_phrases):
                indicators.append("Recent validation contains failure signal.")
                return

    def _detect_uncertainty(self, reflection_texts, indicators):

        uncertainty_phrases = [
            "uncertain",
            "uncertainty",
            "mixed",
            "limited",
            "caution",
            "overconfidence",
            "contradictory"
        ]

        for reflection_text in reflection_texts:
            if self._contains_any(reflection_text, uncertainty_phrases):
                indicators.append(
                    "Recent reflection contains uncertainty or caution signal."
                )
                return

    def _detect_momentum_liquidity_conflicts(
        self,
        current_text,
        historical_texts,
        indicators
    ):

        if "momentum" not in current_text or "liquidity" not in current_text:
            return

        current_supports = self._contains_any(
            current_text,
            ["strengthen", "stronger", "excel", "thrive", "persistence"]
        )
        current_rejects = self._contains_any(
            current_text,
            ["weaken", "weaker", "struggle", "underperform", "breakdown"]
        )

        for historical_text in historical_texts:
            if "momentum" not in historical_text:
                continue

            if "liquidity" not in historical_text:
                continue

            historical_supports = self._contains_any(
                historical_text,
                ["strengthen", "stronger", "excel", "thrive", "persistence"]
            )
            historical_rejects = self._contains_any(
                historical_text,
                ["weaken", "weaker", "struggle", "underperform", "breakdown"]
            )

            if current_supports and historical_rejects:
                indicators.append(
                    "Momentum/liquidity conclusion conflicts with prior "
                    "negative conclusion."
                )
                return

            if current_rejects and historical_supports:
                indicators.append(
                    "Momentum/liquidity conclusion conflicts with prior "
                    "positive conclusion."
                )
                return

    def _validation_text(self, validation) -> str:

        return " ".join(
            [
                validation.validation_summary,
                validation.observed_behavior,
                validation.expected_behavior
            ]
        ).lower()

    def _contains_any(self, text: str, phrases: list[str]) -> bool:

        return any(phrase in text for phrase in phrases)
