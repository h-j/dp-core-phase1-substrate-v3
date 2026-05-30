"""
Regime subtype classification with falsifiability anchors.

Evolves surface observations into explicit regime typologies with boundary conditions.
"""

from typing import Dict, List, Tuple


class RegimeSubtypeClassifier:
    """
    Classifies market regimes into semantic subtypes with falsifiability conditions.
    
    Subtypes:
    - Liquidity-constrained: Volume dry, participation weak, volatility compressed
    - Pressure-loaded range: elevated volume, gap down, rejection upper, range bound
    - Pressure-loaded: Contradictions elevated, multiple weak days, participation deteriorating
    - Fatigue: Momentum weakening, breadth weak, trend extended
    - Expansion-confirmed: Volume elevated, participation strong, volatility expanding
    - Neutral: Mixed or ambiguous signals
    """

    @staticmethod
    def classify(
        observation: object,
        prior_days_observations: List[object],
        contradiction_score: float = 0.0,
        momentum_regime: str = "flat",
    ) -> Tuple[str, List[str]]:
        """
        Classify regime subtype and return falsifiability conditions.
        
        Args:
            observation: Current MarketObservation
            prior_days_observations: Last 3-5 days of observations
            contradiction_score: Current contradiction severity (0-1)
            momentum_regime: "strengthening", "weakening", or "flat"
            
        Returns:
            (regime_subtype, falsifiability_conditions)
        """
        
        # Handle potential None or raw dict observations during synthesis
        if observation is None:
            return "neutral", ["requires additional confirmation signals"]
            
        get_val = lambda attr, default: (
            observation.get(attr, default) if isinstance(observation, dict) 
            else getattr(observation, attr, default)
        )

        # Extract signals
        volume_state = get_val("volume_state", "normal")
        liquidity_state = get_val("liquidity_state", "normal")
        participation_strength = get_val("participation_strength", "normal")
        volatility_state = get_val("volatility_state", "normal")
        trend_state = get_val("trend_state", "unknown")
        breadth_state = get_val("breadth_state", "unknown")
        candle_type = get_val("candle_type", "neutral")
        gap_pct = get_val("gap_pct", 0.0)
        
        # Compute context
        weak_prior_days = sum(
            1 for obs in prior_days_observations[-3:]
            if getattr(obs, "volume_state", "normal") == "dry" or
               getattr(obs, "participation_strength", "normal") == "weak"
        )
        
        is_liquidity_constrained = (
            volume_state == "dry" and 
            participation_strength == "weak" and
            volatility_state in ("compressed", "normal")
        )

        is_pressure_loaded_range = (
            volume_state == "elevated" and
            gap_pct < -0.2 and
            candle_type == "rejection_upper" and
            volatility_state in ("stable", "moderate") and
            trend_state == "range_bound"
        )
        
        is_pressure_loaded = (
            contradiction_score >= 0.5 and
            weak_prior_days >= 2 and
            participation_strength in ("weak", "deteriorated")
        )
        
        is_fatigue = (
            participation_strength == "weak" and
            momentum_regime == "weakening" and
            candle_type == "rejection_upper"
        )
        
        is_expansion_confirmed = (
            volume_state == "elevated" and
            participation_strength in ("strong", "normal") and
            volatility_state == "expanding"
        )
        
        # Classification logic
        if is_expansion_confirmed:
            subtype = "expansion_confirmed"
            conditions = [
                "volume drops below 20d moving average",
                "participation collapses to weak",
                "volatility reverts to compressed",
            ]
        elif is_pressure_loaded_range:
            subtype = "pressure_loaded_range"
            conditions = [
                "price closes above rejection high with stable volume",
                "volatility contracts below average",
            ]
        elif is_liquidity_constrained:
            subtype = "liquidity_constrained"
            conditions = [
                "volume exceeds 5-day average and participation strengthens",
            ]
        elif is_pressure_loaded:
            subtype = "pressure_loaded"
            conditions = [
                "breadth reversal after multi-day decline",
                "participation strengthens despite pressure",
                "contradiction severity drops below 0.4",
            ]
        elif is_fatigue:
            subtype = "fatigue"
            conditions = [
                "momentum re-accelerates despite weak participation",
            ]
        else:
            subtype = "neutral"
            conditions = [
                "requires additional confirmation signals",
            ]
        
        return subtype, conditions
    
    @staticmethod
    def get_regime_description(regime_subtype: str) -> str:
        """Get narrative description of regime subtype."""
        descriptions = {
            "pressure_loaded_range": (
                "Market absorbing supply at resistance after a gap down. "
                "Elevated volume on rejection candles indicates active distribution. "
                "Historical tendency: 3-5 day range before resolving directionally."
            ),
            "liquidity_constrained": (
                "Market structure limited by dry volume and fading liquidity. "
                "Volatility compressed, participation selective. "
                "Historical tendency: 2–3 day consolidation before breakout or reversal."
            ),
            "pressure_loaded": (
                "Multiple consecutive weak days accumulating contradiction pressure. "
                "Participation deteriorating despite elevated volume. "
                "Historical tendency: either sharp mean reversion or breakout within 3–5 days."
            ),
            "fatigue": (
                "Momentum weakening under breadth deterioration. "
                "Participation weak, trend extended. "
                "Historical tendency: consolidation or reversal within 2–3 days."
            ),
            "expansion_confirmed": (
                "Volume elevated with strong participation. "
                "Volatility expanding, direction confirmed. "
                "Historical tendency: continuation for 3–5 days unless contradicted."
            ),
            "neutral": (
                "Mixed or ambiguous regime signals. "
                "Requires additional confirmation. "
                "Historical tendency: neutral until clearer signals emerge."
            ),
        }
        return descriptions.get(regime_subtype, "Unknown regime")
    
    @staticmethod
    def evaluate_falsifiability(
        observation: object,
        regime_subtype: str,
        falsifiability_conditions: List[str],
    ) -> Tuple[bool, List[str]]:
        """
        Evaluate whether falsifiability conditions have been met (regime is contradicted).
        
        Returns:
            (falsified, triggered_conditions)
        """
        triggered = []
        
        volume_state = getattr(observation, "volume_state", "normal")
        participation_strength = getattr(observation, "participation_strength", "normal")
        volatility_state = getattr(observation, "volatility_state", "normal")
        breadth_state = getattr(observation, "breadth_state", "unknown")
        momentum_regime = getattr(observation, "momentum_regime", "flat")
        candle_type = getattr(observation, "candle_type", "neutral")
        
        # Map conditions to evaluation
        condition_checks = {
            "volume exceeds 5d moving average": volume_state == "elevated",
            "volume exceeds 5-day average and participation strengthens": (
                volume_state == "elevated" and participation_strength in ("normal", "strong")
            ),
            "participation normalizes or strengthens": participation_strength in ("normal", "strong"),
            "liquidity returns to normal": getattr(observation, "liquidity_state", "normal") == "normal",
            "volume drops below 20d moving average": volume_state == "dry",
            "participation collapses to weak": participation_strength == "weak",
            "volatility reverts to compressed": volatility_state == "compressed",
            "volatility contracts below average": volatility_state == "compressed",
            "price closes above rejection high with stable volume": (
                candle_type in ("strong_bull", "expansion") and volume_state == "normal"
            ),
            "breadth reversal after multi-day decline": breadth_state == "strengthened",
            "participation strengthens despite pressure": participation_strength in ("normal", "strong"),
            "contradiction severity drops below 0.4": False,  # Evaluated externally
            "momentum re-accelerates while participation remains weak": (
                momentum_regime == "strengthening" and participation_strength == "weak"
            ),
            "momentum re-accelerates despite weak participation": (
                momentum_regime == "strengthening" and participation_strength == "weak"
            ),
            "breadth strengthens after deterioration": breadth_state == "strengthened",
            "volatility expands unexpectedly": volatility_state == "expanding",
            "requires additional confirmation signals": False,  # Always incomplete
        }
        
        for condition in falsifiability_conditions:
            if condition_checks.get(condition, False):
                triggered.append(condition)
        
        falsified = len(triggered) > 0
        return falsified, triggered
