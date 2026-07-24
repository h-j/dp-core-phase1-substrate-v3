"""
Unit & Integration Tests for Counterfactual Ablation Protocol & Preconditions (PROMPT E1_v2 Task 5).

Verifies:
1. Precondition Gate: Fixture lineage below evidence threshold causes run refusal.
2. Miss Counts: Report schema includes substitution_count and reinvocation_count.
3. Positive Control: DPAdapter positive control produces a NON-EMPTY verified_influence_set.
"""
from pathlib import Path
import pytest
from unittest.mock import MagicMock

from experiments.run_e1_positive_control import run_positive_control
from experiments.run_e1_full_protocol import run_e1_protocol

PROJECT_ROOT = Path(__file__).parent.parent


def test_positive_control_verified_influence_non_empty():
    """Verify positive control produces non-empty verified influence set."""
    out_dir = PROJECT_ROOT / "bench" / "results" / "test_positive_control"
    report = run_positive_control(output_dir=out_dir)

    assert report["verdict"] == "PASS"
    assert len(report["verified_influence_set"]) > 0
    assert len(report["unpredicted_divergence_set"]) == 0


def test_precondition_gate_refusal():
    """Verify market run is refused when lineage evidence_count < 5."""
    res = run_e1_protocol(max_days=35)
    # Market replay evidence count is 1.0 < 5.0, so market run must be REFUSED
    assert res["status"] == "REFUSED_PRECONDITIONS_NOT_MET"
    assert res["max_evidence_count"] < 5.0


def test_report_schema_contains_miss_counts():
    """Verify report schema prominently includes substitution_count and reinvocation_count."""
    out_dir = PROJECT_ROOT / "bench" / "results" / "test_positive_control"
    report = run_positive_control(output_dir=out_dir)

    assert "llm_stats" in report
    assert "substitution_count" in report["llm_stats"]
    assert "reinvocation_count" in report["llm_stats"]
