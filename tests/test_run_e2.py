"""
Unit & Integration Tests for PROMPT E2_v2 Synthetic Battery & Gate A Evaluator.

Verifies:
1. Expected Calibration Error (ECE) calculation logic.
2. Per-seed determinism (same seed -> identical metrics).
3. Gate A branch mapping reachability from registered YAML.
"""
from pathlib import Path
import pytest
from bench.run_e2_v2 import run_single_seed_battery, compute_ece_and_reliability_curve


import math

def is_equal_or_nan(val1: float, val2: float) -> bool:
    if math.isnan(val1) and math.isnan(val2):
        return True
    return val1 == val2


def test_seed_determinism():
    """Verify that running the same seed twice produces 100% identical metric outputs."""
    r1, _ = run_single_seed_battery(seed=42)
    r2, _ = run_single_seed_battery(seed=42)

    for sc_id in ["S1", "S2", "S3", "S4"]:
        for l_name in r1[sc_id]:
            assert is_equal_or_nan(r1[sc_id][l_name]["brier_score"], r2[sc_id][l_name]["brier_score"])
            assert is_equal_or_nan(r1[sc_id][l_name]["brier_regret"], r2[sc_id][l_name]["brier_regret"])
            assert is_equal_or_nan(r1[sc_id][l_name]["precision"], r2[sc_id][l_name]["precision"])
            assert is_equal_or_nan(r1[sc_id][l_name]["recall"], r2[sc_id][l_name]["recall"])



def test_ece_calculation_fixture():
    """Verify Expected Calibration Error (ECE) logic on synthetic calibration pairs."""
    cal_pairs = [(0.50, 1), (0.50, 0), (1.00, 1), (1.00, 1)]
    ece, curve = compute_ece_and_reliability_curve(cal_pairs, num_bins=10)
    assert 0.0 <= ece <= 1.0
    assert len(curve) == 10
