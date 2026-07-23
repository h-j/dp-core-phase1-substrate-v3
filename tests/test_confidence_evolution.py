"""
Phase 4: Tests for ScoredConfidenceEngine.
"""
import inspect
import pytest
from cognition.confidence.scored_confidence_engine import ScoredConfidenceEngine
from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.validation.validation_event import ValidationEvent
from cognition.schemas.reflection.reflection_event import ReflectionEvent


def _state(empirical=0.5, regime=0.5, coherence=0.5):
    return ConfidenceState(
        empirical_confidence=empirical,
        regime_confidence=regime,
        theoretical_coherence=coherence,
    )


def _engine():
    return ScoredConfidenceEngine()


def test_aligned_validation_does_not_decrease_empirical():
    state = _state(empirical=0.5)
    result = _engine().evolve(
        confidence_state=state,
        predicate_results=[{"outcome": "supported"}],
    )
    assert result.empirical_confidence > 0.5, (
        "Supported predicate outcome should increase empirical_confidence"
    )


def test_contradicted_validation_reduces_empirical():
    state = _state(empirical=0.5)
    result = _engine().evolve(
        confidence_state=state,
        predicate_results=[{"outcome": "contradicted"}],
    )
    assert result.empirical_confidence < 0.5, (
        "Contradicted predicate outcome should reduce empirical_confidence"
    )


def test_empirical_confidence_bounded_above():
    state = _state(empirical=0.99)
    result = _engine().evolve(state, predicate_results=[{"outcome": "supported"}])
    assert result.empirical_confidence <= 1.0


def test_empirical_confidence_bounded_below():
    state = _state(empirical=0.01)
    result = _engine().evolve(state, predicate_results=[{"outcome": "contradicted"}])
    assert result.empirical_confidence >= 0.0


def test_new_contradictions_penalize_coherence():
    state = _state(coherence=0.5)
    result = _engine().evolve(
        confidence_state=state,
        contradiction_result={
            "score": 0.0,
            "new_contradictions": 5,
            "resolved_contradictions": 0,
            "active_contradictions": 5,
        },
    )
    assert result.theoretical_coherence < 0.5, (
        "5 new contradictions should penalize theoretical_coherence"
    )


def test_evolve_returns_confidence_state():
    state = _state()
    result = _engine().evolve(state)
    assert isinstance(result, ConfidenceState), (
        "evolve() must return a ConfidenceState object"
    )


def test_no_trade_source_in_evolve_signature():
    """Regression: evolve() must not accept any trade-sourced parameter."""
    sig = inspect.signature(ScoredConfidenceEngine.evolve)
    params = set(sig.parameters.keys())
    forbidden = {"pnl", "conviction_score", "decision_result", "capital", "last_rec"}
    overlap = params & forbidden
    assert not overlap, (
        f"evolve() has forbidden trade-sourced parameters: {overlap}. "
        "See AGENTS.md §'Observer-Only Modules'."
    )

