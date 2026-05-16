from market.schemas.strategic_memory_state import StrategicMemoryState
from collections import Counter


class StrategicReflectionSynthesizer:
    """
    Synthesizes strategic cognition from longitudinal history.
    
    Creates reflective strategic summaries that:
    - Preserve uncertainty
    - Highlight contradictions
    - Track coherence evolution
    - Interpret regime sensitivity
    - Surface weakening assumptions
    """

    def synthesize(
        self,
        recent_theories,
        recent_validations,
        recent_reflections,
        recent_confidence_states,
        recent_outcomes,
        theory_survival_analysis,
        contradiction_zone_map,
        market_observations,
        reflective_memory_states
    ):
        """Synthesize strategic cognition snapshot."""

        strategic_summary = self._generate_strategic_summary(
            recent_theories,
            recent_validations,
            recent_reflections,
            recent_confidence_states
        )

        cognition_posture = self._determine_cognition_posture(
            recent_confidence_states,
            theory_survival_analysis,
            market_observations
        )

        major_contradictions = (
            self._extract_major_contradictions(
                theory_survival_analysis,
                contradiction_zone_map,
                recent_reflections
            )
        )

        weakening_assumptions = (
            self._identify_weakening_assumptions(
                theory_survival_analysis,
                recent_validations,
                recent_theories
            )
        )

        strengthening_patterns = (
            self._identify_strengthening_patterns(
                theory_survival_analysis,
                recent_validations,
                recent_reflections
            )
        )

        regime_interpretation = (
            self._interpret_regime_sensitivity(
                recent_confidence_states,
                theory_survival_analysis,
                contradiction_zone_map,
                market_observations
            )
        )

        uncertainty_summary = (
            self._synthesize_uncertainty(
                recent_confidence_states,
                recent_reflections,
                weakening_assumptions
            )
        )

        coherence_trajectory = (
            self._analyze_coherence_trajectory(
                recent_confidence_states,
                reflective_memory_states
            )
        )

        contradiction_frequency = (
            self._track_contradiction_frequency(
                contradiction_zone_map
            )
        )

        return StrategicMemoryState(
            strategic_summary=strategic_summary,
            cognition_posture=cognition_posture,
            major_contradictions=major_contradictions,
            weakening_assumptions=weakening_assumptions,
            strengthening_patterns=strengthening_patterns,
            regime_interpretation=regime_interpretation,
            uncertainty_summary=uncertainty_summary,
            coherence_trajectory=coherence_trajectory,
            contradiction_frequency=contradiction_frequency
        )

    def _generate_strategic_summary(
        self,
        recent_theories,
        recent_validations,
        recent_reflections,
        recent_confidence_states
    ) -> str:
        """Generate strategic summary of current cognition."""

        if not recent_confidence_states:
            return "Insufficient history for strategic interpretation."

        latest_coherence = recent_confidence_states[0].theoretical_coherence
        latest_pressure = (
            recent_confidence_states[0].contradiction_pressure
        )

        summary = "Recent cognition shows "

        if latest_coherence > 0.7:
            summary += "strong theoretical coherence "
        elif latest_coherence > 0.5:
            summary += "moderate theoretical coherence "
        else:
            summary += "weakening theoretical coherence "

        if latest_pressure > 0.5:
            summary += "with material contradiction pressure. "
        elif latest_pressure > 0.2:
            summary += "with emerging contradiction pressure. "
        else:
            summary += "with manageable contradiction levels. "

        # Add validation insights
        if recent_validations:
            validation_scores = [
                v.validation_summary
                for v in recent_validations[:3]
            ]

            if any("supported" in v.lower() for v in validation_scores):
                summary += (
                    "Recent theories are receiving validation support. "
                )
            elif any("contradicted" in v.lower() for v in validation_scores):
                summary += (
                    "Recent theories face validation challenges. "
                )

        # Add reflection insights
        if recent_reflections:
            reflection_text = " ".join(
                r.reflection_summary.lower()
                for r in recent_reflections[:2]
            )

            if "uncertain" in reflection_text:
                summary += "Uncertainty persists in interpretations. "
            elif "strengthening" in reflection_text:
                summary += "Reflections indicate strengthening patterns. "
            elif "weakening" in reflection_text:
                summary += "Reflections indicate weakening foundations. "

        return summary

    def _determine_cognition_posture(
        self,
        recent_confidence_states,
        theory_survival_analysis,
        market_observations
    ) -> str:
        """Determine overall cognition posture."""

        if not recent_confidence_states:
            return "uncertain"

        latest_coherence = recent_confidence_states[0].theoretical_coherence
        latest_pressure = (
            recent_confidence_states[0].contradiction_pressure
        )

        weakening = theory_survival_analysis.get("weakening_theories", [])
        strengthening = theory_survival_analysis.get(
            "strengthening_theories",
            []
        )

        if latest_coherence > 0.75 and latest_pressure < 0.2:
            if len(strengthening) > len(weakening):
                return "confident"
            else:
                return "cautiously_coherent"

        elif latest_coherence > 0.5 and latest_pressure < 0.4:
            if len(weakening) > 0:
                return "adaptive"
            else:
                return "stable"

        elif latest_coherence <= 0.5 or latest_pressure >= 0.5:
            return "contradicted"

        else:
            return "uncertain"

    def _extract_major_contradictions(
        self,
        theory_survival_analysis,
        contradiction_zone_map,
        recent_reflections
    ) -> list[str]:
        """Extract major recurring contradictions."""

        contradictions = []

        # From contradiction zone map
        recurring_zones = contradiction_zone_map.get(
            "recurring_zones",
            {}
        )
        for zone_name, data in list(recurring_zones.items())[:2]:
            zone_readable = zone_name.replace("_", " ").title()
            if data["occurrences"] >= 2:
                contradictions.append(
                    f"{zone_readable} (recurrence: {data['occurrences']})"
                )

        # From theory survival
        recurring_failures = theory_survival_analysis.get(
            "recurring_failures",
            []
        )
        for theory in recurring_failures[:2]:
            contradictions.append(
                f"Theory '{theory['thesis'][:50]}...' repeatedly fails "
                f"({theory['failure_rate']:.0%})"
            )

        # From reflections
        if recent_reflections:
            reflection_text = " ".join(
                r.reflection_summary.lower()
                for r in recent_reflections[:3]
            )

            if "divergence" in reflection_text:
                contradictions.append("Persistent divergence in structure")
            if "contradiction" in reflection_text:
                contradictions.append(
                    "Contradiction themes in recent reflections"
                )

        return list(set(contradictions))

    def _identify_weakening_assumptions(
        self,
        theory_survival_analysis,
        recent_validations,
        recent_theories
    ) -> list[str]:
        """Identify assumptions showing weakness."""

        weakening = []

        # From survival analysis
        weakening_theories = theory_survival_analysis.get(
            "weakening_theories",
            []
        )
        for theory in weakening_theories[:2]:
            weakening.append(
                f"Assumption in '{theory['thesis'][:60]}...' "
                f"weakening ({theory['failure_rate']:.0%} recent failures)"
            )

        # From recent validations
        validation_text = " ".join(
            v.validation_summary.lower()
            for v in recent_validations[:5]
        )

        if "liquidity" in validation_text and "weak" in validation_text:
            weakening.append("Liquidity-led assumptions showing weakness")

        if "momentum" in validation_text and "failed" in validation_text:
            weakening.append("Momentum continuation assumptions failing")

        if "breadth" in validation_text and "diverge" in validation_text:
            weakening.append("Breadth-support assumptions diverging")

        return list(set(weakening))

    def _identify_strengthening_patterns(
        self,
        theory_survival_analysis,
        recent_validations,
        recent_reflections
    ) -> list[str]:
        """Identify patterns showing strength."""

        strengthening = []

        # From survival analysis
        strong_theories = theory_survival_analysis.get(
            "strengthening_theories",
            []
        )
        for theory in strong_theories[:2]:
            strengthening.append(
                f"Theory '{theory['thesis'][:50]}...' "
                f"strengthening (avg score: {theory['avg_score']:.2f})"
            )

        # From validations
        validation_text = " ".join(
            v.validation_summary.lower()
            for v in recent_validations[:5]
        )

        if validation_text.count("supported") >= 2:
            strengthening.append("Repeated validation support across theories")

        # From reflections
        reflection_text = " ".join(
            r.reflection_summary.lower()
            for r in recent_reflections[:3]
        )

        if "align" in reflection_text and "consistent" in reflection_text:
            strengthening.append("Consistent alignment in reflections")

        return list(set(strengthening))

    def _interpret_regime_sensitivity(
        self,
        recent_confidence_states,
        theory_survival_analysis,
        contradiction_zone_map,
        market_observations
    ) -> str:
        """Interpret regime-sensitive cognition patterns."""

        regime_obs = []

        # Analyze regime sensitivity from theories
        weakening = theory_survival_analysis.get("weakening_theories", [])
        if any("volatility" in str(t).lower() for t in weakening):
            regime_obs.append(
                "Theories show volatility sensitivity; "
                "coherence deteriorates during vol expansion"
            )

        if any("regime" in str(t).lower() for t in weakening):
            regime_obs.append(
                "Regime-sensitive assumptions detected; "
                "require adaptive interpretation"
            )

        # Analyze contradiction zones
        zones = contradiction_zone_map.get("recurring_zones", {})
        if "momentum_volatility_mismatch" in zones:
            regime_obs.append(
                "Momentum assumptions prove unstable under volatility stress"
            )

        if "liquidity_participation_gap" in zones:
            regime_obs.append(
                "Liquidity effects diverge from participation patterns "
                "during market dispersion"
            )

        # Regime interpretation from observations
        if market_observations:
            vol_states = [
                o.volatility_state for o in market_observations
            ]
            if vol_states.count("elevated") >= 2:
                regime_obs.append(
                    "Elevated volatility regime: "
                    "theories require regime-conditional interpretation"
                )

            breadth_states = [
                o.breadth_state for o in market_observations
            ]
            if breadth_states.count("weak") >= 2:
                regime_obs.append(
                    "Dispersion regime: selective leadership dominates, "
                    "broad participation themes weakening"
                )

        if regime_obs:
            return "; ".join(regime_obs[:2])

        return "Regime interpretations remain ambiguous; continue observation."

    def _synthesize_uncertainty(
        self,
        recent_confidence_states,
        recent_reflections,
        weakening_assumptions
    ) -> str:
        """Synthesize uncertainty assessment."""

        uncertainty = []

        # From confidence states
        if recent_confidence_states:
            latest_pressure = (
                recent_confidence_states[0].contradiction_pressure
            )
            if latest_pressure > 0.5:
                uncertainty.append(
                    f"Material contradiction pressure ({latest_pressure:.2f}); "
                    "interpretations should be treated with caution"
                )

            latest_empirical = (
                recent_confidence_states[0].empirical_confidence
            )
            if latest_empirical < 0.5:
                uncertainty.append(
                    f"Low empirical confidence ({latest_empirical:.2f}); "
                    "theories lack strong reality grounding"
                )

        # From reflections
        if recent_reflections:
            reflection_text = " ".join(
                r.reflection_summary.lower()
                for r in recent_reflections[:2]
            )

            if "uncertain" in reflection_text:
                uncertainty.append(
                    "Recent reflections explicitly flag uncertainty"
                )

        # From weakening assumptions
        if len(weakening_assumptions) > 2:
            uncertainty.append(
                f"Multiple assumptions weakening ({len(weakening_assumptions)}); "
                "foundation stability questioned"
            )

        if uncertainty:
            return " ".join(uncertainty[:2])

        return (
            "Uncertainty levels manageable; "
            "cognition foundation appears stable."
        )

    def _analyze_coherence_trajectory(
        self,
        recent_confidence_states,
        reflective_memory_states
    ) -> str:
        """Analyze coherence evolution trajectory."""

        if len(recent_confidence_states) < 2:
            return "Insufficient history for trajectory analysis."

        coherence_values = [
            s.theoretical_coherence for s in recent_confidence_states
        ]

        recent_avg = sum(coherence_values[:3]) / min(3, len(coherence_values))
        older_avg = sum(coherence_values[-3:]) / min(3, len(coherence_values))

        trend = recent_avg - older_avg

        if trend > 0.05:
            trajectory = "strengthening"
        elif trend < -0.05:
            trajectory = "weakening"
        else:
            trajectory = "stable"

        base = (
            f"Coherence trajectory is {trajectory} "
            f"(recent avg {recent_avg:.2f}, "
            f"earlier avg {older_avg:.2f})"
        )

        if reflective_memory_states:
            latest_memory = reflective_memory_states[0]
            if trajectory == "weakening":
                base += (
                    "; hotspots identified: "
                    f"{', '.join(latest_memory.contradiction_hotspots[:2])}"
                )
            elif trajectory == "strengthening":
                base += (
                    "; patterns consolidating: "
                    f"{', '.join(latest_memory.strengthening_patterns[:2])}"
                )

        return base

    def _track_contradiction_frequency(
        self,
        contradiction_zone_map
    ) -> dict:
        """Track contradiction zone frequencies."""

        zones = contradiction_zone_map.get("recurring_zones", {})

        frequency = {}
        for zone_name, data in zones.items():
            frequency[zone_name] = {
                "occurrences": data["occurrences"],
                "severity": data["intensity"],
                "last_observed": str(data.get("last_occurrence", "unknown"))
            }

        return frequency
