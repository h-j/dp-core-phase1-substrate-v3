import argparse
import json
import os
from pathlib import Path

import pandas as pd

from flows.synthetic_experiment.agents import (AgentA, AgentB, AgentC, AgentD,
                                               AgentE)
from flows.synthetic_experiment.evaluation import (evaluate_selection,
                                                   run_anova_and_stats)
from flows.synthetic_experiment.synthetic_harness import (
    SyntheticEnvironmentGenerator, compute_evidence, generate_candidates)

# Configuration for the 10 Synthetic Worlds
WORLDS_CONFIG = {
    1: {
        "name": "Stable Baseline",
        "signal_strength": 0.8,
        "noise_level": 0.1,
        "regime_persistence": 0.9,
        "regime_shifts": [500],
    },
    2: {
        "name": "High Noise",
        "signal_strength": 0.8,
        "noise_level": 0.3,
        "regime_persistence": 0.9,
        "regime_shifts": [500],
    },
    3: {
        "name": "Extreme Noise",
        "signal_strength": 0.7,
        "noise_level": 0.4,
        "regime_persistence": 0.9,
        "regime_shifts": [500],
    },
    4: {
        "name": "Strong Signal",
        "signal_strength": 0.9,
        "noise_level": 0.05,
        "regime_persistence": 0.9,
        "regime_shifts": [500],
    },
    5: {
        "name": "Unbalanced Base Rate",
        "signal_strength": 0.8,
        "noise_level": 0.1,
        "regime_persistence": 0.9,
        "regime_shifts": [500],
        "base_rate": 0.6,
    },
    6: {
        "name": "High Persistence Regimes",
        "signal_strength": 0.8,
        "noise_level": 0.1,
        "regime_persistence": 0.96,
        "regime_shifts": [500],
    },
    7: {
        "name": "Low Persistence Regimes",
        "signal_strength": 0.8,
        "noise_level": 0.1,
        "regime_persistence": 0.7,
        "regime_shifts": [500],
    },
    8: {
        "name": "Multiple Shifts",
        "signal_strength": 0.8,
        "noise_level": 0.1,
        "regime_persistence": 0.9,
        "regime_shifts": [300, 700],
    },
    9: {
        "name": "Low Noise Stable",
        "signal_strength": 0.85,
        "noise_level": 0.02,
        "regime_persistence": 0.9,
        "regime_shifts": [500],
    },
    10: {
        "name": "Moderate Noise Shift",
        "signal_strength": 0.75,
        "noise_level": 0.15,
        "regime_persistence": 0.85,
        "regime_shifts": [400, 800],
    },
}


