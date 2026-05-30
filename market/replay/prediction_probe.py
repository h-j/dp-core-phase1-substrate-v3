from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import mean
from typing import Iterable, List, Optional
from market.replay.transition_memory import TransitionExample


class PredictionDirection(str, Enum):
    higher = "higher"
    lower = "lower"
    range_bound = "range_bound"
    uncertain = "uncertain"


@dataclass(frozen=True)
class PredictionProbe:
    direction: PredictionDirection
    confidence: float
    tension: str
    invalidation: str
    transition_examples: List[TransitionExample] = None

    def to_dict(self) -> dict:
        return {
            "direction": self.direction.value,
            "confidence": round(self.confidence, 3),
            "tension": self.tension,
            "invalidation": self.invalidation,
            "transition_examples": [ex.date for ex in self.transition_examples] if self.transition_examples else []
        }


@dataclass(frozen=True)
class PredictionEvaluation:
    prior_direction: str
    actual_direction: str
    direction_score: float
    invalidation_triggered: bool
    confidence: float
    invalidation: str

    def to_dict(self) -> dict:
        return {
            "prior_direction": self.prior_direction,
            "actual_direction": self.actual_direction,
            "direction_score": round(self.direction_score, 3),
            "invalidation_triggered": self.invalidation_triggered,
            "confidence": round(self.confidence, 3),
            "invalidation": self.invalidation,
        }


