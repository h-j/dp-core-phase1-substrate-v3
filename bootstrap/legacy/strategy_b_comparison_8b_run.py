import json
import os
import sys
from pathlib import Path

from config.settings import settings
from flows.minimal_learning_cycle.schemas import PropositionSchema
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow

# Force the Ollama model to llama3 (8B)
settings.OLLAMA_MODEL = "llama3"

# Sampling Rule: Same 6 days from Epoch 3
SAMPLED_DAYS = [0, 8, 16, 24, 32, 40]


class DummyAbstraction:
    def __init__(self, summary: str):
        self.abstraction_summary = summary


def evaluate_semantic_relation(base_claim: str, b_claim: str) -> dict:
    bc = base_claim.strip().lower().replace(".", "").replace(";", "")
    tc = b_claim.strip().lower().replace(".", "").replace(";", "")

    if bc == tc:
        return {
            "classification": "IDENTICAL_OR_EQUIVALENT",
            "rationale": "Literal match between baseline and Strategy B claim text.",
        }

    words_b = set(bc.split())
    words_t = set(tc.split())
    overlap = len(words_b.intersection(words_t)) / max(len(words_b), len(words_t))

    if overlap >= 0.8:
        return {
            "classification": "MINOR_NON_MATERIAL_VARIATION",
            "rationale": f"High lexical overlap ({overlap:.1f}) with minor prose variation.",
        }
    elif overlap >= 0.5:
        return {
            "classification": "MINOR_NON_MATERIAL_VARIATION",
            "rationale": f"Moderate lexical overlap ({overlap:.1f}); meaning is preserved but phrased differently.",
        }
    else:
        return {
            "classification": "MATERIAL_DISTORTION",
            "rationale": f"Low lexical overlap ({overlap:.1f}); potential causal distortion.",
        }


def run_comparison():
    print(
        f"Running Multi-Case Strategy B Comparison on Llama3 (8B) for {len(SAMPLED_DAYS)} days...",
        flush=True,
    )

    # Load baseline claims from findings of Epoch 3
    epoch3_path = Path(
        "/Users/hemantj/.gemini/antigravity-ide/brain/face4af3-acf5-4ebb-a5bd-ccb6af890aa2/multi_case_comparison_findings.json"
    )
    if not epoch3_path.exists():
        print(f"Error: Epoch 3 findings file not found at {epoch3_path}")
        return

    with open(epoch3_path, "r") as f:
        epoch3_data = json.load(f)

    baselines = {item["day"]: item["baseline_claim"] for item in epoch3_data}

    results = []

    for day in SAMPLED_DAYS:
        print(f"Processing Day {day:04d} under Llama3 (8B)...", flush=True)
        sys.stdout.flush()

        snapshot_path = Path(
            f"/Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/data/replay_snapshots/reliance/run_20260701_123929/day_{day:04d}.json"
        )
        with open(snapshot_path, "r") as f:
            data = json.load(f)

        abstraction = DummyAbstraction(data["observation"])
        market_memory_context = data.get("regime_history", {}).get(
            "subtype_memory", "No prior history."
        )
        current_market_observation = data["observation"]
        reflective_memory_summary = data.get("reflection", "No reflection.")
        regime_subtype = data.get("regime_subtype", "neutral")
        falsifiability_conditions = data.get("theory_falsifiability", [])
        regime_history = data.get("regime_history", {})

        # Run Strategy B (spiked) under llama3 (8B)
        os.environ["EKAMNET_STRATEGY_B_SPIKE"] = "1"
        flow_b = TheoryGenerationFlow()
        try:
            theory_b, _ = flow_b.process(
                abstraction=abstraction,
                market_memory_context=market_memory_context,
                current_market_observation=current_market_observation,
                reflective_memory_summary=reflective_memory_summary,
                regime_subtype=regime_subtype,
                falsifiability_conditions=falsifiability_conditions,
                regime_history=regime_history,
                step=day,
            )
            b_claim = theory_b.summary_structured.claim
            ts = theory_b.summary_structured
        except Exception as e:
            print(f"  Day {day} Strategy B under Llama3 (8B) failed: {e}", flush=True)
            continue

        # Check Proposition Compliance
        prop = {
            "proposition_id": f"PROP_DAY_{day:04d}",
            "source_hypothesis_id": f"HYP_DAY_{day:04d}",
            "trigger_definition": ts.trigger_definition,
            "target_definition": ts.target_definition,
            "scope_definition": ts.scope_definition,
            "expected_direction": ts.expected_direction,
            "contradiction_definition": ts.contradiction_definition,
            "specificity_definition": {"type": "deterministic"},
            "complexity_cost": 1.0,
            "generation_source": "strategy_b_generation_8b",
            "creation_timestamp": 12345.67,
            "lifecycle_state": "HYPOTHESIS",
        }
        schema_compliance = PropositionSchema.validate(prop)

        # Get baseline claim from Epoch 3 data
        base_claim = baselines.get(day, "Unknown Baseline")

        # Evaluate Semantic Preservation
        eval_findings = evaluate_semantic_relation(base_claim, b_claim)

        case_result = {
            "day": day,
            "baseline_claim": base_claim,
            "strategy_b_claim": b_claim,
            "schema_compliance": schema_compliance,
            "semantic_preservation_class": eval_findings["classification"],
            "rationale": eval_findings["rationale"],
            "trigger_definition": ts.trigger_definition,
            "target_definition": ts.target_definition,
            "expected_direction": ts.expected_direction,
            "driver": ts.driver,
            "mediator_or_process": ts.mediator_or_process,
            "target_effect": ts.target_effect,
        }
        results.append(case_result)

    output_path = Path(
        "/Users/hemantj/.gemini/antigravity-ide/brain/face4af3-acf5-4ebb-a5bd-ccb6af890aa2/multi_case_comparison_findings_8b.json"
    )
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(
        f"\nCompleted 8B comparison run. Generated results for {len(results)} days.",
        flush=True,
    )

    # Compute aggregates
    total = len(results)
    compliant = len([r for r in results if r["schema_compliance"]])
    identical = len(
        [
            r
            for r in results
            if r["semantic_preservation_class"] == "IDENTICAL_OR_EQUIVALENT"
        ]
    )
    minor_var = len(
        [
            r
            for r in results
            if r["semantic_preservation_class"] == "MINOR_NON_MATERIAL_VARIATION"
        ]
    )
    distortion = len(
        [
            r
            for r in results
            if r["semantic_preservation_class"] == "MATERIAL_DISTORTION"
        ]
    )

    print(f"\nLlama3 (8B) Comparison Metrics:", flush=True)
    print(f"Total cases evaluated: {total}", flush=True)
    print(
        f"Schema compliant: {compliant}/{total} ({compliant/total*100:.1f}%)",
        flush=True,
    )
    print(
        f"Identical claims: {identical}/{total} ({identical/total*100:.1f}%)",
        flush=True,
    )
    print(
        f"Minor non-material variation: {minor_var}/{total} ({minor_var/total*100:.1f}%)",
        flush=True,
    )
    print(
        f"Material distortions: {distortion}/{total} ({distortion/total*100:.1f}%)",
        flush=True,
    )


if __name__ == "__main__":
    run_comparison()
