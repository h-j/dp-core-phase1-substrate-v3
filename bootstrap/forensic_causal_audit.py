import json
import math
import os
from pathlib import Path

import pandas as pd

# Load the simulation runs
csv_path = Path("data/synthetic_experiment_results/simulation_runs.csv")
output_dir = Path("data/synthetic_experiment_results")
output_dir.mkdir(parents=True, exist_ok=True)

if not csv_path.exists():
    print(f"Error: {csv_path} does not exist. Run run_synthetic_experiment first.")
    exit(1)

df = pd.read_csv(csv_path)

# 1. Setup matching groups
# Group by (world_id, seed) and get matched conditions
pivoted_precision = df.pivot(
    index=["world_id", "seed"], columns="condition", values="precision"
).reset_index()
pivoted_lift = df.pivot(
    index=["world_id", "seed"], columns="condition", values="mean_lift"
).reset_index()

agent_cols = [
    "Agent A (Raw Experience)",
    "Agent B (Heuristic Lift)",
    "Agent C (Evidence Representation)",
    "Agent D (Matched Random)",
    "Agent E (Counterfactual Inverted)",
]


# Helper to compute paired stats
def compute_paired_stats(df_pivot, col_x, col_y):
    # Compute X - Y (e.g. Agent C vs Agent X)
    diffs = df_pivot[col_x] - df_pivot[col_y]
    n = len(diffs)
    mean_diff = diffs.mean()
    std_diff = diffs.std(ddof=1)
    se_diff = std_diff / math.sqrt(n) if n > 0 else 0.0

    t_stat = mean_diff / se_diff if se_diff > 0 else 0.0

    # Paired t-test p-value approximation using normal approximation since N=300 is large
    # Z-test p-value
    z = abs(t_stat)
    # approximation of standard normal CDF survival function
    # 1 - 0.5 * (1 + erf(z / sqrt(2)))
    p_val = math.erfc(z / math.sqrt(2))

    # Cohen's d_z for paired differences
    cohens_d = mean_diff / std_diff if std_diff > 0 else 0.0

    # 95% Confidence Interval for mean difference
    margin = 1.96 * se_diff
    ci_lower = mean_diff - margin
    ci_upper = mean_diff + margin

    # Win / Tie / Loss count of col_x vs col_y
    wins = int((diffs > 0).sum())
    ties = int((diffs == 0).sum())
    losses = int((diffs < 0).sum())

    return {
        "mean_diff": float(mean_diff),
        "std_diff": float(std_diff),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "cohens_d": float(cohens_d),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "wins": wins,
        "ties": ties,
        "losses": losses,
        "win_rate": float(wins / n) if n > 0 else 0.0,
    }


# Compute paired stats for Agent C vs others
pairwise_results = {}
for cond in agent_cols:
    if cond == "Agent C (Evidence Representation)":
        continue
    pairwise_results[cond] = {
        "precision": compute_paired_stats(
            pivoted_precision, "Agent C (Evidence Representation)", cond
        ),
        "mean_lift": compute_paired_stats(
            pivoted_lift, "Agent C (Evidence Representation)", cond
        ),
    }

# 2. Per-world Decomposition
world_stats = []
for world_id, w_group in df.groupby("world_id"):
    world_name = w_group["world_name"].iloc[0]
    w_pivot_prec = w_group.pivot(index="seed", columns="condition", values="precision")
    w_pivot_lift = w_group.pivot(index="seed", columns="condition", values="mean_lift")

    cond_stats = {}
    for cond in agent_cols:
        cond_stats[cond] = {
            "mean_precision": float(w_pivot_prec[cond].mean()),
            "mean_lift": float(w_pivot_lift[cond].mean()),
        }

    # Compare C vs B in this world
    c_prec = w_pivot_prec["Agent C (Evidence Representation)"]
    b_prec = w_pivot_prec["Agent B (Heuristic Lift)"]
    prec_diff = c_prec.mean() - b_prec.mean()

    world_stats.append(
        {
            "world_id": int(world_id),
            "world_name": world_name,
            "agents": cond_stats,
            "c_minus_b_precision_diff": float(prec_diff),
            "winner": (
                "Agent C" if prec_diff > 0 else "Agent B" if prec_diff < 0 else "Tie"
            ),
        }
    )

from bootstrap.run_synthetic_experiment import WORLDS_CONFIG
from flows.synthetic_experiment.evaluation import evaluate_selection
# 3. Simulate alternative deterministic policies to compare against Agent C
# We run a quick evaluation of alternate ranking policies on the saved datasets
# To do this, we re-run the generator under the same seeds
from flows.synthetic_experiment.synthetic_harness import (
    SyntheticEnvironmentGenerator, compute_evidence, generate_candidates)

alt_policy_records = []
print("Evaluating alternative deterministic policies...")

