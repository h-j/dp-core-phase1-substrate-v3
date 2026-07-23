"""
PROMPT E1 — Counterfactual Influence Experiment Runner.

Executes a >-30-day (35-day) instrumented market replay baseline (R_base) and counterfactual run (R_cf),
calculates the Predicted Influence Set (P_trace) via influence_trace.py, identifies the Observed
Divergence Set (D_obs), and evaluates:

- PASS: D_unpredicted (D_obs \\ P_trace) is EMPTY AND (P_trace ∩ D_obs) is NON-EMPTY.
- INSTRUMENTATION FAIL: D_unpredicted is NON-EMPTY (missing read sites in E0a).
- NULL: D_obs is EMPTY (accumulated knowledge did not causally change reasoning in this run).
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Set

from dp.observability.consultation_ledger import ConsultationLedger, set_active_consultation_ledger
from dp.observability.influence_trace import parse_consultation_ledger, compute_influence_set
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from market.replay.replay_engine import ReplayExecutor


def run_e1_counterfactual_experiment(max_days: int = 35, target_object_id: str = "0:theory:0") -> Dict[str, Any]:
    """
    Executes the E1 Counterfactual Influence Experiment over max_days market replay.
    """
    print(f"======================================================================")
    print(f"STARTING E1 EXPERIMENT: Baseline 35-Day Replay (R_base)")
    print(f"======================================================================")

    # 1. Baseline Replay Run (R_base)
    exec_base = ReplayExecutor(max_days=max_days, quiet=True, restart=True)
    exec_base.execute(emit_summary=False)
    run_dir_base = exec_base.run_dir
    ledger_base_path = run_dir_base / "consultation_ledger.jsonl"

    print(f"✓ Baseline replay completed: {run_dir_base.name}")
    records_base = parse_consultation_ledger(ledger_base_path)

    # 2. Compute Predicted Influence Set (P_trace)
    influence_res = compute_influence_set(records_base, target_object_id)
    predicted_influence_set: Set[str] = set(influence_res.get("influenced_decisions", []))
    direct_consultations: Set[str] = set(influence_res.get("direct_consultations", []))

    print(f"✓ Target Object ID: {target_object_id}")
    print(f"✓ Direct Consultations ({len(direct_consultations)}): {sorted(direct_consultations)}")
    print(f"✓ Predicted Influence Set P_trace ({len(predicted_influence_set)}): {sorted(predicted_influence_set)}")

    # 3. Counterfactual Replay Run (R_cf) with targeted perturbation at creation site of target_object_id
    print(f"\n======================================================================")
    print(f"STARTING E1 EXPERIMENT: Counterfactual 35-Day Replay (R_cf)")
    print(f"======================================================================")

    original_process = TheoryGenerationFlow.process

    def patched_theory_process(self, *args, **kwargs):
        theory, stats = original_process(self, *args, **kwargs)
        # Apply perturbation to Day 0 target theory summary
        if getattr(theory, "structural_id", "") == target_object_id or kwargs.get("step", 0) == 0:
            theory.summary = "[COUNTERFACTUAL PERTURBATION E1] " + theory.summary
            theory.thesis = "[COUNTERFACTUAL PERTURBATION E1] " + theory.thesis
        return theory, stats

    try:
        TheoryGenerationFlow.process = patched_theory_process

        exec_cf = ReplayExecutor(max_days=max_days, quiet=True, restart=True)
        exec_cf.execute(emit_summary=False)
        run_dir_cf = exec_cf.run_dir
        ledger_cf_path = run_dir_cf / "consultation_ledger.jsonl"

        print(f"✓ Counterfactual replay completed: {run_dir_cf.name}")
        records_cf = parse_consultation_ledger(ledger_cf_path)

    finally:
        TheoryGenerationFlow.process = original_process

    # 4. Compare Decisions between Baseline and Counterfactual runs to extract Observed Divergence Set (D_obs)
    decisions_base: Dict[str, str] = {
        r["decision_id"]: r["output_hash"]
        for r in records_base
        if r.get("kind") == "decision"
    }

    decisions_cf: Dict[str, str] = {
        r["decision_id"]: r["output_hash"]
        for r in records_cf
        if r.get("kind") == "decision"
    }

    all_decision_ids = set(decisions_base.keys()) | set(decisions_cf.keys())
    observed_divergence_set: Set[str] = set()

    for dec_id in sorted(all_decision_ids):
        hash_b = decisions_base.get(dec_id)
        hash_c = decisions_cf.get(dec_id)
        if hash_b != hash_c:
            observed_divergence_set.add(dec_id)

    # 5. Calculate Unpredicted Divergence Set (D_unpredicted) and Intersection
    unpredicted_divergence_set = observed_divergence_set - predicted_influence_set
    predicted_divergences = predicted_influence_set & observed_divergence_set

    print(f"\n======================================================================")
    print(f"E1 EXPERIMENT EVALUATION RESULTS")
    print(f"======================================================================")
    print(f"Observed Divergence Set D_obs ({len(observed_divergence_set)}): {sorted(observed_divergence_set)}")
    print(f"Predicted Divergence Intersection ({len(predicted_divergences)}): {sorted(predicted_divergences)}")
    print(f"Unpredicted Divergence Set D_unpredicted ({len(unpredicted_divergence_set)}): {sorted(unpredicted_divergence_set)}")

    # 6. Outcome Classification
    if len(observed_divergence_set) == 0:
        outcome = "NULL"
        status_message = "NULL: Divergence set D_obs is empty entirely — accumulated knowledge did not causally change reasoning in this bounded run."
    elif len(unpredicted_divergence_set) > 0:
        outcome = "INSTRUMENTATION FAIL"
        status_message = f"INSTRUMENTATION FAIL: Unpredicted divergence non-empty ({len(unpredicted_divergence_set)} decisions). Missing consultation read sites in E0a."
    elif len(predicted_divergences) >= 1:
        outcome = "PASS"
        status_message = "PASS: D_unpredicted set is EMPTY (every observed divergence was predicted by consultation graph) AND P_trace ∩ D_obs is NON-EMPTY."
    else:
        outcome = "NULL"
        status_message = "NULL: No predicted decisions diverged."

    print(f"\nOUTCOME: [{outcome}]")
    print(f"MESSAGE: {status_message}")

    return {
        "outcome": outcome,
        "status_message": status_message,
        "target_object_id": target_object_id,
        "days_run": max_days,
        "predicted_influence_set": sorted(predicted_influence_set),
        "observed_divergence_set": sorted(observed_divergence_set),
        "unpredicted_divergence_set": sorted(unpredicted_divergence_set),
        "predicted_divergences": sorted(predicted_divergences),
        "run_dir_base": str(run_dir_base),
        "run_dir_cf": str(run_dir_cf),
    }


if __name__ == "__main__":
    res = run_e1_counterfactual_experiment(max_days=35, target_object_id="0:theory:0")
    print("\nFinal Results JSON:")
    print(json.dumps(res, indent=2))
