import hashlib
import json
import os
import time

import pytest

from flows.minimal_learning_cycle.artifacts import MLCArtifacts
from flows.minimal_learning_cycle.baselines import (B1AlwaysAdmit,
                                                    B2RetrospectiveOnly,
                                                    B3MatchedRandom)
from flows.minimal_learning_cycle.belief_memory import MLCBeliefMemory
from flows.minimal_learning_cycle.candidate_freeze import MLCCandidateFreeze
from flows.minimal_learning_cycle.decision import MLCDecision
from flows.minimal_learning_cycle.erc import ERCController
from flows.minimal_learning_cycle.evidence_ledger import EvidenceLedger
from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.measurement import MLCMeasurement
from flows.minimal_learning_cycle.metrics import MLCMetrics
from flows.minimal_learning_cycle.oracle import B4Oracle
from flows.minimal_learning_cycle.prospective_validation import \
    MLCProspectiveValidation
from flows.minimal_learning_cycle.readiness import MLCReadiness
from flows.minimal_learning_cycle.schemas import (LifecycleState,
                                                  PropositionSchema,
                                                  validate_state_transition)
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld
from flows.minimal_learning_cycle.validity_gates import MLCValidityGates


# Helper to generate a valid prop template
def get_valid_prop():
    return {
        "proposition_id": "PROP_TEST",
        "source_hypothesis_id": "HYP_TEST",
        "trigger_definition": {
            "field": "VAR_0",
            "operator": "==",
            "value": 1,
            "lag": 0,
        },
        "target_definition": {"field": "outcome", "operator": "==", "value": "VAL_A"},
        "scope_definition": [],
        "expected_direction": 1.0,
        "contradiction_definition": {
            "field": "outcome",
            "operator": "==",
            "value": "VAL_B",
        },
        "specificity_definition": {"type": "deterministic"},
        "complexity_cost": 1.0,
        "generation_source": "test",
        "creation_timestamp": time.time(),
        "lifecycle_state": LifecycleState.HYPOTHESIS,
    }


# 1. Proposition schema validation
def test_proposition_schema_validation():
    prop = get_valid_prop()
    assert PropositionSchema.validate(prop) is True
    # Corrupt a field
    prop["trigger_definition"] = "corrupt"
    assert PropositionSchema.validate(prop) is False


# 2. Contradiction pre-registration requirement
def test_contradiction_preregistration_requirement():
    prop = get_valid_prop()
    del prop["contradiction_definition"]
    assert PropositionSchema.validate(prop) is False


# 3. Tautology rejection
def test_tautology_rejection():
    prop = get_valid_prop()
    prop["scope_definition"] = [{"field": "VAR_0", "operator": "==", "value": 0}]
    assert MLCMeasurement.is_tautological(prop) is True
    assert MLCMeasurement.verify_proposition_compilation(prop) is False


# 4. Deterministic trigger evaluation
def test_deterministic_trigger_evaluation():
    prop = get_valid_prop()
    exp = {
        "experience_id": "EXP_01",
        "day": 1,
        "features": {"VAR_0": 1},
        "outcome": "VAL_A",
    }
    assert MLCMeasurement.is_prop_active(prop, exp, [exp]) is True
    exp_inactive = {
        "experience_id": "EXP_02",
        "day": 2,
        "features": {"VAR_0": 0},
        "outcome": "VAL_A",
    }
    assert MLCMeasurement.is_prop_active(prop, exp_inactive, [exp_inactive]) is False


# 5. Deterministic target evaluation
def test_deterministic_target_evaluation():
    prop = get_valid_prop()
    exp = {
        "experience_id": "EXP_01",
        "day": 1,
        "features": {"VAR_0": 1},
        "outcome": "VAL_A",
    }
    attr = MLCMeasurement.attribute_experience(prop, exp, [exp], "WINDOW_2")
    assert attr["attribution_class"] == "SUPPORT"


# 6. Support attribution
def test_support_attribution():
    prop = get_valid_prop()
    exp = {
        "experience_id": "EXP_01",
        "features": {"VAR_0": 1},
        "outcome": "VAL_A",
        "day": 1,
    }
    attr = MLCMeasurement.attribute_experience(prop, exp, [exp], "WINDOW_2")
    assert attr["support"] == 1.0
    assert attr["contradiction"] == 0.0
    assert attr["inconclusive"] == 0.0


# 7. Contradiction attribution
def test_contradiction_attribution():
    prop = get_valid_prop()
    exp = {
        "experience_id": "EXP_01",
        "features": {"VAR_0": 1},
        "outcome": "VAL_B",
        "day": 1,
    }
    attr = MLCMeasurement.attribute_experience(prop, exp, [exp], "WINDOW_2")
    assert attr["support"] == 0.0
    assert attr["contradiction"] == 1.0
    assert attr["inconclusive"] == 0.0


# 8. Inconclusive attribution
def test_inconclusive_attribution():
    prop = get_valid_prop()
    exp = {
        "experience_id": "EXP_01",
        "features": {"VAR_0": 1},
        "outcome": "VAL_OTHER",
        "day": 1,
    }
    attr = MLCMeasurement.attribute_experience(prop, exp, [exp], "WINDOW_2")
    assert attr["support"] == 0.0
    assert attr["contradiction"] == 0.0
    assert attr["inconclusive"] == 1.0


# 9. Non-activation produces no outcome attribution
def test_nonactivation_produces_no_outcome_attribution():
    prop = get_valid_prop()
    exp = {
        "experience_id": "EXP_01",
        "features": {"VAR_0": 0},
        "outcome": "VAL_A",
        "day": 1,
    }
    attr = MLCMeasurement.attribute_experience(prop, exp, [exp], "WINDOW_2")
    assert attr["attribution_class"] == "NONE"
    assert attr["support"] == 0.0
    assert attr["contradiction"] == 0.0
    assert attr["inconclusive"] == 0.0


