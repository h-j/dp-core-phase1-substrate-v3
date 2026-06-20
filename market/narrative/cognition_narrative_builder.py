from datetime import datetime, UTC


class CognitionNarrativeBuilder:
    """
    Constructs longitudinal cognition narratives.

    Builds coherent stories about:
    - Theory evolution
    - Contradiction history
    - Confidence drift
    - Regime transitions

    Emphasizes uncertainty and adaptive interpretation.
    """

    def build_narrative(
        self,
        recent_theories,
        recent_validations,
        recent_reflections,
        recent_confidence_states,
        recent_outcomes,
        theory_survival_analysis,
        strategic_memory_history,
    ) -> str:
        """Build longitudinal cognition narrative."""

        narrative_parts = []

        # Opening: current state
        opening = self._construct_opening(recent_confidence_states, recent_theories)
        narrative_parts.append(opening)

        # Theory evolution chapter
        evolution_chapter = self._theory_evolution_chapter(
            theory_survival_analysis, recent_validations, recent_theories
        )
        if evolution_chapter:
            narrative_parts.append(evolution_chapter)

        # Contradiction history chapter
        contradiction_chapter = self._contradiction_history_chapter(
            theory_survival_analysis, recent_reflections, recent_outcomes
        )
        if contradiction_chapter:
            narrative_parts.append(contradiction_chapter)

        # Confidence drift chapter
        confidence_chapter = self._confidence_drift_chapter(
            recent_confidence_states, strategic_memory_history
        )
        if confidence_chapter:
            narrative_parts.append(confidence_chapter)

        # Regime transition chapter
        regime_chapter = self._regime_transition_chapter(
            theory_survival_analysis, recent_outcomes
        )
        if regime_chapter:
            narrative_parts.append(regime_chapter)

        # Closing: interpretation and uncertainty
        closing = self._construct_closing(
            recent_confidence_states, recent_reflections, theory_survival_analysis
        )
        narrative_parts.append(closing)

        return "\n\n".join(narrative_parts)

    def _construct_opening(self, recent_confidence_states, recent_theories) -> str:
        """Construct narrative opening."""

        if not recent_confidence_states or not recent_theories:
            return "Cognition history insufficient for full narrative construction."

        latest_state = recent_confidence_states[0]
        coherence = latest_state.theoretical_coherence
        pressure = latest_state.contradiction_pressure

        opening = "LONGITUDINAL COGNITION NARRATIVE\n"
        opening += "=" * 60 + "\n\n"

        opening += f"Current Snapshot (as of {datetime.now(UTC).isoformat()}):\n"
        opening += (
            f"  Coherence: {coherence:.2f}\n"
            f"  Contradiction Pressure: {pressure:.2f}\n"
        )

        if recent_theories:
            theory_count = len(recent_theories)
            opening += f"  Active Theories: {theory_count}\n"

        opening += (
            "\nThis narrative reflects adaptive, "
            "uncertainty-aware interpretation of market cognition evolution."
        )

        return opening

    def _theory_evolution_chapter(
        self, theory_survival_analysis, recent_validations, recent_theories
    ) -> str:
        """Construct theory evolution narrative chapter."""

        chapter = "CHAPTER 1: THEORY EVOLUTION\n"
        chapter += "-" * 60 + "\n\n"

        strengthening = theory_survival_analysis.get("strengthening_theories", [])
        weakening = theory_survival_analysis.get("weakening_theories", [])
        unstable = theory_survival_analysis.get("unstable_theories", [])

        if not strengthening and not weakening and not unstable:
            return None

        if strengthening:
            chapter += "Theories Gaining Strength:\n"
            for theory in strengthening[:2]:
                avg_score = theory.get("avg_score", 0)
                occurrences = theory.get("occurrences", 0)
                chapter += (
                    f"  • {theory['thesis'][:70]}...\n"
                    f"    (avg validation: {avg_score:.2f}, "
                    f"observations: {occurrences})\n"
                )

        if weakening:
            chapter += "\nTheories Losing Coherence:\n"
            for theory in weakening[:2]:
                failure_rate = theory.get("failure_rate", 0)
                chapter += (
                    f"  • {theory['thesis'][:70]}...\n"
                    f"    (failure rate: {failure_rate:.0%})\n"
                )

        if unstable:
            chapter += "\nUnstable Theoretical Structures:\n"
            for theory in unstable[:2]:
                avg_score = theory.get("avg_score", 0)
                chapter += (
                    f"  • {theory['thesis'][:70]}...\n"
                    f"    (inconsistent validation: {avg_score:.2f})\n"
                )

        chapter += (
            "\nInterpretation: Theory evolution shows mixed signals. "
            "Strengthening patterns indicate market comprehension in certain domains, "
            "while weakening theories reveal domains where assumptions break down."
        )

        return chapter

    def _contradiction_history_chapter(
        self, theory_survival_analysis, recent_reflections, recent_outcomes
    ) -> str:
        """Construct contradiction history narrative chapter."""

        chapter = "CHAPTER 2: CONTRADICTION ACCUMULATION\n"
        chapter += "-" * 60 + "\n\n"

        recurring_failures = theory_survival_analysis.get("recurring_failures", [])

        if not recurring_failures and not recent_outcomes:
            return None

        if recurring_failures:
            chapter += "Recurring Theoretical Failures:\n"
            for theory in recurring_failures[:3]:
                failure_rate = theory.get("failure_rate", 0)
                chapter += (
                    f"  • {theory['thesis'][:70]}...\n"
                    f"    (failure recurrence: {failure_rate:.0%})\n"
                )

        if recent_outcomes:
            contradictions_found = [
                outcome.outcome_contradictions
                for outcome in recent_outcomes
                if outcome.outcome_contradictions
            ]
            if contradictions_found:
                chapter += "\nMarket-Reality Contradictions:\n"
                for outcome in recent_outcomes[:2]:
                    if outcome.outcome_contradictions:
                        for contradiction in outcome.outcome_contradictions[:2]:
                            chapter += f"  • {contradiction}\n"

        chapter += (
            "\nInterpretation: Contradictions are not failures, "
            "but signals of theoretical boundary conditions. "
            "They reveal where assumptions break down and where "
            "adaptive interpretation becomes necessary."
        )

        return chapter

    def _confidence_drift_chapter(
        self, recent_confidence_states, strategic_memory_history
    ) -> str:
        """Construct confidence drift narrative chapter."""

        chapter = "CHAPTER 3: CONFIDENCE DRIFT\n"
        chapter += "-" * 60 + "\n\n"

        if len(recent_confidence_states) < 2:
            return None

        empirical_values = [s.empirical_confidence for s in recent_confidence_states]
        coherence_values = [s.theoretical_coherence for s in recent_confidence_states]
        pressure_values = [s.contradiction_pressure for s in recent_confidence_states]

        empirical_trend = empirical_values[0] - empirical_values[-1]
        coherence_trend = coherence_values[0] - coherence_values[-1]
        pressure_trend = pressure_values[0] - pressure_values[-1]

        chapter += "Confidence Evolution Trends:\n"
        chapter += (
            f"  • Empirical Confidence: "
            f"{empirical_values[0]:.2f} "
            f"({'increasing' if empirical_trend > 0 else 'decreasing'}, "
            f"Δ{empirical_trend:+.2f})\n"
        )
        chapter += (
            f"  • Theoretical Coherence: "
            f"{coherence_values[0]:.2f} "
            f"({'strengthening' if coherence_trend > 0 else 'weakening'}, "
            f"Δ{coherence_trend:+.2f})\n"
        )
        chapter += (
            f"  • Contradiction Pressure: "
            f"{pressure_values[0]:.2f} "
            f"({'increasing' if pressure_trend > 0 else 'decreasing'}, "
            f"Δ{pressure_trend:+.2f})\n"
        )

        chapter += (
            "\nInterpretation: Confidence drift reflects the substrate's "
            "real-time adjustment to market observations. "
            "Increases indicate theoretical validation; "
            "decreases signal challenges requiring adaptive interpretation."
        )

        return chapter

    def _regime_transition_chapter(
        self, theory_survival_analysis, recent_outcomes
    ) -> str:
        """Construct regime transition narrative chapter."""

        chapter = "CHAPTER 4: REGIME TRANSITIONS\n"
        chapter += "-" * 60 + "\n\n"

        weakening = theory_survival_analysis.get("weakening_theories", [])

        regime_keywords = ["volatility", "regime", "dispersion", "participation"]

        regime_signals = []
        for theory in weakening:
            thesis = str(theory.get("thesis", "")).lower()
            for keyword in regime_keywords:
                if keyword in thesis:
                    regime_signals.append(
                        f"Theory related to '{keyword}' showing weakness"
                    )

        if regime_signals:
            chapter += "Detected Regime Sensitivity:\n"
            for signal in list(set(regime_signals))[:3]:
                chapter += f"  • {signal}\n"

        if recent_outcomes:
            outcome_trends = []
            volatility_states = [
                o.realized_volatility.lower() for o in recent_outcomes[:5]
            ]
            if volatility_states.count("elevated") >= 2:
                outcome_trends.append("elevated volatility regime detected")

            breadth_states = [o.realized_breadth.lower() for o in recent_outcomes[:5]]
            if breadth_states.count("weak") >= 2:
                outcome_trends.append("participation dispersion regime detected")

            if outcome_trends:
                chapter += "\nMarket Regime Observations:\n"
                for trend in outcome_trends:
                    chapter += f"  • {trend}\n"

        chapter += (
            "\nInterpretation: Regime transitions represent critical "
            "cognitive boundaries. Theories that perform in one regime "
            "may fail in another. Adaptive cognition requires "
            "regime-conditional interpretation frameworks."
        )

        return chapter

    def _construct_closing(
        self, recent_confidence_states, recent_reflections, theory_survival_analysis
    ) -> str:
        """Construct narrative closing with uncertainty emphasis."""

        closing = "NARRATIVE INTERPRETATION\n"
        closing += "-" * 60 + "\n\n"

        closing += (
            "This longitudinal narrative preserves fundamental uncertainty. "
            "Market cognition evolves through cycles of theory generation, "
            "validation, contradiction, and adaptation.\n\n"
        )

        if recent_confidence_states:
            latest_pressure = recent_confidence_states[0].contradiction_pressure
            if latest_pressure > 0.5:
                closing += (
                    f"Current contradiction pressure ({latest_pressure:.2f}) "
                    "suggests heightened interpretive caution is warranted.\n"
                )

        weakening = theory_survival_analysis.get("weakening_theories", [])
        if len(weakening) > 2:
            closing += (
                f"Multiple theories weakening ({len(weakening)}); "
                "suggests market regime transition may be underway.\n"
            )

        closing += (
            "\nThis narrative does NOT provide predictions or trading signals. "
            "It reflects the substrate's evolving understanding of "
            "market structure, theory survival, and contradiction patterns. "
            "Use this for interpretive co-reasoning, not autonomous decision-making."
        )

        return closing
