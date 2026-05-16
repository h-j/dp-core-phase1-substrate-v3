class OutcomeValidationEngine:
    """
    Validates theories against actual market outcomes.
    
    Compares:
    - Prior theory thesis
    - Prior market observation
    - Realized market outcome
    
    Returns validation scores and adaptation recommendations.
    """

    def validate(
        self,
        theory,
        prior_observation,
        market_outcome
    ):
        """
        Validate a theory against realized market outcome.
        
        Args:
            theory: The theoretical prediction
            prior_observation: The initial market observation
            market_outcome: The realized market outcome
            
        Returns:
            Validation result dict with scores and summary
        """

        theory_thesis = theory.thesis.lower()
        observation_text = prior_observation.raw_content.lower()
        outcome_summary = market_outcome.outcome_summary.lower()

        # Calculate alignment scores
        trend_alignment = self._trend_alignment(
            theory_thesis,
            observation_text,
            market_outcome
        )

        breadth_alignment = self._breadth_alignment(
            theory_thesis,
            observation_text,
            market_outcome
        )

        liquidity_alignment = self._liquidity_alignment(
            theory_thesis,
            observation_text,
            market_outcome
        )

        volatility_alignment = self._volatility_alignment(
            theory_thesis,
            observation_text,
            market_outcome
        )

        # Calculate coherence
        average_alignment = (
            trend_alignment
            + breadth_alignment
            + liquidity_alignment
            + volatility_alignment
        ) / 4.0

        # Detect contradictions
        contradictions = self._detect_contradictions(
            theory.assumptions,
            market_outcome,
            observation_text
        )

        contradiction_score = len(contradictions) * 0.15

        # Calculate regime mismatch
        regime_mismatch = self._regime_mismatch(
            theory_thesis,
            observation_text,
            market_outcome
        )

        # Validation score: combination of alignment and contradiction
        validation_score = max(
            0.0,
            min(
                1.0,
                average_alignment - contradiction_score
            )
        )

        # Generate summary
        summary = self._generate_summary(
            theory_thesis,
            market_outcome,
            average_alignment,
            contradictions,
            regime_mismatch
        )

        # Adaptation recommendations
        recommendations = self._generate_recommendations(
            validation_score,
            contradictions,
            regime_mismatch,
            average_alignment
        )

        return {
            "validation_score": validation_score,
            "contradiction_score": contradiction_score,
            "trend_alignment": trend_alignment,
            "breadth_alignment": breadth_alignment,
            "liquidity_alignment": liquidity_alignment,
            "volatility_alignment": volatility_alignment,
            "regime_mismatch": regime_mismatch,
            "contradictions_detected": contradictions,
            "validation_summary": summary,
            "adaptation_recommendations": recommendations
        }

    def _trend_alignment(
        self,
        theory_thesis,
        observation_text,
        market_outcome
    ) -> float:
        """Calculate trend alignment between theory and outcome."""

        trend_keywords = {
            "continuing": ["continuation", "continue", "persistent"],
            "reversing": ["reversal", "reverse", "turned", "correction"],
            "consolidating": ["consolidat", "range", "sideways"]
        }

        theory_trend = None
        for trend_type, keywords in trend_keywords.items():
            if any(k in theory_thesis for k in keywords):
                theory_trend = trend_type
                break

        outcome_trend = market_outcome.realized_trend.lower()

        if theory_trend == "continuing":
            if "higher" in outcome_trend or "up" in outcome_trend:
                return 0.85
            elif "lower" in outcome_trend or "down" in outcome_trend:
                return 0.15
            else:
                return 0.5

        elif theory_trend == "reversing":
            if "reversal" in outcome_trend or "correction" in outcome_trend:
                return 0.8
            elif any(x in outcome_trend for x in ["higher", "lower"]):
                return 0.3
            else:
                return 0.5

        else:
            return 0.5

    def _breadth_alignment(
        self,
        theory_thesis,
        observation_text,
        market_outcome
    ) -> float:
        """Calculate breadth alignment between theory and outcome."""

        breadth_weakness_signals = [
            "weak breadth",
            "narrow",
            "divergence",
            "selective",
            "limited participation"
        ]

        breadth_strength_signals = [
            "broad participation",
            "breadth support",
            "widespread",
            "participation strength"
        ]

        theory_expects_weakness = any(
            sig in theory_thesis for sig in breadth_weakness_signals
        )
        theory_expects_strength = any(
            sig in theory_thesis for sig in breadth_strength_signals
        )

        outcome_breadth = market_outcome.realized_breadth.lower()

        if theory_expects_weakness:
            if any(x in outcome_breadth for x in ["weak", "narrow", "divergence"]):
                return 0.85
            elif "strong" in outcome_breadth or "broad" in outcome_breadth:
                return 0.1
            else:
                return 0.5

        elif theory_expects_strength:
            if "strong" in outcome_breadth or "broad" in outcome_breadth:
                return 0.85
            elif "weak" in outcome_breadth or "narrow" in outcome_breadth:
                return 0.1
            else:
                return 0.5

        else:
            return 0.5

    def _liquidity_alignment(
        self,
        theory_thesis,
        observation_text,
        market_outcome
    ) -> float:
        """Calculate liquidity alignment between theory and outcome."""

        liquidity_signals = [
            "liquidity",
            "volume",
            "flow"
        ]

        theory_mentions_liquidity = any(
            sig in theory_thesis for sig in liquidity_signals
        )

        outcome_liquidity = market_outcome.realized_liquidity.lower()

        if theory_mentions_liquidity:
            if "strong" in outcome_liquidity or "ample" in outcome_liquidity:
                return 0.7
            elif "weak" in outcome_liquidity or "fragmented" in outcome_liquidity:
                return 0.3
            else:
                return 0.5
        else:
            return 0.5

    def _volatility_alignment(
        self,
        theory_thesis,
        observation_text,
        market_outcome
    ) -> float:
        """Calculate volatility alignment between theory and outcome."""

        volatility_keywords = {
            "elevated": ["elevated", "high", "expanded"],
            "compressed": ["compressed", "low", "quiet", "stable"]
        }

        theory_volatility = None
        for vol_type, keywords in volatility_keywords.items():
            if any(k in theory_thesis for k in keywords):
                theory_volatility = vol_type
                break

        outcome_volatility = market_outcome.realized_volatility.lower()

        if theory_volatility == "elevated":
            if any(x in outcome_volatility for x in ["elevated", "high", "expanded"]):
                return 0.8
            elif "low" in outcome_volatility or "compressed" in outcome_volatility:
                return 0.2
            else:
                return 0.5

        elif theory_volatility == "compressed":
            if "low" in outcome_volatility or "compressed" in outcome_volatility:
                return 0.8
            elif any(x in outcome_volatility for x in ["elevated", "high"]):
                return 0.2
            else:
                return 0.5

        else:
            return 0.5

    def _detect_contradictions(
        self,
        assumptions,
        market_outcome,
        observation_text
    ) -> list[str]:
        """Detect contradictions between assumptions and outcome."""

        contradictions = []

        for assumption in assumptions:
            assumption_lower = assumption.lower()

            # Price strength vs weak breadth
            if ("strong" in assumption_lower and "price" in assumption_lower):
                if "weak" in market_outcome.realized_breadth.lower():
                    contradictions.append(
                        "Price strength contradicted by weak breadth"
                    )

            # Momentum persistence vs volatility expansion
            if "momentum" in assumption_lower:
                if "expand" in market_outcome.realized_volatility.lower():
                    contradictions.append(
                        "Momentum persistence weakened by volatility expansion"
                    )

            # Liquidity-led moves vs liquidity fragmentation
            if "liquidity" in assumption_lower:
                if "fragmented" in market_outcome.realized_liquidity.lower():
                    contradictions.append(
                        "Liquidity assumption contradicted by fragmentation"
                    )

        # Add outcome-detected contradictions
        contradictions.extend(market_outcome.outcome_contradictions)

        return list(set(contradictions))

    def _regime_mismatch(
        self,
        theory_thesis,
        observation_text,
        market_outcome
    ) -> float:
        """Detect regime mismatch between theory and outcome."""

        regime_keywords = {
            "trend_heavy": ["trending", "directional", "momentum"],
            "range_heavy": ["range-bound", "consolidat", "mean-revert"],
            "volatile": ["volatile", "choppy", "indecisive"],
            "quiet": ["quiet", "stable", "smooth"]
        }

        theory_regime = None
        for regime, keywords in regime_keywords.items():
            if any(k in theory_thesis for k in keywords):
                theory_regime = regime
                break

        outcome_strings = (
            market_outcome.realized_trend
            + " " + market_outcome.realized_volatility
        ).lower()

        outcome_regime = None
        for regime, keywords in regime_keywords.items():
            if any(k in outcome_strings for k in keywords):
                outcome_regime = regime
                break

        if theory_regime and outcome_regime:
            if theory_regime != outcome_regime:
                return 0.6
            else:
                return 0.0
        else:
            return 0.1

    def _generate_summary(
        self,
        theory_thesis,
        market_outcome,
        average_alignment,
        contradictions,
        regime_mismatch
    ) -> str:
        """Generate validation summary."""

        if average_alignment > 0.7:
            base = "Theory well-supported by market outcome. "
        elif average_alignment > 0.4:
            base = "Theory partially supported by market outcome. "
        else:
            base = "Theory weakly supported or contradicted by market outcome. "

        if contradictions:
            base += f"Detected {len(contradictions)} contradiction(s). "

        if regime_mismatch > 0.5:
            base += "Market regime shifted from theory expectations. "

        return base

    def _generate_recommendations(
        self,
        validation_score,
        contradictions,
        regime_mismatch,
        average_alignment
    ) -> list[str]:
        """Generate adaptation recommendations."""

        recommendations = []

        if validation_score < 0.3:
            recommendations.append(
                "Consider revising assumptions; reality diverged significantly"
            )

        if contradictions:
            recommendations.append(
                f"Investigate recurring contradictions: {contradictions[0]}"
            )

        if regime_mismatch > 0.5:
            recommendations.append(
                "Adapt confidence expectations for regime-sensitive assumptions"
            )

        if average_alignment > 0.7:
            recommendations.append(
                "Strengthen confidence in well-validated assumptions"
            )

        if not recommendations:
            recommendations.append(
                "Continue monitoring theory performance"
            )

        return recommendations
