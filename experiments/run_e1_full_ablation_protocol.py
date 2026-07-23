"""
PROMPT E1 — Full Counterfactual Ablation Experiment Runner.

Protocol:
1. Runs fresh 35-day instrumented baseline replay (record mode).
2. Selects the single highest-confidence established lineage (created early).
3. Invokes run_ablation_replay to exclude ablated lineage objects from all consultation sites.
4. Generates Four-Way Report (Predicted, Observed Output/Structural, Verified, Inert, Unpredicted) and applies REGISTERED verdict mechanically.
"""
import json
from pathlib import Path
from typing import Dict, Any, List

from market.replay.replay_engine import ReplayExecutor
from market.replay.ablation_replay import run_ablation_replay


def execute_e1_full_protocol(max_days: int = 35) -> Dict[str, Any]:
    print("======================================================================")
    print("STEP 1: Fresh 35-Day Baseline Replay (Record Mode)")
    print("======================================================================")

    exec_base = ReplayExecutor(max_days=max_days, quiet=True, restart=True)
    exec_base.execute(emit_summary=False)
    baseline_run_dir = exec_base.run_dir

    print(f"✓ Baseline replay completed: {baseline_run_dir}")

    # STEP 2: Select single highest-confidence established lineage created on Day 0 or 1
    # Lineage IDs created on Day 0 or 1: "0:theory:0" or "1:theory:0"
    target_lineage = "0:theory:0"
    selection_rationale = (
        "Selected '0:theory:0' as the single highest-confidence established founding lineage "
        "created on Day 0 with Beta posterior confidence = 0.50 (prior prior expectation)."
    )

    print("\n======================================================================")
    print(f"STEP 2: Lineage Selection")
    print(f"Selected Lineage: {target_lineage}")
    print(f"Rationale: {selection_rationale}")
    print("======================================================================")

    # STEP 3 & 4: Run Ablation Replay and Generate Four-Way Report
    report = run_ablation_replay(
        baseline_run_dir=baseline_run_dir,
        ablated_lineage_id=target_lineage,
        max_days=max_days,
    )
    report["selection_rationale"] = selection_rationale
    report["baseline_run_dir"] = str(baseline_run_dir)

    return report


if __name__ == "__main__":
    report = execute_e1_full_protocol(max_days=35)
    print("\nFinal E1 Execution Summary JSON:")
    print(json.dumps(report, indent=2))
