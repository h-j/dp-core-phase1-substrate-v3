"""
End-to-End Replay Determinism Verification Test Suite.

Verifies that consecutive replay runs with identical inputs yield 100% identical outputs,
confidence evolution reports, predicate evaluations, contradiction graph statistics, and diagnostics.
"""
import pytest

from cognition.contradiction import ContradictionGraph, ContradictionResolver
from cognition.epistemics.confidence_engine import EpistemicConfidenceEngine
from core.theory_state_machine import TheoryState, TheoryStateMachine, TheoryTransition
from diagnostics.collectors import EpistemicEventCollector
from diagnostics.report_generator import ResearchReportGenerator
from memory.provenance import ReasoningProvenance
from validation.predicate_validation_engine import PredicateValidationEngine


class MockObservation:
    def __init__(self, date_str: str = "2023-01-01"):
        self.date_str = date_str
        self.descriptors = ["passive_absorption", "compressed_range"]
        self.regime_descriptor = "compressed"


class MockTheory:
    def __init__(self, theory_id: str = "TH_DET_01", summary: str = "Price closes higher in bullish regime"):
        self.id = theory_id
        self.summary = summary
        self.confidence = 0.50


def run_simulated_replay():
    """Runs a multi-step simulated replay pipeline and collects diagnostic outputs."""
    collector = EpistemicEventCollector()
    pred_engine = PredicateValidationEngine()
    epistemic_engine = EpistemicConfidenceEngine()
    contradiction_graph = ContradictionGraph()
    contradiction_resolver = ContradictionResolver()
    state_machine = TheoryStateMachine(initial_state=TheoryState.DRAFT, theory_id="TH_DET_01")

    # Step 1: Observation & Theory Creation
    obs1 = MockObservation("2023-01-01")
    collector.record_observation(obs1.date_str, obs1.regime_descriptor, obs1.descriptors)

    th1 = MockTheory("TH_DET_01", "Price closes higher in bullish regime")
    state_machine.transition(TheoryTransition.PROMOTE_TO_CANDIDATE, statement=th1.summary)
    state_machine.transition(TheoryTransition.ACTIVATE)
    collector.record_theory_created(th1.id, th1.summary, th1.confidence)

    # Form Predicate
    pred = pred_engine.form_predicate(theory=th1, step=1, evaluation_window=1)

    # Step 2: Evaluation & Confidence Update
    obs_data2 = {"derived": {"daily_return_pct": 1.50}}
    p_evals = pred_engine.evaluate_pending_predicates(current_step=2, obs_data=obs_data2)
    for pe in p_evals:
        collector.record_predicate_evaluation(pe)

    new_conf, report = epistemic_engine.update_confidence(
        theory=th1,
        evidence=0.85,
        prediction_results={"validation_score": 0.80, "correct": True},
    )
    th1.confidence = new_conf
    collector.record_confidence_report(report)

    # Step 3: Contradiction handling
    th2 = MockTheory("TH_DET_02", "Price closes lower in bearish regime")
    contradiction_graph.add_contradiction(
        source_theory_id=th1.id,
        target_theory_id=th2.id,
        contradiction_type="DIRECTIONAL",
        supporting_evidence=["Opposing directional predictions"],
        confidence=0.70,
        step=2,
    )
    theory_ctx = {
        th1.id: {"confidence": 0.70, "prediction_score": 0.80},
        th2.id: {"confidence": 0.30, "prediction_score": 0.20},
    }
    resolved = contradiction_resolver.resolve_conflicts(contradiction_graph, theory_context=theory_ctx, current_step=3)
    for r in resolved:
        collector.record_contradiction(r.source_theory_id, r.target_theory_id, r.contradiction_type, r.status.value)

    # Generate Research Report
    generator = ResearchReportGenerator()
    report_dict = generator.generate_report_dict(collector)
    graph_stats = contradiction_graph.get_graph_statistics()
    pred_stats = pred_engine.get_diagnostics_summary()

    return {
        "report_dict": report_dict,
        "graph_stats": graph_stats,
        "pred_stats": pred_stats,
        "final_confidence": new_conf,
        "state_history": [h["to_state"] for h in state_machine.history],
        "confidence_justification": report.final_justification,
    }


def test_consecutive_replay_determinism():
    """Verify 100% output identity across consecutive runs."""
    run1 = run_simulated_replay()
    run2 = run_simulated_replay()

    # 1. Final Confidence & Justification
    assert run1["final_confidence"] == run2["final_confidence"]
    assert run1["confidence_justification"] == run2["confidence_justification"]

    # 2. State Machine History
    assert run1["state_history"] == run2["state_history"]

    # 3. Predicate Engine Diagnostics
    assert run1["pred_stats"] == run2["pred_stats"]

    # 4. Contradiction Graph Statistics
    assert run1["graph_stats"] == run2["graph_stats"]

    # 5. Full Research Report Dictionary
    assert run1["report_dict"] == run2["report_dict"]
