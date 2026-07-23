"""
Forensic Attribution Script for Edge Test Historical Diagnostic Data.

Performs quantitative analysis on experiments/edge_test/results/trade_ledger.jsonl
and universe CSVs to generate evidence-backed measurements for FORENSIC_ATTRIBUTION_REPORT.md.
"""
import csv
import json
import math
import numpy as np
from pathlib import Path

def analyze_trade_ledger():
    ledger_path = Path("experiments/edge_test/results/trade_ledger.jsonl")
    if not ledger_path.exists():
        print("Ledger file missing.")
        return

    records = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Loaded {len(records)} records from trade_ledger.jsonl")

    # 1. Trade Attribution Analysis
    losing_trades = [r for r in records if r.get("net_return", 0.0) < 0]
    winning_trades = [r for r in records if r.get("net_return", 0.0) > 0]
    flat_trades = [r for r in records if r.get("net_return", 0.0) == 0]

    print(f"\n--- Trade Breakdown ---")
    print(f"Total Records: {len(records)}")
    print(f"Losing Trades: {len(losing_trades)} ({len(losing_trades)/len(records)*100:.2f}%)")
    print(f"Winning Trades: {len(winning_trades)} ({len(winning_trades)/len(records)*100:.2f}%)")
    print(f"Flat/Zero Days: {len(flat_trades)} ({len(flat_trades)/len(records)*100:.2f}%)")

    total_gross = sum(r.get("gross_return", 0.0) for r in records)
    total_cost_bps = sum(r.get("cost_bps", 0.0) for r in records)
    total_cost_dec = total_cost_bps / 10000.0
    total_net = sum(r.get("net_return", 0.0) for r in records)

    print(f"\n--- Return Decomposition ---")
    print(f"Total Gross Return: {total_gross*100:.2f}%")
    print(f"Total Friction Penalty (Cost Drag): {total_cost_dec*100:.2f}% ({total_cost_bps:.1f} bps total)")
    print(f"Total Net Return: {total_net*100:.2f}%")

    # 2. Position Flips & Turnover Breakdown
    positions = [r.get("target_position", 0) for r in records]
    prev_pos = [r.get("previous_position", 0) for r in records]

    reversals = sum(1 for p, prev in zip(positions, prev_pos) if p != 0 and prev != 0 and p != prev)
    entries = sum(1 for p, prev in zip(positions, prev_pos) if prev == 0 and p != 0)
    exits = sum(1 for p, prev in zip(positions, prev_pos) if p == 0 and prev != 0)
    holds = sum(1 for p, prev in zip(positions, prev_pos) if p == prev and p != 0)
    flats = sum(1 for p, prev in zip(positions, prev_pos) if p == 0 and prev == 0)

    print(f"\n--- Turnover & Execution Breakdown ---")
    print(f"Position Reversals (+1 <-> -1): {reversals} ({reversals/len(records)*100:.2f}%)")
    print(f"New Entries (0 -> +1/-1): {entries} ({entries/len(records)*100:.2f}%)")
    print(f"Exits to Flat (+1/-1 -> 0): {exits} ({exits/len(records)*100:.2f}%)")
    print(f"Position Holds (+1->+1, -1->-1): {holds} ({holds/len(records)*100:.2f}%)")
    print(f"Flat Days (0 -> 0): {flats} ({flats/len(records)*100:.2f}%)")

    # Cost paid by event type
    reversal_cost = reversals * 20.488
    entry_cost = entries * 10.244 # Avg buy/sell entry
    exit_cost = exits * 10.244
    print(f"Cost paid on Reversals: {reversal_cost:.1f} bps ({reversal_cost/total_cost_bps*100:.1f}% of total friction)")
    print(f"Cost paid on Entries/Exits: {(entry_cost + exit_cost):.1f} bps ({(entry_cost + exit_cost)/total_cost_bps*100:.1f}% of total friction)")

    # 3. Regime Attribution Analysis
    # Classify market regimes in dataset via rolling volatility & trend
    regime_matches = 0
    regime_mismatches = 0
    match_returns = []
    mismatch_returns = []

    for r in records:
        open_p = r.get("open_price", 100.0)
        close_p = r.get("close_price", 100.0)
        raw_ret = (close_p - open_p) / open_p if open_p > 0 else 0.0
        pos = r.get("target_position", 0)

        # High volatility / trend regime check
        is_trending_day = abs(raw_ret) > 0.005
        fired = r.get("theory_ids_fired", [])
        if pos != 0:
            if is_trending_day:
                regime_matches += 1
                match_returns.append(r.get("net_return", 0.0))
            else:
                regime_mismatches += 1
                mismatch_returns.append(r.get("net_return", 0.0))

    tot_active = regime_matches + regime_mismatches
    print(f"\n--- Regime Attribution Analysis ---")
    print(f"Active Position Days: {tot_active}")
    print(f"Executed in Matching (Trending) Regime: {regime_matches} ({regime_matches/tot_active*100:.2f}%) | Mean Net Return: {np.mean(match_returns)*100:.4f}%")
    print(f"Executed in Non-Matching (Ranging) Regime: {regime_mismatches} ({regime_mismatches/tot_active*100:.2f}%) | Mean Net Return: {np.mean(mismatch_returns)*100:.4f}%")

    # 4. Hysteresis Simulation
    print(f"\n--- Hysteresis Simulation (Analysis Only) ---")
    # Simulate holding period of min 3 days
    sim_signals = []
    sim_pos = 0
    hold_counter = 0

    sim_trade_records = []
    for i, r in enumerate(records):
        target_p = r.get("target_position", 0)
        if hold_counter > 0:
            # Enforce holding period
            target_p = sim_pos
            hold_counter -= 1
        else:
            if target_p != sim_pos and target_p != 0:
                hold_counter = 2  # Hold for 3 days
                sim_pos = target_p

        cost_bps = 0.0
        prev_p = sim_trade_records[-1]["position"] if sim_trade_records else 0
        if target_p != prev_p:
            if prev_p != 0 and target_p != 0 and prev_p != target_p:
                cost_bps = 20.488
            elif prev_p == 0 and target_p != 0:
                cost_bps = 9.094 if target_p == 1 else 11.394
            elif target_p == 0 and prev_p != 0:
                cost_bps = 11.394 if prev_p == 1 else 9.094

        open_p = r.get("open_price", 100.0)
        close_p = r.get("close_price", 100.0)
        raw_ret = (close_p - open_p) / open_p if open_p > 0 else 0.0
        gross_r = target_p * raw_ret
        net_r = gross_r - (cost_bps / 10000.0)

        sim_trade_records.append({
            "position": target_p,
            "cost_bps": cost_bps,
            "gross_return": gross_r,
            "net_return": net_r,
        })

    sim_costs = sum(r["cost_bps"] for r in sim_trade_records)
    sim_turnover = sum(1 for r in sim_trade_records if r["cost_bps"] > 0) / len(records)
    sim_net_ret = sum(r["net_return"] for r in sim_trade_records)

    print(f"Hysteresis Sim Total Friction: {sim_costs:.1f} bps (vs Baseline {total_cost_bps:.1f} bps) -> Cost Reduction: {(1.0 - sim_costs/total_cost_bps)*100:.2f}%")
    print(f"Hysteresis Sim Turnover: {sim_turnover:.4f} (vs Baseline {sum(1 for p, prev in zip(positions, prev_pos) if p != prev)/len(records):.4f}) -> Turnover Reduction: {(1.0 - sim_turnover/(sum(1 for p, prev in zip(positions, prev_pos) if p != prev)/len(records)))*100:.2f}%")
    print(f"Hysteresis Sim Net Return: {sim_net_ret*100:.2f}% (vs Baseline {total_net*100:.2f}%)")

if __name__ == "__main__":
    analyze_trade_ledger()
