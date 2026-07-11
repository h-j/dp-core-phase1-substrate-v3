import json
import os
from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld

def run_experiment(num_worlds=50, num_confounders=5):
    # Diagnostic seeds: 1 to 50
    # Primary seeds: 51 to 100 (non-overlapping, frozen parameters)
    start_seed = 51
    end_seed = 51 + num_worlds - 1
    
    cond_a_decisions = []
    cond_b_decisions = []
    cond_c_decisions = []
    
    cond_b_winners = []
    cond_c_winners = []
    
    cond_b_optimism = []
    cond_c_optimism = []
    
    # Joint tracking for Condition B (Retrospective selection, decision based on Window 2)
    b_causal_outcomes = {"ADMIT": 0, "DEFER": 0, "REJECT": 0}
    b_confounder_outcomes = {"ADMIT": 0, "DEFER": 0, "REJECT": 0}
    
    # Joint tracking for Condition C (Retrospective selection, decision based on Window 3)
    c_causal_outcomes = {"ADMIT": 0, "DEFER": 0, "REJECT": 0}
    c_confounder_outcomes = {"ADMIT": 0, "DEFER": 0, "REJECT": 0}

    for seed in range(start_seed, end_seed + 1):
        world = MLCSyntheticWorld.generate_world("C2", seed=seed)
        
        # 1. Condition A (No Selection Baseline)
        runner_a = MLCExperimentRunner()
        runner_a.erc.budgets = {"COMPILATION": 10000, "EVIDENCE": 10000, "VALIDATION": 10000}
        dec_a = runner_a.run_lifecycle_with_competition(world, num_confounders=0, enable_prospective_filter=True)
        cond_a_decisions.append(dec_a["decision"])
        
        # 2. Condition B (Selection, No Prospective Filter)
        runner_b = MLCExperimentRunner()
        runner_b.erc.budgets = {"COMPILATION": 10000, "EVIDENCE": 10000, "VALIDATION": 10000}
        dec_b = runner_b.run_lifecycle_with_competition(world, num_confounders=num_confounders, enable_prospective_filter=False)
        dec_b_val = dec_b["decision"]
        cond_b_decisions.append(dec_b_val)
        winner_b = runner_b.propositions[0]["proposition_id"]
        cond_b_winners.append(winner_b)
        
        retro_metrics = next(m for m in runner_b.intrinsic_measurements if m["proposition_id"] == winner_b)
        pro_metrics = next(m for m in runner_b.prospective_measurements if m["proposition_id"] == winner_b)
        cond_b_optimism.append(retro_metrics["comparative_effect"] - pro_metrics["comparative_effect"])
        
        if "_c1" in winner_b:
            b_causal_outcomes[dec_b_val] += 1
        else:
            b_confounder_outcomes[dec_b_val] += 1
            
        # 3. Condition C (Selection, With Prospective Filter)
        runner_c = MLCExperimentRunner()
        runner_c.erc.budgets = {"COMPILATION": 10000, "EVIDENCE": 10000, "VALIDATION": 10000}
        dec_c = runner_c.run_lifecycle_with_competition(world, num_confounders=num_confounders, enable_prospective_filter=True)
        dec_c_val = dec_c["decision"]
        cond_c_decisions.append(dec_c_val)
        winner_c = runner_c.propositions[0]["proposition_id"]
        cond_c_winners.append(winner_c)
        
        retro_metrics_c = next(m for m in runner_c.intrinsic_measurements if m["proposition_id"] == winner_c)
        pro_metrics_c = next(m for m in runner_c.prospective_measurements if m["proposition_id"] == winner_c)
        cond_c_optimism.append(retro_metrics_c["comparative_effect"] - pro_metrics_c["comparative_effect"])
        
        if "_c1" in winner_c:
            c_causal_outcomes[dec_c_val] += 1
        else:
            c_confounder_outcomes[dec_c_val] += 1

    total = num_worlds
    
    # Confounding and True winners counts
    b_total_causal = sum(b_causal_outcomes.values())
    b_total_confounder = sum(b_confounder_outcomes.values())
    
    c_total_causal = sum(c_causal_outcomes.values())
    c_total_confounder = sum(c_confounder_outcomes.values())
    
    mean_optimism_b = sum(cond_b_optimism) / len(cond_b_optimism)
    mean_optimism_c = sum(cond_c_optimism) / len(cond_c_optimism)
    
    summary = {
        "diagnostic_seeds": "1 to 50",
        "primary_seeds": f"{start_seed} to {end_seed}",
        "seed_overlap_status": "STRICTLY_SEPARATED",
        "total_worlds": total,
        "num_confounders": num_confounders,
        "condition_a_baseline": {
            "admit_rate": cond_a_decisions.count("ADMIT") / total,
            "decisions": {d: cond_a_decisions.count(d) for d in set(cond_a_decisions)},
        },
        "condition_b_selection_no_filter": {
            "admit_rate": cond_b_decisions.count("ADMIT") / total,
            "false_winner_rate": b_total_confounder / total,
            "mean_selection_optimism": mean_optimism_b,
            "decisions": {d: cond_b_decisions.count(d) for d in set(cond_b_decisions)},
            "true_causal_outcomes": b_causal_outcomes,
            "confounder_outcomes": b_confounder_outcomes
        },
        "condition_c_selection_with_filter": {
            "admit_rate": cond_c_decisions.count("ADMIT") / total,
            "false_winner_rate": c_total_confounder / total,
            "mean_selection_optimism": mean_optimism_c,
            "decisions": {d: cond_c_decisions.count(d) for d in set(cond_c_decisions)},
            "true_causal_outcomes": c_causal_outcomes,
            "confounder_outcomes": c_confounder_outcomes
        }
    }
    
    print("\n=== EXPERIMENTAL SELECTION RISK PRIMARY RUN SUMMARY ===")
    print(json.dumps(summary, indent=2))
    
    os.makedirs("data", exist_ok=True)
    with open("data/selection_risk_experiment_results.json", "w") as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    run_experiment()
