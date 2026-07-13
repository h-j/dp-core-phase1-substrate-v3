import pytest
from flows.minimal_learning_cycle.completion_gates import (
    MilestoneCompletionGates, GateStatus, ClaimEvidenceConsistencyGate, ClaimStatus, MilestoneScientificClosure
)


def test_executable_gates_validation_success():
    # When all gates pass or are not applicable, validation succeeds
    gates = MilestoneCompletionGates(
        milestone_id="MILESTONE_5_TEST",
        ISOLATION_GATE_STATUS=GateStatus.PASS,
        CAUSAL_NECESSITY_GATE_STATUS=GateStatus.PASS,
        MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
        DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.PASS,
        RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
        SAFEGUARD_BENEFIT_STATUS=GateStatus.PASS,
        SAFEGUARD_COST_STATUS=GateStatus.PASS,
        COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.PASS,
        CLAIM_SCOPE_STATUS=GateStatus.PASS,
        REGRESSION_SAFETY_STATUS=GateStatus.PASS,
    )
    assert gates.milestone_id == "MILESTONE_5_TEST"


def test_executable_gates_validation_fail_closed():
    # If any gate is FAIL, validation must fail with ValueError
    with pytest.raises(ValueError) as excinfo:
        MilestoneCompletionGates(
            milestone_id="MILESTONE_5_FAIL_TEST",
            ISOLATION_GATE_STATUS=GateStatus.PASS,
            CAUSAL_NECESSITY_GATE_STATUS=GateStatus.FAIL,  # Critical gate fails
            MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
            DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.PASS,
            RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
            SAFEGUARD_BENEFIT_STATUS=GateStatus.PASS,
            SAFEGUARD_COST_STATUS=GateStatus.PASS,
            COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.PASS,
            CLAIM_SCOPE_STATUS=GateStatus.PASS,
            REGRESSION_SAFETY_STATUS=GateStatus.PASS,
        )
    assert "CAUSAL_NECESSITY_GATE_STATUS is GateStatus.FAIL" in str(excinfo.value)


def test_executable_gates_validation_fail_indeterminate():
    # If any gate is INDETERMINATE, validation must fail with ValueError
    with pytest.raises(ValueError) as excinfo:
        MilestoneCompletionGates(
            milestone_id="MILESTONE_5_INDETERMINATE_TEST",
            ISOLATION_GATE_STATUS=GateStatus.PASS,
            CAUSAL_NECESSITY_GATE_STATUS=GateStatus.PASS,
            MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
            DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.PASS,
            RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
            SAFEGUARD_BENEFIT_STATUS=GateStatus.PASS,
            SAFEGUARD_COST_STATUS=GateStatus.PASS,
            COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.INDETERMINATE,  # Indeterminate status
            CLAIM_SCOPE_STATUS=GateStatus.PASS,
            REGRESSION_SAFETY_STATUS=GateStatus.PASS,
        )
    assert "COMPLETE_LIFECYCLE_ACCOUNTING_STATUS is GateStatus.INDETERMINATE" in str(excinfo.value)


def test_executable_gates_validation_not_applicable():
    # NOT_APPLICABLE does not prevent completion closure
    gates = MilestoneCompletionGates(
        milestone_id="MILESTONE_6_TEST",
        ISOLATION_GATE_STATUS=GateStatus.PASS,
        CAUSAL_NECESSITY_GATE_STATUS=GateStatus.PASS,
        MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
        DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.NOT_APPLICABLE,  # Not applicable
        RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
        SAFEGUARD_BENEFIT_STATUS=GateStatus.NOT_APPLICABLE,  # Not applicable
        SAFEGUARD_COST_STATUS=GateStatus.NOT_APPLICABLE,  # Not applicable
        COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.PASS,
        CLAIM_SCOPE_STATUS=GateStatus.PASS,
        REGRESSION_SAFETY_STATUS=GateStatus.PASS,
    )
    assert gates.milestone_id == "MILESTONE_6_TEST"


