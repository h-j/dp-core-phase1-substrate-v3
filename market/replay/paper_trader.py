import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from cognition.schemas.decision.decision_record import DecisionRecord

# Configurable Parameters
INITIAL_CAPITAL = 1000000.0  # ₹10,00,000
SLIPPAGE_PCT = 0.001  # 0.1%
FEE_PCT = 0.0005  # 0.05% per trade
RANGE_ACCURACY_THRESHOLD = (
    0.5  # Absolute daily return < 0.5% is correct for range_bound
)


class PaperTrader:
    """
    Simulates paper trading with conviction-based position sizing, slippage, fees,
    and a complete decision evaluation framework.
    """

    def __init__(
        self,
        starting_capital: float = INITIAL_CAPITAL,
        slippage_pct: float = SLIPPAGE_PCT,
        fee_pct: float = FEE_PCT,
        range_threshold: float = RANGE_ACCURACY_THRESHOLD,
    ):
        self.starting_capital = starting_capital
        self.capital = starting_capital
        self.slippage_pct = slippage_pct
        self.fee_pct = fee_pct
        self.range_threshold = range_threshold

        self.trade_log: List[Dict[str, Any]] = []
        self.decision_records: List[DecisionRecord] = []
        self.peak_capital = starting_capital
        self.max_drawdown = 0.0

    def record_day_result(
        self,
        date: str,
        prediction: str,
        conviction_score: float,
        allocation_pct: float,
        open_price: float,
        close_price: float,
        actual_daily_return_pct: float,
        components: Dict[str, Any],
    ) -> DecisionRecord:
        """
        Legacy compatibility wrapper that constructs a DecisionRecord and evaluates it.
        """
        from cognition.schemas.decision.decision import Decision
        from cognition.schemas.decision.decision_record import DecisionRecord

        action = "hold"
        if allocation_pct > 0.0:
            action = "long" if prediction == "higher" else "short"

        decision_obj = Decision(
            date=date,
            prediction_direction=prediction,
            action=action,
            allocation_pct=allocation_pct,
            conviction_score=conviction_score,
            reason="Legacy compatibility wrapper",
        )

        p_support = components.get("principle_support", 0)
        supporting_principles = [str(p_support)] if p_support else []

        record = DecisionRecord(
            prediction_date=date,
            asset="RELIANCE",
            prediction=prediction,
            decision=decision_obj,
            allocation=allocation_pct,
            conviction_score=conviction_score,
            decision_reason="Legacy compatibility wrapper",
            supporting_principles=supporting_principles,
            calibrated_confidence=components.get("calibrated_confidence", 0.0),
            contradiction_pressure=components.get("contradiction_pressure", 0.0),
            empirical_confidence=components.get("empirical_confidence", 0.0),
            transition_pressure=components.get("transition_pressure", 0.0),
        )

        return self.evaluate_decision_outcome(
            record=record,
            open_price=open_price,
            close_price=close_price,
            actual_daily_return_pct=actual_daily_return_pct,
            evaluation_date=date,
        )

    def evaluate_decision_outcome(
        self,
        record: DecisionRecord,
        open_price: float,
        close_price: float,
        actual_daily_return_pct: float,
        evaluation_date: str,
    ) -> DecisionRecord:
        """
        Executes simulated trade based on DecisionRecord, updates capital,
        computes quality metrics, generates post-trade reflection, and updates the record.
        """
        capital_before = self.capital
        trade_val = capital_before * record.allocation

        entry_price = 0.0
        exit_price = 0.0
        pnl = 0.0
        is_correct = False

        prediction = record.prediction
        allocation_pct = record.allocation

        if allocation_pct > 0.0:
            if prediction == "higher":  # Long
                entry_price = open_price * (1.0 + self.slippage_pct)
                exit_price = close_price * (1.0 - self.slippage_pct)
                gross_return = (
                    (exit_price / entry_price) - 1.0 if entry_price > 0 else 0.0
                )
                fee = trade_val * (2 * self.fee_pct)
                pnl = trade_val * gross_return - fee
                is_correct = actual_daily_return_pct > 0.0

            elif prediction == "lower":  # Short
                entry_price = open_price * (1.0 - self.slippage_pct)
                exit_price = close_price * (1.0 + self.slippage_pct)
                gross_return = (
                    1.0 - (exit_price / entry_price) if entry_price > 0 else 0.0
                )
                fee = trade_val * (2 * self.fee_pct)
                pnl = trade_val * gross_return - fee
                is_correct = actual_daily_return_pct < 0.0
        else:
            # Flat/Cash days
            entry_price = 0.0
            exit_price = 0.0
            pnl = 0.0
            if prediction == "range_bound":
                is_correct = abs(actual_daily_return_pct) < self.range_threshold
            else:
                is_correct = False

        self.capital += pnl

        # Update peak and drawdown
        self.peak_capital = max(self.peak_capital, self.capital)
        current_dd = (self.peak_capital - self.capital) / self.peak_capital
        self.max_drawdown = max(self.max_drawdown, current_dd)

        # Classify decision outcome
        decision_result = "neutral"
        if allocation_pct > 0.0:
            decision_result = "correct" if is_correct else "incorrect"
        else:
            if prediction in ["higher", "lower", "range_bound"]:
                decision_result = (
                    "ignored_opportunity" if is_correct else "avoided_bad_trade"
                )

        # Update DecisionRecord fields
        record.evaluation_date = evaluation_date
        record.actual_outcome = f"{actual_daily_return_pct:+.2f}%"
        record.decision_result = decision_result
        record.pnl = float(round(pnl, 2))

        # Generate lightweight reflection
        record.reflection_summary = self._generate_reflection_text(
            record, is_correct, actual_daily_return_pct
        )

        # Save record
        self.decision_records.append(record)

        # Log daily trade details for backward compatibility
        log_entry = {
            "date": evaluation_date,
            "prediction": prediction,
            "conviction_score": record.conviction_score,
            "allocation_pct": allocation_pct,
            "entry_price": float(round(entry_price, 4)) if entry_price else 0.0,
            "exit_price": float(round(exit_price, 4)) if exit_price else 0.0,
            "pnl": float(round(pnl, 2)),
            "capital_before": float(round(capital_before, 2)),
            "cumulative_capital": float(round(self.capital, 2)),
            "is_correct": is_correct,
            # Cognitive components
            "calibrated_confidence": record.calibrated_confidence,
            "contradiction_pressure": record.contradiction_pressure,
            "empirical_confidence": record.empirical_confidence,
            "principle_support": (
                record.supporting_principles[0] if record.supporting_principles else 0
            ),
            "transition_pressure": record.transition_pressure,
        }
        self.trade_log.append(log_entry)

        return record

    def _generate_reflection_text(
        self, record: DecisionRecord, is_correct: bool, actual_return_pct: float
    ) -> str:
        parts = []
        if is_correct:
            parts.append(f"The prediction '{record.prediction}' was correct.")
        else:
            parts.append(
                f"The prediction '{record.prediction}' was incorrect (actual return: {actual_return_pct:+.2f}%)."
            )

        if is_correct and record.calibrated_confidence < 0.40:
            parts.append(
                "Cognitive confidence was inappropriately low for a successful scenario."
            )
        elif not is_correct and record.calibrated_confidence > 0.60:
            parts.append(
                "Cognitive confidence was inappropriately high, failing to capture the risk."
            )

        if not is_correct and record.allocation > 0.10:
            parts.append(
                f"Allocation was too aggressive ({record.allocation * 100:.1f}%) on a failing path."
            )

        if record.contradiction_pressure > 0.40:
            if not is_correct:
                parts.append(
                    f"High contradiction pressure ({record.contradiction_pressure:.2f}) correctly signaled potential failure."
                )
            else:
                parts.append(
                    f"High contradiction pressure ({record.contradiction_pressure:.2f}) introduced unnecessary cognitive friction."
                )

        if not is_correct:
            parts.append(
                "Recommended action: Trigger lineage mutation and open an evidence gap to reconcile contradiction."
            )
        else:
            parts.append(
                "Recommended action: Retain lineage and reinforce principle confidence."
            )

        return " ".join(parts)

    def get_summary(self) -> Dict[str, Any]:
        """
        Computes performance metrics across the trading log.
        """
        total_days = len(self.trade_log)
        if total_days == 0:
            return {
                "total_return_pct": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown_pct": 0.0,
                "directional_accuracy_pct": 0.0,
                "commitment_accuracy_pct": 0.0,
                "avg_conviction_score": 0.0,
                "final_capital": self.capital,
            }

        total_return = (
            (self.capital - self.starting_capital) / self.starting_capital * 100
        )

        # Sharpe ratio calculation
        daily_returns = []
        for t in self.trade_log:
            cap_b = t["capital_before"]
            if cap_b > 0.0:
                daily_returns.append(t["pnl"] / cap_b)
            else:
                daily_returns.append(0.0)

        if len(daily_returns) > 1 and float(np.std(daily_returns)) > 0:
            sharpe = float(
                np.sqrt(252) * np.mean(daily_returns) / np.std(daily_returns)
            )
        else:
            sharpe = 0.0

        # Directional and commitment accuracy
        correct_count = sum(1 for t in self.trade_log if t["is_correct"])
        directional_accuracy = (correct_count / total_days) * 100

        committed_trades = [t for t in self.trade_log if t["allocation_pct"] > 0.0]
        if committed_trades:
            correct_committed = sum(1 for t in committed_trades if t["is_correct"])
            commitment_accuracy = (correct_committed / len(committed_trades)) * 100
        else:
            commitment_accuracy = 0.0

        avg_conviction = float(np.mean([t["conviction_score"] for t in self.trade_log]))

        return {
            "total_return_pct": float(round(total_return, 4)),
            "sharpe_ratio": float(round(sharpe, 4)),
            "max_drawdown_pct": float(round(self.max_drawdown * 100, 4)),
            "directional_accuracy_pct": float(round(directional_accuracy, 4)),
            "commitment_accuracy_pct": float(round(commitment_accuracy, 4)),
            "avg_conviction_score": float(round(avg_conviction, 4)),
            "final_capital": float(round(self.capital, 2)),
        }

    def get_decision_intelligence_metrics(self) -> Dict[str, Any]:
        """
        Computes Section K Decision Intelligence metrics.
        """
        if not self.decision_records:
            return {
                "total_decisions": 0,
                "executed": 0,
                "skipped": 0,
                "high_conviction": 0,
                "low_conviction": 0,
                "decision_accuracy_pct": 0.0,
                "allocation_efficiency": 0.0,
                "avg_conviction": 0.0,
                "false_high_conviction_pct": 0.0,
                "false_low_conviction_pct": 0.0,
                "decision_stability": 1.0,
                "top_lineages": [],
                "top_principles": [],
                "top_memories": [],
                "top_harmful_contradictions": [],
                "knowledge_changes_count": 0,
                "avoided_bad_trades": 0,
                "ignored_opportunities": 0,
            }

        total_decisions = len(self.decision_records)
        executed = sum(1 for r in self.decision_records if r.allocation > 0.0)
        skipped = total_decisions - executed

        high_conv = sum(1 for r in self.decision_records if r.conviction_score >= 0.60)
        low_conv = sum(1 for r in self.decision_records if r.conviction_score < 0.40)

        correct_count = sum(
            1
            for r in self.decision_records
            if r.decision_result in ["correct", "ignored_opportunity"]
        )
        decision_accuracy = (correct_count / total_decisions) * 100

        # False High/Low Conviction Rates
        high_conv_records = [
            r for r in self.decision_records if r.conviction_score >= 0.60
        ]
        incorrect_high = sum(
            1
            for r in high_conv_records
            if r.decision_result in ["incorrect", "avoided_bad_trade"]
        )
        false_high_conv = (
            (incorrect_high / len(high_conv_records) * 100)
            if high_conv_records
            else 0.0
        )

        low_conv_records = [
            r for r in self.decision_records if r.conviction_score < 0.40
        ]
        correct_low = sum(
            1
            for r in low_conv_records
            if r.decision_result in ["correct", "ignored_opportunity"]
        )
        false_low_conv = (
            (correct_low / len(low_conv_records) * 100) if low_conv_records else 0.0
        )

        conv_scores = [r.conviction_score for r in self.decision_records]
        avg_conviction = float(np.mean(conv_scores))
        decision_stability = float(1.0 - np.std(conv_scores))

        # Allocation Efficiency: mean(allocation * directional_return)
        alloc_effs = []
        for r in self.decision_records:
            direction_mult = 0.0
            if r.prediction == "higher":
                direction_mult = 1.0
            elif r.prediction == "lower":
                direction_mult = -1.0
            # Try parsing actual return
            try:
                ret_pct = float(r.actual_outcome.replace("%", "").strip())
            except (ValueError, AttributeError):
                ret_pct = 0.0
            alloc_effs.append(r.allocation * ret_pct * direction_mult)
        allocation_efficiency = float(np.mean(alloc_effs)) if alloc_effs else 0.0

        # Top Lineages, Principles, Memories
        lineage_success = {}
        principle_success = {}
        memory_success = {}
        contradiction_harm = {}
        knowledge_changes_count = 0

        for r in self.decision_records:
            is_correct = r.decision_result in ["correct", "ignored_opportunity"]

            # Supporting Lineages success
            for lineage in r.supporting_lineages:
                if is_correct:
                    lineage_success[lineage] = lineage_success.get(lineage, 0) + 1

            # Supporting Principles success
            for pid in r.supporting_principles:
                if is_correct:
                    principle_success[pid] = principle_success.get(pid, 0) + 1

            # Retrieved Memories success
            for mem in r.retrieved_memories:
                if is_correct:
                    memory_success[mem] = memory_success.get(mem, 0) + 1

            # Contradiction harm
            if r.contradiction_pressure > 0.20 and not is_correct:
                key = f"contradiction_on_{r.prediction_date}"
                contradiction_harm[key] = r.contradiction_pressure

            knowledge_changes_count += len(r.knowledge_changes)

        # Sort and select top items
        top_lineages = sorted(lineage_success, key=lineage_success.get, reverse=True)[
            :3
        ]
        top_principles = sorted(
            principle_success, key=principle_success.get, reverse=True
        )[:3]
        top_memories = sorted(memory_success, key=memory_success.get, reverse=True)[:3]
        top_harmful_contradictions = sorted(
            contradiction_harm, key=contradiction_harm.get, reverse=True
        )[:3]

        avoided_bad = sum(
            1 for r in self.decision_records if r.decision_result == "avoided_bad_trade"
        )
        ignored_opps = sum(
            1
            for r in self.decision_records
            if r.decision_result == "ignored_opportunity"
        )

        return {
            "total_decisions": total_decisions,
            "executed": executed,
            "skipped": skipped,
            "high_conviction": high_conv,
            "low_conviction": low_conv,
            "decision_accuracy_pct": float(round(decision_accuracy, 2)),
            "allocation_efficiency": float(round(allocation_efficiency, 4)),
            "avg_conviction": float(round(avg_conviction, 4)),
            "false_high_conviction_pct": float(round(false_high_conv, 2)),
            "false_low_conviction_pct": float(round(false_low_conv, 2)),
            "decision_stability": float(round(decision_stability, 4)),
            "top_lineages": top_lineages,
            "top_principles": top_principles,
            "top_memories": top_memories,
            "top_harmful_contradictions": top_harmful_contradictions,
            "knowledge_changes_count": knowledge_changes_count,
            "avoided_bad_trades": avoided_bad,
            "ignored_opportunities": ignored_opps,
        }

    def export_log_csv(self, file_path: Path):
        """
        Exports the trade log list to a CSV file.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.trade_log:
            return

        headers = list(self.trade_log[0].keys())
        if "capital_before" in headers:
            headers.remove("capital_before")

        with open(file_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for log in self.trade_log:
                row = {k: v for k, v in log.items() if k in headers}
                for k, v in row.items():
                    if isinstance(v, float):
                        row[k] = round(v, 4)
                writer.writerow(row)
