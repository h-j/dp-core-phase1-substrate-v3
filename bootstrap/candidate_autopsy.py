import json
import os
from pathlib import Path

import pandas as pd

from bootstrap.run_synthetic_experiment import WORLDS_CONFIG
from flows.synthetic_experiment.agents import AgentB, AgentC
from flows.synthetic_experiment.evaluation import get_ground_truth_propositions
from flows.synthetic_experiment.synthetic_harness import (
    SyntheticEnvironmentGenerator, compute_evidence, generate_candidates)

output_dir = Path("data/synthetic_experiment_results")

# We will collect selected candidate characteristics for Agent B and Agent C
autopsy_records = []

for world_id, config in WORLDS_CONFIG.items():
    generator = SyntheticEnvironmentGenerator(
        signal_strength=config.get("signal_strength", 0.8),
        base_rate=config.get("base_rate", 0.5),
        noise_level=config.get("noise_level", 0.1),
        regime_persistence=config.get("regime_persistence", 0.9),
        regime_shifts=config.get("regime_shifts", [500]),
        sample_size=1000,
    )

    for seed in range(1, 31):
        generator.random_seed = seed + (world_id * 100)
        experiences = generator.generate()

        formation_experiences = experiences[:500]
        evaluation_experiences = experiences[500:]
        candidates = generate_candidates(50)
        evidence = compute_evidence(formation_experiences, candidates)
        evidence_map = {e.proposition_id: e for e in evidence}

        true_props = get_ground_truth_propositions(
            501, 1000, config.get("regime_shifts", [500])[0]
        )

        # Agent B (Heuristic Lift) selections
        agent_b = AgentB(strategy="lift")
        sel_b = agent_b.select(evidence, count=5)

        # Agent C (Evidence Representation) selections
        agent_c = AgentC(mock_llm=True, seed=seed)
        sel_c = agent_c.select(candidates, evidence, count=5)

        # Analyze B
        for pid in sel_b:
            ev = evidence_map[pid]
            autopsy_records.append(
                {
                    "agent": "Agent B (Heuristic Lift)",
                    "world_id": world_id,
                    "seed": seed,
                    "proposition_id": pid,
                    "training_signed_lift": ev.signed_lift,
                    "activation_count": ev.activation_count,
                    "stability_score": ev.stability_score,
                    "is_planted": pid in true_props,
                }
            )

        # Analyze C
        for pid in sel_c:
            ev = evidence_map[pid]
            autopsy_records.append(
                {
                    "agent": "Agent C (Evidence Representation)",
                    "world_id": world_id,
                    "seed": seed,
                    "proposition_id": pid,
                    "training_signed_lift": ev.signed_lift,
                    "activation_count": ev.activation_count,
                    "stability_score": ev.stability_score,
                    "is_planted": pid in true_props,
                }
            )

df_autopsy = pd.DataFrame(autopsy_records)

# Calculate averages per agent
autopsy_summary = {}
for agent, group in df_autopsy.groupby("agent"):
    autopsy_summary[agent] = {
        "mean_training_signed_lift": float(group["training_signed_lift"].mean()),
        "mean_activation_count": float(group["activation_count"].mean()),
        "mean_stability_score": float(group["stability_score"].mean()),
        "planted_selection_ratio": float(group["is_planted"].mean()),
    }

with open(output_dir / "candidate_autopsy_summary.json", "w") as f:
    json.dump(autopsy_summary, f, indent=2)

print("Candidate autopsy completed. Summary:")
print(json.dumps(autopsy_summary, indent=2))
