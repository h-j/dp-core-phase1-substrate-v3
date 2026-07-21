"""
Structured Domain Events for DP-Core Reflective Cognition.

Defines Pydantic models for major cognition lifecycle stages:
- ObservationCreated
- MechanismGenerated
- TheoryCreated
- TheoryUpdated
- TheoryRetired
- ReflectionCompleted
- PredictionGenerated
"""
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Event(BaseModel):
    """Base class for all structured domain events."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_id: str = Field(default_factory=lambda: f"EVT_{uuid.uuid4().hex[:12]}")
    timestamp: float = Field(default_factory=time.time)
    publisher: Optional[str] = None


class ObservationCreated(Event):
    """Emitted when a new historical/live market observation is processed."""

    date: str
    symbol: str
    ohlcv: Dict[str, Any]
    derived: Dict[str, Any]


class MechanismGenerated(Event):
    """Emitted when a candidate mechanism/proposition hypothesis is generated."""

    mechanism_id: str
    description: str
    confidence: float
    source_observations: List[str] = Field(default_factory=list)


class TheoryCreated(Event):
    """Emitted when a new reflective theory hypothesis is compiled."""

    theory_id: str
    statement: str
    confidence: float
    source_mechanisms: List[str] = Field(default_factory=list)


class TheoryUpdated(Event):
    """Emitted when a theory's confidence or status is updated based on empirical feedback."""

    theory_id: str
    old_confidence: float
    new_confidence: float
    reason: str


class TheoryRetired(Event):
    """Emitted when a theory is retired due to falsification or low confidence."""

    theory_id: str
    reason: str
    retired_at: float = Field(default_factory=time.time)


class ReflectionCompleted(Event):
    """Emitted when a meta-cognitive reflection cycle completes."""

    reflection_id: str
    insights: List[str] = Field(default_factory=list)


class PredictionGenerated(Event):
    """Emitted when a directional prediction probe is generated."""

    prediction_id: str
    theory_id: Optional[str] = None
    target_date: str
    predicted_direction: str
    conviction: float
