"""
Deterministic market observation synthesis from historical NIFTY data.

Generates observations using rule-based heuristics:
- trend state from price action
- volatility regime from rolling volatility
- liquidity inferences from volume
- breadth heuristics from directional persistence
- contradiction markers from detected mismatches
"""

import pandas as pd

from market.schemas.market_observation import MarketObservation


class MarketObservationSynthesizer:
    """
    Synthesizes deterministic market observations from NIFTY data.
    
    Rule-based synthesis ensures:
    - reproducibility
    - inspectability
    - no LLM drift
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize synthesizer with historical data.
        
        Args:
            data: DataFrame with OHLCV + optional derived fields
        """
        self.data = data.reset_index(drop=True)

    def synthesize(self, day_index: int) -> MarketObservation:
        """
        Generate market observation for a specific day.
        
        Args:
            day_index: 0-based index into data
            
        Returns:
            MarketObservation instance
        """
        if day_index < 0 or day_index >= len(self.data):
            raise IndexError(
                f"Day index {day_index} out of range (0-{len(self.data)-1})"
            )

        row = self.data.iloc[day_index]
        date_str = row["date"]

        # v2.0 Enriched descriptors
        descriptors = self._derive_enriched_descriptors(row)
        candle_structure = self._derive_candle_structure(row)
        participation_signals = self._derive_participation_signals(row)

        # Derive observation components
        trend_state = self._derive_trend_state(day_index)
        volatility_state = self._derive_volatility_state(day_index)
        liquidity_state = self._derive_liquidity_state(day_index)
        breadth_state = self._derive_breadth_state(day_index)
        macro_sentiment = self._derive_macro_sentiment(
            trend_state,
            volatility_state,
            breadth_state,
            descriptors,
            participation_signals,
        )
        contradiction_markers = self._detect_contradiction_markers(
            trend_state,
            volatility_state,
            breadth_state,
            liquidity_state,
            candle_structure,
            participation_signals,
        )

        observation_text = self._synthesize_text(
            trend_state,
            volatility_state,
            liquidity_state,
            breadth_state,
            macro_sentiment,
            descriptors,
            candle_structure,
            participation_signals,
        )

        return MarketObservation(
            market_name="NIFTY 50",
            observation_text=observation_text,
            trend_state=trend_state,
            volatility_state=volatility_state,
            liquidity_state=liquidity_state,
            breadth_state=breadth_state,
            macro_sentiment=macro_sentiment,
            contradiction_markers=contradiction_markers,
            # v2.0 Enriched fields
            volume_state=row.get("volume_state", "normal"),
            volume_ratio_5d=float(row.get("volume_ratio_5d", 1.0)),
            volume_ratio_20d=float(row.get("volume_ratio_20d", 1.0)),
            range_pct=float(row.get("range_pct", 0.0)),
            gap_pct=float(row.get("gap_pct", 0.0)),
            atr_14=float(row.get("atr_14", 0.0)),
            rolling_volatility_10d=float(row.get("rolling_volatility_10d", 0.0)),
            rolling_volatility_30d=float(row.get("rolling_volatility_30d", 0.0)),
            return_3d=float(row.get("return_3d", 0.0)),
            return_5d=float(row.get("return_5d", 0.0)),
            # v2.0 Enriched dimensions
            volatility_regime=volatility_state,
            momentum_regime="strengthening" if float(row.get("return_3d", 0.0)) > 0.5 else "weakening" if float(row.get("return_3d", 0.0)) < -0.5 else "flat",
            descriptors=descriptors,
            body_pct=candle_structure["body_pct"],
            upper_wick_pct=candle_structure["upper_wick_pct"],
            lower_wick_pct=candle_structure["lower_wick_pct"],
            close_position_pct=candle_structure["close_position_pct"],
            open_position_pct=candle_structure["open_position_pct"],
            candle_type=candle_structure["candle_type"],
            participation_strength=participation_signals["participation_strength"],
            participation_confirmation=participation_signals["participation_confirmation"],
            observation_source=f"replay_engine_{date_str}"
        )

    def _derive_trend_state(self, day_index: int) -> str:
        """Determine trend state from price action."""
        row = self.data.iloc[day_index]
        open_price = float(row["open"])
        close_price = float(row["close"])
        high_price = float(row["high"])
        low_price = float(row["low"])

        # Intraday direction
        intraday_return = (close_price - open_price) / open_price

        if intraday_return > 0.005:  # +0.5%
            intraday_direction = "up"
        elif intraday_return < -0.005:  # -0.5%
            intraday_direction = "down"
        else:
            intraday_direction = "neutral"

        # Multi-day persistence (if available)
        if day_index >= 2:
            prior_close = float(self.data.iloc[day_index - 1]["close"])
            trend_persistence = (close_price - prior_close) / prior_close

            if trend_persistence > 0.01 and intraday_direction == "up":
                return "extended_higher"
            elif trend_persistence > 0.005 and intraday_direction == "up":
                return "closed_higher"
            elif trend_persistence < -0.01 and intraday_direction == "down":
                return "extended_lower"
            elif trend_persistence < -0.005 and intraday_direction == "down":
                return "closed_lower"
            elif abs(trend_persistence) < 0.003:
                return "range_bound"

        if intraday_direction == "up":
            return "closed_higher"
        elif intraday_direction == "down":
            return "closed_lower"
        else:
            return "range_bound"

    def _derive_volatility_state(self, day_index: int) -> str:
        """Determine volatility regime."""
        row = self.data.iloc[day_index]

        # Intraday range
        high_price = float(row["high"])
        low_price = float(row["low"])
        close_price = float(row["close"])
        intraday_range_pct = (high_price - low_price) / close_price * 100

        # Rolling volatility if available
        if "rolling_volatility_30d" in row:
            vol_30d = float(row["rolling_volatility_30d"])

            if vol_30d > 2.0:  # High volatility
                if intraday_range_pct > 1.5:
                    return "expanded"
                else:
                    return "high"
            elif vol_30d > 1.0:  # Moderate
                if intraday_range_pct > 1.0:
                    return "moderate"
                else:
                    return "stable"
            else:  # Low volatility
                return "compressed"

        # Fallback to intraday range
        if intraday_range_pct > 1.5:
            return "expanded"
        elif intraday_range_pct > 0.8:
            return "moderate"
        else:
            return "compressed"

    def _derive_liquidity_state(self, day_index: int) -> str:
        """Infer liquidity state from volume and price action."""
        row = self.data.iloc[day_index]
        volume = float(row["volume"])

        # Volume trend
        if day_index >= 20:
            avg_volume = self.data.iloc[max(0, day_index - 20):day_index]["volume"].mean()
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        else:
            volume_ratio = 1.0

        # Price strength with volume
        intraday_return = (
            (float(row["close"]) - float(row["open"])) / float(row["open"])
        )

        if volume_ratio > 1.2:
            if intraday_return > 0:
                return "ample_with_strength"
            else:
                return "ample_with_selling"
        elif volume_ratio > 0.8:
            if abs(intraday_return) > 0.005:
                return "broad_participation"
            else:
                return "even_flow"
        else:
            if abs(intraday_return) > 0.01:
                return "concentrated_in_large_caps"
            else:
                return "selective"

    def _derive_breadth_state(self, day_index: int) -> str:
        """
        Derive breadth from directional persistence.
        
        In absence of true breadth data, use rolling trend consistency
        as a proxy for participation quality.
        """
        if day_index < 5:
            return "nascent"

        # Look at last 5 days
        window = self.data.iloc[max(0, day_index - 4):day_index + 1]
        up_days = (window["close"] > window["open"]).sum()
        down_days = (window["close"] <= window["open"]).sum()

        up_ratio = up_days / len(window)

        if up_ratio >= 0.8:
            return "strongly_participatory"
        elif up_ratio >= 0.6:
            return "strengthened"
        elif up_ratio >= 0.4:
            return "mixed"
        elif up_ratio >= 0.2:
            return "weakened"
        else:
            return "deteriorated"

    def _derive_macro_sentiment(
        self,
        trend_state: str,
        volatility_state: str,
        breadth_state: str,
        descriptors: list = None,
        participation_signals: dict | None = None,
    ) -> str:
        """Synthesize macro sentiment from components."""
        # Positive indicators
        positive_list = [
            "higher" in trend_state or "extended" in trend_state,
            volatility_state in ["compressed", "stable"],
            breadth_state in ["strengthened", "strongly_participatory"],
        ]

        # Negative indicators
        negative = sum([
            "lower" in trend_state or "deteriorated" in trend_state,
            volatility_state in ["expanded", "high"],
            breadth_state in ["weakened", "deteriorated"],
        ])

        # v2.0 momentum influence
        if descriptors:
            if "short-term momentum strengthening" in descriptors:
                positive_list.append(True)
            if "short-term momentum weakening" in descriptors:
                negative += 1

        if participation_signals:
            if participation_signals.get("participation_confirmation") == "bullish_confirmed":
                positive_list.append(True)
            if participation_signals.get("participation_confirmation") == "bearish_confirmed":
                negative += 1
            if participation_signals.get("participation_confirmation") == "divergence":
                negative += 1

        positive = sum(positive_list)

        if positive >= 2:
            return "positive"
        elif negative >= 2:
            return "risk_off"
        elif positive == 1 and negative == 0:
            return "cautiously_positive"
        elif negative == 1 and positive == 0:
            return "uncertain"
        else:
            return "neutral"

    def _detect_contradiction_markers(
        self,
        trend_state: str,
        volatility_state: str,
        breadth_state: str,
        liquidity_state: str,
        candle_structure: dict,
        participation_signals: dict,
    ) -> list:
        """Detect contradiction markers in market state."""
        markers = []

        # Price up + breadth down
        if ("higher" in trend_state or "extended_higher" in trend_state) and (
            "weakened" in breadth_state or "deteriorated" in breadth_state
        ):
            markers.append("price_up_breadth_down")

        # Momentum but volatility expanding
        if "extended" in trend_state and (
            "expanded" in volatility_state or "high" in volatility_state
        ):
            markers.append("momentum_with_volatility_expansion")

        # Liquidity concentration with weak breadth
        if "concentrated" in liquidity_state and (
            "weakened" in breadth_state or "deteriorated" in breadth_state
        ):
            markers.append("liquidity_concentration_weak_breadth")

        # Range bound with volatility lift
        if "range_bound" in trend_state and (
            "expanded" in volatility_state or "high" in volatility_state
        ):
            markers.append("range_bound_volatility_expansion")

        if candle_structure.get("candle_type") == "indecision":
            markers.append("indecision_candle")

        if participation_signals.get("participation_confirmation") == "divergence":
            markers.append("price_participation_divergence")

        return markers

    def _synthesize_text(
        self,
        trend_state: str,
        volatility_state: str,
        liquidity_state: str,
        breadth_state: str,
        macro_sentiment: str,
        descriptors: list = None,
        candle_structure: dict | None = None,
        participation_signals: dict | None = None,
    ) -> str:
        """Generate human-readable observation text."""
        components = []

        # v2.0 Enriched descriptors prefix
        if descriptors:
            components.append(f"[{', '.join(descriptors)}]")

        if candle_structure:
            candle_label = candle_structure.get("candle_type", "neutral").replace("_", " ")
            components.append(f"candle {candle_label}")

        if participation_signals:
            participation_label = participation_signals.get("participation_strength", "normal")
            confirmation_label = participation_signals.get("participation_confirmation", "normal").replace("_", " ")
            components.append(f"participation {participation_label} ({confirmation_label})")

        # Trend
        if "higher" in trend_state:
            components.append("NIFTY closed higher")
        elif "lower" in trend_state:
            components.append("NIFTY closed lower")
        elif "range_bound" in trend_state:
            components.append("NIFTY traded range-bound")
        else:
            components.append("NIFTY showed mixed action")

        # Volatility
        if "compressed" in volatility_state:
            components.append("with volatility compressed")
        elif "expanded" in volatility_state:
            components.append("while volatility expanded")
        elif "stable" in volatility_state:
            components.append("with stable volatility")
        else:
            components.append("amid moderate volatility")

        # Breadth and liquidity
        if "strengthened" in breadth_state:
            components.append("and breadth strengthened")
        elif "weakened" in breadth_state:
            components.append("but breadth weakened")
        elif "participatory" in breadth_state:
            components.append("with broad participation")

        # Construct sentence
        text = " ".join(components) + "."

        # Add liquidity context if notable
        if "concentrated" in liquidity_state:
            text += " Liquidity remained concentrated in large-caps."
        elif "selective" in liquidity_state:
            text += " Participation was selective."

        return text

    def _derive_enriched_descriptors(self, row: pd.Series) -> list:
        """Structured market descriptors for v2.0."""
        descriptors = []
        
        # 1. Volume State
        vol_state = row.get("volume_state", "normal")
        if vol_state != "normal":
            descriptors.append(f"volume {vol_state}")
        
        # 2. Price Range Action
        range_pct = float(row.get("range_pct", 0.0))
        if range_pct > 1.3:
            descriptors.append("range expanding")
        elif range_pct < 0.7:
            descriptors.append("range narrow")
            
        # 3. Gaps
        gap_pct = float(row.get("gap_pct", 0.0))
        if gap_pct > 0.2:
            descriptors.append("gap up")
        elif gap_pct < -0.2:
            descriptors.append("gap down")
            
        # 4. Volatility Regimes
        vol_30d = float(row.get("rolling_volatility_30d", 0.0))
        if vol_30d < 0.8:
            descriptors.append("volatility compressed")
        elif vol_30d > 1.5:
            descriptors.append("volatility expanding")
            
        # 5. Momentum Regimes
        ret_3d = float(row.get("return_3d", 0.0))
        if ret_3d > 0.7:
            descriptors.append("short-term momentum strengthening")
        elif ret_3d < -0.7:
            descriptors.append("short-term momentum weakening")
            
        return descriptors

    def _derive_candle_structure(self, row: pd.Series) -> dict:
        """Derive structured candle metrics from OHLC."""
        open_price = float(row["open"])
        high_price = float(row["high"])
        low_price = float(row["low"])
        close_price = float(row["close"])
        range_value = max(high_price - low_price, 1e-9)

        body_pct = abs(close_price - open_price) / range_value
        upper_wick_pct = max(high_price - max(open_price, close_price), 0.0) / range_value
        lower_wick_pct = max(min(open_price, close_price) - low_price, 0.0) / range_value
        close_position_pct = (close_price - low_price) / range_value
        open_position_pct = (open_price - low_price) / range_value
        daily_return_pct = (close_price - open_price) / open_price * 100

        candle_type = "neutral"
        if body_pct >= 0.65 and close_position_pct >= 0.7 and daily_return_pct > 0:
            candle_type = "strong_bull"
        elif body_pct >= 0.65 and close_position_pct <= 0.3 and daily_return_pct < 0:
            candle_type = "strong_bear"
        elif upper_wick_pct >= 0.5 and body_pct < 0.4:
            candle_type = "rejection_upper"
        elif lower_wick_pct >= 0.5 and body_pct < 0.4:
            candle_type = "rejection_lower"
        elif body_pct < 0.25 and max(upper_wick_pct, lower_wick_pct) < 0.35:
            candle_type = "indecision"
        elif body_pct < 0.3 and range_value / max(open_price, 1e-9) < 0.008:
            candle_type = "compression"
        elif body_pct > 0.5 and range_value / max(open_price, 1e-9) > 0.012:
            candle_type = "expansion"

        return {
            "body_pct": round(body_pct, 4),
            "upper_wick_pct": round(upper_wick_pct, 4),
            "lower_wick_pct": round(lower_wick_pct, 4),
            "close_position_pct": round(close_position_pct, 4),
            "open_position_pct": round(open_position_pct, 4),
            "candle_type": candle_type,
        }

    def _derive_participation_signals(self, row: pd.Series) -> dict:
        """Derive participation strength and confirmation from volume ratios."""
        volume_ratio_5d = float(row.get("volume_ratio_5d", 1.0))
        volume_ratio_20d = float(row.get("volume_ratio_20d", 1.0))
        open_price = float(row["open"])
        close_price = float(row["close"])
        daily_return_pct = (close_price - open_price) / open_price * 100

        if volume_ratio_5d > 1.15 and volume_ratio_20d > 1.1:
            participation_strength = "strong"
        elif volume_ratio_5d < 0.9 and volume_ratio_20d < 0.95:
            participation_strength = "weak"
        else:
            participation_strength = "normal"

        if daily_return_pct > 0.8 and volume_ratio_5d > 1.1 and volume_ratio_20d > 1.0:
            participation_confirmation = "bullish_confirmed"
        elif daily_return_pct < -0.8 and volume_ratio_5d > 1.1 and volume_ratio_20d > 1.0:
            participation_confirmation = "bearish_confirmed"
        elif abs(daily_return_pct) > 0.8 and (
            volume_ratio_5d < 0.95 or volume_ratio_20d < 0.95
        ):
            participation_confirmation = "divergence"
        elif abs(daily_return_pct) > 0.4 and volume_ratio_5d < 0.9:
            participation_confirmation = "weak_move"
        else:
            participation_confirmation = "normal"

        return {
            "participation_strength": participation_strength,
            "participation_confirmation": participation_confirmation,
        }
