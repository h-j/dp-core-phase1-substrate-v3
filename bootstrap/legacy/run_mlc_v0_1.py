import csv
import json
import os

from flows.minimal_learning_cycle.artifacts import MLCArtifacts
from flows.minimal_learning_cycle.config import (ADMIT_THRESHOLD,
                                                 REJECT_THRESHOLD)
from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.metrics import MLCMetrics
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld
from flows.minimal_learning_cycle.validity_gates import MLCValidityGates


def run_smoke_test():
    print("Starting MLC v0.1 Smoke Test...")

    families = ["A", "B", "C1", "C2"]
    seed = 42

    runner = MLCExperimentRunner()

    worlds = []
    # Generate 4 worlds
    for fam in families:
        w = MLCSyntheticWorld.generate_world(fam, seed)
        worlds.append(w)

    print(f"Generated {len(worlds)} worlds for Families {families}.")

    # Run lifecycle for all 4 worlds
    for w in worlds:
        w_id = f"WORLD_{w['family']}_SEED_{w['seed']}"
        print(f"Running lifecycle for {w_id}...")
        runner.run_lifecycle(w)

    print("All lifecycles executed. Evaluating validity gates...")

    # Run validity gates
    gates = MLCValidityGates.run_gates(
        runner.world_registry,
        runner.erc.logs,
        runner.frozen_candidates,
        runner.decisions,
        runner.belief_memory.records,
    )

    # Calculate metrics
    # Reconstruct B4 Oracle and B2 retrospective decisions from baseline_results
    oracle_decisions = []
    b2_decisions = []
    for w in worlds:
        w_id = f"WORLD_{w['family']}_SEED_{w['seed']}"
        oracle_decisions.append(
            {
                "world_id": w_id,
                "decision": w["expected_decision"],
                "reason_code": w["expected_reason"],
            }
        )
        b2_decisions.append(
            {
                "world_id": w_id,
                "decision": runner.baseline_results["b2_decisions"][w_id],
            }
        )

    metrics = MLCMetrics.calculate_metrics(
        runner.decisions,
        oracle_decisions,
        b2_decisions,
        runner.frozen_candidates,
        runner.erc.logs,
    )

    # Write artifacts
    import datetime
    import uuid

    run_id = f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    artifact_dir = os.path.join(
        project_root, "artifacts", "experiments", "mlc_v0_1", run_id
    )
    config_dict = {
        "admit_threshold": ADMIT_THRESHOLD,
        "reject_threshold": REJECT_THRESHOLD,
        "pre_registered_hypotheses": ["H1", "H2", "H3", "H4", "H5"],
    }

    from flows.minimal_learning_cycle.verdicts import MLCVerdictEvaluator

    evaluator = MLCVerdictEvaluator()
    scientific_result = evaluator.evaluate_result(
        decisions=runner.decisions,
        oracle_decisions=runner.ground_truth,
        baseline_results=runner.baseline_results,
        frozen_candidates=runner.frozen_candidates,
        erc_logs=runner.erc.logs,
        validity_gates=gates,
        metrics=metrics,
        run_id=run_id,
    )

    print(f"Writing all artifacts to {artifact_dir}...")
    MLCArtifacts.write_artifacts(
        artifact_dir,
        config_dict,
        runner.world_registry,
        runner.ground_truth,
        runner.propositions,
        runner.erc.logs,
        runner.ledger.get_records(),
        runner.intrinsic_measurements,
        runner.frozen_candidates,
        runner.prospective_measurements,
        runner.decisions,
        runner.belief_memory.records,
        runner.baseline_results,
        gates,
        metrics,
        scientific_result,
    )

    # Forensic reconstruction verification check
    print("Verifying forensic reconstruction check...")
    decisions_path = os.path.join(artifact_dir, "mlc_v0_1_decisions.json")
    with open(decisions_path, "r") as f:
        reconstructed_decisions = json.load(f)
    assert len(reconstructed_decisions) == len(runner.decisions)
    for idx, rd in enumerate(reconstructed_decisions):
        assert rd["decision"] == runner.decisions[idx]["decision"]
        assert rd["reason_code"] == runner.decisions[idx]["reason_code"]
        assert rd["measured_effect"] == runner.decisions[idx]["measured_effect"]

    print("\n" + "=" * 60)
    print("SMOKE TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"World Count: {len(worlds)}")
    print(f"Family Count: {len(families)}")
    print(
        f"Gate Execution Status: {'PASS' if all(g['status'] == 'PASS' for g in gates.values()) else 'FAIL'}"
    )
    print(f"Reconstruction Status: SUCCESS (Persisted matches runtime)")
    print(f"MLC Decisions: {[d['decision'] for d in runner.decisions]}")
    print(f"Oracle Decisions: {[w['expected_decision'] for w in worlds]}")
    print(
        f"B2 Retrospective Decisions: {[runner.baseline_results['b2_decisions'][f'WORLD_{w['family']}_SEED_{w['seed']}'] for w in worlds]}"
    )
    print("=" * 60)


if __name__ == "__main__":
    run_smoke_test()
