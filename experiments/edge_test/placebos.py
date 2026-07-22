"""
Pre-Registered Placebo Controls Engine for Edge Test Experiments.

Implements two pre-registered falsifier controls per PREREGISTRATION.md f):
1. 5-Day Lagged Signal Control (edge must disappear; Sharpe <= 0.2).
2. 1,000 Permutation Direction-Shuffled Control (realized return > 95th percentile).
"""
import copy
from typing import Any, Dict, List, Tuple
import numpy as np

from experiments.edge_test.harness import calculate_trade_execution_cost
from experiments.edge_test.stats import calculate_edge_stats


def run_lagged_signal_placebo(
    trade_records: List[Dict[str, Any]],
    lag_days: int = 5,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Executes 5-day lagged signal placebo control by shifting position signals by +lag_days.
    """
    if len(trade_records) <= lag_days:
        return {"sharpe": 0.0, "passed_falsifier": True, "notes": "Insufficient data for lag"}

    n = len(trade_records)
    original_signals = [r.get("target_position", 0) for r in trade_records]

    # Shift signal array by lag_days
    lagged_signals = [0] * lag_days + original_signals[:-lag_days]

    lagged_records = []
    curr_pos = 0

    for i in range(n):
        orig_rec = trade_records[i]
        target_pos = lagged_signals[i]
        cost_bps = calculate_trade_execution_cost(curr_pos, target_pos)
        cost_decimal = cost_bps / 10000.0

        open_p = orig_rec.get("open_price", 100.0)
        close_p = orig_rec.get("close_price", 100.0)
        raw_price_ret = (close_p - open_p) / open_p if open_p > 0 else 0.0

        gross_ret = target_pos * raw_price_ret
        net_ret = gross_ret - cost_decimal

        lagged_records.append({
            "day_index": orig_rec.get("day_index", i),
            "date": orig_rec.get("date", ""),
            "target_position": target_pos,
            "gross_return": gross_ret,
            "cost_bps": cost_bps,
            "net_return": net_ret,
        })
        curr_pos = target_pos

    lagged_stats = calculate_edge_stats(lagged_records, seed=seed)
    lagged_sharpe = lagged_stats.get("net_sharpe", 0.0)

    # Pre-registered condition: edge must disappear (Sharpe <= 0.2)
    edge_vanished = (lagged_sharpe <= 0.20)

    return {
        "lag_days": lag_days,
        "net_sharpe": lagged_sharpe,
        "total_net_return_pct": lagged_stats.get("total_net_return_pct", 0.0),
        "edge_vanished": edge_vanished,
        "passed_falsifier": edge_vanished,
        "notes": f"Lagged signal Sharpe={lagged_sharpe:.4f} (expected <= 0.20)",
    }


def run_direction_shuffled_placebo(
    trade_records: List[Dict[str, Any]],
    n_permutations: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Executes 1,000 permutation direction-shuffled placebo control by shuffling non-zero direction commitments.
    """
    if not trade_records:
        return {"percentile_rank": 0.0, "p_value_perm": 1.0, "passed_falsifier": False, "notes": "No trade records"}

    real_stats = calculate_edge_stats(trade_records, seed=seed)
    realized_net_return = real_stats.get("total_net_return_pct", 0.0)

    original_signals = np.array([r.get("target_position", 0) for r in trade_records], dtype=int)
    non_zero_indices = np.where(original_signals != 0)[0]

    if len(non_zero_indices) == 0:
        return {"percentile_rank": 50.0, "p_value_perm": 0.50, "passed_falsifier": False, "notes": "No active position signals to shuffle"}

    rng = np.random.RandomState(seed)
    shuffled_returns = np.zeros(n_permutations)

    open_prices = np.array([r.get("open_price", 100.0) for r in trade_records], dtype=float)
    close_prices = np.array([r.get("close_price", 100.0) for r in trade_records], dtype=float)
    raw_price_rets = np.where(open_prices > 0, (close_prices - open_prices) / open_prices, 0.0)

    for p in range(n_permutations):
        shuffled_signals = original_signals.copy()
        shuffled_directions = original_signals[non_zero_indices].copy()
        rng.shuffle(shuffled_directions)
        shuffled_signals[non_zero_indices] = shuffled_directions

        prev_signals = np.roll(shuffled_signals, 1)
        prev_signals[0] = 0

        # Calculate costs using vectorized lookup
        # Entry buy=9.094 bps, entry sell/exit=11.394 bps, reversal=20.488 bps
        pos_change = shuffled_signals - prev_signals
        cost_bps = np.zeros_like(shuffled_signals, dtype=float)

        reversal_mask = (shuffled_signals != 0) & (prev_signals != 0) & (shuffled_signals != prev_signals)
        entry_buy_mask = (prev_signals == 0) & (shuffled_signals == 1)
        entry_sell_mask = (prev_signals == 0) & (shuffled_signals == -1)
        exit_sell_mask = (prev_signals == 1) & (shuffled_signals == 0)
        exit_buy_mask = (prev_signals == -1) & (shuffled_signals == 0)

        cost_bps[reversal_mask] = 20.488
        cost_bps[entry_buy_mask] = 9.094
        cost_bps[entry_sell_mask] = 11.394
        cost_bps[exit_sell_mask] = 11.394
        cost_bps[exit_buy_mask] = 9.094

        gross_rets = shuffled_signals * raw_price_rets
        net_rets = gross_rets - (cost_bps / 10000.0)

        cum_ret = float(np.prod(1.0 + net_rets) - 1.0) * 100.0
        shuffled_returns[p] = cum_ret

    # Percentile of realized net return relative to shuffled distribution
    percentile = float(np.mean(realized_net_return > shuffled_returns) * 100.0)
    p_perm = float(np.mean(shuffled_returns >= realized_net_return))

    # Pre-registered condition: realized net return > 95th percentile (p_perm < 0.05)
    passed = (percentile >= 95.0)

    return {
        "n_permutations": n_permutations,
        "realized_net_return_pct": realized_net_return,
        "shuffled_mean_return_pct": round(float(np.mean(shuffled_returns)), 2),
        "shuffled_95th_percentile_pct": round(float(np.percentile(shuffled_returns, 95)), 2),
        "percentile_rank": round(percentile, 2),
        "p_value_perm": round(p_perm, 4),
        "passed_falsifier": passed,
        "notes": f"Realized return sits at {percentile:.1f}th percentile of 1,000 shuffled permutations (expected >= 95.0%)",
    }
