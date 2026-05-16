from collections import defaultdict
from datetime import datetime, UTC, timedelta


class MarketContradictionMapper:
    """
    Detects and maps recurring contradiction zones in market behavior.
    
    Identifies:
    - Price strength vs weak breadth
    - Momentum persistence vs volatility expansion
    - Liquidity concentration vs broad participation weakness
    - Other unstable market patterns
    """

    def __init__(self):
        self.contradiction_history = defaultdict(list)
        self.zone_intensity = defaultdict(float)

    def detect_zones(
        self,
        market_observation,
        market_outcome,
        prior_theory
    ):
        """Detect contradiction zones from market behavior."""

        zones = []

        # Price strength vs weak breadth
        if self._detect_price_breadth_divergence(
            market_observation,
            market_outcome
        ):
            zones.append({
                "zone": "price_breadth_divergence",
                "description": "Price strength contradicted by weak breadth",
                "severity": self._calc_price_breadth_severity(
                    market_observation,
                    market_outcome
                ),
                "timestamp": datetime.now(UTC)
            })

        # Momentum persistence vs volatility expansion
        if self._detect_momentum_volatility_mismatch(
            market_observation,
            market_outcome
        ):
            zones.append({
                "zone": "momentum_volatility_mismatch",
                "description": "Momentum persistence weakened by volatility expansion",
                "severity": self._calc_momentum_volatility_severity(
                    market_outcome
                ),
                "timestamp": datetime.now(UTC)
            })

        # Liquidity concentration vs participation
        if self._detect_liquidity_participation_gap(
            market_observation,
            market_outcome
        ):
            zones.append({
                "zone": "liquidity_participation_gap",
                "description": "Liquidity concentration despite broad participation weakness",
                "severity": self._calc_liquidity_participation_severity(
                    market_outcome
                ),
                "timestamp": datetime.now(UTC)
            })

        # Trend continuation assumptions failing
        if self._detect_trend_reversal_zone(
            market_observation,
            market_outcome,
            prior_theory
        ):
            zones.append({
                "zone": "trend_reversal_zone",
                "description": "Expected trend continuation failed",
                "severity": 0.7,
                "timestamp": datetime.now(UTC)
            })

        # Update history
        for zone in zones:
            self.contradiction_history[zone["zone"]].append(
                zone["timestamp"]
            )
            self.zone_intensity[zone["zone"]] = zone["severity"]

        return zones

    def map_recurring_zones(self, lookback_hours: int = 168) -> dict:
        """Map recurring contradiction zones with frequency."""

        cutoff_time = datetime.now(UTC) - timedelta(hours=lookback_hours)

        zone_frequencies = {}

        for zone_name, timestamps in self.contradiction_history.items():

            recent_timestamps = [
                ts for ts in timestamps if ts > cutoff_time
            ]

            if recent_timestamps:
                zone_frequencies[zone_name] = {
                    "occurrences": len(recent_timestamps),
                    "intensity": self.zone_intensity.get(zone_name, 0.5),
                    "last_occurrence": max(recent_timestamps)
                }

        # Sort by frequency
        sorted_zones = sorted(
            zone_frequencies.items(),
            key=lambda x: x[1]["occurrences"],
            reverse=True
        )

        return {
            "recurring_zones": dict(sorted_zones),
            "hotspot_count": len(sorted_zones),
            "most_severe": (
                sorted_zones[0]
                if sorted_zones
                else None
            )
        }

    def generate_contradiction_map(self) -> str:
        """Generate human-readable contradiction map."""

        mapping = self.map_recurring_zones()

        summary = "Contradiction Zone Map: "

        zones = mapping["recurring_zones"]

        if zones:
            for zone_name, data in list(zones.items())[:3]:
                summary += (
                    f"{zone_name.replace('_', ' ').title()} "
                    f"({data['occurrences']} occurrences, "
                    f"severity {data['intensity']:.2f}). "
                )
        else:
            summary += "No recurring contradiction zones detected."

        return summary

    def _detect_price_breadth_divergence(
        self,
        market_observation,
        market_outcome
    ) -> bool:
        """Detect price strength vs weak breadth contradiction."""

        trend_strong = any(
            word in market_outcome.realized_trend.lower()
            for word in ["higher", "strong", "up"]
        )

        breadth_weak = any(
            word in market_outcome.realized_breadth.lower()
            for word in ["weak", "narrow", "divergence", "limited"]
        )

        return trend_strong and breadth_weak

    def _calc_price_breadth_severity(
        self,
        market_observation,
        market_outcome
    ) -> float:
        """Calculate severity of price-breadth divergence."""

        if "divergence" in market_outcome.realized_breadth.lower():
            return 0.9
        elif "weak" in market_outcome.realized_breadth.lower():
            return 0.7
        else:
            return 0.5

    def _detect_momentum_volatility_mismatch(
        self,
        market_observation,
        market_outcome
    ) -> bool:
        """Detect momentum persistence vs volatility expansion."""

        momentum_expected = any(
            word in market_observation.observation_text.lower()
            for word in ["momentum", "continuation", "persistent"]
        )

        volatility_expanded = any(
            word in market_outcome.realized_volatility.lower()
            for word in ["expanded", "elevated", "high"]
        )

        return momentum_expected and volatility_expanded

    def _calc_momentum_volatility_severity(
        self,
        market_outcome
    ) -> float:
        """Calculate severity of momentum-volatility mismatch."""

        if "expanded" in market_outcome.realized_volatility.lower():
            return 0.85
        elif "elevated" in market_outcome.realized_volatility.lower():
            return 0.7
        else:
            return 0.5

    def _detect_liquidity_participation_gap(
        self,
        market_observation,
        market_outcome
    ) -> bool:
        """Detect liquidity concentration vs participation weakness."""

        liquidity_strong = any(
            word in market_outcome.realized_liquidity.lower()
            for word in ["ample", "strong", "concentrated"]
        )

        participation_weak = any(
            word in market_outcome.realized_breadth.lower()
            for word in ["weak", "narrow", "selective"]
        )

        return liquidity_strong and participation_weak

    def _calc_liquidity_participation_severity(
        self,
        market_outcome
    ) -> float:
        """Calculate severity of liquidity-participation gap."""

        if "fragmented" in market_outcome.realized_liquidity.lower():
            return 0.75
        elif "concentrated" in market_outcome.realized_liquidity.lower():
            return 0.65
        else:
            return 0.5

    def _detect_trend_reversal_zone(
        self,
        market_observation,
        market_outcome,
        prior_theory
    ) -> bool:
        """Detect zones where trend assumptions reversed."""

        if not prior_theory:
            return False

        theory_predicts_continuation = any(
            word in prior_theory.thesis.lower()
            for word in ["continuation", "persistent", "momentum"]
        )

        outcome_shows_reversal = any(
            word in market_outcome.realized_trend.lower()
            for word in ["reversal", "correction", "reversed"]
        )

        return theory_predicts_continuation and outcome_shows_reversal
