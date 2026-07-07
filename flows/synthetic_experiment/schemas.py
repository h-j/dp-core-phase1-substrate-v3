from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from cognition.schemas.base import CognitionBase


class RelationType(str, Enum):
    STABLE = "STABLE"
    SPURIOUS = "SPURIOUS"
    DECAYING = "DECAYING"
    REGIME_SHIFT = "REGIME_SHIFT"


class PlantedRelation(CognitionBase):
    relation_id: str
    relation_type: RelationType
    trigger_field: str
    trigger_value: str
    scope_field: str
    scope_value: str
    target_field: str = "outcome"
    target_value: str = "UP"
    p_conditional_base: float
    decay_rate: float = 0.0
    shift_step: Optional[int] = None


class Experience(CognitionBase):
    timestamp: int
    regime: str
    features: Dict[str, Any]
    outcome: str


class Predicate(CognitionBase):
    field: str
    operator: str
    value: Any


class CandidateProposition(CognitionBase):
    proposition_id: str
    trigger_predicate: Predicate
    scope_predicates: List[Predicate] = Field(default_factory=list)
    expected_effect_predicate: Predicate
    evaluation_horizon: int = 1


class EvidenceObject(CognitionBase):
    proposition_id: str
    activation_count: int
    support_count: int
    contradiction_count: int
    conditional_probability: float
    unconditional_base_rate: float
    signed_lift: float
    absolute_lift: float
    uncertainty_score: float
    stability_score: float
