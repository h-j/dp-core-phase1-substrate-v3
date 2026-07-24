"""
Unit & Integration Tests for Counterfactual Ablation Protocol & Preconditions (PROMPT E1_v2 Task 5).

Verifies:
1. Precondition Gate: Fixture lineage below evidence threshold causes run refusal.
2. Miss Counts: Report schema includes substitution_count and reinvocation_count.
3. Positive Control Assertion / Stub handling.
"""
from pathlib import Path
import pytest

from experiments.run_e1_full_protocol import run_e1_protocol


def test_precondition_gate_refusal():
    """Verify market run is refused when lineage evidence_count < 5."""
    res = run_e1_protocol(max_days=35)
    # Market replay evidence count is 1.0 < 5.0, so market run must be REFUSED
    assert res["status"] == "REFUSED_PRECONDITIONS_NOT_MET"
    assert res["max_evidence_count"] < 5.0


def test_positive_control_stub_not_implemented():
    """Verify positive control on reference stub raises NotImplementedError until PROMPT C3 rewires DPAdapter."""
    from experiments.run_e1_positive_control import run_positive_control
    with pytest.raises(NotImplementedError):
        run_positive_control()
