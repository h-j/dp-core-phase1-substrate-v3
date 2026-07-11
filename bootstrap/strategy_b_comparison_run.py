import os
import json
from pathlib import Path
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow

class DummyAbstraction:
    def __init__(self, summary: str):
        self.abstraction_summary = summary

def run_comparison():
    print("Loading Day 0000 snapshot inputs...")
    snapshot_path = Path("/Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/data/replay_snapshots/reliance/run_20260701_123929/day_0000.json")
    with open(snapshot_path, "r") as f:
        data = json.load(f)
        
    abstraction = DummyAbstraction(data["observation"])
    market_memory_context = data.get("regime_history", {}).get("subtype_memory", "No prior history.")
    current_market_observation = data["observation"]
    reflective_memory_summary = data.get("reflection", "No reflection.")
    regime_subtype = data.get("regime_subtype", "neutral")
    falsifiability_conditions = data.get("theory_falsifiability", [])
    regime_history = data.get("regime_history", {})
    
    # 1. Run Baseline (Strategy B disabled)
    print("\n--- Running BASELINE Generation (Strategy B = OFF) ---")
    os.environ["EKAMNET_STRATEGY_B_SPIKE"] = "0"
    flow = TheoryGenerationFlow()
    flow.debug = True
    
    try:
        baseline_theory, _ = flow.process(
            abstraction=abstraction,
            market_memory_context=market_memory_context,
            current_market_observation=current_market_observation,
            reflective_memory_summary=reflective_memory_summary,
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
            regime_history=regime_history,
            step=0
        )
        print("Baseline Claim:", baseline_theory.summary_structured.claim)
        print("Baseline Components Count:", len(baseline_theory.summary_structured.mechanism_components))
    except Exception as e:
        print("Baseline failed:", e)
        baseline_theory = None
        
    # 2. Run Strategy B Treatment (Strategy B enabled)
    print("\n--- Running STRATEGY B Generation (Strategy B = ON) ---")
    os.environ["EKAMNET_STRATEGY_B_SPIKE"] = "1"
    flow_b = TheoryGenerationFlow()
    flow_b.debug = True
    
    try:
        b_theory, _ = flow_b.process(
            abstraction=abstraction,
            market_memory_context=market_memory_context,
            current_market_observation=current_market_observation,
            reflective_memory_summary=reflective_memory_summary,
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
            regime_history=regime_history,
            step=0
        )
        print("Strategy B Claim:", b_theory.summary_structured.claim)
        ts = b_theory.summary_structured
        print("Strategy B trigger_definition:", ts.trigger_definition)
        print("Strategy B target_definition:", ts.target_definition)
        print("Strategy B expected_direction:", ts.expected_direction)
        print("Strategy B driver:", ts.driver)
    except Exception as e:
        print("Strategy B failed:", e)
        b_theory = None

    # Save outputs to comparison report
    comp_data = {
        "baseline": {
            "claim": baseline_theory.summary_structured.claim if baseline_theory else None,
            "mechanism": baseline_theory.summary_structured.mechanism if baseline_theory else None,
            "components": [c.to_dict() for c in baseline_theory.summary_structured.mechanism_components] if baseline_theory else []
        } if baseline_theory else None,
        "strategy_b": {
            "claim": b_theory.summary_structured.claim if b_theory else None,
            "mechanism": b_theory.summary_structured.mechanism if b_theory else None,
            "components": [c.to_dict() for c in b_theory.summary_structured.mechanism_components] if b_theory else [],
            "trigger_definition": b_theory.summary_structured.trigger_definition if b_theory else None,
            "target_definition": b_theory.summary_structured.target_definition if b_theory else None,
            "expected_direction": b_theory.summary_structured.expected_direction if b_theory else None,
            "contradiction_definition": b_theory.summary_structured.contradiction_definition if b_theory else None,
            "driver": b_theory.summary_structured.driver if b_theory else None,
            "mediator_or_process": b_theory.summary_structured.mediator_or_process if b_theory else None,
            "target_effect": b_theory.summary_structured.target_effect if b_theory else None
        } if b_theory else None
    }
    
    output_path = Path("/Users/hemantj/.gemini/antigravity-ide/brain/face4af3-acf5-4ebb-a5bd-ccb6af890aa2/strategy_b_comparison_results.json")
    with open(output_path, "w") as f:
        json.dump(comp_data, f, indent=2)
    print(f"\nSaved comparison results to {output_path}")

if __name__ == "__main__":
    run_comparison()
