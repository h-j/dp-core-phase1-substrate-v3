"""
Unit tests for ScoredConfidenceEngine — Beta posterior confidence evolution substrate.

Includes THE DECISIVE TEST asserting complete removal of text keyword influence from confidence evolution.
"""
import json
import pytest

from cognition.confidence.scored_confidence_engine import (
    ScoredConfidenceEngine,
    EvidenceLedgerRecord,
    LineageEvidenceLedger,
)
from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.reflection.reflection_event import ReflectionEvent
from cognition.schemas.validation.validation_event import ValidationEvent
from cognition.evaluation.llm_theory_evaluator import LLMTheoryEvaluator
from cognition.schemas.theory.theory import Theory


def test_the_decisive_test_no_text_keyword_influence():
    """
    THE DECISIVE TEST:
    Construct a reflection whose summary contains "strengthen", "confirmed", "validated", "uncertain"
    and a validation summary containing "increased", run a full evolve cycle with NO resolved terminal states;
    assert confidence is bit-identical before/after.
    """
    engine = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.01)

    initial_state = ConfidenceState(
        alpha=1.0,
        beta=1.0,
        empirical_confidence=0.5,
        regime_confidence=0.5,
        reflection_confidence=0.5,
        theoretical_coherence=0.5,
        contradiction_pressure=0.0,
    )

    reflection = ReflectionEvent(
        related_theory_id="TH_DECISIVE",
        reflection_summary="strengthen confirmed validated uncertain caution mixed limit contradict",
        confidence_impact="high",
    )

    validation = ValidationEvent(
        theory_id="TH_DECISIVE",
        validation_summary="increased momentum showed supported aligned confirmed",
        observed_behavior="price increased strongly opposite failed",
        expected_behavior="strengthen further",
        outcome="SUPPORTED",  # Will be ignored because no predicate_results or resolved terminal states are passed!
    )

    # Run full evolve cycle with NO resolved terminal states
    evolved_state = engine.evolve(
        confidence_state=initial_state,
        validation=validation,
        reflection=reflection,
        market_observation=None,
        contradiction_result={},
        day_idx=1,
        predicate_results=[],  # No resolved terminal states
    )

    # Before evolve: alpha=1.0, beta=1.0 -> confidence = 1.0 / 2.0 = 0.5
    # On day with no resolved terminal states, staleness decay (1 - 0.01) = 0.99
    # alpha=0.99, beta=0.99 -> confidence = 0.99 / (0.99 + 0.99) = 0.5
    # Therefore, empirical_confidence MUST be strictly bit-identical to prior empirical_confidence (0.5)!
    assert evolved_state.empirical_confidence == initial_state.empirical_confidence
    assert evolved_state.empirical_confidence == 0.5
    assert evolved_state.reflection_confidence == 0.5
    assert evolved_state.regime_confidence == 0.5


def test_beta_math_supported_outcome():
    """Verify SUPPORTED predicate outcome updates alpha -> alpha + 1.0."""
    engine = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.01)
    state = ConfidenceState(alpha=1.0, beta=1.0)

    result = engine.evolve(
        confidence_state=state,
        predicate_results=[{"outcome": "confirmed"}],
        day_idx=1,
    )

    assert result.alpha == 2.0
    assert result.beta == 1.0
    assert pytest.approx(result.empirical_confidence, 1e-5) == 2.0 / 3.0


def test_beta_math_falsify_weighting():
    """Verify CONTRADICTED predicate outcome updates beta -> beta + k_falsify (3.0)."""
    engine = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.01)
    state = ConfidenceState(alpha=1.0, beta=1.0)

    result = engine.evolve(
        confidence_state=state,
        predicate_results=[{"outcome": "rejected"}],
        day_idx=1,
    )

    assert result.alpha == 1.0
    assert result.beta == 4.0
    assert pytest.approx(result.empirical_confidence, 1e-5) == 1.0 / 5.0


def test_staleness_decay_increases_uncertainty():
    """Verify staleness decay decreases effective sample size and increases Beta variance / uncertainty."""
    engine = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.10)
    state = ConfidenceState(alpha=5.0, beta=5.0)
    initial_uncertainty = state.uncertainty

    result = engine.evolve(
        confidence_state=state,
        predicate_results=[],  # No resolved terminal states
        day_idx=1,
    )

    assert result.alpha == 4.5
    assert result.beta == 4.5
    # Variance of Beta(4.5, 4.5) > Variance of Beta(5, 5)
    assert result.uncertainty > initial_uncertainty


def test_contradiction_pressure_isolation():
    """Verify contradiction pressure is fed ONLY by numerical contradiction registry counts, never text."""
    engine = ScoredConfidenceEngine()
    state = ConfidenceState(contradiction_pressure=0.0)

    result = engine.evolve(
        confidence_state=state,
        contradiction_result={
            "new_contradictions": 2,
            "active_contradictions": 1,
            "resolved_contradictions": 0,
        },
        reflection=ReflectionEvent(
            related_theory_id="t-1",
            reflection_summary="Everything is wonderful and validated without contradiction",
            confidence_impact="neutral",
        ),
        day_idx=1,
    )

    # 2 * 0.14 + 1 * 0.09 = 0.37
    assert pytest.approx(result.contradiction_pressure, 1e-4) == 0.37


def test_transition_ledger_byte_stability():
    """Verify transition ledger records are byte-stable across identical runs."""
    engine1 = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.01)
    state1 = ConfidenceState(alpha=1.0, beta=1.0)
    engine1.evolve(state1, predicate_results=[{"outcome": "confirmed"}], day_idx=1)

    engine2 = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.01)
    state2 = ConfidenceState(alpha=1.0, beta=1.0)
    engine2.evolve(state2, predicate_results=[{"outcome": "confirmed"}], day_idx=1)

    ledger_json1 = json.dumps(engine1.ledger.to_list(), sort_keys=True)
    ledger_json2 = json.dumps(engine2.ledger.to_list(), sort_keys=True)

    assert ledger_json1 == ledger_json2
    assert "timestamp" not in ledger_json1
    assert "created_at" not in ledger_json1


def test_llm_theory_evaluator_severance():
    """Assert LLMTheoryEvaluator outputs attached to Theory objects do NOT alter confidence state."""
    evaluator = LLMTheoryEvaluator()
    theory = Theory(
        lineage_id="lineage-1",
        thesis="Test mechanism thesis",
        summary="Test mechanism summary",
        confidence_state=ConfidenceState(alpha=1.0, beta=1.0),
    )
    eval_result = evaluator.evaluate(theory)
    object.__setattr__(theory, "llm_evaluation", eval_result)

    engine = ScoredConfidenceEngine()
    state = ConfidenceState(alpha=1.0, beta=1.0)

    # Pass theory with llm_evaluation score of 0.5 to evolve
    result = engine.evolve(confidence_state=state, theory_usefulness=eval_result, day_idx=1)

    # Empirical confidence must remain determined purely by Beta posterior (0.5), unaffected by llm_evaluation
    assert result.empirical_confidence == 0.5


@pytest.mark.requires_postgres
def test_live_wiring_sanity_test():

    """Live Wiring Sanity Test: import replay_initialization, build executor, assert ScoredConfidenceEngine."""
    from market.replay.replay_engine import ReplayExecutor
    from market.replay.replay_initialization import initialize_flows

    executor = ReplayExecutor()
    initialize_flows(executor)

    assert isinstance(executor.confidence_engine, ScoredConfidenceEngine)

