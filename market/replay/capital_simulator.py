"""
Observer-only capital simulator for replay analysis.
Does not affect cognition.
"""

from typing import List, Dict
from typing import Any


class CapitalSimulator:
    """
    Simulates capital growth based on daily predictions and actual market returns.
    Observer-only, does not influence cognition.
    """

    def __init__(self, starting_capital: float = 10000.0):
        self.starting_capital = starting_capital
        self.daily_logs: List[Dict] = []
        self.total_days = 0
        
        # v1.7 Policy Tracking
        self.policy_stats = {
            "baseline": self._init_stats(),
            "high_conviction": self._init_stats(),
            "breakout": self._init_stats()
        }

    def _init_stats(self) -> Dict:
        return {
            "current_capital": self.starting_capital,
            "max_capital": self.starting_capital,
            "max_drawdown_pct": 0.0,
            "win_count": 0,
            "loss_count": 0,
            "trade_count": 0,
            "skipped_days": 0,
            "total_conviction": 0.0
        }

    def record_day_result(
        self,
        date: str,
        prediction_direction: str,
        prediction_confidence: float,
        actual_daily_return_pct: float,
        market_daily_return_pct: float, # For alpha calculation
        decisions: Dict[str, Any] = None
    ):
        """
        Records daily prediction and actual market return to simulate capital.
        """
        self.total_days += 1
        policy_updates = {}

        for name, stats in self.policy_stats.items():
            cap_before = stats["current_capital"]
            
            # Determine action and conviction
            action = "cash"
            conviction = 0.0
            
            if decisions and name in decisions:
                d = decisions[name]
                # Handle both object and dict types defensively
                action = getattr(d, "action", "cash") if not isinstance(d, dict) else d.get("action", "cash")
                conviction = getattr(d, "conviction", 0.0) if not isinstance(d, dict) else d.get("conviction", 0.0)
            else:
                # Fallback to legacy direction mapping if decisions missing (e.g. Day 0)
                if prediction_direction == "higher": action = "buy"
                elif prediction_direction == "lower": action = "sell"
                elif prediction_direction == "range_bound": action = "hold"
                else: action = "cash"
                conviction = prediction_confidence

            # Return logic
            daily_ret = 0.0
            deployed = 0.0
            if action == "buy":
                daily_ret = actual_daily_return_pct
                deployed = 1.0
                stats["trade_count"] += 1
            elif action == "sell":
                daily_ret = 0.0  # Cash exit for sell in this implementation
                deployed = 0.0
                stats["trade_count"] += 1
            elif action == "hold":
                daily_ret = actual_daily_return_pct * 0.5
                deployed = 0.5
            else:
                daily_ret = 0.0
                deployed = 0.0
                stats["skipped_days"] += 1

            # Apply return
            stats["current_capital"] *= (1 + daily_ret / 100)
            stats["total_conviction"] += conviction
            
            if daily_ret > 0: stats["win_count"] += 1
            elif daily_ret < 0: stats["loss_count"] += 1

            # Max Drawdown
            stats["max_capital"] = max(stats["max_capital"], stats["current_capital"])
            drawdown = (stats["max_capital"] - stats["current_capital"]) / stats["max_capital"]
            stats["max_drawdown_pct"] = max(stats["max_drawdown_pct"], drawdown)

            policy_updates[name] = {
                "capital_before": cap_before,
                "capital_after": stats["current_capital"],
                "daily_return_pct": daily_ret,
                "deployed_capital_pct": deployed,
                "action": action,
                "conviction": conviction
            }

        self.daily_logs.append({
            "date": date,
            "prediction_direction": prediction_direction,
            "actual_daily_return_pct": actual_daily_return_pct,
            "market_daily_return_pct": market_daily_return_pct,
            "policies": policy_updates
        })

    def get_summary(self) -> Dict:
        summary = {}
        for name, stats in self.policy_stats.items():
            ret = (stats["current_capital"] - self.starting_capital) / self.starting_capital
            wins_losses = stats["win_count"] + stats["loss_count"]
            
            summary[name] = {
                "ending_capital": stats["current_capital"],
                "return_pct": ret,
                "win_rate": stats["win_count"] / wins_losses if wins_losses > 0 else 0.0,
                "max_drawdown": stats["max_drawdown_pct"],
                "trade_count": stats["trade_count"],
                "skipped_days": stats["skipped_days"],
                "avg_conviction": stats["total_conviction"] / self.total_days if self.total_days > 0 else 0.0
            }
        
        # Best performer
        best = max([n for n in summary.keys()], key=lambda k: summary[k]["return_pct"])
        summary["best_performer"] = best
        return summary

    def get_daily_logs(self) -> List[Dict]:
        """Returns the list of daily capital simulation logs."""
        return self.daily_logs