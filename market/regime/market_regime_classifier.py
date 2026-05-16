class MarketRegimeClassifier:

    def classify(self, observation):

        return {
            "trend_regime": self._trend_regime(observation),
            "volatility_regime": self._volatility_regime(observation),
            "liquidity_regime": self._liquidity_regime(observation)
        }

    def _trend_regime(self, observation):

        trend = observation.trend_state.lower()
        breadth = observation.breadth_state.lower()

        if "higher" in trend or "up" in trend or "bullish" in trend:
            if "weak" in breadth or "narrow" in breadth:
                return "bullish_with_weak_breadth"

            return "bullish"

        if "lower" in trend or "down" in trend or "bearish" in trend:
            return "bearish"

        return "range_bound"

    def _volatility_regime(self, observation):

        volatility = observation.volatility_state.lower()

        if "expanded" in volatility or "high" in volatility:
            return "volatile"

        if "compressed" in volatility or "low" in volatility:
            return "volatility_compression"

        return "stable_volatility"

    def _liquidity_regime(self, observation):

        liquidity = observation.liquidity_state.lower()

        if "expanded" in liquidity or "broad" in liquidity:
            return "liquidity_expansion"

        if "narrow" in liquidity or "concentrated" in liquidity:
            return "liquidity_concentration"

        if "contracted" in liquidity or "thin" in liquidity:
            return "liquidity_contraction"

        return "liquidity_neutral"
