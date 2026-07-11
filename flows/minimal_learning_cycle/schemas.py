from enum import Enum
from typing import Any, Dict, List, Optional


class LifecycleState(str, Enum):
    HYPOTHESIS = "HYPOTHESIS"
    COMPILED_CANDIDATE = "COMPILED_CANDIDATE"
    EVIDENCE_ACCUMULATING = "EVIDENCE_ACCUMULATING"
    EVALUATION_READY = "EVALUATION_READY"
    FROZEN_EVALUATION_CANDIDATE = "FROZEN_EVALUATION_CANDIDATE"
    PROSPECTIVELY_EVALUATED = "PROSPECTIVELY_EVALUATED"
    ADMITTED_BELIEF = "ADMITTED_BELIEF"
    REJECTED_PROPOSITION = "REJECTED_PROPOSITION"
    DEFERRED_PROPOSITION = "DEFERRED_PROPOSITION"
    COMPILATION_REJECTED = "COMPILATION_REJECTED"
    WEAKENED_BELIEF = "WEAKENED_BELIEF"
    RETIRED_BELIEF = "RETIRED_BELIEF"


# Dict of allowed state transitions
ALLOWED_TRANSITIONS = {
    LifecycleState.HYPOTHESIS: [
        LifecycleState.COMPILED_CANDIDATE,
        LifecycleState.COMPILATION_REJECTED,
    ],
    LifecycleState.COMPILED_CANDIDATE: [LifecycleState.EVIDENCE_ACCUMULATING],
    LifecycleState.EVIDENCE_ACCUMULATING: [LifecycleState.EVALUATION_READY],
    LifecycleState.EVALUATION_READY: [LifecycleState.FROZEN_EVALUATION_CANDIDATE],
    LifecycleState.FROZEN_EVALUATION_CANDIDATE: [
        LifecycleState.PROSPECTIVELY_EVALUATED
    ],
    LifecycleState.PROSPECTIVELY_EVALUATED: [
        LifecycleState.ADMITTED_BELIEF,
        LifecycleState.REJECTED_PROPOSITION,
        LifecycleState.DEFERRED_PROPOSITION,
    ],
    LifecycleState.ADMITTED_BELIEF: [
        LifecycleState.ADMITTED_BELIEF,
        LifecycleState.WEAKENED_BELIEF,
        LifecycleState.RETIRED_BELIEF,
    ],
    LifecycleState.WEAKENED_BELIEF: [
        LifecycleState.ADMITTED_BELIEF,
        LifecycleState.WEAKENED_BELIEF,
        LifecycleState.RETIRED_BELIEF,
    ],
    LifecycleState.RETIRED_BELIEF: [
        LifecycleState.RETIRED_BELIEF,
    ],
    LifecycleState.REJECTED_PROPOSITION: [],
    LifecycleState.DEFERRED_PROPOSITION: [],
    LifecycleState.COMPILATION_REJECTED: [],
}


def validate_state_transition(current: LifecycleState, target: LifecycleState):
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"Illegal lifecycle transition from {current} to {target}")


class PropositionSchema:
    @staticmethod
    def validate(prop: Dict[str, Any]) -> bool:
        required_fields = [
            "proposition_id",
            "source_hypothesis_id",
            "trigger_definition",
            "target_definition",
            "scope_definition",
            "expected_direction",
            "contradiction_definition",
            "specificity_definition",
            "complexity_cost",
            "generation_source",
            "creation_timestamp",
            "lifecycle_state",
        ]
        # Check all required keys exist
        if not all(k in prop for k in required_fields):
            return False

        # Validate trigger, scope, target structures
        trigger = prop["trigger_definition"]
        if (
            not isinstance(trigger, dict)
            or "field" not in trigger
            or "operator" not in trigger
            or "value" not in trigger
            or "lag" not in trigger
        ):
            return False
        if (
            trigger["operator"] != "=="
            or trigger["value"] not in [0, 1]
            or trigger["lag"] not in [0, 1]
        ):
            return False

        target = prop["target_definition"]
        if (
            not isinstance(target, dict)
            or "field" not in target
            or "operator" not in target
            or "value" not in target
        ):
            return False
        if (
            target["field"] != "outcome"
            or target["operator"] != "=="
            or target["value"] not in ["VAL_A", "VAL_B"]
        ):
            return False

        scope = prop["scope_definition"]
        if not isinstance(scope, list):
            return False
        for s in scope:
            if (
                not isinstance(s, dict)
                or "field" not in s
                or "operator" not in s
                or "value" not in s
            ):
                return False
            if s["operator"] != "==" or s["value"] not in [0, 1]:
                return False

        # Pre-registered contradiction definition
        contra = prop["contradiction_definition"]
        if (
            not isinstance(contra, dict)
            or "field" not in contra
            or "operator" not in contra
            or "value" not in contra
        ):
            return False

        return True
