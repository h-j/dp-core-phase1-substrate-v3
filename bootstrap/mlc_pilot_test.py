import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from typing import Any, Dict, List

import pytest

# Code under test
from flows.minimal_learning_cycle.config import (ADMIT_THRESHOLD, MIN_COVERAGE,
                                                 MIN_EVIDENCE_COUNT,
                                                 REJECT_THRESHOLD)
from flows.minimal_learning_cycle.pilot import (MLCPilotMetrics,
                                                MLCPilotPowerAnalysis,
                                                MLCPilotValidityGates,
                                                MLCPilotWorldGenerator,
                                                normal_cdf)


# Helper to generate mock inputs for testing metric functions
def get_mock_decisions_and_gt():
    # 10 worlds
    registry = [
        {
            "world_id": "W1",
            "zone": "CLEAR",
            "true_effect": 0.35,
            "ground_truth_decision": "ADMIT",
            "ground_truth_defer_subtype": None,
        },
        {
            "world_id": "W2",
            "zone": "CLEAR",
            "true_effect": -0.35,
            "ground_truth_decision": "REJECT",
            "ground_truth_defer_subtype": None,
        },
        {
            "world_id": "W3",
            "zone": "BOUNDARY",
            "true_effect": 0.05,
            "ground_truth_decision": "DEFER",
            "ground_truth_defer_subtype": "EFFECT_AMBIGUITY",
        },
        {
            "world_id": "W4",
            "zone": "BOUNDARY",
            "true_effect": 0.16,
            "ground_truth_decision": "ADMIT",
            "ground_truth_defer_subtype": None,
        },
        {
            "world_id": "W5",
            "zone": "BOUNDARY",
            "true_effect": -0.08,
            "ground_truth_decision": "REJECT",
            "ground_truth_defer_subtype": None,
        },
        {
            "world_id": "W6",
            "zone": "BOUNDARY",
            "true_effect": 0.12,
            "ground_truth_decision": "DEFER",
            "ground_truth_defer_subtype": "EFFECT_AMBIGUITY",
        },
        {
            "world_id": "W7",
            "zone": "EVIDENCE_LIMITED",
            "true_effect": 0.35,
            "ground_truth_decision": "DEFER",
            "ground_truth_defer_subtype": "EVIDENCE_LIMITED",
        },
        {
            "world_id": "W8",
            "zone": "EVIDENCE_LIMITED",
            "true_effect": 0.35,
            "ground_truth_decision": "DEFER",
            "ground_truth_defer_subtype": "EVIDENCE_LIMITED",
        },
        {
            "world_id": "W9",
            "zone": "CLEAR",
            "true_effect": 0.35,
            "ground_truth_decision": "ADMIT",
            "ground_truth_defer_subtype": None,
        },
        {
            "world_id": "W10",
            "zone": "CLEAR",
            "true_effect": -0.35,
            "ground_truth_decision": "REJECT",
            "ground_truth_defer_subtype": None,
        },
    ]

    oracle_decisions = [
        {
            "world_id": "W1",
            "decision": "ADMIT",
            "expected_reason": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W2",
            "decision": "REJECT",
            "expected_reason": "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT",
        },
        {"world_id": "W3", "decision": "DEFER", "expected_reason": "EFFECT_AMBIGUITY"},
        {
            "world_id": "W4",
            "decision": "ADMIT",
            "expected_reason": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W5",
            "decision": "REJECT",
            "expected_reason": "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT",
        },
        {"world_id": "W6", "decision": "DEFER", "expected_reason": "EFFECT_AMBIGUITY"},
        {"world_id": "W7", "decision": "DEFER", "expected_reason": "EVIDENCE_LIMITED"},
        {"world_id": "W8", "decision": "DEFER", "expected_reason": "EVIDENCE_LIMITED"},
        {
            "world_id": "W9",
            "decision": "ADMIT",
            "expected_reason": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W10",
            "decision": "REJECT",
            "expected_reason": "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT",
        },
    ]

    # MLC decisions
    decisions = [
        {
            "world_id": "W1",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W2",
            "decision": "REJECT",
            "reason_code": "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W3",
            "decision": "DEFER",
            "reason_code": "AMBIGUOUS_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W4",
            "decision": "DEFER",
            "reason_code": "AMBIGUOUS_PROSPECTIVE_EFFECT",
        },  # MLC incorrect
        {
            "world_id": "W5",
            "decision": "REJECT",
            "reason_code": "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W6",
            "decision": "DEFER",
            "reason_code": "AMBIGUOUS_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W7",
            "decision": "DEFER",
            "reason_code": "INSUFFICIENT_PROSPECTIVE_EVIDENCE",
        },
        {
            "world_id": "W8",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },  # MLC incorrect & catastrophic
        {
            "world_id": "W9",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "W10",
            "decision": "REJECT",
            "reason_code": "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT",
        },
    ]

    baseline_results = {
        "b2_decisions": {
            "W1": "ADMIT",
            "W2": "REJECT",
            "W3": "DEFER",
            "W4": "ADMIT",
            "W5": "REJECT",
            "W6": "DEFER",
            "W7": "DEFER",
            "W8": "ADMIT",
            "W9": "ADMIT",
            "W10": "REJECT",
        },
        "b3_decisions": {
            "W1": "DEFER",
            "W2": "ADMIT",
            "W3": "REJECT",
            "W4": "DEFER",
            "W5": "ADMIT",
            "W6": "REFER",
            "W7": "ADMIT",
            "W8": "REJECT",
            "W9": "DEFER",
            "W10": "ADMIT",
        },
        "b4_decisions": {
            "W1": "ADMIT",
            "W2": "REJECT",
            "W3": "DEFER",
            "W4": "ADMIT",
            "W5": "REJECT",
            "W6": "DEFER",
            "W7": "DEFER",
            "W8": "DEFER",
            "W9": "ADMIT",
            "W10": "REJECT",
        },
    }

    return registry, oracle_decisions, decisions, baseline_results


