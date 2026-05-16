from collections import Counter

from cognition.schemas.reflection.reflective_memory_state import (
    ReflectiveMemoryState
)


class ReflectiveMemorySynthesizer:

    def synthesize(
        self,
        theories,
        reflections,
        validations,
        confidence_states,
        contradiction_result,
        market_observations=None
    ):

        market_observations = market_observations or []

        recurring_themes = self._recurring_themes(
            theories,
            reflections,
            validations,
            market_observations
        )
        persistent_uncertainties = self._persistent_uncertainties(
            reflections,
            contradiction_result,
            market_observations
        )
        strengthening_patterns = self._strengthening_patterns(
            validations,
            confidence_states,
            market_observations
        )
        weakening_patterns = self._weakening_patterns(
            confidence_states,
            contradiction_result,
            market_observations
        )
        contradiction_hotspots = self._contradiction_hotspots(
            contradiction_result,
            market_observations
        )
        trajectory_summary = self._trajectory_summary(
            recurring_themes,
            strengthening_patterns,
            weakening_patterns,
            persistent_uncertainties,
            contradiction_hotspots,
            confidence_states
        )

        return ReflectiveMemoryState(
            recurring_themes=recurring_themes,
            strengthening_patterns=strengthening_patterns,
            weakening_patterns=weakening_patterns,
            persistent_uncertainties=persistent_uncertainties,
            contradiction_hotspots=contradiction_hotspots,
            cognition_trajectory_summary=trajectory_summary
        )

    def _recurring_themes(
        self,
        theories,
        reflections,
        validations,
        market_observations
    ):

        watched_terms = [
            "momentum",
            "liquidity",
            "trend",
            "persistence",
            "participation",
            "breadth",
            "volatility",
            "nifty",
            "regime",
            "rotation",
            "confidence",
            "uncertainty",
            "contradiction",
            "market activity"
        ]
        text = self._combined_text(
            theories,
            reflections,
            validations,
            market_observations
        )
        counts = Counter()

        for term in watched_terms:
            counts[term] = text.count(term)

        themes = [
            f"{term} recurring across recent cognition"
            for term, count in counts.most_common()
            if count >= 2
        ]

        return themes[:5] or ["No recurring theme is stable yet."]

    def _persistent_uncertainties(
        self,
        reflections,
        contradiction_result,
        market_observations
    ):

        uncertainty_terms = [
            "uncertain",
            "uncertainty",
            "caution",
            "mixed",
            "limited",
            "contradictory",
            "overconfidence"
        ]
        uncertainties = []

        for reflection in reflections:
            text = reflection.reflection_summary.lower()

            for term in uncertainty_terms:
                if term in text:
                    uncertainties.append(
                        f"Recent reflections continue to mention {term}."
                    )
                    break

        if contradiction_result["score"] > 0:
            uncertainties.append(
                "Contradiction pressure remains present in recent cognition."
            )

        if self._market_marker_count(
            market_observations,
            "uncertain"
        ) >= 1:
            uncertainties.append(
                "Recent NIFTY observations include uncertain macro sentiment."
            )

        if self._market_marker_count(
            market_observations,
            "mixed"
        ) >= 1:
            uncertainties.append(
                "Recent NIFTY observations include mixed breadth or sentiment."
            )

        return self._unique(uncertainties)[:5] or [
            "No persistent uncertainty detected yet."
        ]

    def _strengthening_patterns(
        self,
        validations,
        confidence_states,
        market_observations
    ):

        patterns = []
        validation_text = " ".join(
            validation.validation_summary.lower()
            for validation in validations
        )

        if validation_text.count("liquidity") >= 2:
            patterns.append(
                "Liquidity-linked momentum persistence has repeated support."
            )

        if validation_text.count("trend persistence") >= 2:
            patterns.append(
                "Trend persistence keeps appearing as a supported pattern."
            )

        if self._confidence_trend(
            confidence_states,
            "empirical_confidence"
        ) > 0:
            patterns.append(
                "Empirical confidence is rising across recent states."
            )

        if self._confidence_trend(
            confidence_states,
            "regime_confidence"
        ) > 0:
            patterns.append(
                "Regime confidence is rising across recent states."
            )

        if self._market_marker_count(
            market_observations,
            "broad_participation"
        ) >= 2:
            patterns.append(
                "Broad NIFTY participation is recurring in recent market memory."
            )

        if self._market_marker_count(
            market_observations,
            "strengthened"
        ) >= 2:
            patterns.append(
                "Breadth improvement has repeated across recent NIFTY observations."
            )

        return patterns[:5] or ["No strengthening pattern is stable yet."]

    def _weakening_patterns(
        self,
        confidence_states,
        contradiction_result,
        market_observations
    ):

        patterns = []

        if self._confidence_trend(
            confidence_states,
            "theoretical_coherence"
        ) < 0:
            patterns.append(
                "Theoretical coherence is weakening as pressure accumulates."
            )

        if self._confidence_trend(
            confidence_states,
            "contradiction_pressure"
        ) > 0:
            patterns.append(
                "Contradiction pressure is increasing across recent states."
            )

        if contradiction_result["score"] >= 0.4:
            patterns.append(
                "Current cognition has material contradiction pressure."
            )

        if self._market_marker_count(
            market_observations,
            "weakened"
        ) >= 2:
            patterns.append(
                "NIFTY breadth weakness is recurring in recent market memory."
            )

        if self._market_marker_count(
            market_observations,
            "expanded"
        ) >= 2:
            patterns.append(
                "Volatility expansion is recurring across recent NIFTY observations."
            )

        return patterns[:5] or ["No weakening pattern is stable yet."]

    def _contradiction_hotspots(
        self,
        contradiction_result,
        market_observations
    ):

        indicators = list(contradiction_result["indicators"])

        for observation in market_observations:
            markers = observation.contradiction_markers

            if "price_up_breadth_down" in markers:
                indicators.append(
                    "NIFTY price rose while breadth weakened."
                )

            if "new_high_narrow_breadth" in markers:
                indicators.append(
                    "NIFTY made a new high with narrowing breadth."
                )

            if "volatility_expansion_with_positive_close" in markers:
                indicators.append(
                    "Volatility expanded despite a positive NIFTY close."
                )

            if "high_volatility_recovery" in markers:
                indicators.append(
                    "NIFTY recovered while volatility stayed high."
                )

        if indicators:
            return self._unique(indicators)[:5]

        return ["No contradiction hotspot detected in the current cycle."]

    def _trajectory_summary(
        self,
        recurring_themes,
        strengthening_patterns,
        weakening_patterns,
        persistent_uncertainties,
        contradiction_hotspots,
        confidence_states
    ):

        latest_pressure = None
        latest_coherence = None

        if confidence_states:
            latest_state = confidence_states[0]
            latest_pressure = latest_state.contradiction_pressure
            latest_coherence = latest_state.theoretical_coherence

        theme = recurring_themes[0]
        strengthening = strengthening_patterns[0]
        weakening = weakening_patterns[0]
        uncertainty = persistent_uncertainties[0]
        hotspot = contradiction_hotspots[0]

        if latest_pressure is None:
            return (
                f"Recent cognition is organized around {theme}. "
                f"{strengthening} {weakening} {uncertainty} "
                f"Primary hotspot: {hotspot}"
            )

        return (
            f"Recent cognition is organized around {theme}. "
            f"{strengthening} {weakening} {uncertainty} "
            f"Primary hotspot: {hotspot} "
            f"Latest pressure is {latest_pressure} with coherence "
            f"at {latest_coherence}."
        )

    def _combined_text(
        self,
        theories,
        reflections,
        validations,
        market_observations
    ):

        parts = []

        parts.extend(theory.summary for theory in theories)
        parts.extend(
            reflection.reflection_summary
            for reflection in reflections
        )
        parts.extend(
            validation.validation_summary
            for validation in validations
        )
        parts.extend(
            observation.observation_text
            for observation in market_observations
        )
        parts.extend(
            " ".join(observation.contradiction_markers)
            for observation in market_observations
        )

        return " ".join(parts).lower()

    def _market_marker_count(self, market_observations, phrase: str):

        count = 0

        for observation in market_observations:
            text = " ".join(
                [
                    observation.observation_text,
                    observation.trend_state,
                    observation.volatility_state,
                    observation.liquidity_state,
                    observation.breadth_state,
                    observation.macro_sentiment,
                    " ".join(observation.contradiction_markers)
                ]
            ).lower()

            if phrase in text:
                count += 1

        return count

    def _confidence_trend(self, confidence_states, field_name: str):

        if len(confidence_states) < 2:
            return 0

        latest = getattr(confidence_states[0], field_name)
        oldest = getattr(confidence_states[-1], field_name)

        if latest > oldest:
            return 1

        if latest < oldest:
            return -1

        return 0

    def _unique(self, values):

        seen = set()
        unique_values = []

        for value in values:
            if value in seen:
                continue

            seen.add(value)
            unique_values.append(value)

        return unique_values
