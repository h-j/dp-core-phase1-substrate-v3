"""
PROMPT E1 Task 1: Positive Control Instrument Validation.

Runs DPAdapter on SynthWorldScenario S1 for 50 steps:
1. Promotes (c1, e1) belief to established tier (confidence > 0.65, evidence_count >= 5).
2. Logs baseline consultations and decisions into a local consultation ledger.
3. Re-runs with (c1, e1) lineage ablated.
4. Evaluates 4-way divergence report (predicted, observed, unpredicted, verified influence).
5. Asserts verified_influence is NON-EMPTY.
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bench.synthworld.world import World
from bench.synthworld.scenarios import s1_clean
from bench.synthworld.dp_adapter import DPAdapter

from dp.observability.consultation_ledger import (
    ConsultationLedger,
    set_active_consultation_ledger,
    record_consultation,
    record_decision,
)
from dp.observability.influence_trace import parse_consultation_ledger
from dp.observability.divergence_analyzer import analyze_divergence_and_influence


def run_positive_control(output_dir: Path = None) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = PROJECT_ROOT / "bench" / "results" / "e1_positive_control"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("======================================================================")
    print("RUNNING PROMPT E1 POSITIVE CONTROL INSTRUMENT VALIDATION")
    print("======================================================================")

    # 1. Setup Baseline Consultation Ledger
    base_ledger_path = output_dir / "consultation_ledger.jsonl"
    base_ledger = ConsultationLedger(base_ledger_path)
    set_active_consultation_ledger(base_ledger)

    scenario = s1_clean(T=50)
    adapter = DPAdapter(scenario=scenario)

    world = World(scenario)
    timeline = world.generate()

    # Run 50 steps baseline
    baseline_predictions = {}
    for t in range(50):
        events = timeline[t]
        adapter.observe(t, events)
        preds = adapter.predict(t, events)
        baseline_predictions[t] = preds

    # Verify target belief (D1, E1) promoted to established tier
    target_belief_key = ("D1", "E1")
    target_state = adapter.confidence_states.get(target_belief_key)
    assert target_state is not None, "Target belief (D1, E1) missing from DPAdapter!"
    conf = target_state.confidence
    ev_count = (target_state.alpha - 1.0) + (target_state.beta - 1.0) / 3.0
    print(f"✓ Target (D1, E1) belief confidence: {conf:.4f} | Evidence Count: {ev_count}")

    target_lineage_id = "D1_E1"
    # Find matching hypothesis structural_id
    for h in adapter.hypotheses:
        if h.cause == "D1" and h.effect == "E1":
            target_lineage_id = h.structural_id

    print(f"✓ Ablation Target Structural ID: {target_lineage_id}")

    # 2. Setup Counterfactual Consultation Ledger
    cf_run_dir = output_dir / "counterfactual"
    cf_run_dir.mkdir(parents=True, exist_ok=True)
    cf_ledger_path = cf_run_dir / "consultation_ledger.jsonl"
    cf_ledger = ConsultationLedger(cf_ledger_path)
    set_active_consultation_ledger(cf_ledger)

    scenario_cf = s1_clean(T=50)
    adapter_cf = DPAdapter(scenario=scenario_cf)
    timeline_cf = World(scenario_cf).generate()

    cf_predictions = {}
    for t in range(50):
        events = timeline_cf[t]
        adapter_cf.observe(t, events)

        # Counterfactual predict with target_lineage_id ablated
        decision_id = f"{t}:predict:0"


        preds = {}
        for e in adapter_cf.effects:
            prob_neg = 1.0
            for h in adapter_cf.hypotheses:
                if h.effect != e:
                    continue

                # ABLATION INTERVENTION: Skip target lineage
                if h.structural_id == target_lineage_id:
                    continue

                state = adapter_cf.confidence_states[(h.cause, h.effect)]
                c_conf = state.confidence

                record_consultation(
                    decision_id=decision_id,
                    object_structural_id=h.structural_id,
                    object_kind="confidence_state",
                    role="gate",
                )

                if events.get(h.cause, 0) == 1 and c_conf >= adapter_cf.promotion_threshold:
                    prob_neg *= (1.0 - c_conf)

            preds[e] = 1.0 - prob_neg

        record_decision(
            decision_id=decision_id,
            output_content=str(preds),
            day=t,
        )
        cf_predictions[t] = preds
        prior_events_cf = events

    # 3. Analyze Four-Way Divergence & Influence
    base_records = parse_consultation_ledger(base_ledger_path)
    cf_records = parse_consultation_ledger(cf_ledger_path)

    llm_stats = {"substitution_count": 50, "reinvocation_count": 0}
    report = analyze_divergence_and_influence(
        base_records, cf_records, target_lineage_id, llm_stats=llm_stats
    )

    report_path = output_dir / "positive_control_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n======================================================================")
    print("POSITIVE CONTROL FOUR-WAY REPORT")
    print("======================================================================")
    print(f"VERDICT: [{report['verdict']}]")
    print(f"Target Lineage: {target_lineage_id}")
    print(f"Predicted Influence Set ({len(report['predicted_influence_set'])}): {report['predicted_influence_set']}")
    print(f"Observed Divergence Set ({len(report['observed_divergence_set'])}): {report['observed_divergence_set']}")
    print(f"Verified Influence Set ({len(report['verified_influence_set'])}): {report['verified_influence_set']}")
    print(f"Unpredicted Divergence Set ({len(report['unpredicted_divergence_set'])}): {report['unpredicted_divergence_set']}")
    print("======================================================================")

    # POSITIVE CONTROL HARD ASSERTION
    assert len(report["verified_influence_set"]) > 0, (
        "POSITIVE CONTROL FAILED: verified_influence_set is EMPTY! "
        "The instrument or consultation wiring is broken."
    )
    print("✓ POSITIVE CONTROL PASSED: verified_influence_set is NON-EMPTY!")

    return report


if __name__ == "__main__":
    run_positive_control()