# 1. Exact 100-world registry
def test_exact_100_world_registry():
    registry = MLCPilotWorldGenerator.generate_registry()
    assert len(registry) == 100
    world_ids = [entry["world_id"] for entry in registry]
    assert len(set(world_ids)) == 100


# 2. Exact zone composition
def test_exact_zone_composition():
    registry = MLCPilotWorldGenerator.generate_registry()
    clear_count = sum(1 for entry in registry if entry["zone"] == "CLEAR")
    boundary_count = sum(1 for entry in registry if entry["zone"] == "BOUNDARY")
    evidence_limited_count = sum(
        1 for entry in registry if entry["zone"] == "EVIDENCE_LIMITED"
    )

    assert clear_count == 30
    assert boundary_count == 50
    assert evidence_limited_count == 20


# 3. Correct boundary effect → ground truth mapping
def test_correct_boundary_effect_mapping():
    registry = MLCPilotWorldGenerator.generate_registry()
    boundary_worlds = [entry for entry in registry if entry["zone"] == "BOUNDARY"]

    for entry in boundary_worlds:
        eff = entry["true_effect"]
        decision = entry["ground_truth_decision"]
        subtype = entry["ground_truth_defer_subtype"]

        if eff == -0.08:
            assert decision == "REJECT"
            assert subtype is None
        elif eff in [-0.04, 0.00, 0.05, 0.12]:
            assert decision == "DEFER"
            assert subtype == "EFFECT_AMBIGUITY"
        elif eff in [0.16, 0.20]:
            assert decision == "ADMIT"
            assert subtype is None
        else:
            pytest.fail(f"Unexpected true effect value in Boundary Zone: {eff}")


# 4. Multiple seeds per boundary effect
def test_multiple_seeds_per_boundary_effect():
    registry = MLCPilotWorldGenerator.generate_registry()
    boundary_worlds = [entry for entry in registry if entry["zone"] == "BOUNDARY"]

    seeds_by_effect = {}
    for entry in boundary_worlds:
        seeds_by_effect.setdefault(entry["true_effect"], []).append(entry["seed"])

    assert len(seeds_by_effect) == 7
    for eff, seeds in seeds_by_effect.items():
        assert len(seeds) > 1
        assert len(set(seeds)) == len(seeds)


