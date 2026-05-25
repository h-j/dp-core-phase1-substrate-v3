"""Deterministic multi-horizon cognition views for replay.

The horizon engine uses only observations visible at the current replay step.
It compresses recent market structure into stable labels that can be passed
into abstraction, theory generation, and reflection without prediction logic.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class HorizonView:
    daily: str
    weekly: str
    monthly: str

    def to_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return f"Daily: {self.daily}; Weekly: {self.weekly}; Monthly: {self.monthly}"


class HorizonCognitionEngine:
    """Compute daily, weekly, and monthly structure from prior-visible history."""

    def compute(self, observations: Iterable[object]) -> HorizonView:
        history = list(observations)
        if not history:
            return HorizonView(
                daily="insufficient_history",
                weekly="insufficient_history",
                monthly="insufficient_history",
            )

        return HorizonView(
            daily=self._daily(history[-1]),
            weekly=self._window_state(history[-5:], min_count=3),
            monthly=self._window_state(history[-21:], min_count=10),
        )

    def _daily(self, observation: object) -> str:
        trend = getattr(observation, "trend_state", "")
        breadth = getattr(observation, "breadth_state", "")
        volatility = getattr(observation, "volatility_state", "")
        sentiment = getattr(observation, "macro_sentiment", "")
        if "range_bound" in trend:
            return "range_bound"
        if "higher" in trend and breadth in {
            "strengthened",
            "strongly_participatory",
        }:
            return "strengthening"
        if "higher" in trend and volatility in {"expanded", "high"}:
            return "fragile_strength"
        if "lower" in trend or sentiment == "risk_off":
            return "weakening"
        if breadth in {"weakened", "deteriorated"}:
            return "fatigue"
        return "mixed"

    def _window_state(self, observations: List[object], min_count: int) -> str:
        if len(observations) < min_count:
            return "insufficient_history"

        strengthening = sum(
            1
            for obs in observations
            if (
                "higher" in getattr(obs, "trend_state", "")
                or getattr(obs, "breadth_state", "")
                in {"strengthened", "strongly_participatory"}
            )
        )
        weakening = sum(
            1
            for obs in observations
            if (
                "lower" in getattr(obs, "trend_state", "")
                or getattr(obs, "breadth_state", "") in {"weakened", "deteriorated"}
                or getattr(obs, "macro_sentiment", "") == "risk_off"
            )
        )
        range_bound = sum(
            1
            for obs in observations
            if "range_bound" in getattr(obs, "trend_state", "")
        )
        volatile = sum(
            1
            for obs in observations
            if getattr(obs, "volatility_state", "") in {"expanded", "high"}
        )

        total = len(observations)
        if range_bound / total >= 0.45:
            return "range_bound"
        if strengthening - weakening >= max(2, total // 4):
            return "strengthening" if volatile == 0 else "fragile_strength"
        if weakening - strengthening >= max(2, total // 4):
            return "fatigue"
        if volatile / total >= 0.35:
            return "unstable"
        return "mixed"
