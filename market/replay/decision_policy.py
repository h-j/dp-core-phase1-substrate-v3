from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DecisionSignal:
    date: str
    policy_name: str
    action: str          # buy / sell / hold / cash
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
            "allowed": self.allowed
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
        atr_expansion: bool = False
    ) -> Dict[str, DecisionSignal]:
        """Evaluate all active policies for the current day."""
        return {
            "baseline": self._policy_baseline(prediction_probe, date),
            "high_conviction": self._policy_high_conviction(
                prediction_probe, contradiction_score, theory_usefulness, date, volume_state
            ),
            "breakout": self._policy_breakout(
                prediction_probe, transition_pressure, date, volume_state, atr_expansion
            )
        }

    def _policy_baseline(self, prediction, date: str) -> DecisionSignal:
        direction = getattr(prediction, 'direction', None)
        if hasattr(direction, 'value'):
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
            conviction=getattr(prediction, 'confidence', 0.5),
            reason="Daily execution baseline",
            allowed=True
        )

    def _policy_high_conviction(
        self, prediction, contradiction_score: float, theory_usefulness: float, date: str, volume_state: str
    ) -> DecisionSignal:
        conf = getattr(prediction, 'confidence', 0.0)
        direction = getattr(prediction, 'direction', None)
        if hasattr(direction, 'value'):
            direction = direction.value

        # v2.1 CALIBRATION: require confidence >= 0.50 AND usefulness >= 0.50 AND contradiction <= 0.30 AND healthy volume
        meets_criteria = (
            conf >= 0.50 and 
            theory_usefulness >= 0.50 and 
            contradiction_score <= 0.30 and
            volume_state != "dry"
        )

        if not meets_criteria:
            reason = "Cognition requirements not met" if conf >= 0.5 else "Skipped low confidence"
            if volume_state == "dry": reason = "Skipped weak volume"

            return DecisionSignal(
                date=date,
                policy_name="High Conviction",
                action="cash",
                conviction=conf,
                reason=reason,
                allowed=False
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
            allowed=True
        )

    def _policy_breakout(
        self, prediction, transition_pressure, date: str, volume_state: str, atr_expansion: bool
    ) -> DecisionSignal:
        pressure_score = getattr(transition_pressure, 'pressure_score', 0.0)
        breakout_risk = getattr(transition_pressure, 'breakout_risk', False)
        conf = getattr(prediction, 'confidence', 0.0)
        bias = getattr(transition_pressure, 'direction_bias', 'neutral')

        # v2.1 CALIBRATION: pressure >= 0.60 AND breakout_risk AND ATR expansion AND valid volume
        meets_criteria = (
            pressure_score >= 0.60 and 
            breakout_risk is True and 
            atr_expansion is True and
            volume_state in ["elevated", "normal"]
        )

        if not meets_criteria:
            reason = "Skipped pressure not confirmed" if pressure_score < 0.60 else "Insufficient breakout risk or structural confirmation"
            return DecisionSignal(
                date=date,
                policy_name="Breakout Discipline",
                action="cash",
                conviction=conf,
                reason=reason,
                allowed=False
            )

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
            allowed=True
        )