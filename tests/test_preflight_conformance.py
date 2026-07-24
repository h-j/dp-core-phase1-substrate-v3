"""
Tests for Pre-Flight Conformance & Gate-Branch Mapping (PROMPT E2_v2 Task 7).

Verifies:
1. Preflight failure modes are reachable on non-conforming fixtures.
2. Gate-branch mapping logic against registered experiments/preregistration/gate_a.yaml.
"""
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from bench.preflight import run_preflight_checks

PROJECT_ROOT = Path(__file__).parent.parent


def test_preflight_failure_mode_on_nonconforming_fixture():
    """Verify that preflight script hard-fails (SystemExit 1) on non-conforming benchmark state."""
    with pytest.raises(SystemExit) as exc_info:
        run_preflight_checks()
    assert exc_info.value.code == 1


def test_gate_a_yaml_branch_mapping():
    """Verify registered gate_a.yaml parses cleanly and maps three branches (PASS, FAIL, AMBIGUOUS)."""
    gate_file = PROJECT_ROOT / "experiments" / "preregistration" / "gate_a.yaml"
    assert gate_file.exists(), "gate_a.yaml must exist per PROMPT C1 pre-registration."

    with open(gate_file, "r", encoding="utf-8") as f:
        gate_cfg = yaml.safe_load(f)

    assert "gate_a" in gate_cfg
    assert "three_branch_interpretation_table" in gate_cfg["gate_a"]

    branches = gate_cfg["gate_a"]["three_branch_interpretation_table"]
    assert "PASS" in branches
    assert "FAIL" in branches
    assert "AMBIGUOUS" in branches

    # Verify S1-S3 pass conditions registered
    e2_criteria = gate_cfg["gate_a"]["experiments"]["e2_synthetic_battery"]["criteria"]
    assert "pass_conditions_simultaneous" in e2_criteria
    conds = e2_criteria["pass_conditions_simultaneous"]
    assert len(conds) == 5
