from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DecisionSignal:
    date: str
    policy_name: str
    action: str  # buy / sell / hold / cash
    conviction: float
    reason: str
    allowed: bool

    def to_dict(self):
        return {
            "date": self.date,
            "policy_name": self.policy_name,
            "action": self.action,
            "conviction": self.conviction,
            "reason": self.reason,
            "allowed": self.allowed,
        }


class DecisionPolicyEngine:
    """
    Evaluates trading decisions based on cognition outputs and execution policies.
    """

    def evaluate(
        self,
        prediction_probe,
        transition_pressure,
        contradiction_score: float,
        theory_usefulness: float,
        confidence_state: Any,
        date: str,
        volume_state: str = "normal",
        atr_expansion: bool = False,
        participation_confirmation: str = "normal",
    ) -> Dict[str, DecisionSignal]:
        """Evaluate all active policies for the current day."""
        return {
            "baseline": self._policy_baseline(prediction_probe, date),
            "high_conviction": self._policy_high_conviction(
                prediction_probe,
                contradiction_score,
                theory_usefulness,
                transition_pressure,
                date,
                volume_state,
            ),
            "breakout": self._policy_breakout(
                prediction_probe,
                transition_pressure,
                date,
                volume_state,
                atr_expansion,
                participation_confirmation,
            ),
        }

    def _policy_baseline(self, prediction, date: str) -> DecisionSignal:
        direction = getattr(prediction, "direction", None)
        if hasattr(direction, "value"):
            direction = direction.value

        action = "hold"
        if direction == "higher":
            action = "buy"
        elif direction == "lower":
            action = "sell"
        elif direction in ["range_bound", "uncertain"]:
            action = "hold"

        return DecisionSignal(
            date=date,
            policy_name="Baseline",
            action=action,
            conviction=getattr(prediction, "confidence", 0.5),
            reason="Daily execution baseline",
            allowed=True,
        )

    def _policy_high_conviction(
        self,
        prediction,
        contradiction_score: float,
        theory_usefulness: float,
        transition_pressure,
        date: str,
        volume_state: str,
    ) -> DecisionSignal:
        conf = getattr(prediction, "confidence", 0.0)
        direction = getattr(prediction, "direction", None)
        if hasattr(direction, "value"):
            direction = direction.value

        pressure_score = (
            getattr(transition_pressure, "pressure_score", 0.0)
            if transition_pressure
            else 0.0
        )

        # v2.4 Tuning for actual participation
        meets_criteria = (
            conf >= 0.50 and theory_usefulness >= 0.30 and contradiction_score <= 0.45
        )

        if not meets_criteria:
            reason = "Cognition requirements not met"
            if conf < 0.42:
                reason = "Skipped low confidence"
            return DecisionSignal(
                date=date,
                policy_name="High Conviction",
                action="cash",
                conviction=conf,
                reason=reason,
                allowed=False,
            )

        action = "cash"
        if direction == "higher":
            action = "buy"
        elif direction == "lower":
            action = "sell"

        return DecisionSignal(
            date=date,
            policy_name="High Conviction",
            action=action,
            conviction=conf,
            reason="High conviction criteria met",
            allowed=True,
        )

    def _policy_breakout(
        self,
        prediction,
        transition_pressure,
        date: str,
        volume_state: str,
        atr_expansion: bool,
        participation_confirmation: str = "normal",
    ) -> DecisionSignal:
        pressure_score = getattr(transition_pressure, "pressure_score", 0.0)
        breakout_risk = getattr(transition_pressure, "breakout_risk", False)
        conf = getattr(prediction, "confidence", 0.0)
        bias = getattr(transition_pressure, "direction_bias", "neutral")

        # v2.4 Tuning for actual participation
        meets_criteria = (
            pressure_score >= 0.45 and breakout_risk is True and conf >= 0.36
        )

        if not meets_criteria:
            reason = "Skipped pressure not confirmed"
            if pressure_score < 0.45:
                reason = "Skipped pressure threshold"
            elif not breakout_risk:
                reason = "Skipped breakout risk absent"
            return DecisionSignal(
                date=date,
                policy_name="Breakout Discipline",
                action="cash",
                conviction=conf,
                reason=reason,
                allowed=False,
            )

        if bias == "neutral" and getattr(prediction, "direction", None) is not None:
            direction = getattr(prediction, "direction", None)
            if hasattr(direction, "value"):
                direction = direction.value
            if direction in {"higher", "lower"}:
                bias = direction

        action = "cash"
        if bias == "higher":
            action = "buy"
        elif bias == "lower":
            action = "sell"

        return DecisionSignal(
            date=date,
            policy_name="Breakout Discipline",
            action=action,
            conviction=conf,
            reason="Breakout policy criteria met",
            allowed=True,
        )
