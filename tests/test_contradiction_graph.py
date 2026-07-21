"""
Unit tests for cognition/contradiction/contradiction_graph.py and contradiction_resolver.py.
"""
import pytest

from cognition.contradiction import (
    ContradictionEdge,
    ContradictionGraph,
    ContradictionResolver,
    ContradictionStatus,
)


def test_contradiction_graph_node_and_edge_management():
    graph = ContradictionGraph()

    graph.add_theory_node("TH_A", {"summary": "Bullish trend thesis"})
    graph.add_theory_node("TH_B", {"summary": "Bearish trend thesis"})

    edge = graph.add_contradiction(
        source_theory_id="TH_A",
        target_theory_id="TH_B",
        contradiction_type="DIRECTIONAL",
        supporting_evidence=["Opposing trend signals"],
        confidence=0.75,
        step=1,
    )

    assert edge.id.startswith("CONTR_")
    assert edge.source_theory_id == "TH_A"
    assert edge.target_theory_id == "TH_B"
    assert edge.status == ContradictionStatus.ACTIVE

    # Competing hypotheses retrieval
    competing_a = graph.get_competing_hypotheses("TH_A")
    assert "TH_B" in competing_a

    competing_b = graph.get_competing_hypotheses("TH_B")
    assert "TH_A" in competing_b

    # Active conflicts query
    active = graph.get_active_contradictions()
    assert len(active) == 1
    assert active[0].id == edge.id


def test_contradiction_resolver_evaluates_and_resolves():
    graph = ContradictionGraph()

    graph.add_contradiction(
        source_theory_id="TH_STRONG",
        target_theory_id="TH_WEAK",
        contradiction_type="EMPIRICAL",
        supporting_evidence=["Divergent predictions"],
        step=1,
    )

    theory_context = {
        "TH_STRONG": {
            "confidence": 0.85,
            "prediction_score": 0.80,
            "validation_score": 0.90,
            "reuse_score": 0.70,
            "reflection_score": 0.85,
        },
        "TH_WEAK": {
            "confidence": 0.35,
            "prediction_score": 0.30,
            "validation_score": 0.25,
            "reuse_score": 0.10,
            "reflection_score": 0.40,
        },
    }

    resolver = ContradictionResolver(resolution_threshold=0.15)
    resolved = resolver.resolve_conflicts(graph, theory_context=theory_context, current_step=2)

    assert len(resolved) == 1
    res_edge = resolved[0]
    assert res_edge.status == ContradictionStatus.RESOLVED
    assert res_edge.winning_theory_id == "TH_STRONG"
    assert "outperformed" in res_edge.resolution_notes

    # Verify both nodes remain in the graph (competing hypotheses preserved)
    stats = graph.get_graph_statistics()
    assert stats["total_contradictions"] == 1
    assert stats["active_conflicts"] == 0
    assert stats["resolved_conflicts"] == 1
    assert stats["node_count"] == 2


def test_pending_investigation_transition():
    graph = ContradictionGraph()

    graph.add_contradiction(
        source_theory_id="TH_EVEN_1",
        target_theory_id="TH_EVEN_2",
        contradiction_type="STRUCTURAL",
        step=1,
    )

    # Identical theory scores (diff < threshold)
    theory_context = {
        "TH_EVEN_1": {"confidence": 0.50, "prediction_score": 0.50},
        "TH_EVEN_2": {"confidence": 0.50, "prediction_score": 0.50},
    }

    resolver = ContradictionResolver(resolution_threshold=0.15)
    
    # At step 2 -> unresolved and still active
    res_step2 = resolver.resolve_conflicts(graph, theory_context=theory_context, current_step=2)
    assert len(res_step2) == 0

    # At step 7 (> 5 steps elapsed) -> transitions to PENDING_INVESTIGATION
    res_step7 = resolver.resolve_conflicts(graph, theory_context=theory_context, current_step=7)
    assert len(res_step7) == 1
    assert res_step7[0].status == ContradictionStatus.PENDING_INVESTIGATION

    stats = graph.get_graph_statistics()
    assert stats["pending_investigation_conflicts"] == 1
