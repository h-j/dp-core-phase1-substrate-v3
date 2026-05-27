"""
Deterministic transition pressure inference for replay.

Infers market transition readiness without modifying theory generation.
Derived from: horizon state, regime similarity, contradiction dynamics,
confidence trends, breadth signals, theory usefulness.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Iterable, List


@dataclass(frozen=True)
class TransitionPressure:
    """Lightweight transition pressure signal."""

    direction_bias: str  # "higher" | "lower" | "neutral"
    pressure_score: float  # 0..1, intensity of transition readiness
    stability_score: float  # 0..1, robustness of current state
    drivers: List[str]  # observed signals driving pressure
    breakout_risk: bool  # True if probability of directional move elevated

    def to_dict(self) -> dict:
        return {
            "direction_bias": self.direction_bias,
            "pressure_score": round(self.pressure_score, 3),
            "stability_score": round(self.stability_score, 3),
            "drivers": self.drivers,
            "breakout_risk": self.breakout_risk,
        }


class TransitionPressureEngine:
    """Deterministic transition pressure inference from replay state."""

    def infer(
        self,
        observation: object,
        horizons: object,
        regime_matches: Iterable[object],
        confidence_state: object,
        contradiction_result: dict,
        reflection: object,
        theory_usefulness: dict,
        prior_observations: List[object],
        volume_state: str = "normal",
        atr_expansion: bool = False,
    ) -> TransitionPressure:
        """
        Infer transition pressure from current replay state.

        Args:
            observation: Current market observation
            horizons: HorizonView (daily, weekly, monthly structure)
            regime_matches: Prior similar regimes
            confidence_state: Current confidence levels
            contradiction_result: Contradiction detection output
            reflection: Current reflection output
            theory_usefulness: Theory epistemic scoring
            prior_observations: Recent observations for trend analysis
            volume_state: Current volume regime (v2.1)
            atr_expansion: Whether ATR is expanding (v2.1)

        Returns:
            TransitionPressure signal
        """
        drivers = []
        pressure_components = []
        stability_components = []

        # 1. Horizon divergence (weekly/monthly structure change)
        horizon_divergence = self._infer_horizon_divergence(horizons, prior_observations)
        if horizon_divergence > 0.0:
            drivers.append(f"horizon_divergence_{horizon_divergence:.2f}")
            pressure_components.append(horizon_divergence)

        # 2. Regime similarity weakening
        regime_sim = self._extract_regime_similarity(regime_matches)
        regime_weakening = self._detect_regime_weakening(prior_observations)
        if regime_weakening:
            drivers.append("regime_similarity_weakening")
            pressure_components.append(0.40)  # TUNED: 0.35 → 0.40
        if regime_sim < 0.50:
            stability_components.append(0.25)  # TUNED: 0.4 → 0.25 (decay faster)
        else:
            stability_components.append(0.8)

        # 3. Contradiction dynamics (rising, stacking, persistent)
        contradiction_rising = self._detect_contradiction_rising(
            prior_observations, contradiction_result
        )
        contradiction_score = float(contradiction_result.get("score", 0.0))
        
        # v2.1 CALIBRATION: Reduce contradiction weight contribution by ~25%
        if contradiction_score > 0.2:
            if contradiction_score >= 0.6:
                drivers.append(f"contradiction_severe_{contradiction_score:.2f}")
                # TUNED v2.1: 0.70 -> 0.55 base weight
                severity_weight = min(0.85, 0.55 + (contradiction_score - 0.6) * 0.4)
                pressure_components.append(severity_weight)
                stability_components.append(0.15)
            elif contradiction_score > 0.5:
                drivers.append(f"contradiction_high_{contradiction_score:.2f}")
                pressure_components.append(0.40) # TUNED: 0.50 -> 0.40
                stability_components.append(0.25)
            elif contradiction_rising:
                drivers.append("contradiction_rising")
                pressure_components.append(0.30) # TUNED: 0.40 -> 0.30
            
            if contradiction_score < 0.5:
                stability_components.append(0.5)
        else:
            stability_components.append(0.75)

        # v2.1 ATR and Volume Calibration
        if atr_expansion:
            drivers.append("atr_expansion_confirmed")
            pressure_components.append(0.65) # Strong structural driver
        
        if volume_state == "elevated":
            drivers.append("volume_elevated_confirmation")
            pressure_components.append(0.50)
        elif volume_state == "dry":
            drivers.append("volume_dry_divergence")
            stability_components.append(0.30) # Dry volume reduces stability

        # 4. Breadth signals (strengthening/weakening in range-bound)
        trend = getattr(observation, "trend_state", "").lower()
        breadth = getattr(observation, "breadth_state", "").lower()
        breadth_signal = None
        
        if "range_bound" in trend or "range" in trend:
            if "strengthened" in breadth or "strong" in breadth:
                breadth_signal = "strengthening"
                drivers.append("breadth_strengthening_in_range")
                pressure_components.append(0.48)  # TUNED: 0.42 → 0.48
            elif "weakened" in breadth or "weak" in breadth or "deteriorat" in breadth:
                breadth_signal = "weakening"
                drivers.append("breadth_weakening_in_range")
                pressure_components.append(0.55)  # TUNED: 0.48 → 0.55
        
        # TUNED: Amplify pressure when range-bound + breadth signal + high contradiction align
        if breadth_signal and contradiction_score >= 0.5:
            drivers.append("range_bound_contradiction_alignment")
            pressure_components.append(0.35)  # TUNED: 0.25 → 0.35 (higher synergy bonus)

        # 5. Confidence weakening
        empirical_conf = getattr(confidence_state, "empirical_confidence", 0.5)
        coherence = getattr(confidence_state, "theoretical_coherence", 0.5)
        if empirical_conf < 0.45:
            drivers.append(f"confidence_weakening_{empirical_conf:.2f}")
            pressure_components.append(0.28)  # TUNED: 0.25 → 0.28
        if coherence < 0.40:
            drivers.append(f"coherence_degrading_{coherence:.2f}")
            pressure_components.append(0.22)  # TUNED: 0.20 → 0.22

        # 6. Theory usefulness deteriorating
        usefulness_score = float(theory_usefulness.get("score", 0.5))
        if usefulness_score < 0.4:
            drivers.append(f"theory_usefulness_low_{usefulness_score:.2f}")
            pressure_components.append(0.12)  # v2.1 TUNED: 0.18 -> 0.12

        # 7. Reflection uncertainty
        reflection_text = getattr(reflection, "reflection_summary", "").lower()
        if "uncertain" in reflection_text or "fragile" in reflection_text:
            drivers.append("reflection_uncertainty")
            pressure_components.append(0.12)  # v2.1 TUNED: 0.18 -> 0.12

        # Infer direction bias
        direction_bias = self._infer_direction_bias(
            observation, breadth, drivers, pressure_components
        )

        # Compute aggregates
        pressure_score = (
            mean(pressure_components) if pressure_components else 0.0
        )
        stability_score = (
            mean(stability_components) if stability_components else 0.7
        )

        # TUNED v2: Apply pressure multiplier when high contradiction + breadth signals align
        if contradiction_score >= 0.6 and breadth_signal:
            # Strong amplification for confirmed contradiction + breadth signal
            pressure_score = min(1.0, pressure_score * 1.3)  # 30% multiplier
        elif contradiction_score >= 0.6:
            # Moderate amplification for high contradiction alone
            pressure_score = min(1.0, pressure_score * 1.15)  # 15% multiplier

        # TUNED: Dynamic stability decay when regime + contradiction align
        if regime_weakening and contradiction_score >= 0.5:
            stability_score = max(0.0, stability_score - 0.15)  # ADDED: accelerated decay

        # Breakout risk: TUNED thresholds and driver-count sensitivity
        driver_count = len(drivers)
        breakout_risk = False
        
        # v2.1 Tighten breakout risk thresholds to ensure higher signal quality
        if driver_count >= 4:
            breakout_risk = (
                pressure_score > 0.52  # v2.1: 0.40 -> 0.52
                and stability_score < 0.65 
                and (regime_weakening or contradiction_rising or atr_expansion)
            )
        elif driver_count >= 3:
            breakout_risk = (
                pressure_score > 0.58  # v2.1: 0.42 -> 0.58
                and stability_score < 0.60 
                and (atr_expansion or (contradiction_score >= 0.6 and volume_state != "dry"))
            )
        else:
            breakout_risk = (
                pressure_score > 0.70  # v2.1: 0.60 -> 0.70
                and stability_score < 0.45 
                and atr_expansion
            )

        # v2.1 Requirement: breakout risk requires volume validation
        if volume_state == "dry":
            breakout_risk = False

        return TransitionPressure(
            direction_bias=direction_bias,
            pressure_score=float(min(1.0, pressure_score)),
            stability_score=float(min(1.0, max(0.0, stability_score))),
            drivers=drivers[:12],  # TUNED: 10 → 12 (allow more context)
            breakout_risk=breakout_risk,
        )

    def _infer_horizon_divergence(
        self, horizons: object, prior_observations: List[object]
    ) -> float:
        """Detect structural divergence in horizons."""
        daily = getattr(horizons, "daily", "")
        weekly = getattr(horizons, "weekly", "")
        monthly = getattr(horizons, "monthly", "")

        if daily and weekly and monthly:
            # Divergence: daily suggests one direction, weekly/monthly another
            daily_up = "strength" in daily.lower()
            daily_down = "weak" in daily.lower()
            weekly_up = "strength" in weekly.lower()
            weekly_down = "weak" in weekly.lower()

            if (daily_up and weekly_down) or (daily_down and weekly_up):
                return 0.40
        return 0.0

    def _extract_regime_similarity(self, regime_matches: Iterable[object]) -> float:
        """Extract max similarity from regime matches."""
        matches = list(regime_matches)
        if not matches:
            return 0.0
        try:
            sims = [
                m.get("similarity") if isinstance(m, dict) else getattr(m, "similarity", 0)
                for m in matches
            ]
            return max(sims) if sims else 0.0
        except Exception:
            return 0.0

    def _detect_regime_weakening(self, prior_observations: List[object]) -> bool:
        """Detect regime character changing (e.g., repeated divergence)."""
        if len(prior_observations) < 3:
            return False
        recent = prior_observations[-3:]
        has_divergence = sum(
            1
            for obs in recent
            if "diverge" in getattr(obs, "observation_text", "").lower()
            or "weak" in getattr(obs, "breadth_state", "").lower()
        )
        return has_divergence >= 2

    def _detect_contradiction_rising(
        self, prior_observations: List[object], current_contradiction: dict
    ) -> bool:
        """Detect if contradiction severity is increasing."""
        if len(prior_observations) < 2:
            return False
        current_score = float(current_contradiction.get("score", 0.0))
        # Simple heuristic: if we have persistent contradictions and score > 0.3, flag rising
        contradictions = current_contradiction.get("contradictions", [])
        return current_score > 0.3 and len(contradictions) > 0

    def _infer_direction_bias(
        self, observation: object, breadth: str, drivers: List[str], components: List[float]
    ) -> str:
        """Infer directional bias from breadth + drivers."""
        trend = getattr(observation, "trend_state", "").lower()

        # Check drivers for directional hints
        has_upside_hint = any("strength" in d.lower() for d in drivers)
        has_downside_hint = any(
            "weak" in d.lower() or "deteriorat" in d.lower() for d in drivers
        )

        if has_upside_hint and not has_downside_hint:
            return "higher"
        if has_downside_hint and not has_upside_hint:
            return "lower"

        # Fallback to breadth
        if "strengthened" in breadth or "strong" in breadth:
            return "higher"
        if "weakened" in breadth or "weak" in breadth or "deteriorat" in breadth:
            return "lower"

        return "neutral"
