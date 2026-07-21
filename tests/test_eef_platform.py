"""
Unit & Integration Tests for EEF v1.0 / MVF v1.0 Telemetry & Evaluation Platform
"""

import os
from pathlib import Path
from telemetry.events import (
    BeliefUpdatedEvent,
    MechanismCreatedEvent,
    MechanismReusedEvent,
    PredictionEvaluatedEvent,
    TheoryCreatedEvent,
)
from telemetry.eef_event_bus import TelemetryEventBus
from telemetry.eef_evaluator import EEFEvaluator
from telemetry.eef_store import EEFTelemetryStore


def test_eef_event_bus_and_evaluator():
    bus = TelemetryEventBus()
    
    events_captured = []

    def sample_listener(evt):
        events_captured.append(evt)

    bus.subscribe(sample_listener)

    # Publish events
    evt1 = TheoryCreatedEvent(
        run_id="test_run_001",
        step=1,
        theory_id="th_1",
        lineage_id="lin_1",
        thesis="Test thesis",
        mechanisms=["MECH_001"],
    )
    evt2 = MechanismReusedEvent(
        run_id="test_run_001",
        step=2,
        mechanism_id="MECH_001",
        theory_id="th_1",
        execution_ast_hash="ast_hash_123",
        utility_delta=0.05,
    )
    evt3 = PredictionEvaluatedEvent(
        run_id="test_run_001",
        step=2,
        probe_id="prb_1",
        predicted_direction="HIGHER",
        actual_direction="HIGHER",
        is_correct=True,
        stated_confidence=0.70,
    )

    bus.publish(evt1)
    bus.publish(evt2)
    bus.publish(evt3)

    bus.flush_and_stop()

    assert len(events_captured) >= 3

    # Evaluator Test
    evaluator = EEFEvaluator(run_id="test_run_001", market_name="RELIANCE")
    metrics = evaluator.evaluate_run(
        predictions_history=[{"stated_confidence": 0.70, "is_correct": True}],
        theories_history=[{"id": "th_1"}],
        mechanisms_history=[{"mechanism_id": "MECH_001", "times_reused": 1, "times_modified": 1, "prediction_helped": 1}],
        lessons_history=[],
        principles_history=[{"status": "active", "uses_count": 2, "predictions_helped": 2}],
        contradictions_history=[],
    )

    assert metrics["run_id"] == "test_run_001"
    assert "layer_metrics" in metrics
    assert metrics["evidence_level_achieved"] in ["LEVEL_1_OPERATIONAL", "LEVEL_3_EPISTEMIC", "LEVEL_4_MECHANISTIC"]
    assert "verdict" in metrics
    print("✓ EEF Platform Test Passed successfully!")


if __name__ == "__main__":
    test_eef_event_bus_and_evaluator()