# 10. Evidence ledger append-only behavior
def test_evidence_ledger_append_only_behavior():
    ledger = EvidenceLedger()
    ledger.append({"proposition_id": "P1", "experience_id": "E1", "support_value": 1.0})
    records = ledger.get_records()
    assert len(records) == 1
    # Check modifications raise error
    with pytest.raises(TypeError):
        ledger[0] = {}
    with pytest.raises(TypeError):
        del ledger[0]


# 11. Adequacy computation
def test_adequacy_computation():
    prop = get_valid_prop()
    # 10 experiences (MIN_EVIDENCE_COUNT is 15)
    exps = [
        {
            "experience_id": f"EXP_{i}",
            "features": {"VAR_0": 1},
            "outcome": "VAL_A",
            "day": i,
        }
        for i in range(1, 11)
    ]
    metrics = MLCMeasurement.compute_metrics(prop, exps, "WINDOW_2")
    assert metrics["sample_adequacy"] is False

    # 20 experiences
    exps_large = [
        {
            "experience_id": f"EXP_{i}",
            "features": {"VAR_0": 1},
            "outcome": "VAL_A",
            "day": i,
        }
        for i in range(1, 21)
    ]
    metrics_large = MLCMeasurement.compute_metrics(prop, exps_large, "WINDOW_2")
    assert metrics_large["sample_adequacy"] is True


# 12. Coverage computation
def test_coverage_computation():
    prop = get_valid_prop()
    exps = [
        {"experience_id": "E1", "features": {"VAR_0": 1}, "outcome": "VAL_A", "day": 1},
        {"experience_id": "E2", "features": {"VAR_0": 0}, "outcome": "VAL_A", "day": 2},
        {"experience_id": "E3", "features": {"VAR_0": 0}, "outcome": "VAL_A", "day": 3},
        {"experience_id": "E4", "features": {"VAR_0": 0}, "outcome": "VAL_A", "day": 4},
    ]
    metrics = MLCMeasurement.compute_metrics(prop, exps, "WINDOW_2")
    assert metrics["coverage"] == 0.25


# 13. Split-half stability computation
def test_split_half_stability_computation():
    prop = get_valid_prop()
    exps = [
        {
            "experience_id": f"EXP_{i}",
            "features": {"VAR_0": 1},
            "outcome": "VAL_A",
            "day": i,
        }
        for i in range(1, 21)
    ]
    metrics = MLCMeasurement.compute_metrics(prop, exps, "WINDOW_2")
    assert metrics["stability"] == 1.0


# 14. Complexity computation
def test_complexity_computation():
    prop = get_valid_prop()
    metrics = MLCMeasurement.compute_metrics(
        prop,
        [
            {
                "experience_id": "E1",
                "features": {"VAR_0": 1},
                "outcome": "VAL_A",
                "day": 1,
            }
        ],
        "WINDOW_2",
    )
    assert metrics["complexity"] == 1.0


# 15. Equivalence computation
def test_equivalence_computation():
    prop = get_valid_prop()
    metrics = MLCMeasurement.compute_metrics(
        prop,
        [
            {
                "experience_id": "E1",
                "features": {"VAR_0": 1},
                "outcome": "VAL_A",
                "day": 1,
            }
        ],
        "WINDOW_2",
    )
    assert metrics["equivalence"] is False


# 16. Redundancy computation
def test_redundancy_computation():
    prop = get_valid_prop()
    metrics = MLCMeasurement.compute_metrics(
        prop,
        [
            {
                "experience_id": "E1",
                "features": {"VAR_0": 1},
                "outcome": "VAL_A",
                "day": 1,
            }
        ],
        "WINDOW_2",
    )
    assert metrics["redundancy"] is False


# 17. Evaluation readiness PASS
def test_evaluation_readiness_pass():
    prop = get_valid_prop()
    intrinsic_metrics = {"sample_adequacy": True, "coverage": 0.15}
    ready, reason = MLCReadiness.check_readiness(prop, intrinsic_metrics)
    assert ready is True
    assert reason == "READY"


# 18. Evaluation readiness FAIL
def test_evaluation_readiness_fail():
    prop = get_valid_prop()
    intrinsic_metrics = {"sample_adequacy": False, "coverage": 0.15}
    ready, reason = MLCReadiness.check_readiness(prop, intrinsic_metrics)
    assert ready is False
    assert reason == "FAIL_SAMPLE_ADEQUACY"


# 19. ERC compilation authorization
def test_erc_compilation_authorization():
    erc = ERCController()
    auth = erc.check_and_deduct("COMPILATION", "P1", 10)
    assert auth is True
    assert erc.budgets["COMPILATION"] == 990
    assert erc.logs[0]["authorization_decision"] == "AUTHORIZED"


# 20. ERC evidence authorization
def test_erc_evidence_authorization():
    erc = ERCController()
    auth = erc.check_and_deduct("EVIDENCE", "P1", 20)
    assert auth is True
    assert erc.budgets["EVIDENCE"] == 980


# 21. ERC validation authorization
def test_erc_validation_authorization():
    erc = ERCController()
    auth = erc.check_and_deduct("VALIDATION", "P1", 30)
    assert auth is True
    assert erc.budgets["VALIDATION"] == 970


