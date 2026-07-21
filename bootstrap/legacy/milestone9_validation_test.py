from datetime import datetime, timezone

import pandas as pd
import pytest

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from cognition.schemas.proposition.validation_record import ValidationRecord
from flows.proposition_flow.validation_engine import ValidationEngine
from memory.relational.init_db import Base, engine
from memory.relational.repositories.validation_record_repository import \
    ValidationRecordRepository


@pytest.fixture(autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup after test if needed


def test_validation_engine_untriggered():
    engine_val = ValidationEngine()
    history = pd.DataFrame(
        [
            {"close": 100.0, "delivery_pct_5d": 50.0},
            {"close": 105.0, "delivery_pct_5d": 55.0},
        ]
    )

    # Condition: delivery_pct_5d > 60.0. Met? No, actual is 55.0 on step 1.
    prop = CompiledProposition(
        theory_id="t1",
        lineage_id="l1",
        replay_step=1,
        compilation_status="SUCCESS",
        trigger_definition={
            "field": "delivery_pct_5d",
            "operator": ">",
            "value": 60.0,
        },
        target_definition={"field": "outcome", "operator": "==", "value": "up"},
    )

    record = engine_val.validate(prop, history, current_step=1)
    assert record.validation_state == "UNTRIGGERED"
    assert record.supporting_evidence is None
    assert record.contradicting_evidence is None


def test_validation_engine_triggered():
    engine_val = ValidationEngine()
    history = pd.DataFrame(
        [
            {"close": 100.0, "delivery_pct_5d": 70.0},
        ]
    )

    # Trigger is met (70.0 > 60.0), but lookahead target step (1) is out of bounds
    prop = CompiledProposition(
        theory_id="t1",
        lineage_id="l1",
        replay_step=0,
        compilation_status="SUCCESS",
        trigger_definition={
            "field": "delivery_pct_5d",
            "operator": ">",
            "value": 60.0,
        },
        target_definition={"field": "outcome", "operator": "==", "value": "up"},
    )

    record = engine_val.validate(prop, history, current_step=0)
    assert record.validation_state == "TRIGGERED"


def test_validation_engine_supported_and_contradicted():
    engine_val = ValidationEngine()

    # Trigger met, lookahead outcome close (105.0) > prior close (100.0) -> "up"
    history = pd.DataFrame(
        [
            {"close": 100.0, "delivery_pct_5d": 70.0},
            {"close": 105.0, "delivery_pct_5d": 55.0},
        ]
    )

    prop = CompiledProposition(
        theory_id="t1",
        lineage_id="l1",
        replay_step=0,
        compilation_status="SUCCESS",
        trigger_definition={
            "field": "delivery_pct_5d",
            "operator": ">",
            "value": 60.0,
        },
        target_definition={"field": "outcome", "operator": "==", "value": "up"},
    )

    record = engine_val.validate(prop, history, current_step=0)
    assert record.validation_state == "SUPPORTED"
    assert record.supporting_evidence is not None
    assert record.supporting_evidence["val"] == "up"

    # Now change expected value to "down" -> should be contradicted
    prop.target_definition["value"] = "down"
    record_contra = engine_val.validate(prop, history, current_step=0)
    assert record_contra.validation_state == "CONTRADICTED"
    assert record_contra.contradicting_evidence is not None
    assert record_contra.contradicting_evidence["val"] == "up"


def test_repository_immutability():
    repo = ValidationRecordRepository()
    record = ValidationRecord(
        proposition_id="p1",
        canonical_proposition_id="cp1",
        theory_id="t1",
        lineage_id="l1",
        mechanism_ids=["m1"],
        timestamp=datetime.now(timezone.utc),
        replay_step=1,
        validation_state="SUPPORTED",
        confidence_before=0.6,
        confidence_after=0.6,
        confidence_delta=0.0,
        regime="compressed",
        grounding_version="1.7.0",
        compiler_version="1.7.0",
        validation_engine_version="1.0.0",
    )

    # First save succeeds
    res = repo.save(record)
    assert res["status"] == "stored"

    # Second save with same ID raises ValueError (immutability enforcement)
    with pytest.raises(ValueError, match="Immutability Contract Violation"):
        repo.save(record)


def test_repository_queries():
    repo = ValidationRecordRepository()
    record1 = ValidationRecord(
        proposition_id="prop_query_1",
        canonical_proposition_id="cp_query_1",
        theory_id="t_query",
        lineage_id="l_query",
        mechanism_ids=["m_query"],
        timestamp=datetime.now(timezone.utc),
        replay_step=10,
        validation_state="SUPPORTED",
        confidence_before=0.7,
        confidence_after=0.7,
        confidence_delta=0.0,
        regime="expanded",
        grounding_version="1.7.0",
        compiler_version="1.7.0",
        validation_engine_version="1.0.0",
    )
    repo.save(record1)

    # Test query by proposition
    results_prop = repo.query_by_proposition("prop_query_1")
    assert len(results_prop) >= 1
    assert results_prop[0].lineage_id == "l_query"

    # Test query by lineage
    results_lin = repo.query_by_lineage("l_query")
    assert len(results_lin) >= 1

    # Test query by step
    results_step = repo.query_by_replay_step(10)
    assert len(results_step) >= 1

    # Test query by state
    results_state = repo.query_by_validation_state("SUPPORTED")
    assert len(results_state) >= 1
