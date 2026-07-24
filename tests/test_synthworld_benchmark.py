"""
Unit & Integration Tests for Reference Synthworld Benchmark & DPAdapter (PROMPT E0b / C3).

Verifies:
1. Reference synthworld framework imports cleanly and baseline learners pass.
2. Hypothesis-space equality assertion: set(adapter.hypothesis_space) == set(baseline candidate pairs).
"""
from pathlib import Path
import pytest

from bench.synthworld.world import World, Scenario
from bench.synthworld.scenarios import s1_clean, s2_spurious, s3_regime, s4_scope
from bench.synthworld.learners import TrueModel, FlatBayesian, WindowedFrequency, ContextualBayesian
from bench.synthworld.dp_adapter import DPAdapter


def test_reference_benchmark_scenarios_instantiate():
    """Verify reference benchmark scenario factory functions instantiate correctly."""
    for make in (s1_clean, s2_spurious, s3_regime, s4_scope):
        sc = make()
        assert sc.T > 0
        assert len(sc.drivers) > 0
        assert len(sc.effects) > 0


def test_hypothesis_space_equality():
    """Verify DPAdapter enumerated hypothesis space equals baseline hypothesis space (assert set equality)."""
    sc = s1_clean()
    adapter = DPAdapter(sc)
    baseline = FlatBayesian(sc)

    baseline_space = set((c, e) for c in baseline.causes for e in baseline.effects)
    adapter_space = set(adapter.hypothesis_space)

    assert adapter_space == baseline_space, f"Hypothesis space mismatch: {adapter_space} != {baseline_space}"
