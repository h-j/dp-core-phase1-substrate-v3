"""
Unit & Integration Tests for Synthworld Benchmark & DPAdapter (PROMPT E0b).

Verifies:
1. bench/ synthworld framework imports cleanly and baseline learners pass.
2. Trivial generator enumerates hypothesis space with exact set equality to baselines.
3. DPAdapter satisfies 3-method Learner protocol (observe, predict, beliefs).
4. Smoke test: 200-step S1 run completes for DPAdapter and produces consultation ledger.
5. S1, S2, S3, S4 benchmark scenarios execute successfully.
"""
from pathlib import Path
import pytest

from bench.synthworld.world import SynthWorldScenario
from bench.synthworld.learners import TruModalOracle, ElatraverianLearner, ContextualBayesianLearner
from bench.synthworld.dp_adapter import DPAdapter
from bench.synthworld.harness import BenchmarkHarness
from bench.synthworld.harness_init import get_learner, LEARNER_REGISTRY
from dp.observability.consultation_ledger import ConsultationLedger, set_active_consultation_ledger
from dp.observability.influence_trace import parse_consultation_ledger



def test_hypothesis_space_equality():
    """Verify DPAdapter enumerated hypothesis space equals baseline hypothesis space (assert set equality)."""
    scenario = SynthWorldScenario("S1")
    adapter = DPAdapter(scenario)
    baseline = ElatraverianLearner(scenario)

    baseline_space = set([(c, e) for c in baseline.causes for e in baseline.effects])
    adapter_space = set(adapter.hypothesis_space)

    assert adapter_space == baseline_space, f"Hypothesis space mismatch: {adapter_space} != {baseline_space}"


def test_learner_protocol_compliance():
    """Verify DPAdapter satisfies the 3-method Learner protocol."""
    scenario = SynthWorldScenario("S1")
    adapter = DPAdapter(scenario)

    events = scenario.generate_step(0)

    # 1. Predict
    predictions = adapter.predict(0, events)
    assert isinstance(predictions, dict)
    assert "e1" in predictions
    assert 0.0 <= predictions["e1"] <= 1.0

    # 2. Observe
    adapter.observe(0, events)

    # 3. Beliefs
    beliefs = adapter.beliefs()
    assert isinstance(beliefs, dict)
    assert ("c1", "e1") in beliefs
    assert 0.0 <= beliefs[("c1", "e1")] <= 1.0


def test_smoke_200_step_s1_run_and_consultation_ledger(tmp_path):
    """
    Smoke Test:
    Run 200-step S1 scenario with DPAdapter and verify:
    1. Run completes cleanly.
    2. Consultation ledger is produced with role='gate' entries.
    3. Brier score and discovery rate are recorded.
    """
    ledger_path = tmp_path / "consultation_ledger.jsonl"
    ledger = ConsultationLedger(output_path=ledger_path)
    set_active_consultation_ledger(ledger)

    scenario = SynthWorldScenario("S1", seed=42)
    adapter = DPAdapter(scenario)

    harness = BenchmarkHarness(scenario, steps=200)
    results = harness.run_learner(adapter)

    assert results["steps_run"] == 200
    assert "brier_score" in results
    assert "discovery_rate" in results
    assert results["discovery_rate"] >= 0.50

    # Verify consultation ledger entries
    assert ledger_path.exists()
    records = parse_consultation_ledger(ledger_path)
    gate_records = [r for r in records if r.get("kind") == "consultation" and r.get("role") == "gate"]
    assert len(gate_records) > 0, "Predict() must record consultation ledger entries with role='gate'"


def test_harness_init_registry():
    """Verify harness_init registers all learners including DPAdapter."""
    scenario = SynthWorldScenario("S1")
    assert "dp_adapter" in LEARNER_REGISTRY

    adapter = get_learner("dp_adapter", scenario)
    assert isinstance(adapter, DPAdapter)

    oracle = get_learner("oracle", scenario)
    assert isinstance(oracle, TruModalOracle)


@pytest.mark.parametrize("scenario_id", ["S1", "S2", "S3", "S4"])
def test_all_scenarios_run(scenario_id):
    """Verify all trap scenarios (S1-S4) execute with DPAdapter."""
    scenario = SynthWorldScenario(scenario_id, seed=100)
    adapter = DPAdapter(scenario)
    harness = BenchmarkHarness(scenario, steps=50)

    results = harness.run_learner(adapter)
    assert results["steps_run"] == 50
    assert 0.0 <= results["brier_score"] <= 1.0
