from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from cognition.schemas.knowledge.evidence_gap import EvidenceGap
from cognition.schemas.knowledge.principle import (FalsifiablePrediction,
                                                   Principle, PrincipleStatus)
from flows.knowledge_flow.knowledge_compression_engine import \
    KnowledgeCompressionEngine
from memory.knowledge.knowledge_repository import KnowledgeRepository


def test_evidence_gap_serialization():
    gap = EvidenceGap(
        id=str(uuid4()),
        open_question_id="oq_123",
        missing_evidence="Volume participation rates",
        candidate_data_source="NSE Client Data",
        expected_explanatory_value="To validate participation confirmation bias",
        priority="HIGH",
    )
    data = gap.to_dict()
    assert data["open_question_id"] == "oq_123"
    assert data["priority"] == "HIGH"

    loaded = EvidenceGap.from_dict(data)
    assert loaded.missing_evidence == "Volume participation rates"
    assert loaded.id == gap.id


def test_principle_usefulness_score():
    p = Principle(
        id=str(uuid4()),
        statement="Test principle",
        created_at_step=0,
        uses_count=0,
        predictions_helped=0,
        predictions_harmed=0,
    )
    assert p.usefulness_score == 0.0

    p.uses_count = 5
    p.predictions_helped = 4
    p.predictions_harmed = 1
    # score = (4 - 1)/5 + 0.05 * 5 = 3/5 + 0.25 = 0.60 + 0.25 = 0.85
    assert pytest.approx(p.usefulness_score, 0.01) == 0.85


def test_knowledge_repository_evidence_gaps(tmp_path):
    repo = KnowledgeRepository(base_path=tmp_path)
    gap = EvidenceGap(
        id=str(uuid4()),
        open_question_id="oq_456",
        missing_evidence="Sector rotation flows",
        candidate_data_source="Sector index correlations",
        expected_explanatory_value="Resolve sector attribution errors",
        priority="MEDIUM",
    )
    repo.save_evidence_gap(gap)

    # Reload and test list
    repo2 = KnowledgeRepository(base_path=tmp_path)
    gaps = repo2.list_evidence_gaps()
    assert len(gaps) == 1
    assert gaps[0].open_question_id == "oq_456"


def test_evidence_driven_retirement():
    engine = KnowledgeCompressionEngine()

    fp1 = FalsifiablePrediction(
        id=str(uuid4()),
        target_component="trend_persistence",
        expected_status="failed",
        applicability_filter={"regime_subtype": "neutral"},
    )

    fp2 = FalsifiablePrediction(
        id=str(uuid4()),
        target_component="volume_state",
        expected_status="passed",
        applicability_filter={"regime_subtype": "neutral"},
    )

    # Create a principle with low usefulness score and minimum matches
    p1 = Principle(
        id=str(uuid4()),
        statement="Poorly performing principle",
        status=PrincipleStatus.ACTIVE,
        created_at_step=0,
        uses_count=4,
        predictions_helped=1,
        predictions_harmed=3,  # usefulness_score = (1-3)/4 + 0.05*4 = -0.50 + 0.20 = -0.30 < 0.20
        support_count=1,
        contradiction_count=4,  # total validation support = 5 >= 5
        falsifiable_predictions=[fp1],
    )

    # Create a principle with high usefulness score
    p2 = Principle(
        id=str(uuid4()),
        statement="High performing principle",
        status=PrincipleStatus.ACTIVE,
        created_at_step=0,
        uses_count=4,
        predictions_helped=4,
        predictions_harmed=0,  # usefulness_score = 4/4 + 0.05*4 = 1.20 > 0.20
        support_count=4,
        contradiction_count=0,
        falsifiable_predictions=[fp2],
    )

    principles = [p1, p2]
    history = [{"date": "2026-06-19", "actual_direction": "higher"}]

    reconciled, stats = engine.reconcile_knowledge(
        principles=principles, prediction_history=history, open_questions=[], step=5
    )

    p1_rec = next(p for p in reconciled if p.id == p1.id)
    p2_rec = next(p for p in reconciled if p.id == p2.id)

    assert p1_rec.status == PrincipleStatus.RETIRED
    assert p2_rec.status == PrincipleStatus.ACTIVE
