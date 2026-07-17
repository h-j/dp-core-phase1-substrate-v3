import time
from typing import Any, Dict, List


class MLCBeliefMemory:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def store_record(
        self,
        prop: Dict[str, Any],
        lifecycle_history: List[str],
        window_2_summary: Dict[str, Any],
        window_3_summary: Dict[str, Any],
        decision_dict: Dict[str, Any],
        ground_truth: Dict[str, Any],
        erc_refs: List[str],
        ledger_refs: List[str],
    ):
        dec = decision_dict["decision"]
        if dec == "ADMIT":
            rec_type = "ADMITTED_BELIEF"
        elif dec == "REJECT":
            rec_type = "REJECTED_PROPOSITION"
        elif dec == "COMPILATION_REJECTED":
            rec_type = "COMPILATION_REJECTED"
        else:
            rec_type = "DEFERRED_PROPOSITION"

        record = {
            "record_type": rec_type,
            "proposition": json_copy(prop),
            "full_lifecycle_transition_history": lifecycle_history,
            "evolution_history": [],
            "window_2_measurement_summary": json_copy(window_2_summary),
            "window_3_prospective_summary": json_copy(window_3_summary),
            "decision": dec,
            "decision_reason": decision_dict["reason_code"],
            "ground_truth_label": json_copy(ground_truth),
            "erc_history_references": erc_refs,
            "evidence_ledger_references": ledger_refs,
            "configuration_version": "v0.1_frozen",
            "code_version_metadata": {"engine": "MLC_v0.1_engine"},
            "timestamp": time.time(),
        }

        self.records.append(record)

    def get_active_beliefs(self) -> List[Dict[str, Any]]:
        """
        Returns all records representing active beliefs (ADMITTED or WEAKENED).
        """
        return [
            r
            for r in self.records
            if r["record_type"] in ("ADMITTED_BELIEF", "WEAKENED_BELIEF")
        ]

    def get_rejected_or_retired_triggers(self) -> List[str]:
        """
        Returns a list of trigger fields of propositions that have been rejected or retired.
        """
        rejected_triggers = []
        for r in self.records:
            if r["record_type"] in ("REJECTED_PROPOSITION", "RETIRED_BELIEF"):
                field = r["proposition"]["trigger_definition"]["field"]
                if field not in rejected_triggers:
                    rejected_triggers.append(field)
        return rejected_triggers

    def update_belief_state(
        self,
        proposition_id: str,
        new_state: str,
        trigger_evidence: Dict[str, Any],
        reason_code: str,
    ):
        """
        Transitions the state of an existing admitted/weakened belief to a new state,
        validating the transition and recording the provenance.
        """
        from flows.minimal_learning_cycle.schemas import (
            LifecycleState, validate_state_transition)

        # Find record
        record = None
        for r in self.records:
            if r["proposition"]["proposition_id"] == proposition_id:
                record = r
                break

        if not record:
            raise KeyError(
                f"Belief with proposition_id {proposition_id} not found in belief memory."
            )

        current_state = record["proposition"]["lifecycle_state"]

        # Validate transition using schema rules
        validate_state_transition(
            LifecycleState(current_state), LifecycleState(new_state)
        )

        # Record evolution event
        record["evolution_history"].append(
            {
                "timestamp": time.time(),
                "from_state": record["record_type"],
                "to_state": new_state,
                "trigger_evidence": json_copy(trigger_evidence),
                "reason_code": reason_code,
            }
        )

        # Update states
        record["record_type"] = new_state
        record["proposition"]["lifecycle_state"] = new_state


def json_copy(obj: Any) -> Any:
    import json

    return json.loads(json.dumps(obj))
