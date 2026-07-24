"""
Unit & Integration Tests for Evidence Accumulation Funnel & Wiring Canary (PROMPT C2).

Verifies:
1. Funnel counters byte-stability across duplicate runs.
2. Wiring Canary Test: A fixture theory with a known-triggering predicate produces
   exactly one SUPPORTED resolution and one Beta posterior update end-to-end.
"""
from pathlib import Path
import pandas as pd
import pytest

from telemetry.evidence_funnel import EvidenceFunnel, reset_active_funnel
from cognition.schemas.theory.theory import Theory, TheoryStructured
from cognition.schemas.proposition.market_proposition import CompiledProposition
from flows.proposition_flow.validation_engine import ValidationEngine
from cognition.confidence.scored_confidence_engine import ScoredConfidenceEngine, ConfidenceState


def test_funnel_byte_stability():
    """Verify byte-identical funnel output across identical runs."""
    f1 = EvidenceFunnel()
    f1.record_active_theory(0)
    f1.record_predicate_parsed(0, True)
    f1.record_activation_evaluated(0, True)
    f1.record_terminal_resolution(0, "SUPPORTED")
    f1.record_resolution_delivered(0)
    f1.record_beta_update(0)

    f2 = EvidenceFunnel()
    f2.record_active_theory(0)
    f2.record_predicate_parsed(0, True)
    f2.record_activation_evaluated(0, True)
    f2.record_terminal_resolution(0, "SUPPORTED")
    f2.record_resolution_delivered(0)
    f2.record_beta_update(0)

    assert f1.get_summary_dict() == f2.get_summary_dict()


def test_wiring_canary_end_to_end():
    """
    Wiring Canary Test (PROMPT C2 Task 7).

    A fixture theory with a known-triggering predicate:
    - Evaluates against synthetic market DataFrame.
    - Yields exactly one SUPPORTED resolution from ValidationEngine.
    - Delivers resolution to ScoredConfidenceEngine retrospective buffer.
    - Applies exactly one Beta posterior update (alpha increases from 1.0 to 2.0).
    """
    funnel = reset_active_funnel()

    # 1. Synthetic Market Data: step 0 (volume=2,000,000 > 1,000,000), step 1 (close=105.0 > 100.0)
    history_df = pd.DataFrame([
        {"volume": 2000000.0, "close": 100.0, "high": 102.0, "low": 99.0},
        {"volume": 1500000.0, "close": 105.0, "high": 106.0, "low": 100.0},
    ])

    # 2. Known-Triggering Compiled Proposition
    compiled_prop = CompiledProposition(
        id="prop_canary_001",
        theory_id="0:theory:0",
        lineage_id="0:theory:0",
        replay_step=0,
        compilation_status="SUCCESS",
        trigger_definition={"metric": "volume", "operator": ">=", "threshold": 1000000.0},
        target_definition={"metric": "close", "operator": ">=", "threshold": 102.0},
        scope_definition=[],
    )

    val_engine = ValidationEngine()
    val_rec = val_engine.validate(
        compiled_prop=compiled_prop,
        history_df=history_df,
        current_step=0,
    )

    # Assert ValidationEngine resolved SUPPORTED
    assert val_rec.validation_state == "SUPPORTED"

    # 3. Buffer resolution and evolve ScoredConfidenceEngine
    conf_engine = ScoredConfidenceEngine(k_falsify=3.0, decay_lambda=0.01)
    conf_engine.buffer_retrospective_resolutions([
        {
            "outcome": val_rec.validation_state,
            "lineage_id": val_rec.lineage_id,
            "theory_id": val_rec.theory_id,
        }
    ])

    initial_state = ConfidenceState(alpha=1.0, beta=1.0)
    updated_state = conf_engine.evolve(
        confidence_state=initial_state,
        day_idx=1,
        lineage_id="0:theory:0",
    )

    # 4. Assert Beta update applied (alpha moved off prior 1.0 to 2.0)
    assert updated_state.alpha == 2.0
    assert updated_state.beta == 1.0
    assert updated_state.alpha + updated_state.beta == 3.0
    assert updated_state.confidence > 0.50


    summary = funnel.get_summary_dict()["totals"]
    assert summary["supported_count"] == 1
    assert summary["resolutions_delivered_to_scored_engine"] == 1
    assert summary["beta_updates_applied"] == 1
