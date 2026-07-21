import json
import os

from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld
from flows.minimal_learning_cycle.validity_gates import MLCValidityGates


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

    # Validity gate log aggregators
    b_erc_logs = []
    b_frozen = []
    b_dec = []
    c_erc_logs = []
    c_frozen = []
    c_dec = []

    for seed in range(start_seed, end_seed + 1):
        world = MLCSyntheticWorld.generate_world("C2", seed=seed)

        # 1. Condition A (No Selection Baseline)
        runner_a = MLCExperimentRunner()
        runner_a.erc.budgets = {
            "COMPILATION": 10000,
            "EVIDENCE": 10000,
            "VALIDATION": 10000,
        }
        dec_a = runner_a.run_lifecycle_with_competition(
            world, num_confounders=0, enable_prospective_filter=True
        )
        cond_a_decisions.append(dec_a["decision"])

        # 2. Condition B (Selection, No Prospective Filter)
        runner_b = MLCExperimentRunner()
        runner_b.erc.budgets = {
            "COMPILATION": 10000,
            "EVIDENCE": 10000,
            "VALIDATION": 10000,
        }
        dec_b = runner_b.run_lifecycle_with_competition(
            world, num_confounders=num_confounders, enable_prospective_filter=False
        )
        dec_b_val = dec_b["decision"]
        cond_b_decisions.append(dec_b_val)
        winner_b = runner_b.propositions[0]["proposition_id"]
        cond_b_winners.append(winner_b)

        retro_metrics = next(
            m
            for m in runner_b.intrinsic_measurements
            if m["proposition_id"] == winner_b
        )
        pro_metrics = next(
            m
            for m in runner_b.prospective_measurements
            if m["proposition_id"] == winner_b
        )
        cond_b_optimism.append(
            retro_metrics["comparative_effect"] - pro_metrics["comparative_effect"]
        )

        if "_c1" in winner_b:
            b_causal_outcomes[dec_b_val] += 1
        else:
            b_confounder_outcomes[dec_b_val] += 1

        b_erc_logs.extend(runner_b.erc.logs)
        b_frozen.extend(runner_b.frozen_candidates)
        b_dec.extend(runner_b.decisions)

        # 3. Condition C (Selection, With Prospective Filter)
        runner_c = MLCExperimentRunner()
        runner_c.erc.budgets = {
            "COMPILATION": 10000,
            "EVIDENCE": 10000,
            "VALIDATION": 10000,
        }
        dec_c = runner_c.run_lifecycle_with_competition(
            world, num_confounders=num_confounders, enable_prospective_filter=True
        )
        dec_c_val = dec_c["decision"]
        cond_c_decisions.append(dec_c_val)
        winner_c = runner_c.propositions[0]["proposition_id"]
        cond_c_winners.append(winner_c)

        retro_metrics_c = next(
            m
            for m in runner_c.intrinsic_measurements
            if m["proposition_id"] == winner_c
        )
        pro_metrics_c = next(
            m
            for m in runner_c.prospective_measurements
            if m["proposition_id"] == winner_c
        )
        cond_c_optimism.append(
            retro_metrics_c["comparative_effect"] - pro_metrics_c["comparative_effect"]
        )

        if "_c1" in winner_c:
            c_causal_outcomes[dec_c_val] += 1
        else:
            c_confounder_outcomes[dec_c_val] += 1

        c_erc_logs.extend(runner_c.erc.logs)
        c_frozen.extend(runner_c.frozen_candidates)
        c_dec.extend(runner_c.decisions)

    total = num_worlds

    # Confounding and True winners counts
    b_total_causal = sum(b_causal_outcomes.values())
    b_total_confounder = sum(b_confounder_outcomes.values())

    c_total_causal = sum(c_causal_outcomes.values())
    c_total_confounder = sum(c_confounder_outcomes.values())

    mean_optimism_b = sum(cond_b_optimism) / len(cond_b_optimism)
    mean_optimism_c = sum(cond_c_optimism) / len(cond_c_optimism)

    # 4. RUN VALIDITY GATES FOR WIRED COMPLIANCE
    g1_b = MLCValidityGates.verify_gate_1_temporal_isolation(b_erc_logs, b_dec)
    g7_b = MLCValidityGates.verify_gate_7_erc_authorization(b_erc_logs, b_frozen)
    g8_b = MLCValidityGates.verify_gate_8_candidate_immutability(b_frozen)

    g1_c = MLCValidityGates.verify_gate_1_temporal_isolation(c_erc_logs, c_dec)
    g7_c = MLCValidityGates.verify_gate_7_erc_authorization(c_erc_logs, c_frozen)
    g8_c = MLCValidityGates.verify_gate_8_candidate_immutability(c_frozen)

    # Enforce gates
    assert (
        g1_b["status"] == "PASS"
    ), f"Condition B Gate 1 Temporal Isolation Violation: {g1_b['evidence']}"
    assert (
        g7_b["status"] == "PASS"
    ), f"Condition B Gate 7 ERC Authorization Violation: {g7_b['evidence']}"
    assert (
        g8_b["status"] == "PASS"
    ), f"Condition B Gate 8 Immutability Violation: {g8_b['evidence']}"
    assert (
        g1_c["status"] == "PASS"
    ), f"Condition C Gate 1 Temporal Isolation Violation: {g1_c['evidence']}"
    assert (
        g7_c["status"] == "PASS"
    ), f"Condition C Gate 7 ERC Authorization Violation: {g7_c['evidence']}"
    assert (
        g8_c["status"] == "PASS"
    ), f"Condition C Gate 8 Immutability Violation: {g8_c['evidence']}"

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
            "confounder_outcomes": b_confounder_outcomes,
        },
        "condition_c_selection_with_filter": {
            "admit_rate": cond_c_decisions.count("ADMIT") / total,
            "false_winner_rate": c_total_confounder / total,
            "mean_selection_optimism": mean_optimism_c,
            "decisions": {d: cond_c_decisions.count(d) for d in set(cond_c_decisions)},
            "true_causal_outcomes": c_causal_outcomes,
            "confounder_outcomes": c_confounder_outcomes,
        },
        "validity_gates_compliance": {
            "condition_b": {
                "gate_1": g1_b,
                "gate_7": g7_b,
                "gate_8": g8_b,
            },
            "condition_c": {
                "gate_1": g1_c,
                "gate_7": g7_c,
                "gate_8": g8_c,
            },
        },
    }

    print("\n=== EXPERIMENTAL SELECTION RISK PRIMARY RUN SUMMARY ===")
    print(json.dumps(summary, indent=2))

    os.makedirs("data", exist_ok=True)
    with open("data/selection_risk_experiment_results.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    run_experiment()