def test_claim_evidence_regression_case_1():
    # Milestone 5 Claim: "Prospective Validation reduced false admissions."
    # Since both rates are 0.0, reduction is not demonstrated.
    m5_methodology = MilestoneCompletionGates(
        milestone_id="M5_METHODOLOGY",
        ISOLATION_GATE_STATUS=GateStatus.PASS,
        CAUSAL_NECESSITY_GATE_STATUS=GateStatus.PASS,
        MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
        DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.PASS,
        RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
        SAFEGUARD_BENEFIT_STATUS=GateStatus.PASS,
        SAFEGUARD_COST_STATUS=GateStatus.PASS,
        COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.PASS,
        CLAIM_SCOPE_STATUS=GateStatus.PASS,
        REGRESSION_SAFETY_STATUS=GateStatus.PASS,
    )
    
    invalid_claim = ClaimEvidenceConsistencyGate.evaluate_false_admission_reduction(
        baseline_rate=0.0,
        treatment_rate=0.0,
        claim_text="Prospective Validation reduced false admissions."
    )
    assert invalid_claim.status == ClaimStatus.CLAIM_NOT_DEMONSTRATED
    
    # Validation should fail closed
    from flows.minimal_learning_cycle.completion_gates import MilestoneScientificClosure
    with pytest.raises(ValueError) as excinfo:
        MilestoneScientificClosure(
            milestone_id="M5_CLOSURE_FAIL",
            methodology_gates=m5_methodology,
            claims=[invalid_claim]
        )
    assert "Undemonstrated claims: Prospective Validation reduced false admissions." in str(excinfo.value)
    
    # Narrower valid claim: "Prospective Validation did not reduce false admission rate on the tested primary evidence."
    valid_claim = ClaimEvidenceConsistencyGate.evaluate_false_admission_reduction(
        baseline_rate=0.0,
        treatment_rate=0.0,
        claim_text="Prospective Validation did not reduce false admission rate on the tested primary evidence."
    )
    assert valid_claim.status == ClaimStatus.CLAIM_SUPPORTED
    
    # Closure passes successfully
    closure = MilestoneScientificClosure(
        milestone_id="M5_CLOSURE_PASS",
        methodology_gates=m5_methodology,
        claims=[valid_claim]
    )
    assert closure.milestone_id == "M5_CLOSURE_PASS"


def test_claim_evidence_regression_case_2():
    # Milestone 6 Claim: "Order sensitivity demonstrated."
    # Missing paired-order comparison sequence (e.g. only 1 temporal sequence executed)
    m6_methodology = MilestoneCompletionGates(
        milestone_id="M6_METHODOLOGY",
        ISOLATION_GATE_STATUS=GateStatus.PASS,
        CAUSAL_NECESSITY_GATE_STATUS=GateStatus.PASS,
        MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
        DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.NOT_APPLICABLE,
        RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
        SAFEGUARD_BENEFIT_STATUS=GateStatus.NOT_APPLICABLE,
        SAFEGUARD_COST_STATUS=GateStatus.NOT_APPLICABLE,
        COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.PASS,
        CLAIM_SCOPE_STATUS=GateStatus.PASS,
        REGRESSION_SAFETY_STATUS=GateStatus.PASS,
    )
    
    # Single sequence only
    sequences_single = {"sequence_b_contradiction": ["ADMITTED_BELIEF", "WEAKENED_BELIEF", "RETIRED_BELIEF"]}
    invalid_claim = ClaimEvidenceConsistencyGate.evaluate_order_sensitivity(
        sequences=sequences_single,
        claim_text="Order sensitivity demonstrated."
    )
    assert invalid_claim.status == ClaimStatus.CLAIM_NOT_DEMONSTRATED
    
    from flows.minimal_learning_cycle.completion_gates import MilestoneScientificClosure
    with pytest.raises(ValueError) as excinfo:
        MilestoneScientificClosure(
            milestone_id="M6_CLOSURE_FAIL",
            methodology_gates=m6_methodology,
            claims=[invalid_claim]
        )
    assert "Undemonstrated claims: Order sensitivity demonstrated." in str(excinfo.value)
    
    # Narrower valid claim: "Absorbing retirement behavior observed."
    valid_claim_retirement = ClaimEvidenceConsistencyGate.evaluate_order_sensitivity(
        sequences=sequences_single,
        claim_text="Absorbing retirement behavior observed."
    )
    assert valid_claim_retirement.status == ClaimStatus.CLAIM_SUPPORTED
    
    # Paired sequence comparison
    sequences_paired = {
        "order_a": "ADMITTED_BELIEF",
        "order_b": "WEAKENED_BELIEF"
    }
    valid_claim_order = ClaimEvidenceConsistencyGate.evaluate_order_sensitivity(
        sequences=sequences_paired,
        claim_text="Order sensitivity demonstrated."
    )
    assert valid_claim_order.status == ClaimStatus.CLAIM_SUPPORTED
    
    # Scientific closure with both valid claims succeeds
    closure = MilestoneScientificClosure(
        milestone_id="M6_CLOSURE_PASS",
        methodology_gates=m6_methodology,
        claims=[valid_claim_retirement, valid_claim_order]
    )
    assert closure.milestone_id == "M6_CLOSURE_PASS"


