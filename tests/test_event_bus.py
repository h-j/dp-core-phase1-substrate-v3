"""
Unit tests for core/event_bus.py and domain event infrastructure.
"""
import logging
import time
from unittest.mock import MagicMock

import pytest

from core.event_bus import EventBus, get_event_bus, reset_event_bus
from core.events import (
    Event,
    MechanismGenerated,
    ObservationCreated,
    PredictionGenerated,
    ReflectionCompleted,
    TheoryCreated,
    TheoryRetired,
    TheoryUpdated,
)


@pytest.fixture(autouse=True)
def clean_event_bus():
    bus = reset_event_bus()
    yield bus
    bus.clear()


def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []

    def subscriber(evt: ObservationCreated):
        received.append(evt)

    bus.subscribe(ObservationCreated, subscriber)

    evt = ObservationCreated(
        date="2026-07-21",
        symbol="RELIANCE",
        ohlcv={"open": 100.0, "high": 105.0, "low": 99.0, "close": 102.0, "volume": 5000},
        derived={"trend_5d": "up"},
    )
    bus.publish(evt, publisher="test_publisher")

    assert len(received) == 1
    assert received[0].symbol == "RELIANCE"
    assert received[0].publisher == "test_publisher"


def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []

    def subscriber(evt: TheoryCreated):
        received.append(evt)

    bus.subscribe(TheoryCreated, subscriber)
    bus.unsubscribe(TheoryCreated, subscriber)

    evt = TheoryCreated(
        theory_id="TH_101",
        statement="Trend persistence holds in bullish regimes",
        confidence=0.85,
    )
    bus.publish(evt)

    assert len(received) == 0


def test_deterministic_synchronous_ordering():
    bus = EventBus()
    call_order = []

    def sub1(evt: Event):
        call_order.append("sub1")

    def sub2(evt: Event):
        call_order.append("sub2")

    def sub3(evt: Event):
        call_order.append("sub3")

    bus.subscribe(ReflectionCompleted, sub1)
    bus.subscribe(ReflectionCompleted, sub2)
    bus.subscribe(ReflectionCompleted, sub3)

    evt = ReflectionCompleted(reflection_id="REFL_01", insights=["Insight 1"])
    bus.publish(evt)

    assert call_order == ["sub1", "sub2", "sub3"]


def test_all_initial_domain_event_payloads():
    obs_evt = ObservationCreated(date="2026-01-01", symbol="TCS", ohlcv={}, derived={})
    mech_evt = MechanismGenerated(mechanism_id="M1", description="desc", confidence=0.7)
    th_create = TheoryCreated(theory_id="T1", statement="stmt", confidence=0.8)
    th_update = TheoryUpdated(theory_id="T1", old_confidence=0.8, new_confidence=0.9, reason="valid")
    th_retire = TheoryRetired(theory_id="T1", reason="falsified")
    refl_evt = ReflectionCompleted(reflection_id="R1", insights=["i1"])
    pred_evt = PredictionGenerated(prediction_id="P1", target_date="2026-01-02", predicted_direction="BULLISH", conviction=0.88)

    assert obs_evt.event_id.startswith("EVT_")
    assert mech_evt.confidence == 0.7
    assert th_create.confidence == 0.8
    assert th_update.new_confidence == 0.9
    assert th_retire.reason == "falsified"
    assert refl_evt.insights == ["i1"]
    assert pred_evt.conviction == 0.88


def test_debug_logging_output(caplog):
    caplog.set_level(logging.DEBUG)
    bus = EventBus(debug_logging=True)

    def slow_subscriber(evt: MechanismGenerated):
        time.sleep(0.005)

    bus.subscribe(MechanismGenerated, slow_subscriber)

    evt = MechanismGenerated(mechanism_id="M_TEST", description="test", confidence=0.65)
    bus.publish(evt, publisher="test_component")

    # Verify debug log produced showing event name, publisher, subscriber, and duration
    assert "[EventBus] Event: MechanismGenerated" in caplog.text
    assert "Publisher: test_component" in caplog.text
    assert "slow_subscriber" in caplog.text
    assert "Duration:" in caplog.text


def test_subscriber_exception_isolation(caplog):
    bus = EventBus()
    good_received = []

    def failing_subscriber(evt: TheoryRetired):
        raise ValueError("Simulated subscriber crash")

    def good_subscriber(evt: TheoryRetired):
        good_received.append(evt)

    bus.subscribe(TheoryRetired, failing_subscriber)
    bus.subscribe(TheoryRetired, good_subscriber)

    evt = TheoryRetired(theory_id="TH_BAD", reason="test")
    # Should not raise exception to publisher
    bus.publish(evt)

    assert len(good_received) == 1
    assert "Subscriber" in caplog.text and "failing_subscriber" in caplog.text and "failed processing event" in caplog.text