for world_id, config in WORLDS_CONFIG.items():
    generator = SyntheticEnvironmentGenerator(
        signal_strength=config.get("signal_strength", 0.8),
        base_rate=config.get("base_rate", 0.5),
        noise_level=config.get("noise_level", 0.1),
        regime_persistence=config.get("regime_persistence", 0.9),
        regime_shifts=config.get("regime_shifts", [500]),
        sample_size=1000,
    )

    for seed in range(1, 31):  # 30 seeds
        generator.random_seed = seed + (world_id * 100)
        experiences = generator.generate()

        formation_experiences = experiences[:500]
        evaluation_experiences = experiences[500:]
        candidates = generate_candidates(50)
        evidence = compute_evidence(formation_experiences, candidates)

        # Policy: Max Signed Lift (Agent B)
        sel_max_signed = [
            e.proposition_id
            for e in sorted(evidence, key=lambda e: e.signed_lift, reverse=True)[:5]
        ]

        # Policy: Max Absolute Lift
        sel_max_abs = [
            e.proposition_id
            for e in sorted(evidence, key=lambda e: e.absolute_lift, reverse=True)[:5]
        ]

        # Policy: Max Activation Count (Frequency)
        sel_max_freq = [
            e.proposition_id
            for e in sorted(evidence, key=lambda e: e.activation_count, reverse=True)[
                :5
            ]
        ]

        # Policy: Shrinkage-adjusted Lift: signed_lift * (1.0 - uncertainty_score)
        sel_shrinkage = [
            e.proposition_id
            for e in sorted(
                evidence,
                key=lambda e: e.signed_lift * (1.0 - e.uncertainty_score),
                reverse=True,
            )[:5]
        ]

        # Policy: Threshold filter (activation_count >= 50) then sort by signed_lift
        filtered = [e for e in evidence if e.activation_count >= 50]
        if len(filtered) < 5:
            filtered = evidence
        sel_threshold = [
            e.proposition_id
            for e in sorted(filtered, key=lambda e: e.signed_lift, reverse=True)[:5]
        ]

        eval_max_signed = evaluate_selection(
            sel_max_signed, candidates, evaluation_experiences, 501, 1000
        )
        eval_max_abs = evaluate_selection(
            sel_max_abs, candidates, evaluation_experiences, 501, 1000
        )
        eval_max_freq = evaluate_selection(
            sel_max_freq, candidates, evaluation_experiences, 501, 1000
        )
        eval_shrinkage = evaluate_selection(
            sel_shrinkage, candidates, evaluation_experiences, 501, 1000
        )
        eval_threshold = evaluate_selection(
            sel_threshold, candidates, evaluation_experiences, 501, 1000
        )

        alt_policy_records.append(
            {
                "world_id": world_id,
                "seed": seed,
                "max_signed_precision": eval_max_signed["precision"],
                "max_signed_lift": eval_max_signed["mean_lift"],
                "max_abs_precision": eval_max_abs["precision"],
                "max_abs_lift": eval_max_abs["mean_lift"],
                "max_freq_precision": eval_max_freq["precision"],
                "max_freq_lift": eval_max_freq["mean_lift"],
                "shrinkage_precision": eval_shrinkage["precision"],
                "shrinkage_lift": eval_shrinkage["mean_lift"],
                "threshold_precision": eval_threshold["precision"],
                "threshold_lift": eval_threshold["mean_lift"],
            }
        )

df_alt = pd.DataFrame(alt_policy_records)

# Calculate averages for alternative policies
alt_summary = {
    "Max Signed Lift": {
        "mean_precision": float(df_alt["max_signed_precision"].mean()),
        "mean_lift": float(df_alt["max_signed_lift"].mean()),
    },
    "Max Absolute Lift": {
        "mean_precision": float(df_alt["max_abs_precision"].mean()),
        "mean_lift": float(df_alt["max_abs_lift"].mean()),
    },
    "Max Frequency": {
        "mean_precision": float(df_alt["max_freq_precision"].mean()),
        "mean_lift": float(df_alt["max_freq_lift"].mean()),
    },
    "Shrinkage Adjusted Lift": {
        "mean_precision": float(df_alt["shrinkage_precision"].mean()),
        "mean_lift": float(df_alt["shrinkage_lift"].mean()),
    },
    "Threshold + Signed Lift": {
        "mean_precision": float(df_alt["threshold_precision"].mean()),
        "mean_lift": float(df_alt["threshold_lift"].mean()),
    },
}

# Save audit results to JSON
audit_report = {
    "pairwise_matched_tests": pairwise_results,
    "world_decomposition": world_stats,
    "alternative_policies": alt_summary,
}

with open(output_dir / "s1_audit_data.json", "w") as f:
    json.dump(audit_report, f, indent=2)

print(
    "Forensic audit analysis completed. Results written to data/synthetic_experiment_results/s1_audit_data.json"
)
