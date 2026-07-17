from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd
import pytest

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from cognition.schemas.proposition.validation_record import ValidationRecord
from cognition.schemas.validation.belief_state import (BeliefState,
                                                       BeliefTransitionEvent)
from flows.proposition_flow.belief_dynamics_engine import BeliefDynamicsEngine
from flows.proposition_flow.pattern_consolidation_engine import \
    PatternConsolidationEngine
from memory.relational.repositories.belief_state_repository import \
    BeliefStateRepository
from memory.relational.repositories.compiled_proposition_repository import \
    CompiledPropositionRepository
from memory.relational.repositories.validation_record_repository import \
    ValidationRecordRepository


@pytest.fixture
def mock_history():
    data = {
        "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
        "close": [100.0, 102.0, 101.0, 104.0, 105.0],
        "delivery_pct_5d": [
            0.45,
            0.47,
            0.42,
            0.49,
            0.95,
        ],  # includes an outlier at the end
    }
    return pd.DataFrame(data)


def test_belief_dynamics_math_supported(mock_history):
    repo = BeliefStateRepository()
    engine = BeliefDynamicsEngine(belief_repo=repo)

    lineage_id = f"lineage_test_{uuid4().hex[:8]}"
    prop = CompiledProposition(
        id=str(uuid4()),
        theory_id=str(uuid4()),
        lineage_id=lineage_id,
        trigger_definition={"field": "delivery_pct_5d"},
        target_definition={"field": "close"},
        compilation_status="SUCCESS",
        replay_step=1,
    )

    val_rec = ValidationRecord(
        id=str(uuid4()),
        proposition_id=prop.id,
        canonical_proposition_id=str(uuid4()),
        theory_id=prop.theory_id,
        lineage_id=lineage_id,
        replay_step=1,
        validation_state="SUPPORTED",
        confidence_before=0.5,
        confidence_after=0.5,
        confidence_delta=0.0,
        regime="neutral",
        grounding_version="1.0.0",
        compiler_version="1.0.0",
        validation_engine_version="1.0.0",
    )

    # 1. Run dynamic update
    event = engine.process_validation(
        val_record=val_rec, compiled_prop=prop, history_df=mock_history, current_step=1
    )

    assert event.lineage_id == lineage_id
    assert event.confidence_after > 0.50
    assert event.uncertainty_after < 0.50

    # Fetch from db to verify persistence
    state = repo.get_belief_state_by_lineage(lineage_id)
    assert state is not None
    assert state.confidence == event.confidence_after
    assert state.uncertainty == event.uncertainty_after


def test_belief_dynamics_math_contradicted(mock_history):
    repo = BeliefStateRepository()
    engine = BeliefDynamicsEngine(belief_repo=repo)

    lineage_id = f"lineage_test_{uuid4().hex[:8]}"
    prop = CompiledProposition(
        id=str(uuid4()),
        theory_id=str(uuid4()),
        lineage_id=lineage_id,
        trigger_definition={"field": "delivery_pct_5d"},
        target_definition={"field": "close"},
        compilation_status="SUCCESS",
        replay_step=1,
    )

    val_rec = ValidationRecord(
        id=str(uuid4()),
        proposition_id=prop.id,
        canonical_proposition_id=str(uuid4()),
        theory_id=prop.theory_id,
        lineage_id=lineage_id,
        replay_step=1,
        validation_state="CONTRADICTED",
        confidence_before=0.5,
        confidence_after=0.5,
        confidence_delta=0.0,
        regime="neutral",
        grounding_version="1.0.0",
        compiler_version="1.0.0",
        validation_engine_version="1.0.0",
    )

    event = engine.process_validation(
        val_record=val_rec, compiled_prop=prop, history_df=mock_history, current_step=1
    )

    assert event.confidence_after < 0.50
    assert event.uncertainty_after > 0.50


def test_pattern_consolidation_nomination(mock_history):
    belief_repo = BeliefStateRepository()
    val_repo = ValidationRecordRepository()
    prop_repo = CompiledPropositionRepository()

    lineage_id = f"lineage_test_{uuid4().hex[:8]}"

    # Pre-populate some validation records
    for i in range(1, 5):
        val_rec = ValidationRecord(
            id=str(uuid4()),
            proposition_id=str(uuid4()),
            canonical_proposition_id=str(uuid4()),
            theory_id=str(uuid4()),
            lineage_id=lineage_id,
            replay_step=i,
            validation_state="SUPPORTED",
            confidence_before=0.5,
            confidence_after=0.5,
            confidence_delta=0.0,
            regime="neutral",
            grounding_version="1.0.0",
            compiler_version="1.0.0",
            validation_engine_version="1.0.0",
        )
        val_repo.save(val_rec)

    prop = CompiledProposition(
        id=str(uuid4()),
        theory_id=str(uuid4()),
        lineage_id=lineage_id,
        trigger_definition={"field": "delivery_pct_5d"},
        target_definition={"field": "close"},
        compilation_status="SUCCESS",
        replay_step=1,
    )
    prop_repo.save(prop)

    # Establish belief state
    belief = BeliefState(
        lineage_id=lineage_id,
        active_theory_id=prop.theory_id,
        confidence=0.85,
        uncertainty=0.25,
        status="ACTIVE",
    )
    belief_repo.save_belief_state(belief)

    # Run Pattern Consolidation
    consolidator = PatternConsolidationEngine(
        min_validations=3,
        min_temporal_span=3,
        min_confidence=0.70,
        max_uncertainty=0.40,
        min_success_rate=0.70,
        belief_repo=belief_repo,
        val_record_repo=val_repo,
        comp_prop_repo=prop_repo,
    )

    nominations = consolidator.consolidate_patterns(mock_history, current_step=4)
    nom = next((n for n in nominations if lineage_id in n["lineage_ids"]), None)
    assert nom is not None
    assert nom["success_rate"] == 1.0
