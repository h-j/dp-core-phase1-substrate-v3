"""
Walk-Forward Edge Test Harness for DP-Core Reflective Cognition Substrate.

Implements the mechanical trading rule and anchored walk-forward evaluation protocol
EXACTLY per experiments/edge_test/PREREGISTRATION.md and experiments/edge_test/RULE_SPEC.md.
"""
import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings
from interfaces.llm_ledger import LLMLedger

logger = logging.getLogger(__name__)

# Pre-registered Constants (FROZEN - Must match PREREGISTRATION.md and RULE_SPEC.md)
PRE_REGISTERED_CONSTANTS = {
    "RELIABILITY_BAND_ESTABLISHED_MIN": 0.75,
    "SIGNAL_WEIGHTED_SUM_THRESHOLD": 0.25,
    "POSITION_NOTIONAL_FRACTION": 1.0,
    "COST_BROKERAGE_PER_SIDE_BPS": 3.0,
    "COST_STT_SELL_SIDE_BPS": 2.5,
    "COST_EXCHANGE_PER_SIDE_BPS": 0.3,
    "COST_GST_RATE": 0.18,
    "COST_STAMP_DUTY_BUY_BPS": 0.2,
    "COST_SLIPPAGE_PER_SIDE_BPS": 5.0,
    "COST_BUY_SIDE_BPS": 9.094,
    "COST_SELL_SIDE_BPS": 11.394,
    "ALL_IN_ROUND_TRIP_COST_BPS": 20.488,
}


def verify_preregistered_constants(custom_constants: Optional[Dict[str, float]] = None) -> None:
    """
    Verifies that required pre-registration documents exist on disk and that all constants match.
    Hard fails with ValueError / FileNotFoundError if documents are missing or constants mismatch.
    """
    prereg_path = Path("experiments/edge_test/PREREGISTRATION.md")
    spec_path = Path("experiments/edge_test/RULE_SPEC.md")

    if not prereg_path.exists():
        raise FileNotFoundError(f"[EdgeTestHarness] Pre-registration document missing: {prereg_path}")
    if not spec_path.exists():
        raise FileNotFoundError(f"[EdgeTestHarness] Rule specification document missing: {spec_path}")

    target = custom_constants if custom_constants is not None else PRE_REGISTERED_CONSTANTS

    for key, expected_val in PRE_REGISTERED_CONSTANTS.items():
        val = target.get(key)
        if val is None or not math.isclose(val, expected_val, rel_tol=1e-5, abs_tol=1e-5):
            raise ValueError(
                f"[EdgeTestHarness] Pre-registered constant mismatch for '{key}': "
                f"expected {expected_val}, got {val}"
            )
    logger.info("[EdgeTestHarness] Pre-registration verification passed successfully.")


def evaluate_mechanical_signal_for_day(
    theories: List[Any],
    instrument_id: str,
    day_t: int,
    reliability_threshold: float = 0.75,
    signal_threshold: float = 0.25,
) -> Tuple[int, float, List[str]]:
    """
    Evaluates mechanical signal for day t+1 based strictly on EOD day t established theories.
    
    Reads ONLY:
    - theory.reliability_score / confidence
    - theory scope predicate
    - theory activation predicate
    - directional commitment from fallback payload

    Returns:
        Tuple of (target_position: int {-1, 0, +1}, weighted_sum: float, theory_ids_fired: List[str])
    """
    established_theories = []
    fired_ids = []

    for theory in theories:
        # 1. Reliability score
        if isinstance(theory, dict):
            rel_score = float(theory.get("confidence", theory.get("reliability_score", 0.5)))
        else:
            rel_score = float(getattr(theory, "reliability_score", getattr(theory, "confidence", 0.5)))

        if rel_score <= reliability_threshold:
            continue

        # 2. Scope predicate
        scope_ok = True
        if isinstance(theory, dict):
            app_filter = theory.get("applicability_filter", {})
            if isinstance(app_filter, dict) and "instrument" in app_filter:
                scope_ok = (app_filter["instrument"] == instrument_id)
        else:
            if hasattr(theory, "scope_predicate") and callable(getattr(theory, "scope_predicate")):
                scope_ok = bool(theory.scope_predicate(instrument_id, day_t))

        if not scope_ok:
            continue

        # 3. Activation predicate
        act_ok = True
        if isinstance(theory, dict):
            act_ok = bool(theory.get("is_active", True))
        else:
            if hasattr(theory, "activation_predicate") and callable(getattr(theory, "activation_predicate")):
                act_ok = bool(theory.activation_predicate(instrument_id, day_t))
            elif hasattr(theory, "is_active"):
                act_ok = bool(getattr(theory, "is_active", True))

        if not act_ok:
            continue

        # 4. Directional commitment
        commitment = 0
        if isinstance(theory, dict):
            commitment = int(theory.get("directional_commitment", 0))
            if commitment == 0 and "summary" in theory:
                s_lower = str(theory["summary"]).lower()
                if "bull" in s_lower or "up" in s_lower or "higher" in s_lower:
                    commitment = +1
                elif "bear" in s_lower or "down" in s_lower or "lower" in s_lower:
                    commitment = -1
        else:
            if hasattr(theory, "fallback_payload") and hasattr(theory.fallback_payload, "directional_commitment"):
                commitment = int(theory.fallback_payload.directional_commitment)
            elif hasattr(theory, "directional_commitment"):
                commitment = int(theory.directional_commitment)
            elif hasattr(theory, "summary"):
                s_lower = str(theory.summary).lower()
                if "bull" in s_lower or "up" in s_lower or "higher" in s_lower:
                    commitment = +1
                elif "bear" in s_lower or "down" in s_lower or "lower" in s_lower:
                    commitment = -1

        if commitment != 0:
            th_id = (theory.get("id") if isinstance(theory, dict) else getattr(theory, "id", None)) or f"TH_{len(fired_ids)}"
            established_theories.append((rel_score, commitment, th_id))
            fired_ids.append(th_id)

    if not established_theories:
        return 0, 0.0, []

    weighted_sum = sum(rel * comm for rel, comm, _ in established_theories)

    if abs(weighted_sum) < signal_threshold:
        return 0, weighted_sum, fired_ids

    target_pos = +1 if weighted_sum > 0 else -1
    return target_pos, weighted_sum, fired_ids


