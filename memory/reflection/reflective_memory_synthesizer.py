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
        contradiction_result
    ):

        recurring_themes = self._recurring_themes(
            theories,
            reflections,
            validations
        )
        persistent_uncertainties = self._persistent_uncertainties(
            reflections,
            contradiction_result
        )
        strengthening_patterns = self._strengthening_patterns(
            validations,
            confidence_states
        )
        weakening_patterns = self._weakening_patterns(
            confidence_states,
            contradiction_result
        )
        contradiction_hotspots = self._contradiction_hotspots(
            contradiction_result
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

    def _recurring_themes(self, theories, reflections, validations):

        watched_terms = [
            "momentum",
            "liquidity",
            "trend",
            "persistence",
            "participation",
            "confidence",
            "uncertainty",
            "contradiction",
            "market activity"
        ]
        text = self._combined_text(theories, reflections, validations)
        counts = Counter()

        for term in watched_terms:
            counts[term] = text.count(term)

        themes = [
            f"{term} recurring across recent cognition"
            for term, count in counts.most_common()
            if count >= 2
        ]

        return themes[:5] or ["No recurring theme is stable yet."]

    def _persistent_uncertainties(self, reflections, contradiction_result):

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

        return self._unique(uncertainties)[:5] or [
            "No persistent uncertainty detected yet."
        ]

    def _strengthening_patterns(self, validations, confidence_states):

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

        return patterns[:5] or ["No strengthening pattern is stable yet."]

    def _weakening_patterns(self, confidence_states, contradiction_result):

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

        return patterns[:5] or ["No weakening pattern is stable yet."]

    def _contradiction_hotspots(self, contradiction_result):

        indicators = contradiction_result["indicators"]

        if indicators:
            return indicators[:5]

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

    def _combined_text(self, theories, reflections, validations):

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

        return " ".join(parts).lower()

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
