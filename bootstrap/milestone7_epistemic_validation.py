import json
import os
from typing import Dict, Any, List
from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld

def run_experiment_on_range(start_seed: int, end_seed: int) -> Dict[str, Any]:
    print(f"Executing MLC Epistemic Validation on seeds {start_seed} to {end_seed}...")
    
    family_a_triggered = 0
    family_a_c_correct = 0
    family_a_d_correct = 0
    family_a_c_comp_budget = 0
    family_a_d_comp_budget = 0
    family_a_c_ev_budget = 0
    family_a_d_ev_budget = 0
    family_a_c_val_budget = 0
    family_a_d_val_budget = 0

    family_b_triggered = 0
    family_b_c_correct = 0
    family_b_d_correct = 0
    family_b_c_comp_budget = 0
    family_b_d_comp_budget = 0
    family_b_c_ev_budget = 0
    family_b_d_ev_budget = 0
    family_b_c_val_budget = 0
    family_b_d_val_budget = 0

    # Evaluated seeds
    for seed in range(start_seed, end_seed + 1):
        world_t0 = MLCSyntheticWorld.generate_world("C2", seed=seed)
        
        # T0: Populate memory
        runner_t0 = MLCExperimentRunner()
        runner_t0.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
        runner_t0.run_lifecycle_with_competition(
            world_t0, num_confounders=2, enable_prospective_filter=True, enable_learning=False
        )
        
        rejected_triggers = runner_t0.belief_memory.get_rejected_or_retired_triggers()
        if not rejected_triggers:
            continue
            
        # ----------------------------------------------------
        # FAMILY A: Stable Confounder (T1 seed == T0 seed)
        # ----------------------------------------------------
        family_a_triggered += 1
        
        # Condition C (Influence Blocked)
        runner_c = MLCExperimentRunner()
        runner_c.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
        runner_c.belief_memory.records = [r for r in runner_t0.belief_memory.records]
        runner_c.run_lifecycle_with_competition(
            world_t0, num_confounders=2, enable_prospective_filter=True, enable_learning=True, bypass_pruning=True
        )
        
        # Condition D (Influence Enabled)
        runner_d = MLCExperimentRunner()
        runner_d.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
        runner_d.belief_memory.records = [r for r in runner_t0.belief_memory.records]
        runner_d.run_lifecycle_with_competition(
            world_t0, num_confounders=2, enable_prospective_filter=True, enable_learning=True, bypass_pruning=False
        )
        
        # Epistemic Metric for Family A: Selection of correct causal winner (_c1)
        c1_id = f"PROP_WORLD_C2_SEED_{seed}_c1"
        
        c_winner = next((p for p in runner_c.propositions if p["proposition_id"] == c1_id), None)
        if c_winner:
            family_a_c_correct += 1
            
        d_winner = next((p for p in runner_d.propositions if p["proposition_id"] == c1_id), None)
        if d_winner:
            family_a_d_correct += 1

        # Resource spent
        family_a_c_comp_budget += (1000 - runner_c.erc.budgets["COMPILATION"])
        family_a_d_comp_budget += (1000 - runner_d.erc.budgets["COMPILATION"])
        family_a_c_ev_budget += (1000 - runner_c.erc.budgets["EVIDENCE"])
        family_a_d_ev_budget += (1000 - runner_d.erc.budgets["EVIDENCE"])
        family_a_c_val_budget += (1000 - runner_c.erc.budgets["VALIDATION"])
        family_a_d_val_budget += (1000 - runner_d.erc.budgets["VALIDATION"])

        # ----------------------------------------------------
        # FAMILY B: Context Shift
        # Find a seed where rejected_triggers[0] is the true causal trigger
        # ----------------------------------------------------
        target_var = rejected_triggers[0]
        shift_seed = 1000
        shift_world = None
        while shift_seed < 5000:
            world_check = MLCSyntheticWorld.generate_world("C2", seed=shift_seed)
            if world_check["trigger_var"] == target_var:
                shift_world = world_check
                break
            shift_seed += 1
            
        if shift_world:
            family_b_triggered += 1
            
            # T1 Condition C (Pruning Blocked)
            runner_b_c = MLCExperimentRunner()
            runner_b_c.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
            runner_b_c.belief_memory.records = [r for r in runner_t0.belief_memory.records]
            runner_b_c.run_lifecycle_with_competition(
                shift_world, num_confounders=2, enable_prospective_filter=True, enable_learning=True, bypass_pruning=True
            )
            
            # T1 Condition D (Pruning Enabled)
            runner_b_d = MLCExperimentRunner()
            runner_b_d.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
            runner_b_d.belief_memory.records = [r for r in runner_t0.belief_memory.records]
            runner_b_d.run_lifecycle_with_competition(
                shift_world, num_confounders=2, enable_prospective_filter=True, enable_learning=True, bypass_pruning=False
            )
            
            # Epistemic Metric for Family B: Selection of the true causal winner
            shift_c1_id = f"PROP_WORLD_C2_SEED_{shift_seed}_c1"
            
            c_b_winner = next((p for p in runner_b_c.propositions if p["proposition_id"] == shift_c1_id), None)
            if c_b_winner:
                family_b_c_correct += 1
                
            d_b_winner = next((p for p in runner_b_d.propositions if p["proposition_id"] == shift_c1_id), None)
            if d_b_winner:
                family_b_d_correct += 1

            # Resource spent
            family_b_c_comp_budget += (1000 - runner_b_c.erc.budgets["COMPILATION"])
            family_b_d_comp_budget += (1000 - runner_b_d.erc.budgets["COMPILATION"])
            family_b_c_ev_budget += (1000 - runner_b_c.erc.budgets["EVIDENCE"])
            family_b_d_ev_budget += (1000 - runner_b_d.erc.budgets["EVIDENCE"])
            family_b_c_val_budget += (1000 - runner_b_c.erc.budgets["VALIDATION"])
            family_b_d_val_budget += (1000 - runner_b_d.erc.budgets["VALIDATION"])

    # Compute selection rates
    family_a_c_rate = (family_a_c_correct / family_a_triggered) if family_a_triggered > 0 else 0.0
    family_a_d_rate = (family_a_d_correct / family_a_triggered) if family_a_triggered > 0 else 0.0
    family_b_c_rate = (family_b_c_correct / family_b_triggered) if family_b_triggered > 0 else 0.0
    family_b_d_rate = (family_b_d_correct / family_b_triggered) if family_b_triggered > 0 else 0.0

    # Primary epistemic metric: true causal selection rate difference
    # Under Family A, it should be neutral/0 (learning preserves selection rate).
    # Under Family B, it should degrade (Condition D true selection rate < Condition C selection rate).
    epistemic_metric_diff_a = family_a_d_rate - family_a_c_rate
    epistemic_metric_diff_b = family_b_d_rate - family_b_c_rate

    # Evidence sufficiency check (at least 2 triggered runs per family)
    evidence_sufficiency_satisfied = (family_a_triggered >= 2 and family_b_triggered >= 2)

    return {
        "start_seed": start_seed,
        "end_seed": end_seed,
        "evidence_sufficiency_satisfied": evidence_sufficiency_satisfied,
        "epistemic_metric_measured": True,
        "primary_epistemic_metric": "true_causal_selection_rate",
        "family_a_stable_confounder": {
            "triggered_events": family_a_triggered,
            "condition_c_selection_rate": family_a_c_rate,
            "condition_d_selection_rate": family_a_d_rate,
            "selection_rate_diff": epistemic_metric_diff_a,
            "mean_compilation_budget_saved": ((family_a_c_comp_budget - family_a_d_comp_budget) / family_a_triggered) if family_a_triggered > 0 else 0.0,
            "mean_evidence_budget_saved": ((family_a_c_ev_budget - family_a_d_ev_budget) / family_a_triggered) if family_a_triggered > 0 else 0.0,
            "mean_validation_budget_saved": ((family_a_c_val_budget - family_a_d_val_budget) / family_a_triggered) if family_a_triggered > 0 else 0.0,
        },
        "family_b_context_shift": {
            "triggered_events": family_b_triggered,
            "condition_c_selection_rate": family_b_c_rate,
            "condition_d_selection_rate": family_b_d_rate,
            "selection_rate_diff": epistemic_metric_diff_b,
            "mean_compilation_budget_saved": ((family_b_c_comp_budget - family_b_d_comp_budget) / family_b_triggered) if family_b_triggered > 0 else 0.0,
            "mean_evidence_budget_saved": ((family_b_c_ev_budget - family_b_d_ev_budget) / family_b_triggered) if family_b_triggered > 0 else 0.0,
            "mean_validation_budget_saved": ((family_b_c_val_budget - family_b_d_val_budget) / family_b_triggered) if family_b_triggered > 0 else 0.0,
        }
    }

if __name__ == "__main__":
    # Primary execution (seeds 151 to 350)
    results = run_experiment_on_range(151, 350)
    print("\nPrimary Results (151-350):")
    print(json.dumps(results, indent=2))
    
    os.makedirs("data", exist_ok=True)
    with open("data/epistemic_effect_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✓ Primary results written to data/epistemic_effect_validation_results.json")
