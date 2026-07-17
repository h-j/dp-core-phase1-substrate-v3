import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from cognition.schemas.theory.theory import Theory, TheoryStructured
from flows.proposition_flow.proposition_compiler import \
    MarketPropositionCompiler
from market.replay.replay_engine import ReplayEngine
from memory.relational.repositories.compiled_proposition_repository import \
    CompiledPropositionRepository


def test_compiled_proposition_schema():
    # Test valid schema creation
    prop = CompiledProposition(
        theory_id="th_123",
        lineage_id="lin_456",
        replay_step=1,
        compilation_status="SUCCESS",
        trigger_definition={
            "field": "delivery_pct_5d",
            "operator": ">",
            "value": 65.0,
            "lag": 0,
        },
        target_definition={"field": "outcome", "operator": "==", "value": "up"},
        scope_definition=[
            {"field": "volatility_regime", "operator": "==", "value": "compressed"}
        ],
        compiler_trace={
            "source_mechanisms": ["MECH_001"],
            "source_theory": "th_123",
            "compiler_version": "v1",
        },
    )
    assert prop.theory_id == "th_123"
    assert prop.compilation_status == "SUCCESS"
    assert prop.trigger_definition["value"] == 65.0


def test_compiled_proposition_repository_save():
    repo = CompiledPropositionRepository()
    prop = CompiledProposition(
        theory_id="th_test_save",
        lineage_id="lin_test_save",
        replay_step=5,
        compilation_status="SUCCESS",
        trigger_definition={
            "field": "fii_net",
            "operator": ">",
            "value": 1500.0,
            "lag": 0,
        },
        target_definition={"field": "outcome", "operator": "==", "value": "down"},
        scope_definition=[],
        compiler_trace={"source_theory": "th_test_save", "compiler_version": "v1"},
    )

    # Save to database
    save_res = repo.save(prop)
    assert save_res["status"] == "stored"
    assert save_res["proposition_id"] == prop.id

    # Retrieve from database
    retrieved = repo.list_by_theory("th_test_save")
    assert len(retrieved) >= 1
    matched = next((r for r in retrieved if r.id == prop.id), None)
    assert matched is not None
    assert matched.trigger_definition["value"] == 1500.0


def test_market_proposition_compiler_mock():
    # Mock OllamaClient response conforming to SemanticCompiler prompt
    mock_client = MagicMock()
    mock_client.generate.return_value = json.dumps(
        {
            "compilation_status": "SUCCESS",
            "failure_reason": None,
            "causal_direction": "positive",
            "trigger_concept": {
                "concept": "sector_relative_strength",
                "qualifier": "ELEVATED",
                "lag": 0,
            },
            "target_concept": {
                "concept": "asset_price",
                "qualifier": "GREATER_THAN_PREVIOUS",
                "duration_steps": 1,
            },
            "scope_concept": [{"concept": "volume_state", "qualifier": "COMPRESSED"}],
        }
    )

    compiler = MarketPropositionCompiler(client=mock_client)

    theory = Theory(
        id="th_mock_comp",
        lineage_id="lin_mock_comp",
        thesis="Sector is outperforming strongly.",
        summary="Sector Z-score exceeds 1.5 with high volume spike.",
        summary_structured=TheoryStructured(
            claim="Sector outperforms",
            if_branch={"condition": "zscore >= 1.5", "action": "predict up"},
            else_branch={"condition": "else", "action": "neutral"},
            falsified_if="falls below 0",
            forbidden_state="negative",
        ),
        confidence_state=ConfidenceState(),
    )

    canon, prop = compiler.compile_theory(theory, 2)
    assert canon.causal_direction == "positive"
    assert prop.compilation_status == "SUCCESS"
    assert prop.trigger_definition["field"] == "sector_zscore"
    assert prop.trigger_definition["operator"] == ">"
    assert prop.target_definition["operand_left"]["field"] == "close"
    assert prop.target_definition["operand_right"]["field"] == "close"
    assert prop.target_definition["operator"] == ">"
    assert prop.scope_definition[0]["field"] == "volume"
    assert prop.compiler_trace["source_theory"] == "th_mock_comp"


from market.replay.replay_engine import ReplayEngine, ReplayExecutor


def test_replay_integration_observational():
    # Instantiate ReplayExecutor with max_days=1 to execute integrated run
    # Verification checks: check that compilation metrics exist
    executor = ReplayExecutor(
        max_days=1,
        dataset_path="data/reliance_daily_3y.csv",
        market_name="RELIANCE",
        quiet=True,
    )
    # Ensure flows are initialized
    executor._initialize_flows()
    assert executor.proposition_compiler is not None
    assert executor.compiled_proposition_repo is not None
    assert "theories_generated" in executor.compilation_metrics