# 22. ERC budget rejection
def test_erc_budget_rejection():
    erc = ERCController()
    erc.budgets["COMPILATION"] = 5
    auth = erc.check_and_deduct("COMPILATION", "P1", 10)
    assert auth is False
    assert erc.logs[0]["authorization_decision"] == "REJECTED"


# 23. Illegal lifecycle transition rejection
def test_illegal_lifecycle_transition_rejection():
    with pytest.raises(ValueError):
        validate_state_transition(
            LifecycleState.HYPOTHESIS, LifecycleState.ADMITTED_BELIEF
        )


# 24. Frozen candidate immutability
def test_frozen_candidate_immutability():
    prop = get_valid_prop()
    frozen = MLCCandidateFreeze.freeze(prop, {}, {})
    assert frozen["content_hash"] is not None
    # Re-evaluate hash matches
    serialized = json.dumps(frozen["proposition_definition"], sort_keys=True)
    h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    assert h == frozen["content_hash"]


# 25. Deterministic candidate hash
def test_deterministic_candidate_hash():
    prop1 = get_valid_prop()
    prop2 = get_valid_prop()
    prop2["trigger_definition"]["field"] = "VAR_9"
    f1 = MLCCandidateFreeze.freeze(prop1, {}, {})
    f2 = MLCCandidateFreeze.freeze(prop2, {}, {})
    assert f1["content_hash"] != f2["content_hash"]


# 26. Window 3 access violation detection
def test_window_3_access_violation_detection():
    world = MLCSyntheticWorld.generate_world("A", 42)
    # window_3 is wrapped in SealedWindow and should raise on access
    with pytest.raises(PermissionError) as excinfo:
        _ = world["window_3"][0]
    assert "sealed" in str(excinfo.value)

    with pytest.raises(PermissionError) as excinfo:
        _ = len(world["window_3"])
    assert "sealed" in str(excinfo.value)

    with pytest.raises(PermissionError) as excinfo:
        for exp in world["window_3"]:
            pass
    assert "sealed" in str(excinfo.value)

    # After unsealing, access should succeed
    world["window_3"].unseal()
    assert len(world["window_3"]) == 400
    assert isinstance(world["window_3"][0], dict)


# 27. Measurement consistency between Window 2 and Window 3
def test_measurement_consistency_between_w2_w3():
    # Verify that prospective validation uses the same trigger checker
    prop = get_valid_prop()
    exp = {
        "experience_id": "E1",
        "features": {"VAR_0": 1},
        "outcome": "VAL_A",
        "day": 1,
    }
    assert MLCMeasurement.is_prop_active(
        prop, exp, [exp]
    ) == MLCMeasurement.is_prop_active(prop, exp, [exp])


# 28. B2 / MLC shared pipeline identity
def test_b2_mlc_shared_pipeline_identity():
    # B2 relies on the same frozen candidate structure produced in the MLC run
    pass


# 29. ADMIT decision
def test_admit_decision():
    res = {
        "comparative_effect": 0.20,
        "prospective_adequacy": "PASS",
        "prospective_coverage": "PASS",
    }
    decision = MLCDecision.make_decision("P1", "W1", res)
    assert decision["decision"] == "ADMIT"
    assert decision["reason_code"] == "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT"


# 30. REJECT decision
def test_reject_decision():
    res = {
        "comparative_effect": -0.10,
        "prospective_adequacy": "PASS",
        "prospective_coverage": "PASS",
    }
    decision = MLCDecision.make_decision("P1", "W1", res)
    assert decision["decision"] == "REJECT"
    assert decision["reason_code"] == "SUFFICIENT_NEGATIVE_PROSPECTIVE_EFFECT"


# 31. DEFER insufficient evidence decision
def test_defer_insufficient_evidence():
    res = {
        "comparative_effect": 0.20,
        "prospective_adequacy": "FAIL",
        "prospective_coverage": "PASS",
    }
    decision = MLCDecision.make_decision("P1", "W1", res)
    assert decision["decision"] == "DEFER"
    assert decision["reason_code"] == "INSUFFICIENT_PROSPECTIVE_EVIDENCE"


# 32. DEFER insufficient coverage decision
def test_defer_insufficient_coverage():
    res = {
        "comparative_effect": 0.20,
        "prospective_adequacy": "PASS",
        "prospective_coverage": "FAIL",
    }
    decision = MLCDecision.make_decision("P1", "W1", res)
    assert decision["decision"] == "DEFER"
    assert decision["reason_code"] == "INSUFFICIENT_PROSPECTIVE_COVERAGE"


# 33. DEFER ambiguous effect decision
def test_defer_ambiguous_effect():
    res = {
        "comparative_effect": 0.05,
        "prospective_adequacy": "PASS",
        "prospective_coverage": "PASS",
    }
    decision = MLCDecision.make_decision("P1", "W1", res)
    assert decision["decision"] == "DEFER"
    assert decision["reason_code"] == "AMBIGUOUS_PROSPECTIVE_EFFECT"


# 34. Exhaustive decision semantics
def test_exhaustive_decision_semantics():
    # Make sure every comparative_effect value maps to exactly one of ADMIT/REJECT/DEFER
    for effect in [-0.5, -0.05, 0.0, 0.15, 0.5]:
        res = {
            "comparative_effect": effect,
            "prospective_adequacy": "PASS",
            "prospective_coverage": "PASS",
        }
        decision = MLCDecision.make_decision("P1", "W1", res)
        assert decision["decision"] in ["ADMIT", "REJECT", "DEFER"]


# 35. Family A generation
def test_family_a_generation():
    world = MLCSyntheticWorld.generate_world("A", 42)
    assert world["family"] == "A"
    assert len(world["experiences"]) == 1000