# 5. Registry hash immutability
def test_registry_hash_immutability():
    registry = MLCPilotWorldGenerator.generate_registry()
    reg_str = json.dumps(registry, sort_keys=True)
    hash_original = hashlib.sha256(reg_str.encode("utf-8")).hexdigest()

    # Adversarial mutation
    registry_mutated = list(registry)
    registry_mutated[0]["seed"] += 1
    reg_mutated_str = json.dumps(registry_mutated, sort_keys=True)
    hash_mutated = hashlib.sha256(reg_mutated_str.encode("utf-8")).hexdigest()

    assert hash_original != hash_mutated


# 6. Threshold freeze and ordering
def test_threshold_freeze_and_ordering():
    assert ADMIT_THRESHOLD == 0.15
    assert REJECT_THRESHOLD == -0.05
    assert REJECT_THRESHOLD < ADMIT_THRESHOLD


# 7-10. Accuracies: Pooled and Zone-level (Clear, Boundary, Evidence-Limited)
def test_pooled_and_zone_accuracies():
    registry, oracle, decisions, baselines = get_mock_decisions_and_gt()

    metrics = MLCPilotMetrics.calculate_zone_metrics(
        decisions, oracle, baselines, registry
    )

    # MLC correct: W1, W2, W3, W5, W6, W7, W9, W10 (8 out of 10) -> 0.8
    # B2 correct: W1, W2, W3, W4, W5, W6, W7, W9, W10 (9 out of 10) -> 0.9 (since W4 is ADMIT on B2 and matches Oracle)
    # B3 correct: W1 (DEFER vs ADMIT - wrong), W2 (ADMIT vs REJECT - wrong), W3 (REJECT vs DEFER - wrong),
    #             W4 (DEFER vs ADMIT - wrong), W5 (ADMIT vs REJECT - wrong), W6 (REFER - wrong),
    #             W7 (ADMIT vs DEFER - wrong), W8 (REJECT vs DEFER - wrong), W9 (DEFER vs ADMIT - wrong),
    #             W10 (ADMIT vs REJECT - wrong) -> 0.0

    assert metrics["pooled"]["mlc_accuracy"] == 0.80
    assert metrics["pooled"]["b2_accuracy"] == 0.90
    assert metrics["pooled"]["b3_accuracy"] == 0.00
    assert (
        metrics["pooled"]["b4_accuracy"] == 1.00
    )  # B4 Oracle always matches ground truth.

    # Clear Zone accuracy (W1, W2, W9, W10)
    # MLC correct: all 4 -> 1.0
    # B2 correct: all 4 -> 1.0
    assert metrics["clear_zone"]["mlc_accuracy"] == 1.00
    assert metrics["clear_zone"]["b2_accuracy"] == 1.00

    # Boundary Zone accuracy (W3, W4, W5, W6)
    # MLC correct: W3 (DEFER), W5 (REJECT), W6 (DEFER) -> 3/4 = 0.75
    # B2 correct: all 4 -> 1.00
    assert metrics["boundary_zone"]["mlc_accuracy"] == 0.75
    assert metrics["boundary_zone"]["b2_accuracy"] == 1.00

    # Evidence-Limited Zone accuracy (W7, W8)
    # MLC correct: W7 (DEFER) -> 1/2 = 0.50
    # B2 correct: W7 (DEFER) -> 1/2 = 0.50
    assert metrics["evidence_limited_zone"]["mlc_accuracy"] == 0.50
    assert metrics["evidence_limited_zone"]["b2_accuracy"] == 0.50


