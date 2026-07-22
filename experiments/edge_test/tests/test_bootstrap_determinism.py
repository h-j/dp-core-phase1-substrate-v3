"""
Test Stationary Bootstrap & PSR Determinism under Fixed Seed.
"""
import numpy as np
import pytest

from experiments.edge_test.stats import calculate_edge_stats, compute_psr, stationary_bootstrap_pvalue


def test_bootstrap_pvalue_determinism():
    rng = np.random.RandomState(123)
    returns = rng.normal(0.0005, 0.01, size=250)

    # Execution 1
    p1 = stationary_bootstrap_pvalue(returns, n_resamples=1000, mean_block_length=10.0, seed=42)
    # Execution 2
    p2 = stationary_bootstrap_pvalue(returns, n_resamples=1000, mean_block_length=10.0, seed=42)

    assert p1 == p2, f"Bootstrap p-value must be 100% deterministic under fixed seed (got {p1} vs {p2})"


def test_calculate_edge_stats_determinism():
    records = []
    rng = np.random.RandomState(456)
    for i in range(100):
        records.append({
            "day_index": i,
            "target_position": 1 if i % 2 == 0 else -1,
            "net_return": float(rng.normal(0.0008, 0.008)),
            "gross_return": float(rng.normal(0.0010, 0.008)),
            "cost_bps": 9.094 if i % 2 == 0 else 11.394,
        })

    stats1 = calculate_edge_stats(records, seed=42)
    stats2 = calculate_edge_stats(records, seed=42)

    assert stats1 == stats2
    assert "psr" in stats1
    assert "bootstrap_pvalue" in stats1