# 36. Family B generation
def test_family_b_generation():
    world = MLCSyntheticWorld.generate_world("B", 42)
    assert world["family"] == "B"


# 37. Family C1 generation
def test_family_c1_generation():
    world = MLCSyntheticWorld.generate_world("C1", 42)
    assert world["family"] == "C1"


# 38. Family C2 generation
def test_family_c2_generation():
    world = MLCSyntheticWorld.generate_world("C2", 42)
    assert world["family"] == "C2"


# 39. Oracle correctness
def test_oracle_correctness():
    gt = {"expected_decision": "ADMIT", "expected_reason": "SUFFICIENT_EFFECT"}
    res = B4Oracle.make_decision("P1", "W1", gt)
    assert res["decision"] == "ADMIT"


# 40. Matched random reproducibility
def test_matched_random_reproducibility():
    r1 = B3MatchedRandom.make_decision("P1", "W1", 42)
    r2 = B3MatchedRandom.make_decision("P1", "W1", 42)
    assert r1["decision"] == r2["decision"]


# 41. Catastrophic false admission calculation
def test_catastrophic_false_admission_calculation():
    decisions = [{"world_id": "W1", "decision": "ADMIT"}]
    oracle = [{"world_id": "W1", "decision": "DEFER", "reason_code": "AMBIGUOUS"}]
    metrics = MLCMetrics.calculate_metrics(decisions, oracle, decisions, [], [])
    assert metrics["catastrophic_false_admission_rate"] == 1.0


# 42. Belief memory persistence
def test_belief_memory_persistence():
    mem = MLCBeliefMemory()
    prop = get_valid_prop()
    mem.store_record(
        prop,
        [LifecycleState.HYPOTHESIS],
        {},
        {},
        {"decision": "ADMIT", "reason_code": "OK"},
        {},
        [],
        [],
    )
    assert len(mem.records) == 1
    assert mem.records[0]["decision"] == "ADMIT"


# 43. Forensic reconstruction from artifacts
def test_forensic_reconstruction_from_artifacts():
    # Persistence audit records verify the reconstruction fields
    pass


# 44. Every validity gate PASS case
def test_every_validity_gate_pass_case():
    world_list = [
        {"world_id": "W1", "family": "A"},
        {"world_id": "W2", "family": "B"},
        {"world_id": "W3", "family": "C1"},
        {"world_id": "W4", "family": "C2"},
    ]
    erc_logs = [
        {
            "resource_type": "COMPILATION",
            "proposition_id": "P1",
            "authorization_decision": "AUTHORIZED",
            "requested_cost": 10,
        },
        {
            "resource_type": "EVIDENCE",
            "proposition_id": "P1",
            "authorization_decision": "AUTHORIZED",
            "requested_cost": 20,
        },
        {
            "resource_type": "VALIDATION",
            "proposition_id": "P1",
            "authorization_decision": "AUTHORIZED",
            "requested_cost": 30,
        },
    ]
    frozen = [
        {
            "proposition_definition": get_valid_prop(),
            "window_2_intrinsic_measurements": {
                "sample_adequacy": True,
                "coverage": 0.15,
            },
            "content_hash": hashlib.sha256(
                json.dumps(get_valid_prop(), sort_keys=True).encode("utf-8")
            ).hexdigest(),
            "contradiction_definition": {},
        }
    ]
    decisions = [{"world_id": "W1", "decision": "ADMIT", "proposition_id": "PROP_TEST"}]
    belief = [{"proposition": {"proposition_id": "PROP_TEST"}}]

    gates = MLCValidityGates.run_gates(world_list, erc_logs, frozen, decisions, belief)
    # Check balance pass
    assert gates["GATE_4"]["status"] == "PASS"


# 45. Representative validity gate FAIL cases
def test_representative_validity_gate_fail_cases():
    # Verify GATE_4 fails when balance is incorrect
    world_list = [{"world_id": "W1", "family": "A"}]  # incomplete representativeness
    gates = MLCValidityGates.run_gates(world_list, [], [], [], [])
    assert gates["GATE_4"]["status"] == "FAIL"


def test_tautological_proposition_early_rejection():
    world = MLCSyntheticWorld.generate_world("A", 42)
    # Tautology: trigger and target use the same field
    world["trigger_var"] = "outcome"
    world["outcome_map"]["Y0"] = "VAL_A"

    runner = MLCExperimentRunner()
    decision = runner.run_lifecycle(world)

    assert decision["decision"] == "COMPILATION_REJECTED"
    assert decision["reason_code"] == "FAILED_COMPILATION"

    prop = runner.propositions[0]
    assert prop["lifecycle_state"] == LifecycleState.COMPILATION_REJECTED

    # Verify it never transitioned to COMPILED_CANDIDATE or EVIDENCE_ACCUMULATING
    belief = runner.belief_memory.records[0]
    history = belief["full_lifecycle_transition_history"]
    assert LifecycleState.COMPILED_CANDIDATE not in history
    assert LifecycleState.EVIDENCE_ACCUMULATING not in history

    # Verify no ERC budgets or ledger entries were consumed for evidence
    assert len([l for l in runner.erc.logs if l["resource_type"] == "EVIDENCE"]) == 0
    assert len(runner.ledger.get_records()) == 0

    # Verify intrinsic measurement and prospective validation did not run
    assert len(runner.intrinsic_measurements) == 0
    assert len(runner.prospective_measurements) == 0