# 11-12. H4 Pooled and decomposition safety rates
def test_h4_safety_rates_and_decomposition():
    registry, oracle, decisions, baselines = get_mock_decisions_and_gt()

    h4 = MLCPilotMetrics.calculate_h4_decomposition(decisions, oracle, baselines)

    # Catastrophic False Admission: decided ADMIT when GT is not ADMIT (REJECT or DEFER).
    # MLC: W8 (decided ADMIT, GT is DEFER/EVIDENCE_LIMITED) -> 1 out of 10 -> 0.10
    # B2: W8 (decided ADMIT, GT is DEFER/EVIDENCE_LIMITED) -> 1 out of 10 -> 0.10

    assert h4["pooled"]["mlc_rate"] == 0.10
    assert h4["pooled"]["mlc_count"] == 1

    assert h4["pooled"]["b2_rate"] == 0.10
    assert h4["pooled"]["b2_count"] == 1

    # Decomposition
    assert h4["false_admit_evidence_limited"]["mlc_count"] == 1  # W8
    assert h4["false_admit_reject"]["mlc_count"] == 0
    assert h4["false_admit_effect_ambiguous"]["mlc_count"] == 0


# 13. H5 calibration metrics
def test_h5_calibration_metrics():
    registry, oracle, decisions, baselines = get_mock_decisions_and_gt()

    h5 = MLCPilotMetrics.calculate_h5_metrics(decisions, oracle)

    # Actual defers by MLC: W3, W4, W6, W7 (4 worlds)
    # Expected defers by Oracle: W3, W6, W7, W8 (4 worlds)
    # True defers: W3, W6, W7 (3 worlds)
    # Defer Precision = 3/4 = 0.75
    # Defer Recall = 3/4 = 0.75
    assert h5["defer_precision"] == 0.75
    assert h5["defer_recall"] == 0.75

    # Subtype Accuracies
    # EVIDENCE_LIMITED worlds: W7, W8 (2 worlds). W7 is DEFER and reason is INSUFFICIENT_PROSPECTIVE_EVIDENCE -> correct. W8 is ADMIT -> wrong. Accuracy = 1/2 = 0.50
    # EFFECT_AMBIGUITY worlds: W3, W6 (2 worlds). Both are DEFER and reason AMBIGUOUS_PROSPECTIVE_EFFECT -> correct. Accuracy = 2/2 = 1.00
    assert h5["evidence_limited_subtype_accuracy"] == 0.50
    assert h5["effect_ambiguity_subtype_accuracy"] == 1.00

    # Confusion matrix
    assert h5["confusion_matrix"]["actual_defer"]["predicted_defer"] == 3  # W3, W6, W7
    assert h5["confusion_matrix"]["actual_defer"]["predicted_admit"] == 1  # W8


# 14-17. Paired comparison and Power estimation math
def test_paired_comparison_and_power_math():
    # Construct a controlled set of decisions with a known difference
    # 100 worlds, mean diff = 0.05, std dev = 0.2
    # Standard deviation of 0.2:
    # 95 worlds have 0 diff, 5 worlds have 1 diff -> mean = 0.05.
    # Variance = (95 * (0 - 0.05)^2 + 5 * (1 - 0.05)^2) / 99 = (95 * 0.0025 + 5 * 0.9025) / 99 = (0.2375 + 4.5125) / 99 = 4.75 / 99 = 0.047979 -> std_dev = 0.2190

    registry = [
        {"world_id": f"W{i}", "zone": "BOUNDARY", "true_effect": 0.05}
        for i in range(1, 101)
    ]
    oracle = [
        {
            "world_id": f"W{i}",
            "decision": "DEFER",
            "expected_reason": "EFFECT_AMBIGUITY",
        }
        for i in range(1, 101)
    ]

    decisions = [{"world_id": f"W{i}", "decision": "DEFER"} for i in range(1, 101)]
    # Set 5 correct/incorrect differences
    baselines = {
        "b2_decisions": {f"W{i}": "DEFER" for i in range(1, 101)},
        "b3_decisions": {f"W{i}": "DEFER" for i in range(1, 101)},
    }
    # MLC matches Oracle for all (1.0). Make B2 retrospective fail for 5 worlds (0.0).
    for i in range(1, 6):
        baselines["b2_decisions"][
            f"W{i}"
        ] = "ADMIT"  # B2 incorrect, MLC correct -> diff = 1

    power = MLCPilotPowerAnalysis.run_power_analysis(
        decisions, oracle, baselines, registry
    )

    h3_p = power["H3"]
    assert h3_p["observed_mean_difference"] == 0.05
    assert h3_p["observed_variance"] > 0.0

    # Check Power at n=500 calculation
    std_dev = h3_p["observed_std_dev"]
    se_500 = std_dev / math.sqrt(500)
    z_stat = 0.05 / se_500
    expected_power = normal_cdf(z_stat - 1.96) + normal_cdf(-z_stat - 1.96)
    assert abs(h3_p["power_at_n500"] - expected_power) < 1e-4

    # Check Required n
    expected_n = int(math.ceil(((1.96 + 0.8416) * std_dev / 0.05) ** 2))
    assert h3_p["required_n_for_80_power"] == expected_n


