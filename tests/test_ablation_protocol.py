"""
Unit & Integration Tests for Counterfactual Ablation Protocol & Preconditions (PROMPT E1_v2 Task 5).

Verifies:
1. Precondition Gate: Fixture lineage below evidence threshold causes run refusal.
2. Positive Control: DPAdapter positive control produces non-empty verified_influence_set.
"""
from pathlib import Path
import pytest

from experiments.run_e1_full_protocol import run_e1_protocol
from experiments.run_e1_positive_control import run_positive_control


def test_positive_control_verified_influence_non_empty():
    """Verify positive control produces non-empty verified influence set."""
    report = run_positive_control()
    assert report["verdict"] == "PASS"
    assert len(report["verified_influence_set"]) > 0
    assert len(report["unpredicted_divergence_set"]) == 0


def test_precondition_gate_refusal():
    """Verify market run is refused when lineage evidence_count < 5."""
    res = run_e1_protocol(max_days=35)
    # Market replay evidence count is 1.0 < 5.0, so market run must be REFUSED
    assert res["status"] == "REFUSED_PRECONDITIONS_NOT_MET"
    assert res["max_evidence_count"] < 5.0