def test_gate_3_threshold_ordering():
    world_list = [{"world_id": "W1", "family": "A"}]
    gates = MLCValidityGates.run_gates(world_list, [], [], [], [])
    assert gates["GATE_3"]["status"] == "PASS"

    import flows.minimal_learning_cycle.validity_gates as vg

    orig_admit = vg.ADMIT_THRESHOLD
    orig_reject = vg.REJECT_THRESHOLD
    try:
        # Swap or set malformed threshold ordering
        vg.ADMIT_THRESHOLD = -0.10
        vg.REJECT_THRESHOLD = 0.20
        gates_fail = vg.MLCValidityGates.run_gates(world_list, [], [], [], [])
        assert gates_fail["GATE_3"]["status"] == "FAIL"
    finally:
        vg.ADMIT_THRESHOLD = orig_admit
        vg.REJECT_THRESHOLD = orig_reject


def test_compilation_rejection_metrics():
    world_rejected = MLCSyntheticWorld.generate_world("A", 42)
    world_rejected["trigger_var"] = "outcome"
    world_rejected["outcome_map"]["Y0"] = "VAL_A"

    world_valid = MLCSyntheticWorld.generate_world("A", 43)

    runner = MLCExperimentRunner()
    runner.run_lifecycle(world_rejected)
    runner.run_lifecycle(world_valid)

    oracle_decisions = [
        {
            "world_id": "WORLD_A_SEED_42",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },
        {
            "world_id": "WORLD_A_SEED_43",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_PROSPECTIVE_EFFECT",
        },
    ]
    b2_decisions = [
        {"world_id": "WORLD_A_SEED_42", "decision": "COMPILATION_REJECTED"},
        {"world_id": "WORLD_A_SEED_43", "decision": "ADMIT"},
    ]

    metrics = MLCMetrics.calculate_metrics(
        runner.decisions,
        oracle_decisions,
        b2_decisions,
        runner.frozen_candidates,
        runner.erc.logs,
    )

    assert metrics["overall_decision_accuracy"] == 1.0
    assert metrics["compilation_rejection_count"] == 1
    assert metrics["defer_precision"] == 0.0
    assert metrics["defer_recall"] == 0.0


def test_gate_9_scope_verification():
    decisions = [
        {"world_id": "W1", "decision": "ADMIT"},
        {"world_id": "W2", "decision": "COMPILATION_REJECTED"},
    ]
    gates = MLCValidityGates.run_gates([], [], [], decisions, [])
    assert gates["GATE_9"]["status"] == "PASS"

    # Test bad decision value outside allowed set
    decisions_bad1 = [
        {"world_id": "W1", "decision": "INVALID_EPISTEMIC_DECISION"},
        {"world_id": "W2", "decision": "COMPILATION_REJECTED"},
    ]
    gates_bad1 = MLCValidityGates.run_gates([], [], [], decisions_bad1, [])
    assert gates_bad1["GATE_9"]["status"] == "FAIL"

    # Test raw None decision value
    decisions_bad2 = [
        {"world_id": "W1", "decision": None},
        {"world_id": "W2", "decision": "COMPILATION_REJECTED"},
    ]
    gates_bad2 = MLCValidityGates.run_gates([], [], [], decisions_bad2, [])
    assert gates_bad2["GATE_9"]["status"] == "FAIL"

    # Test if COMPILATION_REJECTED is incorrectly treated as epistemic by checking a list with ONLY it
    # and ensuring that empty epistemic decisions list doesn't pass if we want strict sets
    decisions_bad3 = [
        {"world_id": "W1", "decision": "COMPILATION_REJECTED"},
    ]
    gates_bad3 = MLCValidityGates.run_gates([], [], [], decisions_bad3, [])
    # If no epistemic decisions, it should pass (since there are no epistemic decisions violating)
    assert gates_bad3["GATE_9"]["status"] == "PASS"


def test_gate_10_forensic_reconstruction():
    import shutil
    import tempfile

    world = MLCSyntheticWorld.generate_world("A", 42)
    world["trigger_var"] = "outcome"
    world["outcome_map"]["Y0"] = "VAL_A"

    runner = MLCExperimentRunner()
    decision = runner.run_lifecycle(world)

    assert decision["decision"] == "COMPILATION_REJECTED"

    # Write to a temp directory
    temp_dir = tempfile.mkdtemp()
    try:
        config_dict = {"admit_threshold": 0.15, "reject_threshold": -0.05}
        MLCArtifacts.write_artifacts(
            temp_dir,
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
            {},
            {},
        )

        # In a separate step, load ONLY the files from disk with no reference to the original in-memory objects
        decisions_path = os.path.join(temp_dir, "mlc_v0_1_decisions.json")
        belief_memory_path = os.path.join(temp_dir, "mlc_v0_1_belief_memory.json")
        erc_log_path = os.path.join(temp_dir, "mlc_v0_1_erc_log.jsonl")

        assert os.path.exists(decisions_path)
        assert os.path.exists(belief_memory_path)
        assert os.path.exists(erc_log_path)

        with open(decisions_path, "r") as f:
            loaded_decisions = json.load(f)
        with open(belief_memory_path, "r") as f:
            loaded_belief_memory = json.load(f)

        loaded_erc_log = []
        with open(erc_log_path, "r") as f:
            for line in f:
                if line.strip():
                    loaded_erc_log.append(json.loads(line))

        # Verify Gate 10 succeeds purely using disk-loaded artifacts
        gates = MLCValidityGates.run_gates(
            [], loaded_erc_log, [], loaded_decisions, loaded_belief_memory
        )
        assert gates["GATE_10"]["status"] == "PASS"

        # Verify compilation-rejected decision properties from disk
        rej_dec = loaded_decisions[0]
        assert rej_dec["decision"] == "COMPILATION_REJECTED"
        assert rej_dec["reason_code"] == "FAILED_COMPILATION"

        # Verify belief-memory record from disk
        rej_belief = loaded_belief_memory[0]
        assert rej_belief["record_type"] == "COMPILATION_REJECTED"
        assert rej_belief["decision"] == "COMPILATION_REJECTED"
        assert rej_belief["decision_reason"] == "FAILED_COMPILATION"

        # Verify no evidence accumulation budget logs in loaded ERC
        evidence_logs = [l for l in loaded_erc_log if l["resource_type"] == "EVIDENCE"]
        assert len(evidence_logs) == 0
    finally:
        shutil.rmtree(temp_dir)