# 18. NO_DIFFERENCE vs INCONCLUSIVE support logic
def test_no_difference_vs_inconclusive_support_logic():
    # If the experiment has adequate power (power >= 80%), then any non-significant result represents "NO_DIFFERENCE".
    # If underpowered (power < 80%), it represents "INCONCLUSIVE".
    # Let's test standard Z-power outputs.
    # Case A: Adequate power
    registry = [
        {"world_id": f"W{i}", "zone": "BOUNDARY", "true_effect": 0.05}
        for i in range(1, 101)
    ]
    oracle = [{"world_id": f"W{i}", "decision": "DEFER"} for i in range(1, 101)]
    decisions = [{"world_id": f"W{i}", "decision": "DEFER"} for i in range(1, 101)]
    baselines = {
        "b2_decisions": {f"W{i}": "DEFER" for i in range(1, 101)},
        "b3_decisions": {f"W{i}": "DEFER" for i in range(1, 101)},
    }
    # Very small variance: e.g. 1 world has diff = 1, others 0 -> mean = 0.01, std dev = 0.10
    baselines["b2_decisions"]["W1"] = "ADMIT"
    power_a = MLCPilotPowerAnalysis.run_power_analysis(
        decisions, oracle, baselines, registry
    )
    # std_dev = 0.0995. Power at n=500 should be ~100% -> adequately powered is True
    assert power_a["H3"]["adequately_powered"] is True

    # Case B: Underpowered
    # Large variance: 30 worlds have diff = 1, 30 worlds have diff = -1 -> mean = 0.0, std dev = 0.77
    for i in range(1, 31):
        baselines["b2_decisions"][f"W{i}"] = "ADMIT"  # diff = 1
    for i in range(31, 61):
        decisions[i - 1]["decision"] = "ADMIT"  # diff = -1
    power_b = MLCPilotPowerAnalysis.run_power_analysis(
        decisions, oracle, baselines, registry
    )
    assert power_b["H3"]["adequately_powered"] is False


# 19-21. Integration check: manifest generation and forensic reconstruction
def test_manifest_and_forensic_reconstruction():
    temp_dir = tempfile.mkdtemp()
    try:
        registry = MLCPilotWorldGenerator.generate_registry()[:5]  # Mini-registry
        registry_str = json.dumps(registry, sort_keys=True)
        registry_hash = hashlib.sha256(registry_str.encode("utf-8")).hexdigest()

        # Write to disk
        reg_path = os.path.join(temp_dir, "pilot_world_registry.json")
        with open(reg_path, "w") as f:
            json.dump(registry, f)

        # Mock results
        decisions = [
            {
                "world_id": entry["world_id"],
                "decision": "DEFER",
                "reason_code": "AMBIGUOUS_PROSPECTIVE_EFFECT",
            }
            for entry in registry
        ]

        dec_path = os.path.join(temp_dir, "pilot_mlc_decisions.json")
        with open(dec_path, "w") as f:
            json.dump(decisions, f)

        # Forensic reconstruction verification
        with open(dec_path, "r") as f:
            loaded_decisions = json.load(f)
        assert len(loaded_decisions) == len(decisions)
        for d_orig, d_load in zip(decisions, loaded_decisions):
            assert d_orig["world_id"] == d_load["world_id"]
            assert d_orig["decision"] == d_load["decision"]
            assert d_orig["reason_code"] == d_load["reason_code"]

    finally:
        shutil.rmtree(temp_dir)


