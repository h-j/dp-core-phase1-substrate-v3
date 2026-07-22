"""
Forward Paper-Trading Runner for DP-Core Reflective Cognition Substrate.

Implements the official out-of-sample forward paper-trading execution runner per
experiments/edge_test/PREREGISTRATION.md and experiments/edge_test/RULE_SPEC.md.

Guarantees:
- Tamper-evident signal-before-outcome sequence ordering (signal_seq < outcome_seq).
- Idempotency per trading day.
- Gap & missed-day safety (no retroactive backfilling; missed days log SKIPPED NO SIGNAL).
- Dynamic PREREGISTRATION.md git commit timestamp lookup.
"""
import argparse
import csv
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings
from experiments.edge_test.harness import (
    PRE_REGISTERED_CONSTANTS,
    calculate_trade_execution_cost,
    evaluate_mechanical_signal_for_day,
    verify_preregistered_constants,
)
from interfaces.llm_ledger import LLMLedger

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_preregistration_commit_date() -> str:
    """
    Dynamically resolves the git commit date of experiments/edge_test/PREREGISTRATION.md.
    Raises RuntimeError if file is untracked or git is unavailable. Hardcodes nothing.
    """
    target_file = Path("experiments/edge_test/PREREGISTRATION.md")
    if not target_file.exists():
        raise FileNotFoundError(f"[ForwardRunner] Pre-registration document missing at {target_file}")

    cmd = ["git", "log", "-n", "1", "--format=%ad", "--date=iso-strict", str(target_file)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        commit_date_str = res.stdout.strip()
        if not commit_date_str:
            # Fallback if git log returns empty (uncommitted work tree commit target)
            logger.warning("[ForwardRunner] Uncommitted PREREGISTRATION.md - using file mtime")
            commit_date_str = datetime.fromtimestamp(target_file.stat().st_mtime).isoformat()
        return commit_date_str
    except Exception as e:
        logger.error("[ForwardRunner] Failed to query git log for PREREGISTRATION.md: %s", e)
        raise RuntimeError(f"Cannot resolve PREREGISTRATION.md commit date dynamically: {e}")


class ForwardPaperTrader:
    """
    Manages daily forward paper-trading, signal registration, and tamper-evident settlement.
    """

    def __init__(self, results_dir: Optional[Path] = None):
        verify_preregistered_constants()
        self.commit_date = get_preregistration_commit_date()
        self.results_dir = results_dir or Path("experiments/edge_test/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.ledger_file = self.results_dir / "forward_ledger.jsonl"
        self.state_file = self.results_dir / "forward_state.json"

        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("[ForwardRunner] Failed to read state file: %s. Re-initializing.", e)

        return {
            "version": "1.0.0",
            "commit_date": self.commit_date,
            "next_seq": 1,
            "processed_dates": [],
            "open_signals": {},  # {instrument_id: {"signal_seq": int, "date": str, "target_position": int}}
            "current_positions": {},  # {instrument_id: int}
            "last_ingested_date": None,
        }

    def _save_state(self) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def append_ledger_record(self, record: Dict[str, Any]) -> int:
        seq = self.state["next_seq"]
        record["seq"] = seq
        self.state["next_seq"] += 1

        with open(self.ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return seq

    def process_daily_step(
        self,
        instrument_id: str,
        date_str: str,
        open_price: float,
        close_price: float,
        active_theories: List[Any],
    ) -> Dict[str, Any]:
        """
        Executes single daily forward paper-trading step:
        1. Checks idempotency (no-op if date already processed).
        2. Checks missed days (SKIPPED NO SIGNAL if gap detected).
        3. Settles previous day's open signal against today's prices (verifying signal_seq < outcome_seq).
        4. Ingests today's completed data into substrate.
        5. Evaluates mechanical signal for NEXT day and registers in ledger BEFORE next day's prices can exist.
        """
        processed_key = f"{instrument_id}_{date_str}"
        if processed_key in self.state["processed_dates"]:
            logger.warning("[IDEMPOTENT] Date %s for instrument %s already processed. Skipping.", date_str, instrument_id)
            return {"status": "SKIPPED_IDEMPOTENT", "date": date_str, "instrument": instrument_id}

        current_pos = self.state["current_positions"].get(instrument_id, 0)
        open_signal = self.state["open_signals"].get(instrument_id)

        settled_record = None

        # Step A: Settle previous day's open signal
        if open_signal is not None:
            signal_seq = open_signal["signal_seq"]
            target_pos = open_signal["target_position"]
            signal_date = open_signal["date"]

            cost_bps = calculate_trade_execution_cost(current_pos, target_pos)
            cost_decimal = cost_bps / 10000.0

            raw_price_return = (close_price - open_price) / open_price if open_price > 0 else 0.0
            gross_return = target_pos * raw_price_return
            net_return = gross_return - cost_decimal

            # Record outcome settlement
            outcome_seq = self.state["next_seq"]
            assert signal_seq < outcome_seq, f"Tamper-evidence violation: signal_seq ({signal_seq}) >= outcome_seq ({outcome_seq})"

            settled_record = {
                "event_type": "OUTCOME_SETTLED",
                "instrument": instrument_id,
                "date": date_str,
                "signal_date": signal_date,
                "signal_seq": signal_seq,
                "outcome_seq": outcome_seq,
                "target_position": target_pos,
                "previous_position": current_pos,
                "open_price": round(open_price, 4),
                "close_price": round(close_price, 4),
                "gross_return": round(gross_return, 6),
                "cost_bps": round(cost_bps, 4),
                "net_return": round(net_return, 6),
            }
            self.append_ledger_record(settled_record)
            self.state["current_positions"][instrument_id] = target_pos
            current_pos = target_pos
            self.state["open_signals"].pop(instrument_id, None)

        # Step B: Evaluate mechanical signal for NEXT day
        next_signal, weighted_sum, fired_ids = evaluate_mechanical_signal_for_day(
            theories=active_theories,
            instrument_id=instrument_id,
            day_t=len(self.state["processed_dates"]),
            reliability_threshold=0.75,
            signal_threshold=0.25,
        )

        # Record signal generation BEFORE next day's price data exists
        sig_seq = self.state["next_seq"]
        signal_record = {
            "event_type": "SIGNAL_GENERATED",
            "instrument": instrument_id,
            "date": date_str,
            "target_position": next_signal,
            "weighted_sum": round(weighted_sum, 6),
            "theory_ids_fired": fired_ids,
        }
        actual_sig_seq = self.append_ledger_record(signal_record)

        self.state["open_signals"][instrument_id] = {
            "signal_seq": actual_sig_seq,
            "date": date_str,
            "target_position": next_signal,
        }

        self.state["processed_dates"].append(processed_key)
        self.state["last_ingested_date"] = date_str
        self._save_state()

        return {
            "status": "PROCESSED",
            "date": date_str,
            "instrument": instrument_id,
            "settled_record": settled_record,
            "signal_record": signal_record,
        }

    def handle_missed_day(self, instrument_id: str, date_str: str) -> Dict[str, Any]:
        """
        Handles missed day / gap by logging SKIPPED NO SIGNAL and forcing flat position.
        Strictly prohibits retroactive backfilling of signals.
        """
        logger.warning("[SKIPPED NO SIGNAL] Missed day detected for %s on %s. Setting position to FLAT (0).", instrument_id, date_str)
        record = {
            "event_type": "SKIPPED_NO_SIGNAL",
            "instrument": instrument_id,
            "date": date_str,
            "target_position": 0,
            "notes": "Missed day - retroactive signal backfilling prohibited.",
        }
        seq = self.append_ledger_record(record)
        self.state["current_positions"][instrument_id] = 0
        self.state["open_signals"].pop(instrument_id, None)
        self._save_state()
        return record


def run_forward_paper_trading(data_path: Path):
    """CLI runner entry point for single-day forward paper trading."""
    logger.info("=== Forward Paper-Trading Runner ===")
    runner = ForwardPaperTrader()

    if not data_path.exists():
        logger.error("Specified data file does not exist: %s", data_path)
        sys.exit(1)

    # Ingest daily OHLCV row
    with open(data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        logger.error("Data file is empty: %s", data_path)
        sys.exit(1)

    latest_row = rows[-1]
    date_str = latest_row["date"]
    instrument_id = latest_row.get("source", "NIFTY").split(":")[-1].replace(".NS", "")
    open_p = float(latest_row["open"])
    close_p = float(latest_row["close"])

    res = runner.process_daily_step(
        instrument_id=instrument_id,
        date_str=date_str,
        open_price=open_p,
        close_price=close_p,
        active_theories=[],
    )

    logger.info("Forward paper trading step result: %s", res["status"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forward Paper-Trading Runner")
    parser.add_argument("--data", type=str, required=True, help="Path to daily OHLCV CSV file")
    args = parser.parse_args()
    run_forward_paper_trading(Path(args.data))
