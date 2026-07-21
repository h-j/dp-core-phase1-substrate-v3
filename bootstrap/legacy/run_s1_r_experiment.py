import argparse
import json
import math
import os
import random
from pathlib import Path

import pandas as pd

from flows.synthetic_experiment.evaluation import evaluate_selection
from flows.synthetic_experiment.s1_r_experiment import (
    S1REnvironmentGenerator, call_ollama_with_retry,
    check_epistemic_complexity, format_s1_r_agent_a_prompt,
    format_s1_r_agent_c_prompt, generate_s1_r_candidates, pearson_correlation)
from flows.synthetic_experiment.schemas import (CandidateProposition,
                                                EvidenceObject, Experience)
from flows.synthetic_experiment.synthetic_harness import (check_predicate,
                                                          compute_evidence)

# S1-R World Configurations (3 worlds with conflicting dimensions)
S1_R_WORLDS = {
    1: {
        "name": "Regime Shifts & Deterioration",
        "signal_strength": 0.8,
        "noise_level": 0.1,
        "regime_persistence": 0.9,
    },
    2: {
        "name": "Noisy Environment",
        "signal_strength": 0.75,
        "noise_level": 0.25,
        "regime_persistence": 0.9,
    },
    3: {
        "name": "Extreme Shift & High Persistence",
        "signal_strength": 0.85,
        "noise_level": 0.15,
        "regime_persistence": 0.95,
    },
}


