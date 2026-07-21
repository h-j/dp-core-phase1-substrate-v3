"""
Unit tests for memory retrieval quality metrics and reasoning provenance.
"""
import pytest

from memory.provenance import (
    IgnoredCandidate,
    ReasoningProvenance,
    RetrievalDetail,
    RetrievalExplanation,
)
from memory.replay.regime_memory import (
    RegimeMemoryRecord,
    RegimeMemoryStore,
    RegimeSignature,
)
from market.replay.replay_analysis import ReplayAnalysisEngine


def test_retrieve_explainable_metrics_and_ignored_candidates():
    store = RegimeMemoryStore()

    # Persist two records
    sig1 = RegimeSignature(
        date="2023-01-01",
        trend="bullish",
        volatility_state="compressed",
        sentiment="positive",
        confidence_profile="high",
        contradiction_severity=0.10,
        active_theory_count=2,
    )
    store.persist(step=1, signature=sig1, active_theories=["TH_01"], contradictions=[], confidence=0.75)

    sig2 = RegimeSignature(
        date="2023-01-05",
        trend="bearish",
        volatility_state="expanded",
        sentiment="negative",
        confidence_profile="low",
        contradiction_severity=0.80,
        active_theory_count=1,
    )
    store.persist(step=5, signature=sig2, active_theories=["TH_02"], contradictions=[], confidence=0.40)

    # Query with signature highly similar to sig1
    query_sig = RegimeSignature(
        date="2023-01-10",
        trend="bullish",
        volatility_state="compressed",
        sentiment="positive",
        confidence_profile="high",
        contradiction_severity=0.10,
        active_theory_count=2,
    )
    
    matches, explanation = store.retrieve_explainable(
        signature=query_sig,
        current_contradictions=[],
        limit=3,
        min_similarity=0.50,
    )

    assert isinstance(explanation, RetrievalExplanation)
    assert explanation.retrieval_success is True
    assert len(explanation.retrieved_memories) >= 1

    top_retrieved = explanation.retrieved_memories[0]
    assert top_retrieved.ranking == 1
    assert top_retrieved.date == "2023-01-01"
    assert top_retrieved.similarity >= 0.50
    assert top_retrieved.recency_contribution >= 0.0
    assert top_retrieved.retrieval_score > 0.0
    assert len(top_retrieved.provenance_chain) >= 2

    # Ignored candidates should record sig2 if similarity < 0.50
    if len(matches) < 2:
        assert len(explanation.ignored_candidates) >= 1
        ignored = explanation.ignored_candidates[0]
        assert "below minimum threshold" in ignored.reason


def test_reasoning_provenance_structure():
    prov = ReasoningProvenance(
        observations_used=["OBS_2023-01-01", "OBS_2023-01-02"],
        mechanisms_used=["MECH_VOLUME_CONFIRMATION"],
        retrieved_memories=[{"date": "2023-01-01", "similarity": 0.85}],
        reflections_consulted=["Reflected high coherence"],
        validation_results_incorporated=["VAL_REC_1001"],
    )

    assert len(prov.observations_used) == 2
    assert "MECH_VOLUME_CONFIRMATION" in prov.mechanisms_used
    assert prov.retrieved_memories[0]["similarity"] == 0.85
    assert len(prov.reflections_consulted) == 1
    assert len(prov.validation_results_incorporated) == 1


def test_replay_analysis_engine_provenance_diagnostics():
    analysis = ReplayAnalysisEngine(market_name="TEST_MARKET")

    detail1 = RetrievalDetail(
        memory_id="MEM_2023-01-01",
        date="2023-01-01",
        retrieval_score=0.88,
        ranking=1,
        similarity=0.90,
        recency_contribution=0.80,
        usefulness_estimate=0.75,
        provenance_chain=["record_date:2023-01-01", "record_step:1"],
    )
    ignored1 = IgnoredCandidate(
        memory_id="MEM_2022-12-01",
        date="2022-12-01",
        similarity=0.30,
        reason="Similarity below threshold",
    )
    explanation = RetrievalExplanation(
        retrieved_memories=[detail1],
        ignored_candidates=[ignored1],
        retrieval_success=True,
        top_score=0.88,
    )

    analysis.record_retrieval_explanation(explanation)
    diag = analysis.get_memory_provenance_diagnostics()

    assert diag["total_queries"] == 1
    assert diag["successful_retrievals"] == 1
    assert diag["retrieval_hit_rate"] == 1.0
    assert diag["average_retrieval_score"] == 0.88
    assert diag["ignored_candidates_count"] == 1
    assert len(diag["top_retrieved_memories"]) == 1
    assert diag["provenance_graph_summary"]["nodes_tracked"] == 1
    assert diag["provenance_graph_summary"]["edges_tracked"] == 2