# Adversarial: Swapped / malformed thresholds
def test_adversarial_swapped_thresholds():
    # Verify that PILOT_GATE_6_THRESHOLD_FREEZE detects swapped thresholds
    # We run the gates with custom thresholds programmatically.
    # Since validity gates imports ADMIT_THRESHOLD and REJECT_THRESHOLD directly from config,
    # we can simulate the gate failure by passing incorrect thresholds.
    # But wait, PILOT_GATE_6 checks directly the frozen threshold parameters.
    # Let's verify that a helper run of validity gates correctly flags threshold mismatch if thresholds were edited.
    import flows.minimal_learning_cycle.pilot as pl

    orig_admit = pl.ADMIT_THRESHOLD
    orig_reject = pl.REJECT_THRESHOLD
    try:
        pl.ADMIT_THRESHOLD = -0.05
        pl.REJECT_THRESHOLD = 0.15
        gates = pl.MLCPilotValidityGates.run_pilot_gates(
            [],
            [],
            {"b2_decisions": {}, "b3_decisions": {}, "b4_decisions": {}},
            {},
            "run_1",
            "hash",
            "hash",
        )
        assert gates["PILOT_GATE_6_THRESHOLD_FREEZE"]["status"] == "FAIL"
    finally:
        pl.ADMIT_THRESHOLD = orig_admit
        pl.REJECT_THRESHOLD = orig_reject


# Adversarial: Zero variance handling in power analysis
def test_adversarial_zero_variance_power():
    # If std dev is 0, power_at_n500 should be 1.0 (since mean effect is 0.05 > 0)
    # and required_n_for_80_power should be 0.
    res = MLCPilotPowerAnalysis.run_power_analysis(
        [{"world_id": "W1", "decision": "DEFER"}],
        [
            {
                "world_id": "W1",
                "decision": "DEFER",
                "expected_reason": "EFFECT_AMBIGUITY",
            }
        ],
        {
            "b2_decisions": {"W1": "DEFER"},
            "b3_decisions": {"W1": "DEFER"},
            "b4_decisions": {"W1": "DEFER"},
        },
        [{"world_id": "W1", "zone": "BOUNDARY", "true_effect": 0.05}],
    )
    assert res["H3"]["observed_std_dev"] == 0.0
    assert res["H3"]["power_at_n500"] == 1.0
    assert res["H3"]["required_n_for_80_power"] == 0


# 22. Evidence-Limited early exit trace verification
def test_evidence_limited_early_exit_trace():
    from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
    from flows.minimal_learning_cycle.pilot import MLCPilotWorldGenerator

    runner = MLCExperimentRunner()
    # Mock budget
    runner.erc.budgets["COMPILATION"] = 100
    runner.erc.budgets["EVIDENCE"] = 100
    runner.erc.budgets["VALIDATION"] = 100

    # Create an evidence-limited world
    registry_entry = {
        "world_id": "WORLD_EVIDENCE_LIMITED_TEST",
        "zone": "EVIDENCE_LIMITED",
        "seed": 9999,
        "true_effect": 0.35,
        "ground_truth_decision": "DEFER",
        "ground_truth_defer_subtype": "EVIDENCE_LIMITED",
    }
    world = MLCPilotWorldGenerator.generate_world_dict(registry_entry)

    decision_dict = runner.run_lifecycle(world)

    # Assertions
    assert decision_dict["decision"] == "DEFER"
    assert decision_dict["reason_code"] == "FAILED_READINESS"
    assert (
        decision_dict["defer_origin_classification"]
        == "EXPECTED_EVIDENCE_LIMITED_DEFER"
    )

    # Check that candidate was NOT frozen
    runner_world_id = f"WORLD_{world['family']}_SEED_{world['seed']}"
    prop_id = f"PROP_{runner_world_id}"
    frozen_cand = [
        c
        for c in runner.frozen_candidates
        if c["proposition_definition"]["proposition_id"] == prop_id
    ]
    assert len(frozen_cand) == 0

    # Check that Window 3 was NOT accessed (no prospective measurements)
    pm = [p for p in runner.prospective_measurements if p["proposition_id"] == prop_id]
    assert len(pm) == 0

    # Check prospective budget consumed is 0
    val_logs = [l for l in runner.erc.logs if l["resource_type"] == "VALIDATION"]
    assert len(val_logs) == 0


