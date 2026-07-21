"""
Authoritative Theory Lifecycle State Machine for DP-Core Reflective Cognition.

Defines explicit theory states, transition rules, validation requirements,
and side effects (such as EventBus notification).
"""
import enum
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from core.event_bus import get_event_bus
from core.events import TheoryRetired, TheoryUpdated

logger = logging.getLogger(__name__)


class TheoryState(str, enum.Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    WEAKENING = "weakening"
    RETIRED = "retired"
    ARCHIVED = "archived"

    @classmethod
    def from_str(cls, val: str) -> "TheoryState":
        val_lower = str(val).strip().lower()
        for state in cls:
            if state.value == val_lower:
                return state
        raise ValueError(f"Invalid TheoryState '{val}'. Supported states: {[s.value for s in cls]}")


class TheoryTransition(str, enum.Enum):
    PROMOTE_TO_CANDIDATE = "promote_to_candidate"
    ACTIVATE = "activate"
    WEAKEN = "weaken"
    REINFORCE = "reinforce"
    RETIRE = "retire"
    REVIVE = "revive"
    ARCHIVE = "archive"


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal theory state transition is attempted."""
    pass


# Map of allowed state transitions: (from_state, transition) -> resulting_state
ALLOWED_TRANSITIONS: Dict[Tuple[TheoryState, TheoryTransition], TheoryState] = {
    (TheoryState.DRAFT, TheoryTransition.PROMOTE_TO_CANDIDATE): TheoryState.CANDIDATE,
    (TheoryState.DRAFT, TheoryTransition.ACTIVATE): TheoryState.ACTIVE,
    (TheoryState.DRAFT, TheoryTransition.RETIRE): TheoryState.RETIRED,
    
    (TheoryState.CANDIDATE, TheoryTransition.ACTIVATE): TheoryState.ACTIVE,
    (TheoryState.CANDIDATE, TheoryTransition.RETIRE): TheoryState.RETIRED,
    
    (TheoryState.ACTIVE, TheoryTransition.WEAKEN): TheoryState.WEAKENING,
    (TheoryState.ACTIVE, TheoryTransition.RETIRE): TheoryState.RETIRED,
    
    (TheoryState.WEAKENING, TheoryTransition.REINFORCE): TheoryState.ACTIVE,
    (TheoryState.WEAKENING, TheoryTransition.WEAKEN): TheoryState.WEAKENING,
    (TheoryState.WEAKENING, TheoryTransition.RETIRE): TheoryState.RETIRED,
    
    (TheoryState.RETIRED, TheoryTransition.REVIVE): TheoryState.CANDIDATE,
    (TheoryState.RETIRED, TheoryTransition.ARCHIVE): TheoryState.ARCHIVED,
}


class TheoryStateMachine:
    """
    Manages state transitions and validation rules for a theory lifecycle.
    """

    def __init__(self, initial_state: TheoryState = TheoryState.DRAFT, theory_id: Optional[str] = None):
        self.state: TheoryState = initial_state
        self.theory_id: str = theory_id or "TH_UNKNOWN"
        self.history: List[Dict[str, Any]] = [
            {
                "timestamp": time.time(),
                "from_state": None,
                "to_state": self.state.value,
                "transition": "initialize",
                "reason": "Initial state creation",
            }
        ]

    def can_transition(self, transition_type: TheoryTransition) -> bool:
        """Check if a transition type is valid from the current state."""
        return (self.state, transition_type) in ALLOWED_TRANSITIONS

    def transition(
        self,
        transition_type: TheoryTransition,
        reason: str = "",
        statement: str = "",
        confidence: float = 0.5,
        contradiction_pressure: float = 0.0,
        evidence_support: float = 0.0,
        regime_match: bool = False,
    ) -> TheoryState:
        """
        Executes a state transition if allowed and valid. Raises InvalidStateTransitionError on illegal moves.
        """
        key = (self.state, transition_type)
        if key not in ALLOWED_TRANSITIONS:
            raise InvalidStateTransitionError(
                f"[TheoryStateMachine] Illegal transition '{transition_type.value}' "
                f"from state '{self.state.value}' for theory '{self.theory_id}'."
            )

        target_state = ALLOWED_TRANSITIONS[key]

        # Specific transition validation rules
        if transition_type == TheoryTransition.PROMOTE_TO_CANDIDATE:
            if not statement or not statement.strip():
                raise InvalidStateTransitionError(
                    f"[TheoryStateMachine] Cannot promote theory '{self.theory_id}' to CANDIDATE: statement is empty."
                )

        elif transition_type == TheoryTransition.REVIVE:
            # Revival rules: requires sufficient evidence support (>= 0.50) OR active regime match
            if evidence_support < 0.50 and not regime_match:
                raise InvalidStateTransitionError(
                    f"[TheoryStateMachine] Revival rejected for theory '{self.theory_id}': "
                    f"requires evidence_support >= 0.50 or regime_match=True (got support={evidence_support:.2f}, match={regime_match})."
                )

        # Record state change
        old_state = self.state
        self.state = target_state

        self.history.append(
            {
                "timestamp": time.time(),
                "from_state": old_state.value,
                "to_state": self.state.value,
                "transition": transition_type.value,
                "reason": reason,
            }
        )

        logger.info(
            "[TheoryStateMachine] Theory '%s' transitioned: %s -> %s via '%s' (reason: %s)",
            self.theory_id,
            old_state.value,
            self.state.value,
            transition_type.value,
            reason,
        )

        # Side effects: publish event telemetry on EventBus
        self._notify_event_bus(old_state, target_state, transition_type, reason, confidence)

        return self.state

    def evaluate_confidence_transition(
        self, confidence: float, contradiction_pressure: float = 0.0, reason: str = ""
    ) -> TheoryState:
        """
        Evaluates current state against confidence and contradiction dynamics to request transitions.
        """
        if self.state == TheoryState.ACTIVE:
            if confidence < 0.25 or contradiction_pressure >= 0.8:
                return self.transition(
                    TheoryTransition.RETIRE,
                    reason=reason or f"Confidence dropped below 0.25 ({confidence:.2f}) or high contradiction ({contradiction_pressure:.2f})",
                    confidence=confidence,
                    contradiction_pressure=contradiction_pressure,
                )
            elif confidence < 0.45 or contradiction_pressure > 0.5:
                return self.transition(
                    TheoryTransition.WEAKEN,
                    reason=reason or f"Confidence weakened ({confidence:.2f}) / contradiction pressure ({contradiction_pressure:.2f})",
                    confidence=confidence,
                    contradiction_pressure=contradiction_pressure,
                )

        elif self.state == TheoryState.WEAKENING:
            if confidence < 0.25 or contradiction_pressure >= 0.8:
                return self.transition(
                    TheoryTransition.RETIRE,
                    reason=reason or f"Weakened theory dropped below 0.25 threshold ({confidence:.2f})",
                    confidence=confidence,
                    contradiction_pressure=contradiction_pressure,
                )
            elif confidence >= 0.50 and contradiction_pressure <= 0.4:
                return self.transition(
                    TheoryTransition.REINFORCE,
                    reason=reason or f"Confidence recovered ({confidence:.2f})",
                    confidence=confidence,
                    contradiction_pressure=contradiction_pressure,
                )

        return self.state

    def request_revival(self, evidence_support: float, regime_match: bool = False, reason: str = "") -> TheoryState:
        """Explicit revival API for retired theories."""
        if self.state != TheoryState.RETIRED:
            raise InvalidStateTransitionError(
                f"[TheoryStateMachine] Cannot request revival for theory '{self.theory_id}' in state '{self.state.value}' (must be RETIRED)."
            )
        return self.transition(
            TheoryTransition.REVIVE,
            reason=reason or f"Revival requested (support={evidence_support:.2f}, regime_match={regime_match})",
            evidence_support=evidence_support,
            regime_match=regime_match,
        )

    def _notify_event_bus(
        self,
        old_state: TheoryState,
        new_state: TheoryState,
        transition: TheoryTransition,
        reason: str,
        confidence: float,
    ) -> None:
        try:
            bus = get_event_bus()
            if new_state == TheoryState.RETIRED:
                bus.publish(
                    TheoryRetired(theory_id=self.theory_id, reason=reason),
                    publisher="theory_state_machine",
                )
            else:
                bus.publish(
                    TheoryUpdated(
                        theory_id=self.theory_id,
                        old_confidence=confidence,
                        new_confidence=confidence,
                        reason=f"Transition: {old_state.value} -> {new_state.value} via {transition.value}. {reason}",
                    ),
                    publisher="theory_state_machine",
                )
        except Exception as _exc:
            logger.debug("[TheoryStateMachine] EventBus notification exception: %s", _exc)
