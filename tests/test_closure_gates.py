"""
Unit Tests for Scientific Completion Gates & Pre-Registered MME Thresholds (PROMPT R3).

Verifies that:
1. All three gate outcomes (PASS, FAIL, INSUFFICIENT_EVIDENCE) are reachable on fixture artifacts.
2. Absence of artifacts yields INSUFFICIENT_EVIDENCE (never PASS).
3. Pre-registered thresholds are read dynamically from configuration, never inlined.
"""
from pathlib import Path
import pytest

from bootstrap.verify_scientific_closures import (
    evaluate_milestone_5_gate,
    evaluate_milestone_6_gate,
    evaluate_milestone_7_gate,
    load_preregistered_thresholds,
)
from flows.minimal_learning_cycle.completion_gates import GateStatus


@pytest.fixture
def mock_thresholds():
    return {
        "milestone_5": {
            "metric": "causal_selection_rate_lift_vs_matched_random",
            "mme_threshold": 0.10,
            "min_sample": 50,
        },
        "milestone_6": {
            "metric": "median_steps_to_weakened",
            "mme_threshold": 20,
            "collateral_retired_threshold": 0,
            "min_sample": 5,
        },
        "milestone_7": {
            "mme_threshold_family_a": 0.10,
            "mme_threshold_family_b": -0.10,
            "min_sample": 50,
        },
    }


def test_load_preregistered_thresholds_from_config():
    """Verify that pre-registered thresholds are loaded dynamically from config/cognition.yaml."""
    thresholds = load_preregistered_thresholds()
    assert "milestone_5" in thresholds
    assert "milestone_6" in thresholds
    assert "milestone_7" in thresholds
    assert thresholds["milestone_5"]["mme_threshold"] == 0.10
    assert thresholds["milestone_5"]["min_sample"] == 50


def test_milestone_5_three_outcomes(mock_thresholds):
    """Verify Milestone 5 yields INSUFFICIENT_EVIDENCE, PASS, and FAIL appropriately."""
    # 1. Absence of artifacts / small sample -> INSUFFICIENT_EVIDENCE
    results_small = {"family_a_stable_confounder": {"triggered_events": 10, "selection_rate_diff": 0.50}}
    status, msg = evaluate_milestone_5_gate(mock_thresholds, results_small)
    assert status == GateStatus.INSUFFICIENT_EVIDENCE

    # 2. Sample >= 50 and lift >= 0.10 -> PASS
    results_pass = {"family_a_stable_confounder": {"triggered_events": 60, "selection_rate_diff": 0.15}}
    status, msg = evaluate_milestone_5_gate(mock_thresholds, results_pass)
    assert status == GateStatus.PASS

    # 3. Sample >= 50 and lift < 0.10 -> FAIL
    results_fail = {"family_a_stable_confounder": {"triggered_events": 60, "selection_rate_diff": 0.05}}
    status, msg = evaluate_milestone_5_gate(mock_thresholds, results_fail)
    assert status == GateStatus.FAIL


def test_milestone_6_three_outcomes(mock_thresholds):
    """Verify Milestone 6 yields INSUFFICIENT_EVIDENCE, PASS, and FAIL appropriately."""
    # 1. Absence of artifacts -> INSUFFICIENT_EVIDENCE
    status, msg = evaluate_milestone_6_gate(mock_thresholds, {})
    assert status == GateStatus.INSUFFICIENT_EVIDENCE

    # 2. Sample >= 5, median_steps <= 20, collateral == 0 -> PASS
    results_pass = {"milestone_6_belief_transitions": {"runs_count": 10, "median_steps_to_weakened": 12, "collateral_retired_true_rules": 0}}
    status, msg = evaluate_milestone_6_gate(mock_thresholds, results_pass)
    assert status == GateStatus.PASS

    # 3. Sample >= 5, median_steps > 20 -> FAIL
    results_fail = {"milestone_6_belief_transitions": {"runs_count": 10, "median_steps_to_weakened": 25, "collateral_retired_true_rules": 0}}
    status, msg = evaluate_milestone_6_gate(mock_thresholds, results_fail)
    assert status == GateStatus.FAIL


def test_milestone_7_three_outcomes(mock_thresholds):
    """Verify Milestone 7 yields INSUFFICIENT_EVIDENCE, PASS, and FAIL (e.g. context shift degradation)."""
    # 1. Missing Family B -> INSUFFICIENT_EVIDENCE
    results_missing = {"family_a_stable_confounder": {"triggered_events": 60, "selection_rate_diff": 0.50}}
    status, msg = evaluate_milestone_7_gate(mock_thresholds, results_missing)
    assert status == GateStatus.INSUFFICIENT_EVIDENCE

    # 2. Both Family A & B pass -> PASS
    results_pass = {
        "family_a_stable_confounder": {"triggered_events": 60, "selection_rate_diff": 0.50},
        "family_b_context_shift": {"triggered_events": 60, "selection_rate_diff": -0.05},
    }
    status, msg = evaluate_milestone_7_gate(mock_thresholds, results_pass)
    assert status == GateStatus.PASS

    # 3. Family B degradation -0.7692 < -0.10 -> FAIL (encodes known context-shift failure!)
    results_fail = {
        "family_a_stable_confounder": {"triggered_events": 60, "selection_rate_diff": 0.5385},
        "family_b_context_shift": {"triggered_events": 60, "selection_rate_diff": -0.7692},
    }
    status, msg = evaluate_milestone_7_gate(mock_thresholds, results_fail)
    assert status == GateStatus.FAIL