def run_experiment(
    num_seeds: int = 30,
    mock_llm: bool = True,
    output_dir: str = "data/synthetic_experiment_results",
) -> None:
    print(f"Starting Synthetic Belief Learning Harness (Experiment S1)")
    print(f"Seeds: {num_seeds} | Mock LLM: {mock_llm}\n")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    records = []

    for world_id, config in WORLDS_CONFIG.items():
        print(f"Running World {world_id}: {config['name']}...")

        # Setup environment generator
        generator = SyntheticEnvironmentGenerator(
            signal_strength=config.get("signal_strength", 0.8),
            base_rate=config.get("base_rate", 0.5),
            noise_level=config.get("noise_level", 0.1),
            regime_persistence=config.get("regime_persistence", 0.9),
            regime_shifts=config.get("regime_shifts", [500]),
            sample_size=1000,
        )

        for seed in range(1, num_seeds + 1):
            generator.random_seed = seed + (world_id * 100)
            experiences = generator.generate()

            # Split into Formation and Evaluation (Temporal Isolation)
            formation_experiences = experiences[:500]
            evaluation_experiences = experiences[500:]

            # Generate candidate pool of 50 propositions
            candidates = generate_candidates(50)

            # Compute historical evidence objects on formation window
            evidence = compute_evidence(formation_experiences, candidates)

            # Define Agents
            agent_a = AgentA(mock_llm=mock_llm, seed=seed)
            agent_b_lift = AgentB(strategy="lift")
            agent_c = AgentC(mock_llm=mock_llm, seed=seed)
            agent_d = AgentD(seed=seed)
            agent_e = AgentE(mock_llm=mock_llm, seed=seed, manipulation="invert")

            # Selection step
            sel_a = agent_a.select(candidates, formation_experiences, evidence, count=5)
            sel_b_lift = agent_b_lift.select(evidence, count=5)
            sel_c = agent_c.select(candidates, evidence, count=5)
            sel_d = agent_d.select(candidates, count=5)
            sel_e = agent_e.select(candidates, evidence, count=5)

            # Evaluate out-of-sample metrics
            eval_a = evaluate_selection(
                sel_a, candidates, evaluation_experiences, 501, 1000
            )
            eval_b_lift = evaluate_selection(
                sel_b_lift, candidates, evaluation_experiences, 501, 1000
            )
            eval_c = evaluate_selection(
                sel_c, candidates, evaluation_experiences, 501, 1000
            )
            eval_d = evaluate_selection(
                sel_d, candidates, evaluation_experiences, 501, 1000
            )
            eval_e = evaluate_selection(
                sel_e, candidates, evaluation_experiences, 501, 1000
            )

            # Record results
            for cond, results in [
                ("Agent A (Raw Experience)", eval_a),
                ("Agent B (Heuristic Lift)", eval_b_lift),
                ("Agent C (Evidence Representation)", eval_c),
                ("Agent D (Matched Random)", eval_d),
                ("Agent E (Counterfactual Inverted)", eval_e),
            ]:
                records.append(
                    {
                        "world_id": world_id,
                        "world_name": config["name"],
                        "seed": seed,
                        "condition": cond,
                        "precision": results["precision"],
                        "mean_lift": results["mean_lift"],
                        "selected_ids": results["selected_ids"],
                    }
                )

    df = pd.DataFrame(records)

    # Perform ANOVA
    anova_res = run_anova_and_stats(df)

    # Compile Summary
    summary = {}
    print("\n=== EXPERIMENT SUMMARY ===")
    for cond, group in df.groupby("condition"):
        mean_precision = group["precision"].mean()
        mean_lift = group["mean_lift"].mean()
        summary[cond] = {
            "mean_precision": mean_precision,
            "mean_lift": mean_lift,
        }
        print(
            f"{cond:35s} | Precision: {mean_precision:.4f} | Realized Lift: {mean_lift:.4f}"
        )

    # Output Reports
    with open(out_path / "summary_report.json", "w") as f:
        json.dump(
            {
                "parameters": {
                    "num_seeds": num_seeds,
                    "mock_llm": mock_llm,
                },
                "anova": anova_res,
                "summary": summary,
            },
            f,
            indent=2,
        )

    df.to_csv(out_path / "simulation_runs.csv", index=False)

    # Generate Markdown Report
    with open(out_path / "experiment_report.md", "w") as f:
        f.write("# Experiment S1: Synthetic Belief Learning Harness Report\n\n")
        f.write(f"- **Total Worlds**: {len(WORLDS_CONFIG)}\n")
        f.write(f"- **Seeds per World**: {num_seeds}\n")
        f.write(f"- **Total Simulation Runs**: {len(df)}\n")
        f.write(
            f"- **LLM Execution Mode**: {'Mock Mode' if mock_llm else 'Ollama/Local'}\n\n"
        )

        f.write("## Overall Agent Performance\n\n")
        f.write(
            "| Agent Condition | Mean Precision (P@K) | Mean Realized Lift (OOS) |\n"
        )
        f.write("| --- | --- | --- |\n")
        for cond, metrics in summary.items():
            f.write(
                f"| {cond} | {metrics['mean_precision']:.4f} | {metrics['mean_lift']:.4f} |\n"
            )

        f.write("\n## Statistical ANOVA Results\n\n")
        for metric, res in anova_res.items():
            f.write(f"### Metric: {metric.capitalize()}\n")
            f.write(f"- **F-Statistic**: {res['F_statistic']:.4f}\n")
            f.write(f"- **p-value**: {res['p_value']}\n")
            f.write(
                f"- **Degrees of Freedom**: Between={res['df_between']}, Within={res['df_within']}\n\n"
            )
            f.write("#### Group Means:\n")
            for grp, mn in res["group_means"].items():
                f.write(f"  - **{grp}**: {mn:.4f}\n")
            f.write("\n")

    print(f"\nReport and raw logs written to {out_path}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Experiment S1 Synthetic Belief Learning Harness"
    )
    parser.add_argument(
        "--seeds", type=int, default=30, help="Number of seeds to run per world"
    )
    parser.add_argument(
        "--real-llm",
        action="store_true",
        help="Run with actual local Ollama LLM instead of mock fallback",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/synthetic_experiment_results",
        help="Output directory",
    )
    args = parser.parse_args()

    run_experiment(
        num_seeds=args.seeds, mock_llm=not args.real_llm, output_dir=args.output
    )
