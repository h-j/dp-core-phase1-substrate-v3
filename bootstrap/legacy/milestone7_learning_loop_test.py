import pytest

from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.schemas import LifecycleState
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld


def test_learning_loop_retrieval_and_pruning():
    world = MLCSyntheticWorld.generate_world("C2", seed=101)
    runner = MLCExperimentRunner()
    runner.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}

    # 1. T0: Run Condition B to generate a rejected confounder proposition in belief memory.
    # In Condition B, we disable prospective filtering, and the winner is decided on Window 2.
    # We will manually inject a rejection record into belief_memory to simulate confounder rejection.
    prop_dummy = {
        "proposition_id": "PROP_WORLD_DUMMY_c2",
        "trigger_definition": {"field": "VAR_2"},
        "lifecycle_state": "REJECTED_PROPOSITION",
    }
    runner.belief_memory.store_record(
        prop=prop_dummy,
        lifecycle_history=["HYPOTHESIS", "REJECTED_PROPOSITION"],
        window_2_summary={},
        window_3_summary={},
        decision_dict={"decision": "REJECT", "reason_code": "CONTRADICTION"},
        ground_truth={},
        erc_refs=[],
        ledger_refs=[],
    )

    # Verify that query retrieves VAR_2
    rejected = runner.belief_memory.get_rejected_or_retired_triggers()
    assert "VAR_2" in rejected

    # 2. T1: Run Condition C (Retrieval Enabled, Influence Blocked)
    # We expect all candidates to be compiled (no pruning)
    runner_c = MLCExperimentRunner()
    # Copy memory from runner
    runner_c.belief_memory = runner.belief_memory

    runner_c.run_lifecycle_with_competition(
        world,
        num_confounders=2,
        enable_prospective_filter=True,
        enable_learning=True,
        bypass_pruning=True,
    )
    # Check compiled candidates: should be 3 (1 causal + 2 confounders)
    # We can check propositions or ledger logs
    assert len(runner_c.propositions) == 1  # 1 selected winner
    # But let's check learning_audit_log
    assert not hasattr(runner_c, "learning_audit_log")

    # 3. T1: Run Condition D (Retrieval Enabled, Influence Enabled)
    # We expect candidate with trigger field "VAR_2" to be pruned/skipped
    runner_d = MLCExperimentRunner()
    runner_d.belief_memory = runner.belief_memory

    runner_d.run_lifecycle_with_competition(
        world,
        num_confounders=2,
        enable_prospective_filter=True,
        enable_learning=True,
        bypass_pruning=False,
    )

    # Check that candidate c2 (which uses VAR_2 in seed 101) was pruned
    assert hasattr(runner_d, "learning_audit_log")
    assert len(runner_d.learning_audit_log) == 1
    assert runner_d.learning_audit_log[0]["trigger_field"] == "VAR_2"
    assert runner_d.learning_audit_log[0]["action"] == "PRUNED"


def test_learning_loop_negative_controls():
    world = MLCSyntheticWorld.generate_world("C2", seed=102)
    runner = MLCExperimentRunner()
    runner.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}

    # 1. Irrelevant Memory Control
    # Stored rejection is for VAR_99 (which is not in this world)
    prop_irrelevant = {
        "proposition_id": "PROP_WORLD_DUMMY_irrelevant",
        "trigger_definition": {"field": "VAR_99"},
        "lifecycle_state": "REJECTED_PROPOSITION",
    }
    runner.belief_memory.store_record(
        prop=prop_irrelevant,
        lifecycle_history=["HYPOTHESIS", "REJECTED_PROPOSITION"],
        window_2_summary={},
        window_3_summary={},
        decision_dict={"decision": "REJECT", "reason_code": "CONTRADICTION"},
        ground_truth={},
        erc_refs=[],
        ledger_refs=[],
    )

    # Run Condition D (learning enabled)
    runner.run_lifecycle_with_competition(
        world,
        num_confounders=2,
        enable_prospective_filter=True,
        enable_learning=True,
        bypass_pruning=False,
    )
    # No pruning should have occurred because VAR_99 is not compiled
    assert not hasattr(runner, "learning_audit_log")

    # 2. Sham Retrieval Control
    # We supply a sham trigger that doesn't match any confounders in world
    runner_sham = MLCExperimentRunner()
    runner_sham.run_lifecycle_with_competition(
        world,
        num_confounders=2,
        enable_prospective_filter=True,
        enable_learning=True,
        bypass_pruning=False,
        sham_trigger="VAR_99",
    )
    assert not hasattr(runner_sham, "learning_audit_log")