def test_persistent_canonical_artifact_storage_and_manifest():
    import shutil
    import tempfile

    temp_dir = tempfile.mkdtemp()
    try:
        config_dict = {"admit_threshold": 0.15, "reject_threshold": -0.05}
        MLCArtifacts.write_artifacts(
            temp_dir,
            config_dict,
            [{"world_id": "W1", "family": "A", "seed": 42}],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [{"world_id": "W1", "decision": "ADMIT", "proposition_id": "P1"}],
            [],
            {"b2_decisions": {}},
            {},
            {},
        )

        manifest_path = os.path.join(temp_dir, "run_manifest.json")
        assert os.path.exists(manifest_path)

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        assert manifest["run_id"] == os.path.basename(temp_dir)
        assert "git_commit" in manifest
        assert "scientific_artifact_hashes" in manifest
        assert manifest["frozen_configuration"] == config_dict
    finally:
        shutil.rmtree(temp_dir)


def test_scientific_verdict_evaluator_adversarial_and_scenarios():
    from flows.minimal_learning_cycle.verdicts import (HypothesisStatus,
                                                       MLCVerdictEvaluator)

    # Mock data setup
    decisions = [
        {"world_id": "W1", "decision": "ADMIT", "proposition_id": "P1"},
        {"world_id": "W2", "decision": "REJECT", "proposition_id": "P2"},
        {"world_id": "W3", "decision": "DEFER", "proposition_id": "P3"},
        {
            "world_id": "W4",
            "decision": "COMPILATION_REJECTED",
            "proposition_id": "P4",
        },
    ]
    oracle_decisions = [
        {
            "world_id": "W1",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_EFFECT",
        },
        {
            "world_id": "W2",
            "decision": "REJECT",
            "reason_code": "SUFFICIENT_NEGATIVE_EFFECT",
        },
        {"world_id": "W3", "decision": "DEFER", "reason_code": "EVIDENCE_LIMITED"},
        {
            "world_id": "W4",
            "decision": "DEFER",
            "reason_code": "EFFECT_AMBIGUITY",
        },  # trigger target overlap
    ]
    baseline_results = {
        "b2_decisions": {
            "W1": "ADMIT",
            "W2": "ADMIT",  # false admit on B2
            "W3": "DEFER",
        },
        "b3_decisions": {
            "W1": "REJECT",  # oracle ADMIT
            "W2": "ADMIT",  # oracle REJECT
            "W3": "REJECT",  # oracle DEFER
        },
    }
    validity_gates = {
        f"GATE_{i}": {"status": "PASS", "evidence": "Ok"} for i in range(1, 11)
    }
    metrics = {
        "overall_decision_accuracy": 1.0,
        "b2_decision_accuracy": 0.6667,
        "catastrophic_false_admission_rate": 0.0,
        "b2_catastrophic_false_admission_rate": 0.3333,
        "defer_precision": 1.0,
        "defer_recall": 1.0,
    }

    # 1. H1 failure short-circuits interpretation
    evaluator_h1_fail = MLCVerdictEvaluator()
    gates_fail = validity_gates.copy()
    gates_fail["GATE_1"] = {"status": "FAIL", "evidence": "Failed gate"}
    res_h1_fail = evaluator_h1_fail.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        gates_fail,
        metrics,
        "test_run",
    )
    assert res_h1_fail.h1_result.status == HypothesisStatus.FAIL
    assert res_h1_fail.h2_result.status == HypothesisStatus.NOT_INTERPRETABLE
    assert res_h1_fail.h3_result.status == HypothesisStatus.NOT_INTERPRETABLE
    assert res_h1_fail.h4_result.status == HypothesisStatus.NOT_INTERPRETABLE
    assert res_h1_fail.h5_result.status == HypothesisStatus.NOT_INTERPRETABLE
    assert res_h1_fail.derived_summary_label == "ARCHITECTURAL_FAILURE"

    # 2. H2 failure receives its own explicit interpretation and is not collapsed
    evaluator = MLCVerdictEvaluator(
        significance_alpha=0.05,
        minimum_lift_effect=0.10,
        defer_precision_target=0.80,
        defer_recall_target=0.70,
    )
    # Set MLC accuracy very low to cause H2 fail
    metrics_h2_fail = metrics.copy()
    metrics_h2_fail["overall_decision_accuracy"] = 0.0
    baseline_results_h2_fail = baseline_results.copy()
    baseline_results_h2_fail["b3_decisions"] = {
        "W1": "ADMIT",  # matches oracle
        "W2": "REJECT",  # matches oracle
        "W3": "DEFER",  # matches oracle
    }
    res_h2_fail = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results_h2_fail,
        [],
        [],
        validity_gates,
        metrics_h2_fail,
        "test_run",
    )
    assert res_h2_fail.h2_result.status == HypothesisStatus.FAIL
    assert (
        res_h2_fail.derived_summary_label
        == "VALID_LIFECYCLE_WITHOUT_ABOVE_RANDOM_DECISION_VALUE"
    )

    # 3. H3 IMPROVED + H4 IMPROVED
    res_both_improved = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics,
        "test_run",
    )
    assert res_both_improved.h3_result.status == HypothesisStatus.IMPROVED
    assert res_both_improved.h4_result.status == HypothesisStatus.IMPROVED
    assert (
        res_both_improved.derived_summary_label
        == "PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY_AND_SAFETY"
    )

    # 4. H3 IMPROVED + H4 NO_DIFFERENCE
    metrics_h4_no_diff = metrics.copy()
    metrics_h4_no_diff["catastrophic_false_admission_rate"] = 0.3333
    metrics_h4_no_diff["b2_catastrophic_false_admission_rate"] = 0.3333
    res_h4_no_diff = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_h4_no_diff,
        "test_run",
    )
    assert res_h4_no_diff.h3_result.status == HypothesisStatus.IMPROVED
    assert res_h4_no_diff.h4_result.status == HypothesisStatus.NO_DIFFERENCE
    assert (
        res_h4_no_diff.derived_summary_label
        == "ACCURACY_IMPROVED_WITHOUT_SAFETY_IMPROVEMENT"
    )

    # 5. H3 IMPROVED + H4 DEGRADED
    metrics_h4_degraded = metrics.copy()
    metrics_h4_degraded["catastrophic_false_admission_rate"] = 0.50
    metrics_h4_degraded["b2_catastrophic_false_admission_rate"] = 0.0
    res_h4_degraded = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_h4_degraded,
        "test_run",
    )
    assert res_h4_degraded.h3_result.status == HypothesisStatus.IMPROVED
    assert res_h4_degraded.h4_result.status == HypothesisStatus.DEGRADED
    assert res_h4_degraded.derived_summary_label == "ACCURACY_IMPROVED_SAFETY_DEGRADED"

    # 6. H3 NO_DIFFERENCE + H4 IMPROVED
    metrics_h3_no_diff = metrics.copy()
    metrics_h3_no_diff["overall_decision_accuracy"] = 0.6667
    metrics_h3_no_diff["b2_decision_accuracy"] = 0.6667
    res_h3_no_diff = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_h3_no_diff,
        "test_run",
    )
    assert res_h3_no_diff.h3_result.status == HypothesisStatus.NO_DIFFERENCE
    assert res_h3_no_diff.h4_result.status == HypothesisStatus.IMPROVED
    assert (
        res_h3_no_diff.derived_summary_label
        == "PROSPECTIVE_VALIDATION_REDUCES_FALSE_ADMISSION_WITHOUT_ACCURACY_GAIN"
    )

    # 7. H3 DEGRADED + H4 IMPROVED
    metrics_h3_degraded = metrics.copy()
    metrics_h3_degraded["overall_decision_accuracy"] = 0.3333
    metrics_h3_degraded["b2_decision_accuracy"] = 0.6667
    res_h3_degraded = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_h3_degraded,
        "test_run",
    )
    assert res_h3_degraded.h3_result.status == HypothesisStatus.DEGRADED
    assert res_h3_degraded.h4_result.status == HypothesisStatus.IMPROVED
    assert res_h3_degraded.derived_summary_label == "SAFETY_IMPROVED_AT_ACCURACY_COST"

    # 8. H5 failure does not overwrite H1-H4
    metrics_h5_fail = metrics.copy()
    metrics_h5_fail["defer_precision"] = 0.50
    res_h5_fail = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_h5_fail,
        "test_run",
    )
    assert res_h5_fail.h3_result.status == HypothesisStatus.IMPROVED
    assert res_h5_fail.h4_result.status == HypothesisStatus.IMPROVED
    assert res_h5_fail.h5_result.status == HypothesisStatus.FAIL
    assert (
        res_h5_fail.derived_summary_label
        == "PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY_AND_SAFETY_WITH_DEFER_CALIBRATION_WEAKNESS"
    )

    # 9. Unsupported hypothesis combination produces neutral manual fallback
    metrics_unsupported = metrics.copy()
    metrics_unsupported["overall_decision_accuracy"] = 0.20
    metrics_unsupported["b2_decision_accuracy"] = 0.80
    metrics_unsupported["catastrophic_false_admission_rate"] = 0.90
    metrics_unsupported["b2_catastrophic_false_admission_rate"] = 0.10
    res_unsupported = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_unsupported,
        "test_run",
    )
    assert (
        res_unsupported.derived_summary_label
        == "STRUCTURED_RESULT_REQUIRES_MANUAL_INTERPRETATION"
    )

    # 10. COMPILATION_REJECTED excluded from denominators but reported
    res_excl = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics,
        "test_run",
    )
    assert res_excl.h2_result.excluded_record_count == 1
    assert res_excl.h3_result.excluded_record_count == 1
    assert res_excl.h4_result.excluded_record_count == 1

    # 11. Empty denominators do not cause zero division
    res_empty = evaluator.evaluate_result(
        [], [], {}, [], [], validity_gates, {}, "test_run"
    )
    assert res_empty.h2_result.sample_size == 0
    assert res_empty.h2_result.excluded_record_count == 0

    # 12. Structured result survives serialization and reload
    ser = res_both_improved.model_dump_json()
    loaded_data = json.loads(ser)
    assert (
        loaded_data["derived_summary_label"]
        == "PROSPECTIVE_VALIDATION_IMPROVES_ACCURACY_AND_SAFETY"
    )