def test_claim_evidence_milestone_7():
    # Case A: Behavior changes, resources decrease, but no epistemic metric measured.
    results_case_a = {
        "pruning_triggered_seeds_count": 2,
        "condition_c_influence_blocked": {
            "mean_compiled_candidates": 3.0,
            "mean_compilation_budget_spent": 30.0,
            "mean_evidence_budget_spent": 60.0
        },
        "condition_d_influence_enabled": {
            "mean_compiled_candidates": 2.0,
            "mean_compilation_budget_spent": 20.0,
            "mean_evidence_budget_spent": 40.0
        },
        "epistemic_metric_measured": False
    }
    claim_a = ClaimEvidenceConsistencyGate.evaluate_minimal_causal_learning(
        results=results_case_a,
        claim_text="Minimal causal learning demonstrated."
    )
    assert claim_a.status == ClaimStatus.CLAIM_NOT_DEMONSTRATED

    # Case B: Behavior changes, resources decrease, but epistemic performance degrades.
    results_case_b = {
        "pruning_triggered_seeds_count": 2,
        "primary_epistemic_metric": "true_causal_selection_rate",
        "epistemic_metric_measured": True,
        "epistemic_metric_diff": -0.5,  # degraded performance in D relative to C
        "evidence_sufficiency_satisfied": True
    }
    claim_b = ClaimEvidenceConsistencyGate.evaluate_minimal_causal_learning(
        results=results_case_b,
        claim_text="Minimal causal learning demonstrated."
    )
    assert claim_b.status == ClaimStatus.CLAIM_CONTRADICTED

    # Case C: Behavior changes, resources decrease, and epistemic performance improves.
    results_case_c = {
        "pruning_triggered_seeds_count": 2,
        "primary_epistemic_metric": "true_causal_selection_rate",
        "epistemic_metric_measured": True,
        "epistemic_metric_diff": 0.2,  # improved performance
        "evidence_sufficiency_satisfied": True
    }
    claim_c = ClaimEvidenceConsistencyGate.evaluate_minimal_causal_learning(
        results=results_case_c,
        claim_text="Minimal causal learning demonstrated."
    )
    assert claim_c.status == ClaimStatus.CLAIM_SUPPORTED

    # Case D: Behavior changes, epistemic performance is measured, and neutrality satisfied.
    results_case_d = {
        "pruning_triggered_seeds_count": 2,
        "primary_epistemic_metric": "true_causal_selection_rate",
        "epistemic_metric_measured": True,
        "epistemic_metric_diff": 0.0,
        "neutrality_criterion_satisfied": True,
        "evidence_sufficiency_satisfied": True
    }
    claim_d = ClaimEvidenceConsistencyGate.evaluate_minimal_causal_learning(
        results=results_case_d,
        claim_text="Minimal causal learning demonstrated."
    )
    assert claim_d.status == ClaimStatus.NEUTRAL_EFFECT_DEMONSTRATED


