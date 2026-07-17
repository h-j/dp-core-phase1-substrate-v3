from unittest.mock import MagicMock
from uuid import uuid4

import pandas as pd
import pytest

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.proposition.canonical_semantic_proposition import \
    CanonicalSemanticProposition
from cognition.schemas.theory.theory import Theory
from flows.proposition_flow.parameter_grounder import ParameterGrounder
from flows.proposition_flow.proposition_compiler import \
    MarketPropositionCompiler
from flows.proposition_flow.semantic_compiler import SemanticCompiler


def test_parameter_grounder_deterministic():
    # 1. Create a dummy history dataframe
    data = {
        "date": pd.date_range(start="2026-01-01", periods=10),
        "delivery_pct_5d": [50.0, 52.0, 55.0, 58.0, 60.0, 62.0, 65.0, 70.0, 75.0, 80.0],
        "volume": [1000] * 10,
        "close": [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 103.5, 105.0, 106.0, 105.5],
    }
    df = pd.DataFrame(data)

    # 2. Create CanonicalSemanticProposition object
    canonical = CanonicalSemanticProposition(
        id=str(uuid4()),
        theory_id="th_1",
        lineage_id="lin_1",
        trigger_concept={
            "concept": "speculative_liquidity",
            "qualifier": "ELEVATED",
            "lag": 1,
        },
        target_concept={"concept": "asset_price", "qualifier": "GREATER_THAN_PREVIOUS"},
        scope_concept=[{"concept": "volatility_regime", "qualifier": "NORMAL"}],
        causal_direction="positive",
        compiler_provenance={"status": "SUCCESS"},
    )

    grounder = ParameterGrounder()
    compiled = grounder.ground(canonical, df, step=9)

    assert compiled.compilation_status == "SUCCESS"
    assert compiled.trigger_definition["field"] == "delivery_pct_5d"
    assert compiled.trigger_definition["operator"] == ">"
    assert (
        compiled.trigger_definition["value"] > 70.0
    )  # 85th percentile of the sequence

    # Target is relative comparison close[t] > close[t-1]
    assert compiled.target_definition["operand_left"]["field"] == "close"
    assert compiled.target_definition["operand_right"]["field"] == "close"
    assert compiled.target_definition["operator"] == ">"
    assert compiled.target_definition["operand_right"]["time_offset"] == -1

    assert grounder.percentile_groundings_applied == 1
    assert grounder.relative_references_resolved == 1


def test_semantic_compiler_mock():
    client = MagicMock()
    # Mock LLM JSON output conforming to SemanticCompiler prompt constraints
    client.generate.return_value = """
    {
      "compilation_status": "SUCCESS",
      "failure_reason": null,
      "causal_direction": "negative",
      "trigger_concept": {
        "concept": "speculative_liquidity",
        "qualifier": "ELEVATED",
        "lag": 1
      },
      "target_concept": {
        "concept": "daily_high",
        "qualifier": "GREATER_THAN_PREVIOUS",
        "duration_steps": 1
      },
      "scope_concept": [
        {
          "concept": "volatility_regime",
          "qualifier": "COMPRESSED"
        }
      ]
    }
    """

    theory = Theory(
        id="th_1",
        lineage_id="lin_1",
        thesis="High delivery triggers price drop",
        summary="High delivery triggers price drop",
        summary_structured=None,
        confidence_state=ConfidenceState(score=0.5, evolution_path=[]),
    )

    compiler = SemanticCompiler(client=client)
    canon = compiler.compile(theory)

    assert canon.causal_direction == "negative"
    assert canon.trigger_concept["concept"] == "speculative_liquidity"
    assert canon.target_concept["concept"] == "daily_high"
    assert canon.scope_concept[0]["qualifier"] == "COMPRESSED"
