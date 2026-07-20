"""
Phase 4: Tests for ConfidenceEvolutionEngine.

Uses proper schema objects and behavioral expectations derived from
the actual engine implementation. No external services required.
"""
import inspect
import pytest
from cognition.confidence.confidence_evolution_engine import ConfidenceEvolutionEngine
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
    return ConfidenceEvolutionEngine()


def _aligned_validation():
    """A validation that _validation_aligns() returns True for."""
    return ValidationEvent(
        theory_id="t-test",
        validation_summary="market showed strong support for the theory",
        observed_behavior="price increased strongly as expected",
        expected_behavior="price increase when FII buys",
        outcome="SUPPORTED",
    )


def _neutral_reflection():
    return ReflectionEvent(
        related_theory_id="t-test",
        reflection_summary="theory remains consistent with market structure",
        confidence_impact="neutral",
    )


def _evolve(state, outcome_score=None, aligned=True):
    validation = _aligned_validation() if aligned else ValidationEvent(
        theory_id="t-test",
        validation_summary="theory showed no support",
        observed_behavior="price failed to increase, declined instead",
        expected_behavior="price increase",
        outcome="CONTRADICTED",
    )
    return _engine().evolve(
        confidence_state=state,
        validation=validation,
        reflection=_neutral_reflection(),
        contradiction_result={
            "score": 0.0,
            "new_contradictions": 0,
            "resolved_contradictions": 0,
            "active_contradictions": 0,
        },
        outcome_validation_result=(
            {"validation_score": outcome_score} if outcome_score is not None else None
        ),
        lineage_event={},
        theory_usefulness={"score": 0.5},
    )


def test_aligned_validation_does_not_decrease_empirical():
    """With aligned validation and neutral outcome, empirical must not decrease."""
    state = _state(empirical=0.5)
    result = _evolve(state, aligned=True)
    assert result.empirical_confidence >= 0.45, (
        "Aligned validation should not substantially reduce empirical_confidence"
    )


def test_contradicted_validation_reduces_empirical():
    """A validation with failed/declined observed_behavior should reduce empirical."""
    state = _state(empirical=0.5)
    result = _evolve(state, aligned=False)
    assert result.empirical_confidence < 0.5, (
        "Contradicted validation should reduce empirical_confidence"
    )


def test_empirical_confidence_bounded_above():
    state = _state(empirical=0.99)
    result = _evolve(state, outcome_score=1.0, aligned=True)
    assert result.empirical_confidence <= 1.0


def test_empirical_confidence_bounded_below():
    state = _state(empirical=0.01)
    result = _evolve(state, outcome_score=0.0, aligned=False)
    assert result.empirical_confidence >= 0.0


def test_regime_confidence_bounded():
    state = _state(regime=0.01)
    result = _evolve(state, aligned=False)
    assert result.regime_confidence >= 0.0
    state2 = _state(regime=0.99)
    result2 = _evolve(state2, aligned=True)
    assert result2.regime_confidence <= 1.0


def test_new_contradictions_penalize_coherence():
    state = _state(coherence=0.5)
    result = _engine().evolve(
        confidence_state=state,
        validation=_aligned_validation(),
        reflection=_neutral_reflection(),
        contradiction_result={
            "score": 0.0,
            "new_contradictions": 5,
            "resolved_contradictions": 0,
            "active_contradictions": 5,
        },
        outcome_validation_result=None,
        lineage_event={},
        theory_usefulness={"score": 0.5},
    )
    assert result.theoretical_coherence < 0.5, (
        "5 new contradictions should penalize theoretical_coherence"
    )


def test_evolve_returns_confidence_state():
    state = _state()
    result = _evolve(state)
    assert isinstance(result, ConfidenceState), (
        "evolve() must return a ConfidenceState object"
    )


def test_no_trade_source_in_evolve_signature():
    """Regression: evolve() must not accept any trade-sourced parameter."""
    sig = inspect.signature(ConfidenceEvolutionEngine.evolve)
    params = set(sig.parameters.keys())
    forbidden = {"pnl", "conviction_score", "decision_result", "capital", "last_rec"}
    overlap = params & forbidden
    assert not overlap, (
        f"evolve() has forbidden trade-sourced parameters: {overlap}. "
        "See AGENTS.md §'Observer-Only Modules'."
    )