def test_milestone_scientific_closure_validation():
    from flows.minimal_learning_cycle.completion_gates import MilestoneCompletionGates, GateStatus
    
    dummy_gates = MilestoneCompletionGates(
        milestone_id="M7_GATES",
        ISOLATION_GATE_STATUS=GateStatus.PASS,
        CAUSAL_NECESSITY_GATE_STATUS=GateStatus.PASS,
        MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
        DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.PASS,
        RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
        SAFEGUARD_BENEFIT_STATUS=GateStatus.PASS,
        SAFEGUARD_COST_STATUS=GateStatus.PASS,
        COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.PASS,
        CLAIM_SCOPE_STATUS=GateStatus.PASS,
        REGRESSION_SAFETY_STATUS=GateStatus.PASS,
    )
    
    # Verify closure fails closed if primary epistemic metric is unmeasured
    with pytest.raises(ValueError, match="PRIMARY_EPISTEMIC_METRIC_NOT_MEASURED"):
        MilestoneScientificClosure(
            milestone_id="M7_FAIL",
            methodology_gates=dummy_gates,
            claims=[],
            primary_epistemic_metric_measured=False
        )

    # Verify closure fails closed if evidence sufficiency is not satisfied
    with pytest.raises(ValueError, match="EVIDENCE_SUFFICIENCY_REQUIREMENT_NOT_SATISFIED"):
        MilestoneScientificClosure(
            milestone_id="M7_FAIL",
            methodology_gates=dummy_gates,
            claims=[],
            evidence_sufficiency_satisfied=False
        )

    # Verify closure fails closed if diagnostic primary separation fails
    with pytest.raises(ValueError, match="DIAGNOSTIC_PRIMARY_SEPARATION_FAILED"):
        MilestoneScientificClosure(
            milestone_id="M7_FAIL",
            methodology_gates=dummy_gates,
            claims=[],
            diagnostic_primary_separation=False
        )


def test_power_calculation_variance_source():
    from flows.minimal_learning_cycle.completion_gates import ClaimSpecification, ClaimType, ClaimEvidenceConsistencyGate
    
    spec = ClaimSpecification(
        claim_id="TEST_POWER_CLAIM",
        claim_text="Test Power Claim",
        claim_type=ClaimType.POSITIVE_IMPROVEMENT,
        minimum_meaningful_effect=0.15
    )
    
    # Results 1: p_c = 0.1, p_d = 0.8
    res1 = {"sample_size": 13, "condition_c_rate": 0.1, "condition_d_rate": 0.8}
    gate1 = ClaimEvidenceConsistencyGate.evaluate_claim_consistency(res1, spec)
    
    # Results 2: p_c = 0.4, p_d = 0.5
    res2 = {"sample_size": 13, "condition_c_rate": 0.4, "condition_d_rate": 0.5}
    gate2 = ClaimEvidenceConsistencyGate.evaluate_claim_consistency(res2, spec)
    
    assert gate1.n_required == gate2.n_required
    assert gate1.n_required == 167  # (1.96 + 0.84)^2 * (0.5*0.5 + 0.65*0.35) / 0.15^2 -> 167


def test_dynamic_critical_value_power_scaling():
    from flows.minimal_learning_cycle.completion_gates import ClaimSpecification, ClaimType, ClaimEvidenceConsistencyGate
    
    spec_power_80 = ClaimSpecification(
        claim_id="TEST_POWER_80",
        claim_text="Power 80%",
        claim_type=ClaimType.POSITIVE_IMPROVEMENT,
        minimum_meaningful_effect=0.15,
        target_power=0.80
    )
    
    spec_power_90 = ClaimSpecification(
        claim_id="TEST_POWER_90",
        claim_text="Power 90%",
        claim_type=ClaimType.POSITIVE_IMPROVEMENT,
        minimum_meaningful_effect=0.15,
        target_power=0.90
    )
    
    res = {"sample_size": 13, "condition_c_rate": 0.1, "condition_d_rate": 0.8}
    gate_80 = ClaimEvidenceConsistencyGate.evaluate_claim_consistency(res, spec_power_80)
    gate_90 = ClaimEvidenceConsistencyGate.evaluate_claim_consistency(res, spec_power_90)
    
    # Target power 90% requires more sample size than 80%
    assert gate_90.n_required > gate_80.n_required
    assert gate_80.n_required == 167
    assert gate_90.n_required > 167