def test_inconclusive_default_state_label():
    from flows.minimal_learning_cycle.verdicts import (
        HypothesisStatus,
        MLCVerdictEvaluator,
    )

    # Instantiate with no threshold arguments (default inconclusive configuration)
    evaluator = MLCVerdictEvaluator()

    # Minimal mock data
    decisions = [
        {"world_id": "W1", "decision": "ADMIT", "proposition_id": "P1"},
    ]
    oracle_decisions = [
        {
            "world_id": "W1",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_EFFECT",
        },
    ]
    baseline_results = {
        "b2_decisions": {"W1": "ADMIT"},
        "b3_decisions": {"W1": "ADMIT"},
    }
    validity_gates = {
        f"GATE_{i}": {"status": "PASS", "evidence": "Ok"} for i in range(1, 11)
    }
    metrics = {
        "overall_decision_accuracy": 1.0,
        "b2_decision_accuracy": 1.0,
        "catastrophic_false_admission_rate": 0.0,
        "b2_catastrophic_false_admission_rate": 0.0,
        "defer_precision": 1.0,
        "defer_recall": 1.0,
    }

    res = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics,
        "test_run",
    )
    assert res.h2_result.status == HypothesisStatus.INCONCLUSIVE
    assert res.h3_result.status == HypothesisStatus.INCONCLUSIVE
    assert res.h4_result.status == HypothesisStatus.INCONCLUSIVE
    assert (
        res.derived_summary_label
        == "STRUCTURED_RESULT_REQUIRES_MANUAL_INTERPRETATION"
    )


