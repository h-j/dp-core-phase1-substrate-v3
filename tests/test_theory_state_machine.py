"""
Unit tests for core/theory_state_machine.py.
"""
import pytest

from core.event_bus import reset_event_bus
from core.theory_state_machine import (
    InvalidStateTransitionError,
    TheoryState,
    TheoryStateMachine,
    TheoryTransition,
)


@pytest.fixture(autouse=True)
def clean_event_bus():
    bus = reset_event_bus()
    yield bus
    bus.clear()


def test_initial_state():
    sm = TheoryStateMachine(initial_state=TheoryState.DRAFT, theory_id="TH_001")
    assert sm.state == TheoryState.DRAFT
    assert sm.theory_id == "TH_001"
    assert len(sm.history) == 1


def test_valid_lifecycle_flow():
    sm = TheoryStateMachine(initial_state=TheoryState.DRAFT, theory_id="TH_FLOW")

    # 1. Draft -> Candidate
    st1 = sm.transition(TheoryTransition.PROMOTE_TO_CANDIDATE, statement="Momentum persistence in trend", reason="Structured claim")
    assert st1 == TheoryState.CANDIDATE

    # 2. Candidate -> Active
    st2 = sm.transition(TheoryTransition.ACTIVATE, confidence=0.75, reason="Empirical validation passed")
    assert st2 == TheoryState.ACTIVE

    # 3. Active -> Weakening
    st3 = sm.transition(TheoryTransition.WEAKEN, confidence=0.40, contradiction_pressure=0.55, reason="High contradiction")
    assert st3 == TheoryState.WEAKENING

    # 4. Weakening -> Active (Recovery / Reinforce)
    st4 = sm.transition(TheoryTransition.REINFORCE, confidence=0.65, contradiction_pressure=0.20, reason="Contradiction resolved")
    assert st4 == TheoryState.ACTIVE

    # 5. Active -> Retired
    st5 = sm.transition(TheoryTransition.RETIRE, reason="Low confidence drop")
    assert st5 == TheoryState.RETIRED

    # 6. Retired -> Archived
    st6 = sm.transition(TheoryTransition.ARCHIVE, reason="Permanent cleanup")
    assert st6 == TheoryState.ARCHIVED


def test_invalid_transitions_raise_exception():
    sm = TheoryStateMachine(initial_state=TheoryState.DRAFT, theory_id="TH_INVALID")

    # Draft -> Weakening is illegal
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        sm.transition(TheoryTransition.WEAKEN)
    assert "Illegal transition" in str(exc_info.value)

    # Transition to Candidate first
    sm.transition(TheoryTransition.PROMOTE_TO_CANDIDATE, statement="Valid statement")
    sm.transition(TheoryTransition.ACTIVATE)
    sm.transition(TheoryTransition.RETIRE)
    assert sm.state == TheoryState.RETIRED

    # Retired -> Active directly is illegal
    with pytest.raises(InvalidStateTransitionError):
        sm.transition(TheoryTransition.ACTIVATE)

    # Transition to Archived
    sm.transition(TheoryTransition.ARCHIVE)
    assert sm.state == TheoryState.ARCHIVED

    # Archived -> Draft is illegal
    with pytest.raises(InvalidStateTransitionError):
        sm.transition(TheoryTransition.PROMOTE_TO_CANDIDATE, statement="New claim")


def test_promote_to_candidate_empty_statement_fails():
    sm = TheoryStateMachine(initial_state=TheoryState.DRAFT)
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        sm.transition(TheoryTransition.PROMOTE_TO_CANDIDATE, statement="   ")
    assert "statement is empty" in str(exc_info.value)


def test_revival_success_and_failure():
    sm = TheoryStateMachine(initial_state=TheoryState.RETIRED, theory_id="TH_REVIVE")

    # Revival fails with insufficient evidence and no regime match
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        sm.request_revival(evidence_support=0.20, regime_match=False)
    assert "Revival rejected" in str(exc_info.value)
    assert sm.state == TheoryState.RETIRED

    # Revival succeeds with evidence_support >= 0.50
    new_st = sm.request_revival(evidence_support=0.65, regime_match=False, reason="New empirical evidence")
    assert new_st == TheoryState.CANDIDATE

    # Re-activate
    sm.transition(TheoryTransition.ACTIVATE)
    assert sm.state == TheoryState.ACTIVE


def test_confidence_driven_transitions():
    sm = TheoryStateMachine(initial_state=TheoryState.ACTIVE, theory_id="TH_CONF")

    # Drop confidence -> transitions to WEAKENING
    st1 = sm.evaluate_confidence_transition(confidence=0.40, contradiction_pressure=0.55)
    assert st1 == TheoryState.WEAKENING

    # Repeated weakening drop below threshold -> RETIRED
    st2 = sm.evaluate_confidence_transition(confidence=0.20, contradiction_pressure=0.85)
    assert st2 == TheoryState.RETIRED
