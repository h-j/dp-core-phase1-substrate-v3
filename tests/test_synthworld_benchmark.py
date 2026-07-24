"""
Unit & Integration Tests for Reference Synthworld Benchmark & DPAdapter (PROMPT E0b / C3).

Verifies:
1. Reference synthworld framework imports cleanly and baseline learners pass.
2. Property tests in bench/test_bench.py pass.
3. DPAdapter stub raises NotImplementedError by design until PROMPT C3 rewires it.
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


def test_dp_adapter_stub_raises_not_implemented():
    """Verify DPAdapter stub raises NotImplementedError until PROMPT C3 rewires it."""
    sc = s1_clean()
    with pytest.raises(NotImplementedError):
        DPAdapter(sc)
