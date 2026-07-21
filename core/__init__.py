"""
Core package for DP-Core reflective cognition infrastructure.
"""
from core.event_bus import EventBus, get_event_bus, reset_event_bus
from core.events import (
    Event,
    MechanismGenerated,
    ObservationCreated,
    PredictionGenerated,
    ReflectionCompleted,
    TheoryCreated,
    TheoryRetired,
    TheoryUpdated,
)

from core.theory_state_machine import (
    InvalidStateTransitionError,
    TheoryState,
    TheoryStateMachine,
    TheoryTransition,
)

__all__ = [
    "EventBus",
    "get_event_bus",
    "reset_event_bus",
    "Event",
    "ObservationCreated",
    "MechanismGenerated",
    "TheoryCreated",
    "TheoryUpdated",
    "TheoryRetired",
    "ReflectionCompleted",
    "PredictionGenerated",
    "TheoryState",
    "TheoryTransition",
    "TheoryStateMachine",
    "InvalidStateTransitionError",
]