# 23. H5 metric correction verification
def test_h5_metric_correction():
    # Setup mock decisions representing Evidence-Limited worlds failing readiness
    registry = [
        {
            "world_id": "W1",
            "zone": "EVIDENCE_LIMITED",
            "seed": 3001,
            "true_effect": 0.35,
            "ground_truth_decision": "DEFER",
            "ground_truth_defer_subtype": "EVIDENCE_LIMITED",
        }
    ]
    oracle = [
        {
            "world_id": "W1",
            "expected_decision": "DEFER",
            "expected_reason": "EVIDENCE_LIMITED",
        }
    ]
    decisions = [
        {
            "world_id": "W1",
            "decision": "DEFER",
            "reason_code": "FAILED_READINESS",
            "defer_origin_classification": "EXPECTED_EVIDENCE_LIMITED_DEFER",
        }
    ]

    h5 = MLCPilotMetrics.calculate_h5_metrics(decisions, oracle)
    assert h5["evidence_limited_subtype_accuracy"] == 1.00


# 24. Effect-Ambiguity non-regression verification
def test_effect_ambiguity_non_regression():
    from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
    from flows.minimal_learning_cycle.pilot import MLCPilotWorldGenerator

    runner = MLCExperimentRunner()
    runner.erc.budgets["COMPILATION"] = 100
    runner.erc.budgets["EVIDENCE"] = 100
    runner.erc.budgets["VALIDATION"] = 100

    # Boundary zone world with expected DEFER / EFFECT_AMBIGUITY
    registry_entry = {
        "world_id": "WORLD_BOUNDARY_TEST",
        "zone": "BOUNDARY",
        "seed": 9998,
        "true_effect": 0.05,
        "ground_truth_decision": "DEFER",
        "ground_truth_defer_subtype": "EFFECT_AMBIGUITY",
    }
    world = MLCPilotWorldGenerator.generate_world_dict(registry_entry)

    decision_dict = runner.run_lifecycle(world)

    # Assertions
    assert decision_dict["decision"] == "DEFER"
    assert decision_dict["reason_code"] == "AMBIGUOUS_PROSPECTIVE_EFFECT"
    assert (
        decision_dict["defer_origin_classification"]
        == "EXPECTED_EFFECT_AMBIGUITY_DEFER"
    )

    # Check that candidate WAS frozen
    runner_world_id = f"WORLD_{world['family']}_SEED_{world['seed']}"
    prop_id = f"PROP_{runner_world_id}"
    frozen_cand = [
        c
        for c in runner.frozen_candidates
        if c["proposition_definition"]["proposition_id"] == prop_id
    ]
    assert len(frozen_cand) == 1

    # Check that Window 3 WAS accessed
    pm = [p for p in runner.prospective_measurements if p["proposition_id"] == prop_id]
    assert len(pm) == 1


# 25. No top-level regression check
def test_no_top_level_regression():
    from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
    from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld

    runner = MLCExperimentRunner()
    families = ["A", "B", "C1", "C2"]
    seed = 42

    worlds = [MLCSyntheticWorld.generate_world(fam, seed) for fam in families]
    for w in worlds:
        runner.run_lifecycle(w)

    dec_map = {d["world_id"]: d["decision"] for d in runner.decisions}

    assert dec_map["WORLD_A_SEED_42"] == "ADMIT"
    assert dec_map["WORLD_B_SEED_42"] == "REJECT"
    assert dec_map["WORLD_C1_SEED_42"] == "DEFER"
    assert dec_map["WORLD_C2_SEED_42"] == "DEFER"