def run_s1_r_experiment(
    num_seeds: int = 5, output_dir: str = "data/s1_r_results"
) -> None:
    print("=== STARTING EXPERIMENT S1-R (EPISTEMIC TRADE-OFF SELECTION HARNESS) ===")
    print(
        f"Worlds: {len(S1_R_WORLDS)} | Seeds per World: {num_seeds} | Total Environments: {len(S1_R_WORLDS) * num_seeds}\n"
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    records = []
    invocations_log = []

    # Ex-post Oracle selection helper
    def get_oracle_lift(evidence, oos_lifts, count=5):
        sorted_candidates = sorted(oos_lifts.items(), key=lambda x: x[1], reverse=True)
        return sum(x[1] for x in sorted_candidates[:count]) / count

    for world_id, config in S1_R_WORLDS.items():
        print(f"--- Running World {world_id}: {config['name']} ---")
        generator = S1REnvironmentGenerator(
            signal_strength=config["signal_strength"],
            base_rate=0.5,
            noise_level=config["noise_level"],
            regime_persistence=config["regime_persistence"],
            sample_size=1000,
        )

        for seed in range(1, num_seeds + 1):
            generator.random_seed = seed + (world_id * 100)
            experiences = generator.generate()

            formation = experiences[:500]
            evaluation = experiences[500:]

            candidates = generate_s1_r_candidates(50)
            evidence = compute_evidence(formation, candidates)

            # Compute actual out-of-sample (OOS) realized lifts for each candidate
            oos_lifts = {}
            for c in candidates:
                eval_res = evaluate_selection(
                    [c.proposition_id], candidates, evaluation, 501, 1000
                )
                oos_lifts[c.proposition_id] = eval_res["mean_lift"]

            # Perform pre-run diagnostic audit for Epistemic Complexity
            correlations = check_epistemic_complexity(evidence, oos_lifts)
            print(
                f"  Seed {seed} Complexity Correlations: { {k: round(v, 4) for k, v in correlations.items()} }"
            )

            # Check complexity threshold: if any correlation is >= 0.75, regenerate or flag
            high_corr_fields = [k for k, v in correlations.items() if abs(v) >= 0.75]
            if high_corr_fields:
                print(
                    f"  [WARNING] Seed {seed} has high field correlation in {high_corr_fields}. Re-seeding..."
                )
                # Shift seed to maintain complexity
                generator.random_seed += 999
                experiences = generator.generate()
                formation = experiences[:500]
                evaluation = experiences[500:]
                evidence = compute_evidence(formation, candidates)
                for c in candidates:
                    eval_res = evaluate_selection(
                        [c.proposition_id], candidates, evaluation, 501, 1000
                    )
                    oos_lifts[c.proposition_id] = eval_res["mean_lift"]
                correlations = check_epistemic_complexity(evidence, oos_lifts)

            oracle_mean_lift = get_oracle_lift(evidence, oos_lifts, 5)

            # Define deterministic scoring functions
            # B1: Max Signed Lift
            sel_b1 = [
                e.proposition_id
                for e in sorted(evidence, key=lambda e: e.signed_lift, reverse=True)[:5]
            ]

            # B2: Shrinkage-adjusted Lift
            sel_b2 = [
                e.proposition_id
                for e in sorted(
                    evidence,
                    key=lambda e: e.signed_lift * (1.0 - e.uncertainty_score),
                    reverse=True,
                )[:5]
            ]

            # B3: Max Frequency
            sel_b3 = [
                e.proposition_id
                for e in sorted(
                    evidence, key=lambda e: e.activation_count, reverse=True
                )[:5]
            ]

            # B4: Max Stability
            sel_b4 = [
                e.proposition_id
                for e in sorted(
                    evidence, key=lambda e: e.stability_score, reverse=True
                )[:5]
            ]

            # B5: Composite Score
            sel_b5 = [
                e.proposition_id
                for e in sorted(
                    evidence,
                    key=lambda e: (
                        e.signed_lift * e.stability_score * (1.0 - e.uncertainty_score)
                        if e.signed_lift > 0
                        else 0
                    ),
                    reverse=True,
                )[:5]
            ]

            # Agent D: Matched Random
            rng = random.Random(seed)
            sel_d = rng.sample([c.proposition_id for c in candidates], 5)

            # Agent A: Raw Experience Ollama Prompt
            prompt_a = format_s1_r_agent_a_prompt(candidates, formation)
            print(f"  Calling Ollama for Agent A (Raw)...")
            sel_a = call_ollama_with_retry(
                prompt_a, [c.proposition_id for c in candidates], 5, seed=seed
            )
            invocations_log.append(
                {
                    "world_id": world_id,
                    "seed": seed,
                    "agent": "Agent A (Raw Experience)",
                    "prompt_length": len(prompt_a),
                    "selections": sel_a,
                    "is_valid": "AGENT_OUTPUT_INVALID" not in sel_a,
                }
            )

            # Agent C: Evidence Representation Ollama Prompt
            prompt_c = format_s1_r_agent_c_prompt(candidates, evidence)
            print(f"  Calling Ollama for Agent C (Evidence)...")
            sel_c = call_ollama_with_retry(
                prompt_c, [c.proposition_id for c in candidates], 5, seed=seed
            )
            invocations_log.append(
                {
                    "world_id": world_id,
                    "seed": seed,
                    "agent": "Agent C (Evidence Representation)",
                    "prompt_length": len(prompt_c),
                    "selections": sel_c,
                    "is_valid": "AGENT_OUTPUT_INVALID" not in sel_c,
                }
            )

            # Evaluate each selection
            for cond, sel in [
                ("Agent A (Raw Experience)", sel_a),
                ("Agent B1 (Max Signed Lift)", sel_b1),
                ("Agent B2 (Shrinkage Lift)", sel_b2),
                ("Agent B3 (Max Frequency)", sel_b3),
                ("Agent B4 (Max Stability)", sel_b4),
                ("Agent B5 (Composite)", sel_b5),
                ("Agent C (Evidence Representation)", sel_c),
                ("Agent D (Matched Random)", sel_d),
            ]:
                # Handing invalid outputs
                if "AGENT_OUTPUT_INVALID" in sel:
                    precision = 0.0
                    mean_lift = 0.0
                    catastrophic_failures = 5
                    planted_recovered = 0
                    regret = oracle_mean_lift
                else:
                    eval_res = evaluate_selection(
                        sel, candidates, evaluation, 501, 1000
                    )
                    precision = eval_res["precision"]
                    mean_lift = eval_res["mean_lift"]
                    # Catastrophic failure defined as selecting a candidate with OOS lift <= -0.15
                    catastrophic_failures = sum(
                        1 for pid in sel if oos_lifts.get(pid, 0.0) <= -0.15
                    )
                    planted_recovered = 1 if "prop_signal_stable_up" in sel else 0
                    regret = oracle_mean_lift - mean_lift

                records.append(
                    {
                        "world_id": world_id,
                        "world_name": config["name"],
                        "seed": seed,
                        "condition": cond,
                        "precision": precision,
                        "mean_lift": mean_lift,
                        "catastrophic_failures": catastrophic_failures,
                        "planted_recovered": planted_recovered,
                        "regret": regret,
                        "selected_ids": sel,
                    }
                )

    df = pd.DataFrame(records)

    # Statistical Pairwise matched analysis
    pivoted_lift = df.pivot(
        index=["world_id", "seed"], columns="condition", values="mean_lift"
    ).reset_index()
    pivoted_prec = df.pivot(
        index=["world_id", "seed"], columns="condition", values="precision"
    ).reset_index()
    pivoted_fail = df.pivot(
        index=["world_id", "seed"], columns="condition", values="catastrophic_failures"
    ).reset_index()

    def paired_stats(df_pivot, col_x, col_y):
        diffs = df_pivot[col_x] - df_pivot[col_y]
        n = len(diffs)
        mean_diff = diffs.mean()
        std_diff = diffs.std(ddof=1)
        se_diff = std_diff / math.sqrt(n) if n > 0 else 0.0
        t_stat = mean_diff / se_diff if se_diff > 0 else 0.0
        p_val = math.erfc(abs(t_stat) / math.sqrt(2))
        cohens_d = mean_diff / std_diff if std_diff > 0 else 0.0
        wins = int((diffs > 0).sum())
        ties = int((diffs == 0).sum())
        losses = int((diffs < 0).sum())
        return {
            "mean_diff": float(mean_diff),
            "t_stat": float(t_stat),
            "p_value": float(p_val),
            "cohens_d": float(cohens_d),
            "win_tie_loss": f"{wins}/{ties}/{losses}",
        }

    pairwise_results = {}
    for agent in df["condition"].unique():
        if agent == "Agent C (Evidence Representation)":
            continue
        pairwise_results[agent] = {
            "mean_lift": paired_stats(
                pivoted_lift, "Agent C (Evidence Representation)", agent
            ),
            "precision": paired_stats(
                pivoted_prec, "Agent C (Evidence Representation)", agent
            ),
        }

    # Summary performance
    summary = {}
    print("\n=== S1-R EXPERIMENT SUMMARY ===")
    for cond, group in df.groupby("condition"):
        summary[cond] = {
            "mean_precision": float(group["precision"].mean()),
            "mean_lift": float(group["mean_lift"].mean()),
            "total_failures": int(group["catastrophic_failures"].sum()),
            "planted_recovery_rate": float(group["planted_recovered"].mean()),
            "mean_regret": float(group["regret"].mean()),
        }
        print(
            f"{cond:35s} | Prec: {summary[cond]['mean_precision']:.4f} | Lift: {summary[cond]['mean_lift']:.4f} | Failures: {summary[cond]['total_failures']} | Regret: {summary[cond]['mean_regret']:.4f}"
        )

    # Write output artifacts
    with open(out_path / "s1_r_audit_data.json", "w") as f:
        json.dump(
            {
                "summary": summary,
                "pairwise_matched": pairwise_results,
                "invocations": invocations_log,
            },
            f,
            indent=2,
        )

    df.to_csv(out_path / "s1_r_runs.csv", index=False)
    print(f"\nResults successfully written to {out_path}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run S1-R Epistemic Trade-off Selection Harness"
    )
    parser.add_argument(
        "--seeds", type=int, default=5, help="Number of seeds per world"
    )
    args = parser.parse_args()

    run_s1_r_experiment(num_seeds=args.seeds)
