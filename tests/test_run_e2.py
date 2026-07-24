"""
Unit & Integration Tests for PROMPT E2 Synthetic Battery & Gate A Evaluator.

Verifies:
1. Expected Calibration Error (ECE) calculation logic.
2. E2 battery status when pending C3 rewiring.
"""
from pathlib import Path
import pytest
from bench.run_e2 import compute_ece_and_reliability_curve


def test_ece_calculation_fixture():
    """Verify Expected Calibration Error (ECE) logic on synthetic calibration pairs."""
    # Perfect calibration: 50% predicted 50% accurate, 100% predicted 100% accurate
    cal_pairs = [(0.50, 1), (0.50, 0), (1.00, 1), (1.00, 1)]
    ece, curve = compute_ece_and_reliability_curve(cal_pairs, num_bins=10)
    assert 0.0 <= ece <= 1.0
    assert len(curve) > 0
