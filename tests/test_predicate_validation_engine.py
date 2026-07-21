"""
Unit tests for validation/predicate_validation_engine.py.
"""
import pytest

from cognition.epistemics.confidence_engine import EpistemicConfidenceEngine
from validation.predicate_validation_engine import (
    Predicate,
    PredicateEvaluationResult,
    PredicateOutcome,
    PredicateStatus,
    PredicateValidationEngine,
)


class MockTheory:
    def __init__(self, theory_id: str = "TH_PRED_01", summary: str = "Price closes higher in bullish regime"):
        self.id = theory_id
        self.summary = summary


def test_form_and_store_predicate():
    engine = PredicateValidationEngine()
    theory = MockTheory(theory_id="TH_100", summary="Market is in bullish regime with higher returns")

    pred = engine.form_predicate(theory=theory, step=2, evaluation_window=1)

    assert pred.id.startswith("PRED_VAL_")
    assert pred.theory_id == "TH_100"
    assert pred.created_at_step == 2
    assert pred.evaluation_window == 1
    assert pred.status == PredicateStatus.PENDING
    assert pred.condition["operator"] == ">="


def test_predicate_evaluation_confirmed():
    engine = PredicateValidationEngine()
    theory = MockTheory(theory_id="TH_CONFIRMED")
    pred = engine.form_predicate(theory=theory, step=1, evaluation_window=1)

    obs_data = {"derived": {"daily_return_pct": 1.25}}
    
    # At step 1 -> not matured yet (target step is 1 + 1 = 2)
    res_immature = engine.evaluate_pending_predicates(current_step=1, obs_data=obs_data)
    assert len(res_immature) == 0

    # At step 2 -> matures and evaluates
    res_matured = engine.evaluate_pending_predicates(current_step=2, obs_data=obs_data)
    assert len(res_matured) == 1
    eval_res = res_matured[0]
    assert eval_res.outcome == PredicateOutcome.CONFIRMED
    assert eval_res.observed_value == 1.25
    assert eval_res.confidence_impact > 0.0
    assert pred.status == PredicateStatus.EVALUATED


def test_predicate_evaluation_rejected():
    engine = PredicateValidationEngine()
    theory = MockTheory(theory_id="TH_REJECTED")
    pred = engine.form_predicate(
        theory=theory,
        step=5,
        evaluation_window=1,
        condition_override={"metric": "daily_return_pct", "operator": ">=", "threshold": 2.0},
    )

    obs_data = {"derived": {"daily_return_pct": -1.50}}
    results = engine.evaluate_pending_predicates(current_step=6, obs_data=obs_data)

    assert len(results) == 1
    assert results[0].outcome == PredicateOutcome.REJECTED
    assert results[0].confidence_impact < 0.0


def test_predicate_evaluation_insufficient_evidence():
    engine = PredicateValidationEngine()
    theory = MockTheory(theory_id="TH_MISSING")
    engine.form_predicate(
        theory=theory,
        step=0,
        evaluation_window=1,
        condition_override={"metric": "non_existent_metric", "operator": "==", "threshold": "test"},
    )

    obs_data = {"derived": {}}
    results = engine.evaluate_pending_predicates(current_step=1, obs_data=obs_data)

    assert len(results) == 1
    assert results[0].outcome == PredicateOutcome.INSUFFICIENT_EVIDENCE
    assert "not available" in results[0].justification


def test_diagnostics_summary():
    engine = PredicateValidationEngine()

    th1 = MockTheory("TH_1", "bullish claim")
    th2 = MockTheory("TH_2", "bearish claim")

    p1 = engine.form_predicate(th1, step=0, evaluation_window=1, condition_override={"metric": "daily_return_pct", "operator": ">", "threshold": 0.0})
    p2 = engine.form_predicate(th2, step=0, evaluation_window=1, condition_override={"metric": "daily_return_pct", "operator": "<", "threshold": -5.0})

    # Evaluate at step 1
    obs_data = {"derived": {"daily_return_pct": 1.5}}
    engine.evaluate_pending_predicates(current_step=1, obs_data=obs_data)

    diag = engine.get_diagnostics_summary()

    assert diag["predicates_evaluated"] == 2
    assert diag["confirmed_count"] == 1
    assert diag["rejected_count"] == 1
    assert diag["success_rate"] == 0.5
    assert len(diag["failures"]) == 1
    assert diag["failures"][0]["theory_id"] == "TH_2"


def test_epistemic_confidence_engine_consumes_predicate_outcome():
    epistemic_engine = EpistemicConfidenceEngine()
    
    class ConfTheory:
        def __init__(self):
            self.id = "TH_PRED_CONF"
            self.confidence = 0.50

    theory = ConfTheory()
    
    # Confirmed outcome feeds positive empirical evidence
    conf_boost, report = epistemic_engine.update_confidence(
        theory=theory,
        evidence=0.85,
    )
    assert conf_boost > 0.50

    # Rejected outcome feeds negative empirical evidence
    conf_drop, report_drop = epistemic_engine.update_confidence(
        theory=theory,
        evidence=0.20,
    )
    assert conf_drop < 0.50
