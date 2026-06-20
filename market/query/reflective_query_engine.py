class ReflectiveQueryEngine:
    """
    Reflective query layer for cognition introspection.

    Supports queries:
    - Why is coherence weakening?
    - Which theories repeatedly failed?
    - Which contradictions recur most?
    - Which regimes destabilize confidence?
    - What assumptions weakened?

    Uses explicit retrieval logic, no embeddings.
    """

    def query_coherence_decline(
        self, recent_confidence_states, recent_reflections, theory_survival_analysis
    ) -> str:
        """Query: Why is coherence weakening?"""

        if len(recent_confidence_states) < 2:
            return "Insufficient history to assess coherence trend."

        recent_coherence = recent_confidence_states[0].theoretical_coherence
        older_coherence = recent_confidence_states[-1].theoretical_coherence

        trend = recent_coherence - older_coherence

        if trend >= -0.05:
            return (
                "Coherence is stable or improving. "
                f"Current level: {recent_coherence:.2f}. "
                "No concerning decline detected."
            )

        # Coherence is declining
        response = (
            f"Coherence is declining (from {older_coherence:.2f} "
            f"to {recent_coherence:.2f}, Δ{trend:.2f}).\n\n"
            "Contributing factors:\n"
        )

        # Factor 1: Contradiction pressure
        recent_pressure = recent_confidence_states[0].contradiction_pressure
        if recent_pressure > 0.5:
            response += (
                f"  1. High contradiction pressure ({recent_pressure:.2f}) "
                "eroding theoretical coherence\n"
            )

        # Factor 2: Weakening theories
        weakening = theory_survival_analysis.get("weakening_theories", [])
        if len(weakening) > 1:
            response += (
                f"  2. Multiple theories weakening ({len(weakening)}), "
                "suggesting foundational instability\n"
            )

        # Factor 3: Reflective uncertainty
        if recent_reflections:
            uncertain_reflections = [
                r
                for r in recent_reflections[:3]
                if "uncertain" in r.reflection_summary.lower()
                or "caution" in r.reflection_summary.lower()
            ]
            if uncertain_reflections:
                response += (
                    f"  3. Recent reflections flag uncertainty "
                    f"({len(uncertain_reflections)} instances)\n"
                )

        response += (
            "\nRecommendation: Review weakening assumptions and "
            "consider regime-sensitive interpretation frameworks."
        )

        return response

    def query_repeated_failures(self, theory_survival_analysis, recent_outcomes) -> str:
        """Query: Which theories repeatedly failed?"""

        recurring_failures = theory_survival_analysis.get("recurring_failures", [])

        if not recurring_failures:
            return "No recurring theory failures detected in recent history."

        response = (
            f"Detected {len(recurring_failures)} recurring failure pattern(s):\n\n"
        )

        for i, theory in enumerate(recurring_failures[:5], 1):
            thesis = theory.get("thesis", "")[:80]
            failure_rate = theory.get("failure_rate", 0)
            occurrences = theory.get("occurrences", 0)

            response += (
                f"{i}. Theory: {thesis}...\n"
                f"   Failure Rate: {failure_rate:.0%} "
                f"({int(failure_rate * occurrences)} of {occurrences})\n"
                f"   Last Seen: {theory.get('last_seen', 'unknown')}\n\n"
            )

        # Analyze failure patterns
        response += "FAILURE PATTERN ANALYSIS:\n"

        if all(
            "volatility" in str(t.get("thesis", "")).lower()
            for t in recurring_failures[:3]
        ):
            response += "  • Volatility-related assumptions show consistent failure\n"

        if all(
            "liquidity" in str(t.get("thesis", "")).lower()
            for t in recurring_failures[:3]
        ):
            response += (
                "  • Liquidity-based theories deteriorate under " "certain regimes\n"
            )

        if all(
            "breadth" in str(t.get("thesis", "")).lower()
            for t in recurring_failures[:3]
        ):
            response += "  • Breadth-led assumptions repeatedly break down\n"

        response += (
            "\nRecommendation: Investigate regime-specific "
            "conditions under which these failures occur."
        )

        return response

    def query_contradiction_frequency(
        self, contradiction_zone_map, recent_reflections
    ) -> str:
        """Query: Which contradictions recur most frequently?"""

        zones = contradiction_zone_map.get("recurring_zones", {})

        if not zones:
            return (
                "No recurring contradiction zones detected. "
                "Recent cognition appears coherent."
            )

        response = f"Detected {len(zones)} recurring contradiction zone(s):\n\n"

        sorted_zones = sorted(
            zones.items(), key=lambda x: x[1]["occurrences"], reverse=True
        )

        for zone_name, data in sorted_zones[:5]:
            readable_name = zone_name.replace("_", " ").title()
            occurrences = data["occurrences"]
            severity = data["intensity"]

            response += (
                f"• {readable_name}\n"
                f"  Occurrences: {occurrences}\n"
                f"  Severity: {severity:.2f}/1.0\n\n"
            )

        # High-frequency analysis
        most_frequent = sorted_zones[0] if sorted_zones else None
        if most_frequent and most_frequent[1]["occurrences"] >= 3:
            response += (
                f"PRIMARY HOTSPOT: {most_frequent[0].replace('_', ' ').title()}\n"
                "This contradiction appears consistently. "
                "Theoretical frameworks should account for this tension.\n"
            )

        response += (
            "\nRecommendation: Embed these contradiction zones "
            "into adaptive interpretation frameworks."
        )

        return response

    def query_regime_sensitivity(
        self, theory_survival_analysis, recent_confidence_states, recent_outcomes
    ) -> str:
        """Query: Which regimes destabilize confidence?"""

        if not recent_outcomes or not recent_confidence_states:
            return "Insufficient outcome data for regime sensitivity analysis."

        # Identify regime-specific weakness
        weakening = theory_survival_analysis.get("weakening_theories", [])

        regime_weak_theories = [
            t
            for t in weakening
            if any(
                keyword in str(t.get("thesis", "")).lower()
                for keyword in ["volatility", "regime", "dispersion"]
            )
        ]

        response = "REGIME SENSITIVITY ANALYSIS:\n\n"

        # Regime 1: Volatility
        vol_outcomes = [
            o
            for o in recent_outcomes
            if "expand" in o.realized_volatility.lower()
            or "elevated" in o.realized_volatility.lower()
        ]
        if len(vol_outcomes) >= 2:
            vol_coherence = [
                s.theoretical_coherence for s in recent_confidence_states[:3]
            ]
            response += (
                f"VOLATILITY REGIME: Elevated volatility detected in "
                f"{len(vol_outcomes)} recent outcomes.\n"
                f"  Avg Coherence During Vol: {sum(vol_coherence)/max(1, len(vol_coherence)):.2f}\n"
                f"  Theories Affected: "
                f"{len([t for t in weakening if 'vol' in str(t).lower()])} weakening\n\n"
            )

        # Regime 2: Dispersion
        disp_outcomes = [
            o
            for o in recent_outcomes
            if "weak" in o.realized_breadth.lower()
            or "narrow" in o.realized_breadth.lower()
        ]
        if len(disp_outcomes) >= 2:
            response += (
                f"DISPERSION REGIME: Narrow breadth detected in "
                f"{len(disp_outcomes)} recent outcomes.\n"
                f"  Theories Affected: "
                f"{len([t for t in weakening if 'breadth' in str(t).lower()])} weakening\n\n"
            )

        # Regime 3: Liquidity stress
        liq_outcomes = [
            o
            for o in recent_outcomes
            if "fragmented" in o.realized_liquidity.lower()
            or "uneven" in o.realized_liquidity.lower()
        ]
        if len(liq_outcomes) >= 2:
            response += (
                f"LIQUIDITY STRESS REGIME: Fragmented liquidity in "
                f"{len(liq_outcomes)} recent outcomes.\n"
                f"  Theories Affected: "
                f"{len([t for t in weakening if 'liquidity' in str(t).lower()])} weakening\n\n"
            )

        if not (vol_outcomes or disp_outcomes or liq_outcomes):
            response += (
                "No clear regime-specific stress patterns detected. "
                "Confidence destabilization appears regime-neutral.\n"
            )

        response += (
            "Recommendation: Apply regime-conditional interpretation "
            "weights when assessing theory confidence."
        )

        return response

    def query_weakening_assumptions(
        self, theory_survival_analysis, recent_validations
    ) -> str:
        """Query: What assumptions weakened recently?"""

        weakening_theories = theory_survival_analysis.get("weakening_theories", [])

        if not weakening_theories:
            return (
                "No weakening assumptions detected. "
                "Theoretical foundations appear stable."
            )

        response = f"Identified {len(weakening_theories)} weakening assumption(s):\n\n"

        for theory in weakening_theories[:5]:
            thesis = theory.get("thesis", "")[:80]
            failure_rate = theory.get("failure_rate", 0)
            trend = theory.get("recent_trend", 0)

            response += f"• {thesis}...\n"
            response += (
                f"  Recent Trend: "
                f"{'deteriorating' if trend < -0.05 else 'unstable'}\n"
                f"  Failure Rate: {failure_rate:.0%}\n"
                f"  Recommendation: "
            )

            if failure_rate > 0.7:
                response += "Consider deprioritizing this assumption\n"
            elif failure_rate > 0.5:
                response += "Apply caution; regime-conditional use only\n"
            else:
                response += "Monitor for further deterioration\n"

            response += "\n"

        response += (
            "PATTERN SUMMARY:\n"
            "Weakening assumptions often indicate boundary conditions "
            "where theories break down. They highlight "
            "regime-dependent limitations rather than fundamental errors."
        )

        return response

    def query_confidence_trajectory(self, recent_confidence_states) -> str:
        """Query: How is confidence evolving?"""

        if len(recent_confidence_states) < 2:
            return "Insufficient history for confidence trajectory analysis."

        response = "CONFIDENCE EVOLUTION TRAJECTORY:\n\n"

        # Extract time series
        empirical = [s.empirical_confidence for s in recent_confidence_states]
        regime = [s.regime_confidence for s in recent_confidence_states]
        reflection = [s.reflection_confidence for s in recent_confidence_states]
        coherence = [s.theoretical_coherence for s in recent_confidence_states]
        pressure = [s.contradiction_pressure for s in recent_confidence_states]

        # Analyze trends
        def trend_description(values):
            if len(values) < 2:
                return "stable (insufficient history)"
            delta = values[0] - values[-1]
            if delta > 0.1:
                return f"increasing (Δ+{delta:.2f})"
            elif delta < -0.1:
                return f"decreasing (Δ{delta:.2f})"
            else:
                return "stable"

        response += f"Empirical Confidence: {trend_description(empirical)}\n"
        response += f"Regime Confidence: {trend_description(regime)}\n"
        response += f"Reflection Confidence: {trend_description(reflection)}\n"
        response += f"Theoretical Coherence: {trend_description(coherence)}\n"
        response += f"Contradiction Pressure: {trend_description(pressure)}\n"

        # Summary
        response += "\nINTERPRETATION:\n"
        avg_coherence = sum(coherence) / len(coherence)
        avg_pressure = sum(pressure) / len(pressure)

        if avg_coherence > 0.7 and avg_pressure < 0.3:
            response += "System shows strong theoretical coherence with low pressure.\n"
        elif avg_coherence > 0.5 and avg_pressure < 0.5:
            response += (
                "System shows moderate coherence with manageable pressure. "
                "Adaptive interpretation frameworks active.\n"
            )
        elif avg_coherence <= 0.5 or avg_pressure >= 0.5:
            response += (
                "System shows weakening coherence or elevated pressure. "
                "Regime transitions or major contradiction zones likely present.\n"
            )

        return response
