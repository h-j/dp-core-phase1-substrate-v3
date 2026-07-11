import json
import os
from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld

def run_learning_experiment():
    print("=== STARTING MILESTONE 7 MINIMAL CAUSAL LEARNING LOOP EXPERIMENT ===")
    
    start_seed = 101
    end_seed = 150
    num_worlds = end_seed - start_seed + 1
    
    pruning_triggered_seeds = []
    
    # Budgets spent aggregates across seeds where pruning was triggered
    cond_c_comp_budget = 0
    cond_c_ev_budget = 0
    cond_d_comp_budget = 0
    cond_d_ev_budget = 0
    
    cond_c_candidates_count = 0
    cond_d_candidates_count = 0

    for seed in range(start_seed, end_seed + 1):
        world = MLCSyntheticWorld.generate_world("C2", seed=seed)
        
        # 1. T0: Populate memory using standard competition
        runner_t0 = MLCExperimentRunner()
        runner_t0.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
        runner_t0.run_lifecycle_with_competition(
            world, num_confounders=2, enable_prospective_filter=True, enable_learning=False
        )
        
        # Check if memory has a rejected confounder trigger
        rejected_triggers = runner_t0.belief_memory.get_rejected_or_retired_triggers()
        
        # 2. T1: Run Condition C (Retrieval Enabled, Influence Blocked)
        runner_c = MLCExperimentRunner()
        runner_c.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
        # Inject T0 memory
        runner_c.belief_memory.records = [r for r in runner_t0.belief_memory.records]
        
        runner_c.run_lifecycle_with_competition(
            world,
            num_confounders=2,
            enable_prospective_filter=True,
            enable_learning=True,
            bypass_pruning=True
        )
        
        # 3. T1: Run Condition D (Retrieval Enabled, Influence Enabled)
        runner_d = MLCExperimentRunner()
        runner_d.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
        # Inject T0 memory
        runner_d.belief_memory.records = [r for r in runner_t0.belief_memory.records]
        
        runner_d.run_lifecycle_with_competition(
            world,
            num_confounders=2,
            enable_prospective_filter=True,
            enable_learning=True,
            bypass_pruning=False
        )
        
        # Check if learning pruning was triggered on this seed
        pruned_logs = getattr(runner_d, "learning_audit_log", [])
        if pruned_logs:
            pruning_triggered_seeds.append(seed)
            # Accumulate metrics
            # Budget consumed = starting budget (1000) - current budget
            cond_c_comp_budget += (1000 - runner_c.erc.budgets["COMPILATION"])
            cond_c_ev_budget += (1000 - runner_c.erc.budgets["EVIDENCE"])
            
            cond_d_comp_budget += (1000 - runner_d.erc.budgets["COMPILATION"])
            cond_d_ev_budget += (1000 - runner_d.erc.budgets["EVIDENCE"])
            
            # Count compiled candidates
            # Condition C compiles 3 candidates (1 correct + 2 confounders)
            cond_c_candidates_count += 3
            # Condition D compiles 3 - pruned_count
            cond_d_candidates_count += (3 - len(pruned_logs))

    total_triggered = len(pruning_triggered_seeds)
    print(f"\nPruning was triggered on {total_triggered} seeds out of {num_worlds} runs.")
    
    summary = {
        "scientific_manifest": "MILESTONE_7_MINIMAL_CAUSAL_LEARNING_LOOP",
        "primary_seeds": f"{start_seed} to {end_seed}",
        "total_seeds_evaluated": num_worlds,
        "pruning_triggered_seeds_count": total_triggered,
        "pruning_triggered_seeds_list": pruning_triggered_seeds,
        "condition_c_influence_blocked": {
            "mean_compiled_candidates": (cond_c_candidates_count / total_triggered) if total_triggered > 0 else 0,
            "mean_compilation_budget_spent": (cond_c_comp_budget / total_triggered) if total_triggered > 0 else 0,
            "mean_evidence_budget_spent": (cond_c_ev_budget / total_triggered) if total_triggered > 0 else 0
        },
        "condition_d_influence_enabled": {
            "mean_compiled_candidates": (cond_d_candidates_count / total_triggered) if total_triggered > 0 else 0,
            "mean_compilation_budget_spent": (cond_d_comp_budget / total_triggered) if total_triggered > 0 else 0,
            "mean_evidence_budget_spent": (cond_d_ev_budget / total_triggered) if total_triggered > 0 else 0
        }
    }
    
    print("\n=== EXPERIMENTAL LEARNING LOOP RUN SUMMARY ===")
    print(json.dumps(summary, indent=2))
    
    os.makedirs("data", exist_ok=True)
    with open("data/learning_loop_experiment_results.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n✓ Verification manifest written to data/learning_loop_experiment_results.json.")

if __name__ == "__main__":
    run_learning_experiment()