class PredictionProbeGenerator:
    """Deterministic prediction probe generator for replay."""

    def generate_prediction(
        self,
        observation: object,
        horizons: object,
        regime_matches: Iterable[object],
        theory: object,
        contradictions: dict,
        reflection: object,
        transition_examples: List[TransitionExample] = None,
        volume_state: str = "normal",
        momentum_regime: str = "flat",
        volatility_regime: str = "normal",
        volume_ratio_5d: float = 1.0,
        return_3d: float = 0.0,
        return_5d: float = 0.0,
        close_position_pct: float = 0.5,
        participation_confirmation: str = "normal",
        theory_usefulness: dict = None
    ) -> PredictionProbe:
        direction = self._infer_direction(
            observation,
            theory,
            reflection,
            volume_ratio_5d=volume_ratio_5d,
            return_3d=return_3d,
            return_5d=return_5d,
            close_position_pct=close_position_pct,
            participation_confirmation=participation_confirmation,
        )
        confidence = self._infer_confidence(
            direction,
            contradictions,
            theory,
            reflection,
            transition_examples,
            volume_state,
            momentum_regime,
            volatility_regime,
            regime_matches,
            volume_ratio_5d,
            return_3d,
            return_5d,
            close_position_pct,
            participation_confirmation,
            theory_usefulness=theory_usefulness,
        )
        tension = self._compose_tension(theory, reflection, contradictions, horizons)
        invalidation = self._compose_invalidation(theory, reflection, contradictions)
        return PredictionProbe(
            direction=direction,
            confidence=confidence,
            tension=tension,
            invalidation=invalidation,
            transition_examples=transition_examples or []
        )

    def score_actual(
        self, prior_prediction: PredictionProbe, actual_observation: object
    ) -> PredictionEvaluation:
        actual_direction = self._actual_direction(actual_observation)
        direction_score = self._score_direction(prior_prediction.direction, actual_direction)
        invalidation_triggered = bool(
            prior_prediction.invalidation
            and actual_direction != prior_prediction.direction
            and prior_prediction.direction != PredictionDirection.uncertain
        )
        return PredictionEvaluation(
            prior_direction=prior_prediction.direction.value,
            actual_direction=actual_direction.value,
            direction_score=direction_score,
            invalidation_triggered=invalidation_triggered,
            confidence=prior_prediction.confidence,
            invalidation=prior_prediction.invalidation,
        )

    def _infer_direction(
        self,
        observation: object,
        theory: object,
        reflection: object,
        volume_ratio_5d: float = 1.0,
        return_3d: float = 0.0,
        return_5d: float = 0.0,
        close_position_pct: float = 0.5,
        participation_confirmation: str = "normal",
    ) -> PredictionDirection:
        trend = getattr(observation, "trend_state", "").lower()
        breadth = getattr(observation, "breadth_state", "").lower()
        sentiment = getattr(observation, "macro_sentiment", "").lower()
        theory_text = getattr(theory, "summary", "").lower()
        reflection_text = getattr(reflection, "reflection_summary", "").lower()
        candle_type = getattr(observation, "candle_type", "").lower()
        gap_pct = getattr(observation, "gap_pct", 0.0)
        descriptors = [str(item).lower() for item in getattr(observation, "descriptors", []) or []]

        strong_up = (
            return_3d > 0.3
            and return_5d > 0.5
            and (
                volume_ratio_5d > 1.0
                or gap_pct > 0.35
                or "asset participation surge" in descriptors
            )
        )
        strong_down = (
            return_3d < -0.3
            and return_5d < -0.5
            and (
                volume_ratio_5d > 1.0
                or gap_pct < -0.35
            )
        )
        close_high = close_position_pct >= 0.80 or candle_type == "strong_bull"
        close_low = close_position_pct <= 0.20 or candle_type == "strong_bear"

        if "uncertain" in sentiment or "uncertain" in reflection_text or "fragile" in reflection_text:
            return PredictionDirection.uncertain

        if strong_up and (
            close_high
            or "bullish_confirmed" in participation_confirmation
            or volume_ratio_5d > 1.25
            or "asset participation surge" in descriptors
        ):
            return PredictionDirection.higher
        if strong_down and (
            close_low
            or "bearish_confirmed" in participation_confirmation
            or volume_ratio_5d > 1.25
        ):
            return PredictionDirection.lower

        if any(word in trend for word in ["higher", "up", "extended_higher", "recovered_intraday"]):
            if "weak" in breadth or "deteriorat" in breadth or "risk_off" in sentiment:
                if not (
                    strong_up
                    or "asset participation surge" in descriptors
                    or gap_pct > 0.35
                ):
                    return PredictionDirection.uncertain
            return PredictionDirection.higher
        if any(word in trend for word in ["lower", "down", "closed_lower"]):
            if "strong" in breadth or "support" in reflection_text:
                return PredictionDirection.uncertain
            return PredictionDirection.lower

        if "range_bound" in trend or "range_bound" in theory_text:
            if strong_up and (
                close_high
                or volume_ratio_5d > 1.15
                or "asset participation surge" in descriptors
                or candle_type == "strong_bull"
            ):
                return PredictionDirection.higher
            if strong_down and (
                close_low
                or volume_ratio_5d > 1.15
                or candle_type == "strong_bear"
            ):
                return PredictionDirection.lower
            if abs(return_3d) < 0.25 and abs(return_5d) < 0.35 and volume_ratio_5d <= 1.05 and not close_high and not close_low:
                return PredictionDirection.range_bound
            if "uncertain" in sentiment or "uncertain" in reflection_text:
                return PredictionDirection.uncertain
            if strong_up and (volume_ratio_5d > 1.05 or gap_pct > 0.25):
                return PredictionDirection.higher
            if strong_down and (volume_ratio_5d > 1.05 or gap_pct < -0.25):
                return PredictionDirection.lower
            return PredictionDirection.range_bound

        if strong_up:
            return PredictionDirection.higher
        if strong_down:
            return PredictionDirection.lower

        if "uncertain" in sentiment or "uncertain" in reflection_text:
            return PredictionDirection.uncertain
        return PredictionDirection.range_bound

    def _infer_confidence(
        self,
        direction: PredictionDirection,
        contradictions: dict,
        theory: object,
        reflection: object,
        transition_examples: List[TransitionExample] = None,
        volume_state: str = "normal",
        momentum_regime: str = "flat",
        volatility_regime: str = "normal",
        regime_matches: Iterable[object] = None,
        volume_ratio_5d: float = 1.0,
        return_3d: float = 0.0,
        return_5d: float = 0.0,
        close_position_pct: float = 0.5,
        participation_confirmation: str = "normal",
        theory_usefulness: dict = None,
    ) -> float:
        # v2.4 CALIBRATION: align confidence to stronger signal clusters
        if direction == PredictionDirection.uncertain:
            base = 0.42
        elif direction == PredictionDirection.range_bound:
            base = 0.48
        else:
            base = 0.62

        contra_score = contradictions.get("score", 0)
        if contra_score > 0.55:
            base -= 0.20
        elif contra_score > 0.35:
            base -= 0.10
        elif contra_score < 0.25:
            base += 0.04

        if volume_state == "dry":
            base -= 0.12
        elif volume_state == "elevated":
            base += 0.05

        if volume_ratio_5d > 1.1:
            base += 0.06
        if close_position_pct >= 0.80 or close_position_pct <= 0.20:
            base += 0.05

        if (direction == PredictionDirection.higher and momentum_regime == "strengthening") or (
            direction == PredictionDirection.lower and momentum_regime == "weakening"
        ):
            base += 0.05

        if volume_state == "normal" and momentum_regime == "flat" and volatility_regime == "normal":
            base -= 0.06

        matches = list(regime_matches) if regime_matches else []
        if matches and any(getattr(m, 'similarity', 0) > 0.9 for m in matches):
            base += 0.08

        text = (getattr(theory, "summary", "") + " " + getattr(reflection, "reflection_summary", "")).lower()
        if "uncertain" in text or "fragile" in text or "caution" in text:
            base -= 0.08
        if "weak" in text and direction in {PredictionDirection.higher, PredictionDirection.lower}:
            base -= 0.04
        if "strength" in text and direction in {PredictionDirection.higher, PredictionDirection.lower}:
            base += 0.03

        if transition_examples and len(transition_examples) > 0:
            base += 0.04

        if "bullish_confirmed" in participation_confirmation or "bearish_confirmed" in participation_confirmation:
            base += 0.04

        if contra_score > 0.55 and direction in {PredictionDirection.higher, PredictionDirection.lower}:
            base -= 0.05

        # v2.6 Calibration Logic
        raw_confidence = base
        if raw_confidence >= 0.75:
            base *= 0.82
        elif raw_confidence >= 0.60:
            base *= 0.88
        elif raw_confidence <= 0.25:
            base *= 1.05

        usefulness_score = theory_usefulness.get("score", 0.0) if theory_usefulness else 0.0
        if direction != PredictionDirection.uncertain and usefulness_score < 0.15:
            base = min(base, 0.55)

        print(f"[Probe v2.6] Raw: {raw_confidence:.3f} | Calibrated: {base:.3f} | Usefulness: {usefulness_score:.3f}")

        return float(max(0.05, min(0.95, round(base, 3))))

    def _compose_tension(
        self,
        theory: object,
        reflection: object,
        contradictions: dict,
        horizons: object,
    ) -> str:
        text = (getattr(theory, "summary", "") + " " + getattr(reflection, "reflection_summary", "")).lower()
        if "breadth" in text and "strength" in text:
            return "strength vs weakening breadth"
        if "volatility" in text and "expans" in text:
            return "volatility expansion vs structural support"
        if "liquidity" in text and "pressure" in text:
            return "liquidity support vs pressure"
        if "continuation" in text and "uncertain" in text:
            return "continuation strength vs uncertainty"
        if contradictions.get("contradictions"):
            return " vs ".join(
                str(item).replace("Trend contradiction:", "")
                for item in contradictions.get("contradictions", [])[:2]
            )
        return "observation coherence vs residual uncertainty"

    def _compose_invalidation(self, theory: object, reflection: object, contradictions: dict) -> str:
        reflection_text = getattr(reflection, "reflection_summary", "").lower()
        if contradictions.get("contradictions"):
            return str(contradictions.get("contradictions", [""])[0])
        if "volatility" in reflection_text:
            return "volatility expansion"
        if "uncertain" in reflection_text:
            return "uncertainty persistence"
        if "contradict" in reflection_text:
            return "contradiction signal"
        return "structural mismatch"

    def _actual_direction(self, observation: object) -> PredictionDirection:
        trend = getattr(observation, "trend_state", "").lower()
        if "range_bound" in trend:
            return PredictionDirection.range_bound
        if any(word in trend for word in ["higher", "up", "extended_higher", "recovered_intraday"]):
            return PredictionDirection.higher
        if any(word in trend for word in ["lower", "down", "closed_lower"]):
            return PredictionDirection.lower
        return PredictionDirection.uncertain

    def _score_direction(
        self,
        predicted: PredictionDirection,
        actual: PredictionDirection,
    ) -> float:
        if predicted == PredictionDirection.uncertain:
            return 0.0
        if predicted == actual:
            return 1.0
        if predicted == PredictionDirection.range_bound and actual in {
            PredictionDirection.higher,
            PredictionDirection.lower,
        }:
            return 0.5
        return 0.0
