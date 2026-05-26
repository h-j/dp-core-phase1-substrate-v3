"""
Observer-only capital simulator for replay analysis.
Does not affect cognition.
"""

from typing import List, Dict
from datetime import datetime


class CapitalSimulator:
    """
    Simulates capital growth based on daily predictions and actual market returns.
    Observer-only, does not influence cognition.
    """

    def __init__(self, starting_capital: float = 10000.0):
        self.starting_capital = starting_capital
        self.current_capital = starting_capital
        self.daily_logs: List[Dict] = []
        self.max_capital = starting_capital
        self.min_capital = starting_capital
        self.max_drawdown_pct = 0.0
        self.win_count = 0
        self.loss_count = 0
        self.total_days = 0

    def record_day_result(
        self,
        date: str,
        prediction_direction: str,
        prediction_confidence: float,
        actual_daily_return_pct: float,
        market_daily_return_pct: float, # For alpha calculation
    ):
        """
        Records daily prediction and actual market return to simulate capital.

        Args:
            date: Current day's date.
            prediction_direction: Predicted direction ("higher", "lower", "range_bound", "uncertain").
            prediction_confidence: Confidence of the prediction.
            actual_daily_return_pct: The actual daily return percentage of the market.
            market_daily_return_pct: The actual daily return percentage of the market (for alpha).
        """
        self.total_days += 1
        capital_before = self.current_capital
        daily_return_pct = 0.0
        deployed_capital_pct = 0.0

        if prediction_direction == "higher":
            deployed_capital_pct = 1.0 # 100% long
            daily_return_pct = actual_daily_return_pct
        elif prediction_direction == "lower":
            deployed_capital_pct = 0.0 # Cash
            daily_return_pct = 0.0
        elif prediction_direction == "range_bound":
            deployed_capital_pct = 0.5 # 50% deployed
            daily_return_pct = actual_daily_return_pct * 0.5
        elif prediction_direction == "uncertain":
            deployed_capital_pct = 0.0 # Cash
            daily_return_pct = 0.0

        # Update capital
        self.current_capital *= (1 + daily_return_pct / 100)
        capital_after = self.current_capital

        # Track win/loss
        if daily_return_pct > 0:
            self.win_count += 1
        elif daily_return_pct < 0:
            self.loss_count += 1

        # Track max drawdown
        self.max_capital = max(self.max_capital, self.current_capital)
        drawdown = (self.max_capital - self.current_capital) / self.max_capital
        self.max_drawdown_pct = max(self.max_drawdown_pct, drawdown)

        self.daily_logs.append({
            "date": date,
            "prediction_direction": prediction_direction,
            "prediction_confidence": prediction_confidence,
            "actual_daily_return_pct": actual_daily_return_pct,
            "market_daily_return_pct": market_daily_return_pct,
            "capital_before": capital_before,
            "capital_after": capital_after,
            "daily_return_pct": daily_return_pct,
            "deployed_capital_pct": deployed_capital_pct,
        })

    def get_summary(self) -> Dict:
        """Returns a summary of the capital simulation."""
        ending_capital = self.current_capital
        return_pct = (ending_capital - self.starting_capital) / self.starting_capital if self.starting_capital else 0.0

        # Annualized return (assuming 252 trading days in a year)
        annualized_return = (1 + return_pct) ** (252 / self.total_days) - 1 if self.total_days > 0 else 0.0

        win_rate = self.win_count / (self.win_count + self.loss_count) if (self.win_count + self.loss_count) > 0 else 0.0

        # Alpha vs Cash (assuming cash earns 0%)
        alpha_vs_cash = return_pct

        # Best/Worst day
        daily_returns = [log["daily_return_pct"] for log in self.daily_logs]
        best_day = max(daily_returns) if daily_returns else 0.0
        worst_day = min(daily_returns) if daily_returns else 0.0

        return {
            "starting_capital": self.starting_capital,
            "ending_capital": ending_capital,
            "return_pct": return_pct,
            "annualized_return": annualized_return,
            "win_rate": win_rate,
            "max_drawdown": self.max_drawdown_pct,
            "best_day": best_day,
            "worst_day": worst_day,
            "alpha_vs_cash": alpha_vs_cash,
            "total_days": self.total_days,
        }

    def get_daily_logs(self) -> List[Dict]:
        """Returns the list of daily capital simulation logs."""
        return self.daily_logs