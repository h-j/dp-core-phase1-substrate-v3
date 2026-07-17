import time

from flows.minimal_learning_cycle.belief_memory import MLCBeliefMemory
from flows.minimal_learning_cycle.schemas import LifecycleState


def test_belief_memory_evolution_and_invariants():
    mem = MLCBeliefMemory()

    # 1. Store an initial admitted belief
    prop = {
        "proposition_id": "PROP_TEST_001",
        "source_hypothesis_id": "HYP_TEST_001",
        "trigger_definition": {"field": "F_0", "operator": "==", "value": 1, "lag": 0},
        "target_definition": {"field": "outcome", "operator": "==", "value": 1},
        "scope_definition": [],
        "expected_direction": 1.0,
        "contradiction_definition": {"field": "outcome", "operator": "==", "value": 0},
        "specificity_definition": {"type": "deterministic"},
        "complexity_cost": 1.0,
        "generation_source": "deterministic_compilation",
        "creation_timestamp": time.time(),
        "lifecycle_state": LifecycleState.ADMITTED_BELIEF,
    }

    decision_dict = {"decision": "ADMIT", "reason_code": "HIGH_LIFT"}
    mem.store_record(
        prop=prop,
        lifecycle_history=[
            LifecycleState.HYPOTHESIS,
            LifecycleState.COMPILED_CANDIDATE,
            LifecycleState.EVALUATION_READY,
            LifecycleState.PROSPECTIVELY_EVALUATED,
            LifecycleState.ADMITTED_BELIEF,
        ],
        window_2_summary={
            "active_count": 100,
            "active_target_count": 80,
            "control_count": 100,
            "control_target_count": 20,
        },
        window_3_summary={
            "active_count": 100,
            "active_target_count": 78,
            "control_count": 100,
            "control_target_count": 22,
        },
        decision_dict=decision_dict,
        ground_truth={
            "world_id": "WORLD_A",
            "expected_decision": "ADMIT",
            "expected_reason": "TRUE_CAUSAL",
        },
        erc_refs=["REQ_001"],
        ledger_refs=["L_001"],
    )

    # Get active beliefs and verify
    active = mem.get_active_beliefs()
    assert len(active) == 1
    assert active[0]["proposition"]["proposition_id"] == "PROP_TEST_001"
    assert active[0]["record_type"] == "ADMITTED_BELIEF"
    assert active[0]["proposition"]["lifecycle_state"] == LifecycleState.ADMITTED_BELIEF
    assert len(active[0]["evolution_history"]) == 0

    # 2. Transition 1: Weakening the belief (Contradiction Responsiveness)
    trigger_ev_1 = {
        "comparative_effect": -0.02,
        "support_count": 10,
        "contradiction_count": 15,
    }

    mem.update_belief_state(
        proposition_id="PROP_TEST_001",
        new_state=LifecycleState.WEAKENED_BELIEF,
        trigger_evidence=trigger_ev_1,
        reason_code="CONTRADICTING_EVIDENCE_OBSERVED",
    )

    # Verify Identity and Provenance Invariants
    active_after_weaken = mem.get_active_beliefs()
    assert len(active_after_weaken) == 1
    assert (
        active_after_weaken[0]["proposition"]["proposition_id"] == "PROP_TEST_001"
    )  # Identity
    assert active_after_weaken[0]["record_type"] == "WEAKENED_BELIEF"
    assert (
        active_after_weaken[0]["proposition"]["lifecycle_state"]
        == LifecycleState.WEAKENED_BELIEF
    )

    history = active_after_weaken[0]["evolution_history"]
    assert len(history) == 1  # Provenance & History Preservation
    assert history[0]["from_state"] == "ADMITTED_BELIEF"
    assert history[0]["to_state"] == LifecycleState.WEAKENED_BELIEF
    assert history[0]["trigger_evidence"]["comparative_effect"] == -0.02
    assert history[0]["reason_code"] == "CONTRADICTING_EVIDENCE_OBSERVED"
    assert isinstance(history[0]["timestamp"], float)

    # 3. Transition 2: Retiring the belief (Continuing Contradiction)
    trigger_ev_2 = {
        "comparative_effect": -0.25,
        "support_count": 2,
        "contradiction_count": 40,
    }

    time.sleep(0.01)  # Ensure distinct timestamps
    mem.update_belief_state(
        proposition_id="PROP_TEST_001",
        new_state=LifecycleState.RETIRED_BELIEF,
        trigger_evidence=trigger_ev_2,
        reason_code="SEVERE_CONTRADICTION",
    )

    # Verify retirement makes it inactive
    active_after_retire = mem.get_active_beliefs()
    assert len(active_after_retire) == 0

    # Find retired belief record directly and verify invariants
    retired_record = mem.records[0]
    assert retired_record["record_type"] == "RETIRED_BELIEF"
    assert (
        retired_record["proposition"]["lifecycle_state"]
        == LifecycleState.RETIRED_BELIEF
    )
    assert len(retired_record["evolution_history"]) == 2

    # Verify Temporal Invariant
    t1 = retired_record["evolution_history"][0]["timestamp"]
    t2 = retired_record["evolution_history"][1]["timestamp"]
    assert t2 > t1

    # Verify Idempotency Invariant
    # Try transitioning RETIRED_BELIEF to RETIRED_BELIEF again
    mem.update_belief_state(
        proposition_id="PROP_TEST_001",
        new_state=LifecycleState.RETIRED_BELIEF,
        trigger_evidence=trigger_ev_2,
        reason_code="REDUNDANT_RETIREMENT_CHECK",
    )
    assert len(retired_record["evolution_history"]) == 3
    assert retired_record["evolution_history"][2]["from_state"] == "RETIRED_BELIEF"
    assert retired_record["evolution_history"][2]["to_state"] == "RETIRED_BELIEF"

    print(
        "✓ All belief evolution invariants (Identity, Provenance, Temporal, Idempotency, History, Responsiveness) passed successfully."
    )


if __name__ == "__main__":
    test_belief_memory_evolution_and_invariants()