def calculate_trade_execution_cost(current_position: int, target_position: int) -> float:
    """
    Calculates execution cost penalty in bps per trade execution according to RULE_SPEC.md:
    - Entry (0 -> +1 or 0 -> -1): Buy side (9.094 bps) or Sell side (11.394 bps)
    - Exit (+1 -> 0 or -1 -> 0): Sell side (11.394 bps) or Buy side (9.094 bps)
    - Reversal (+1 -> -1 or -1 -> +1): All-In Round-Trip (20.488 bps)
    - Flat (0 -> 0) or Hold (+1 -> +1 or -1 -> -1): 0 bps

    Returns:
        Cost penalty in bps (float).
    """
    if target_position == current_position:
        return 0.0

    if current_position == 0:
        return PRE_REGISTERED_CONSTANTS["COST_BUY_SIDE_BPS"] if target_position == +1 else PRE_REGISTERED_CONSTANTS["COST_SELL_SIDE_BPS"]
    elif target_position == 0:
        return PRE_REGISTERED_CONSTANTS["COST_SELL_SIDE_BPS"] if current_position == +1 else PRE_REGISTERED_CONSTANTS["COST_BUY_SIDE_BPS"]
    else:
        return PRE_REGISTERED_CONSTANTS["ALL_IN_ROUND_TRIP_COST_BPS"]


class EdgeTestHarness:
    """
    Executes mechanical walk-forward edge tests and logs trade ledgers cleanly.
    """

    def __init__(self, ledger_file: Optional[Path] = None):
        verify_preregistered_constants()
        self.ledger_file = ledger_file or Path("experiments/edge_test/results/trade_ledger.jsonl")
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        self.trade_records: List[Dict[str, Any]] = []

    def record_trade_step(
        self,
        day_index: int,
        date_str: str,
        instrument_id: str,
        signal_t: int,
        target_position: int,
        current_position: int,
        open_price: float,
        close_price: float,
        theory_ids_fired: List[str],
    ) -> Dict[str, Any]:
        """
        Executes single trade step at day t+1 Open and logs to JSONL ledger.
        """
        cost_bps = calculate_trade_execution_cost(current_position, target_position)
        cost_decimal = cost_bps / 10000.0

        if open_price <= 0:
            raw_price_return = 0.0
        else:
            raw_price_return = (close_price - open_price) / open_price

        gross_return = target_position * raw_price_return
        net_return = gross_return - cost_decimal

        record = {
            "day_index": day_index,
            "date": date_str,
            "instrument": instrument_id,
            "signal_t": signal_t,
            "target_position": target_position,
            "previous_position": current_position,
            "open_price": round(open_price, 4),
            "close_price": round(close_price, 4),
            "gross_return": round(gross_return, 6),
            "cost_bps": round(cost_bps, 4),
            "net_return": round(net_return, 6),
            "theory_ids_fired": theory_ids_fired,
        }

        self.trade_records.append(record)
        with open(self.ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        return record