def test_ondisk_artifacts_validation():
    from flows.minimal_learning_cycle.completion_gates import EpistemicValidationManifestReader
    # Test loading actual files on disk
    manifest = EpistemicValidationManifestReader.load_manifest("data/scientific_closures_manifest.json")
    assert manifest is not None
    assert manifest.milestone_5 is not None
    assert manifest.milestone_6 is not None
    assert manifest.milestone_7 is not None
    assert manifest.milestone_7_closure is None


def test_ondisk_artifacts_validation_rejects_invalid(tmp_path):
    import json
    from flows.minimal_learning_cycle.completion_gates import EpistemicValidationManifestReader
    
    # 1. Deliberately tampered JSON (does not conform to schema)
    invalid_json_path = tmp_path / "tampered_manifest.json"
    with open(invalid_json_path, "w") as f:
        json.dump({"random_key": "some_value"}, f)
        
    with pytest.raises(ValueError):
        EpistemicValidationManifestReader.load_manifest(str(invalid_json_path))
        
    # 2. Manifest containing a claim with status CLAIM_CONTRADICTED
    tampered_manifest = {
        "milestone_5": None,
        "milestone_6": None,
        "milestone_7": None,
        "milestone_7_closure": None,
        "claims": [
            {
                "claim_id": "TAMPERED_CLAIM",
                "claim_text": "Causal selection rate improvement",
                "claim_type": "positive_improvement",
                "minimum_meaningful_effect": 0.05,
                "expected_baseline_proportion": 0.5,
                "confidence_level": 0.95,
                "target_power": 0.80
            }
        ],
        "results": {
            "sample_size": 1600,
            "condition_c_rate": 0.5,
            "condition_d_rate": 0.2,
            "epistemic_metric_diff": -0.3
        }
    }
    
    tampered_path = tmp_path / "tampered_contradicted_manifest.json"
    with open(tampered_path, "w") as f:
        json.dump(tampered_manifest, f)
        
    with pytest.raises(ValueError, match="Consumption Blocked: Manifest contains failed/underpowered status"):
        EpistemicValidationManifestReader.load_manifest(str(tampered_path))


def test_indeterminate_no_power_target_defined_blocks_closure():
    from flows.minimal_learning_cycle.completion_gates import (
        MilestoneScientificClosure, MilestoneCompletionGates, GateStatus, ClaimEvidenceConsistencyGate, ClaimStatus
    )
    
    dummy_gates = MilestoneCompletionGates(
        milestone_id="M7_GATES",
        ISOLATION_GATE_STATUS=GateStatus.PASS,
        CAUSAL_NECESSITY_GATE_STATUS=GateStatus.PASS,
        MECHANISM_STRENGTH_GATE_STATUS=GateStatus.PASS,
        DIAGNOSTIC_PRIMARY_SEPARATION_STATUS=GateStatus.PASS,
        RESOURCE_CONTAMINATION_STATUS=GateStatus.PASS,
        SAFEGUARD_BENEFIT_STATUS=GateStatus.PASS,
        SAFEGUARD_COST_STATUS=GateStatus.PASS,
        COMPLETE_LIFECYCLE_ACCOUNTING_STATUS=GateStatus.PASS,
        CLAIM_SCOPE_STATUS=GateStatus.PASS,
        REGRESSION_SAFETY_STATUS=GateStatus.PASS,
    )
    
    indeterminate_claim = ClaimEvidenceConsistencyGate(
        claim_id="M7_INDETERMINATE_CLAIM",
        claim_text="Unverified claim without MME",
        status=ClaimStatus.INDETERMINATE_NO_POWER_TARGET_DEFINED
    )
    
    with pytest.raises(ValueError, match="Scientific Closure Failure for M7_FAIL: Undemonstrated claims: Unverified claim without MME \\(INDETERMINATE_NO_POWER_TARGET_DEFINED\\)"):
        MilestoneScientificClosure(
            milestone_id="M7_FAIL",
            methodology_gates=dummy_gates,
            claims=[indeterminate_claim]
        )


