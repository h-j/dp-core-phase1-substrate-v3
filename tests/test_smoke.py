"""
Smoke test suite verifying schema imports and default model instantiations across cognition/schemas/.
"""
import pytest

# 1. Import every schema module under cognition.schemas
from cognition.schemas.abstraction.abstraction_unit import AbstractionUnit
from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.decision.decision import Decision
from cognition.schemas.decision.decision_record import DecisionRecord
from cognition.schemas.experience.experience import Experience
from cognition.schemas.knowledge.principle import Principle
from cognition.schemas.knowledge.world_model import WorldModel
from cognition.schemas.observation.observation_event import ObservationEvent
from cognition.schemas.pattern.pattern import Pattern
from cognition.schemas.proposition.canonical_semantic_proposition import (
    CanonicalSemanticProposition,
)
from cognition.schemas.proposition.market_proposition import CompiledProposition
from cognition.schemas.proposition.validation_record import ValidationRecord
from cognition.schemas.reflection.reflection_event import ReflectionEvent
from cognition.schemas.reflection.reflective_memory_state import ReflectiveMemoryState
from cognition.schemas.theory.theory import Branch, Theory, TheoryStructured
from cognition.schemas.validation.belief_state import BeliefState
from cognition.schemas.validation.validation_event import ValidationEvent


def test_import_cognition_schemas():
    """Verify that all cognition schema modules import successfully."""
    assert AbstractionUnit is not None
    assert ConfidenceState is not None
    assert Decision is not None
    assert DecisionRecord is not None
    assert Experience is not None
    assert Principle is not None
    assert WorldModel is not None
    assert ObservationEvent is not None
    assert Pattern is not None
    assert CompiledProposition is not None
    assert CanonicalSemanticProposition is not None
    assert ValidationRecord is not None
    assert ReflectionEvent is not None
    assert ReflectiveMemoryState is not None
    assert Theory is not None
    assert TheoryStructured is not None
    assert BeliefState is not None
    assert ValidationEvent is not None


def test_instantiate_schema_models_with_defaults():
    """Verify each Pydantic model can be instantiated with default arguments or minimal required fields."""

    # Abstraction Unit
    abs_unit = AbstractionUnit(
        source_observation_id="OBS_001",
        abstraction_summary="Sample abstraction summary",
    )
    assert abs_unit.source_observation_id == "OBS_001"

    # Confidence State
    conf = ConfidenceState()
    assert conf.empirical_confidence == 0.5

    # Decision & Decision Record
    dec = Decision(
        date="2023-01-01",
        prediction_direction="BULLISH",
        action="LONG",
        allocation_pct=0.10,
        conviction_score=0.75,
        reason="Strong trend confirmation",
    )
    assert dec.action == "LONG"

    dec_rec = DecisionRecord(
        prediction_date="2023-01-01",
        asset="RELIANCE",
        prediction="BULLISH",
        decision=dec,
        allocation=0.10,
        conviction_score=0.75,
        decision_reason="Strong trend confirmation",
    )
    assert dec_rec.asset == "RELIANCE"

    # Experience
    exp = Experience(
        experience_id="EXP_001",
        lineage_id="L_001",
        theory_family_id="FAM_001",
        created_at="2023-01-01T00:00:00Z",
    )
    assert exp.experience_id == "EXP_001"

    # Knowledge / Principle
    principle = Principle(statement="Trend Persistence", created_at_step=0)
    assert principle.statement == "Trend Persistence"

    world_model = WorldModel(step=0, narrative_summary="World model summary")
    assert world_model.step == 0

    # Observation Event
    obs_event = ObservationEvent(source_type="MARKET", raw_content="Market observation text")
    assert obs_event.source_type == "MARKET"

    # Pattern
    pattern = Pattern(pattern_id="PAT_001", failed_component="VOLUME", root_cause="DIVERGENCE")
    assert pattern.pattern_id == "PAT_001"

    # Proposition & Validation Record
    comp_prop = CompiledProposition(
        theory_id="TH_001",
        lineage_id="L_001",
        replay_step=0,
        compilation_status="SUCCESS",
    )
    assert comp_prop.theory_id == "TH_001"

    canon_prop = CanonicalSemanticProposition(
        theory_id="TH_001",
        lineage_id="L_001",
        causal_direction="positive",
    )
    assert canon_prop.causal_direction == "positive"

    val_rec = ValidationRecord(
        proposition_id="PROP_001",
        canonical_proposition_id="CANON_001",
        theory_id="TH_001",
        lineage_id="L_001",
        replay_step=1,
        validation_state="SUPPORTED",
        confidence_before=0.5,
        confidence_after=0.6,
        confidence_delta=0.1,
        regime="bullish",
        grounding_version="1.0",
        compiler_version="1.0",
        validation_engine_version="1.0",
    )
    assert val_rec.proposition_id == "PROP_001"

    # Reflection
    ref_event = ReflectionEvent(
        related_theory_id="TH_001",
        reflection_summary="Insight summary",
        confidence_impact="INCREASED",
    )
    assert ref_event.related_theory_id == "TH_001"

    ref_state = ReflectiveMemoryState(cognition_trajectory_summary="Trajectory summary")
    assert ref_state.cognition_trajectory_summary == "Trajectory summary"

    # Theory & TheoryStructured
    branch1 = Branch(condition="volume > avg", action="BULLISH")
    branch2 = Branch(condition="volume <= avg", action="NEUTRAL")
    theory_struct = TheoryStructured(
        claim="Core claim",
        if_branch=branch1,
        else_branch=branch2,
        falsified_if="price drops 5%",
    )
    assert theory_struct.claim == "Core claim"

    theory = Theory(
        lineage_id="LINEAGE_001",
        thesis="Bullish thesis",
        summary="Theory summary",
        confidence_state=ConfidenceState(),
    )
    assert theory.lineage_id == "LINEAGE_001"

    # Validation & Belief State
    belief_state = BeliefState(lineage_id="L_001", active_theory_id="TH_001")
    assert belief_state.active_theory_id == "TH_001"

    val_event = ValidationEvent(
        theory_id="TH_001",
        validation_summary="Validation summary",
        observed_behavior="Price up 2%",
        expected_behavior="Price up 2%",
    )
    assert val_event.theory_id == "TH_001"