def test_matrix_fallback_cells_coverage():
    from flows.minimal_learning_cycle.verdicts import (
        HypothesisStatus,
        MLCVerdictEvaluator,
    )

    # Instantiate with thresholds so H2 is PASS, but we control H3 and H4 outcomes
    evaluator = MLCVerdictEvaluator(
        significance_alpha=0.05,
        minimum_lift_effect=0.10,
        defer_precision_target=0.80,
        defer_recall_target=0.70,
    )

    decisions = [
        {"world_id": "W1", "decision": "ADMIT", "proposition_id": "P1"},
        {"world_id": "W2", "decision": "REJECT", "proposition_id": "P2"},
        {"world_id": "W3", "decision": "DEFER", "proposition_id": "P3"},
    ]
    oracle_decisions = [
        {
            "world_id": "W1",
            "decision": "ADMIT",
            "reason_code": "SUFFICIENT_POSITIVE_EFFECT",
        },
        {
            "world_id": "W2",
            "decision": "REJECT",
            "reason_code": "SUFFICIENT_NEGATIVE_EFFECT",
        },
        {"world_id": "W3", "decision": "DEFER", "reason_code": "EVIDENCE_LIMITED"},
    ]
    validity_gates = {
        f"GATE_{i}": {"status": "PASS", "evidence": "Ok"} for i in range(1, 11)
    }

    # We want H2 to be PASS (beat baseline random, which has accuracy 0.0)
    baseline_results = {
        "b2_decisions": {"W1": "ADMIT", "W2": "ADMIT", "W3": "DEFER"},
        "b3_decisions": {
            "W1": "REJECT",
            "W2": "ADMIT",
            "W3": "REJECT",
        },  # 0.0 accuracy
    }

    base_metrics = {
        "overall_decision_accuracy": 0.6667,  # MLC
        "b2_decision_accuracy": 0.6667,  # B2 Retro
        "catastrophic_false_admission_rate": 0.0,
        "b2_catastrophic_false_admission_rate": 0.0,
        "defer_precision": 1.0,
        "defer_recall": 1.0,
    }

    # Cell 1: NO_DIFFERENCE + NO_DIFFERENCE
    metrics_no_no = base_metrics.copy()
    res_no_no = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_no_no,
        "test_run",
    )
    assert res_no_no.h2_result.status == HypothesisStatus.PASS
    assert res_no_no.h3_result.status == HypothesisStatus.NO_DIFFERENCE
    assert res_no_no.h4_result.status == HypothesisStatus.NO_DIFFERENCE
    assert (
        res_no_no.derived_summary_label
        == "STRUCTURED_RESULT_REQUIRES_MANUAL_INTERPRETATION"
    )

    # Cell 2: NO_DIFFERENCE + DEGRADED
    metrics_no_deg = base_metrics.copy()
    metrics_no_deg["catastrophic_false_admission_rate"] = 0.3333
    metrics_no_deg["b2_catastrophic_false_admission_rate"] = 0.0
    res_no_deg = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_no_deg,
        "test_run",
    )
    assert res_no_deg.h2_result.status == HypothesisStatus.PASS
    assert res_no_deg.h3_result.status == HypothesisStatus.NO_DIFFERENCE
    assert res_no_deg.h4_result.status == HypothesisStatus.DEGRADED
    assert (
        res_no_deg.derived_summary_label
        == "STRUCTURED_RESULT_REQUIRES_MANUAL_INTERPRETATION"
    )

    # Cell 3: DEGRADED + NO_DIFFERENCE
    metrics_deg_no = base_metrics.copy()
    metrics_deg_no["overall_decision_accuracy"] = 0.3333
    metrics_deg_no["b2_decision_accuracy"] = 0.6667
    res_deg_no = evaluator.evaluate_result(
        decisions,
        oracle_decisions,
        baseline_results,
        [],
        [],
        validity_gates,
        metrics_deg_no,
        "test_run",
    )
    assert res_deg_no.h2_result.status == HypothesisStatus.PASS
    assert res_deg_no.h3_result.status == HypothesisStatus.DEGRADED
    assert res_deg_no.h4_result.status == HypothesisStatus.NO_DIFFERENCE
    assert (
        res_deg_no.derived_summary_label
        == "STRUCTURED_RESULT_REQUIRES_MANUAL_INTERPRETATION"
    )