def test_wired_gate_1_temporal_isolation_violation():
    from flows.minimal_learning_cycle.validity_gates import MLCValidityGates
    
    # Case 1: Validated candidate exists, and validation request exists in ERC but not authorized
    erc_logs = [{"resource_type": "VALIDATION", "proposition_id": "prop_1", "authorization_decision": "DENIED"}]
    decisions = [{"proposition_id": "prop_1", "decision": "ADMIT", "reason_code": "SUFFICIENT_LIFT"}]
    res = MLCValidityGates.verify_gate_1_temporal_isolation(erc_logs, decisions)
    assert res["status"] == "FAIL"

    # Case 2: Validation auth log exists, matching validated candidate
    erc_logs = [{"resource_type": "VALIDATION", "proposition_id": "prop_1", "authorization_decision": "AUTHORIZED"}]
    res = MLCValidityGates.verify_gate_1_temporal_isolation(erc_logs, decisions)
    assert res["status"] == "PASS"


def test_wired_gate_7_erc_authorization_violation():
    from flows.minimal_learning_cycle.validity_gates import MLCValidityGates
    
    # Case 1: Frozen candidate exists, but no compilation/evidence auth logs exist in ERC
    frozen_candidates = [{"content_hash": "hash_1", "proposition_definition": {}}]
    erc_logs = []
    res = MLCValidityGates.verify_gate_7_erc_authorization(erc_logs, frozen_candidates)
    assert res["status"] == "FAIL"

    # Case 2: With auth logs
    erc_logs = [
        {"resource_type": "COMPILATION", "proposition_id": "prop_1", "authorization_decision": "AUTHORIZED"},
        {"resource_type": "EVIDENCE", "proposition_id": "prop_1", "authorization_decision": "AUTHORIZED"}
    ]
    res = MLCValidityGates.verify_gate_7_erc_authorization(erc_logs, frozen_candidates)
    assert res["status"] == "PASS"


def test_wired_gate_8_candidate_immutability_violation():
    import hashlib
    import json
    from flows.minimal_learning_cycle.validity_gates import MLCValidityGates
    
    prop_def = {"proposition_id": "prop_1", "value": 42}
    serialized = json.dumps(prop_def, sort_keys=True)
    correct_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    
    # Case 1: Matching hash
    frozen_candidates = [{"content_hash": correct_hash, "proposition_definition": prop_def}]
    res = MLCValidityGates.verify_gate_8_candidate_immutability(frozen_candidates)
    assert res["status"] == "PASS"

    # Case 2: Tampered definition
    tampered_prop_def = {"proposition_id": "prop_1", "value": 99}
    frozen_candidates_tampered = [{"content_hash": correct_hash, "proposition_definition": tampered_prop_def}]
    res = MLCValidityGates.verify_gate_8_candidate_immutability(frozen_candidates_tampered)
    assert res["status"] == "FAIL"


def test_wired_gate_1_temporal_isolation_empty_logs_indeterminate():
    from flows.minimal_learning_cycle.validity_gates import MLCValidityGates
    res1 = MLCValidityGates.verify_gate_1_temporal_isolation([], [])
    assert res1["status"] == "INDETERMINATE"
    assert "empty" in res1["evidence"]

    res2 = MLCValidityGates.verify_gate_1_temporal_isolation([{"resource_type": "VALIDATION"}], [])
    assert res2["status"] == "INDETERMINATE"

    res3 = MLCValidityGates.verify_gate_1_temporal_isolation([], [{"proposition_id": "p"}])
    assert res3["status"] == "INDETERMINATE"



