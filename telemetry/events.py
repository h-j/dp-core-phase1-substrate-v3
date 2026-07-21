"""
Pydantic v2 Telemetry Event Schemas for EEF v1.0 / MVF v1.0.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict


class EventType(str, Enum):
    THEORY_CREATED = "TheoryCreated"
    THEORY_UPDATED = "TheoryUpdated"
    THEORY_RETIRED = "TheoryRetired"
    MECHANISM_CREATED = "MechanismCreated"
    MECHANISM_REUSED = "MechanismReused"
    BELIEF_UPDATED = "BeliefUpdated"
    REFLECTION_GENERATED = "ReflectionGenerated"
    LESSON_PROMOTED = "LessonPromoted"
    PREDICTION_EVALUATED = "PredictionEvaluated"
    REGIME_TRANSITION = "RegimeTransition"
    CONTRADICTION_DETECTED = "ContradictionDetected"
    COUNTERFACTUAL_EVALUATED = "CounterfactualEvaluated"


class BaseTelemetryEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid4()), description="UUIDv4 event identifier")
    run_id: str = Field(..., description="Unique replay run identifier")
    step: int = Field(..., ge=0, description="Zero-indexed trading step")
    event_type: EventType = Field(..., description="Typed event classification")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TheoryCreatedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.THEORY_CREATED
    theory_id: str
    lineage_id: str
    parent_ids: List[str] = Field(default_factory=list)
    thesis: str
    mechanisms: List[str]
    if_branch_condition: Optional[str] = None
    else_branch_condition: Optional[str] = None
    unless_clause: Optional[str] = None
    initial_confidence: float = Field(default=0.50, ge=0.0, le=1.0)


class TheoryUpdatedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.THEORY_UPDATED
    theory_id: str
    lineage_id: str
    mutation_type: str = Field(..., description="MUTATE | REINFORCE | DIALECTICAL_SYNTHESIS")
    mutated_components: List[str] = Field(default_factory=list)
    mutation_reason: str = ""


class TheoryRetiredEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.THEORY_RETIRED
    theory_id: str
    lineage_id: str
    retirement_reason: str = ""
    survival_steps: int = Field(default=0, ge=0)


class MechanismCreatedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.MECHANISM_CREATED
    mechanism_id: str
    canonical_name: str
    concept_tags: List[str] = Field(default_factory=list)
    relation_type: str = "CO-OCCURS_WITH"


class MechanismReusedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.MECHANISM_REUSED
    mechanism_id: str
    theory_id: str
    execution_ast_hash: str = Field(default="hash_stub", description="SHA-256 hash of compiled AST logic")
    utility_delta: float = Field(default=0.0, description="Observed outcome utility delta")


class BeliefUpdatedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.BELIEF_UPDATED
    empirical_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    regime_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    reflection_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    theoretical_coherence: float = Field(default=0.50, ge=0.0, le=1.0)
    contradiction_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    ece: float = Field(default=0.0, ge=0.0, le=1.0)
    rce: float = Field(default=0.0, ge=0.0, le=1.0)
    fragmentation_entropy: float = Field(default=0.0, ge=0.0)


class ReflectionGeneratedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.REFLECTION_GENERATED
    reflection_id: str
    trigger_reason: str = ""
    pre_accuracy_5d: float = 0.50
    post_accuracy_5d: float = 0.50
    payoff_ratio: float = 1.0


class LessonPromotedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.LESSON_PROMOTED
    lesson_id: str
    target_regime: Dict[str, Any] = Field(default_factory=dict)
    affected_components: List[str] = Field(default_factory=list)
    status_before: str = "candidate"
    status_after: str = "retired"
    support_count: int = 0
    falsification_count: int = 0


class PredictionEvaluatedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.PREDICTION_EVALUATED
    probe_id: str
    prediction_id: str = ""
    predicted_direction: str = "FLAT"
    actual_direction: str = "FLAT"
    is_correct: bool = False
    stated_confidence: float = Field(default=0.50, ge=0.0, le=1.0)
    error_magnitude: float = 0.0


class RegimeTransitionEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.REGIME_TRANSITION
    previous_regime: str = "neutral"
    new_regime: str = "neutral"
    volatility_zscore: float = 0.0
    trigger_indicators: List[str] = Field(default_factory=list)


class ContradictionDetectedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.CONTRADICTION_DETECTED
    theory_id: str = ""
    contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conflicting_observation: Dict[str, Any] = Field(default_factory=dict)


class CounterfactualEvaluatedEvent(BaseTelemetryEvent):
    event_type: EventType = EventType.COUNTERFACTUAL_EVALUATED
    mechanism_id: str = ""
    scrambled_feature: str = ""
    counterfactual_accuracy: float = Field(default=0.50, ge=0.0, le=1.0)

