"""
Test No-Lookahead Data Isolation for Edge Test Harness.

Verifies that a probe theory created or activated by day t+1 data does NOT affect day t signal evaluation.
"""
from dataclasses import dataclass
from typing import Any, Dict
import pytest

from experiments.edge_test.harness import evaluate_mechanical_signal_for_day


@dataclass
class MockTheory:
    id: str
    confidence: float
    directional_commitment: int
    active_on_days: Dict[str, bool]

    def scope_predicate(self, instrument: str, day: int) -> bool:
        return True

    def activation_predicate(self, instrument: str, day: int) -> bool:
        return self.active_on_days.get(f"{instrument}_{day}", False)

    @property
    def fallback_payload(self):
        class Payload:
            def __init__(self, d):
                self.directional_commitment = d
        return Payload(self.directional_commitment)


def test_no_lookahead_probe_isolation():
    instrument = "RELIANCE"
    day_t = 5
    day_t_plus_1 = 6

    # 1. Existing established theory active on day t
    established_t = MockTheory(
        id="TH_ESTABLISHED_01",
        confidence=0.85,
        directional_commitment=+1,
        active_on_days={f"{instrument}_{day_t}": True, f"{instrument}_{day_t_plus_1}": True},
    )

    # 2. Probe theory activated strictly by day t+1 data
    probe_t_plus_1 = MockTheory(
        id="TH_PROBE_FUTURE_02",
        confidence=0.95,
        directional_commitment=-1,
        active_on_days={f"{instrument}_{day_t}": False, f"{instrument}_{day_t_plus_1}": True},
    )

    theories_at_t = [established_t, probe_t_plus_1]

    # Evaluate signal for day t
    pos_t, weighted_sum_t, fired_ids_t = evaluate_mechanical_signal_for_day(
        theories=theories_at_t,
        instrument_id=instrument,
        day_t=day_t,
    )

    # Day t signal must reflect ONLY established_t (+1), ignoring probe_t_plus_1 (-1)
    assert pos_t == +1
    assert weighted_sum_t == 0.85
    assert fired_ids_t == ["TH_ESTABLISHED_01"]

    # Evaluate signal for day t+1
    pos_t1, weighted_sum_t1, fired_ids_t1 = evaluate_mechanical_signal_for_day(
        theories=theories_at_t,
        instrument_id=instrument,
        day_t=day_t_plus_1,
    )

    # Day t+1 signal incorporates both established_t (+1 @ 0.85) and probe_t_plus_1 (-1 @ 0.95) -> -0.10 -> Flat (0)
    assert pos_t1 == 0
    assert abs(weighted_sum_t1 - (-0.10)) < 1e-5
    assert set(fired_ids_t1) == {"TH_ESTABLISHED_01", "TH_PROBE_FUTURE_02"}
