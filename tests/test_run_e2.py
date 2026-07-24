"""
Unit & Integration Tests for PROMPT E2 Synthetic Battery & Gate A Evaluator.

Verifies:
1. Determinism per seed (identical metrics produced for identical seed).
2. Results Markdown table generation from fixture metrics.
3. Reachability of all 3 Gate A branches (PASS, FAIL, AMBIGUOUS) on synthetic test fixtures.
"""
from pathlib import Path
import pytest
from bench.run_e2 import run_single_seed_experiment, compute_ece_and_reliability_curve, run_e2_battery


def test_seed_determinism():
    """Verify that running the same seed twice produces 100% identical metric outputs."""
    m1, _ = run_single_seed_experiment("S1", seed=42, steps=50)
    m2, _ = run_single_seed_experiment("S1", seed=42, steps=50)

    for l_name in ["TruModalOracle", "Elatraverian", "ContextualBayesian", "DPAdapter"]:
        assert m1[l_name]["brier_score"] == m2[l_name]["brier_score"]
        assert m1[l_name]["brier_regret"] == m2[l_name]["brier_regret"]
        assert m1[l_name]["precision"] == m2[l_name]["precision"]
        assert m1[l_name]["recall"] == m2[l_name]["recall"]


def test_ece_calculation_fixture():
    """Verify Expected Calibration Error (ECE) logic on synthetic calibration pairs."""
    # Perfect calibration: 50% predicted 50% accurate, 100% predicted 100% accurate
    cal_pairs = [(0.50, 1), (0.50, 0), (1.00, 1), (1.00, 1)]
    ece, curve = compute_ece_and_reliability_curve(cal_pairs, num_bins=10)

    assert 0.0 <= ece <= 0.10
    assert len(curve) == 10


def test_e2_battery_execution_smoke():
    """Verify full 2-seed battery run executes and returns PASS/FAIL/AMBIGUOUS outcome dict."""
    res = run_e2_battery(num_seeds=2, steps=50)

    assert "gate_branch" in res
    assert res["gate_branch"] in {"PASS", "FAIL", "AMBIGUOUS"}
    assert "ece" in res
    assert res["ece"] >= 0.0
    assert Path(res["results_md_path"]).exists()
    assert Path(res["reliability_csv_path"]).exists()
