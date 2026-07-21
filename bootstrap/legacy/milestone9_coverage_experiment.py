import glob
import json
import os

import pandas as pd

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from flows.proposition_flow.validation_engine import ValidationEngine


def run_experiment():
    print("==========================================================")
    print("MILESTONE 9 VALIDATION COVERAGE EXPERIMENT")
    print("==========================================================")

    # 1. Load full history data
    data_path = "data/reliance_daily_3y.csv"
    if not os.path.exists(data_path):
        print(f"Error: Data path {data_path} not found.")
        return
    history_df = pd.read_csv(data_path)
    print(f"Loaded history data: {len(history_df)} rows.")

    # 2. Discover latest run snapshots directory
    run_dirs = sorted(glob.glob("data/replay_snapshots/reliance/run_*"))
    if not run_dirs:
        print("Error: No replay snapshots found.")
        return
    latest_run = run_dirs[-1]
    print(f"Targeting latest replay snapshot: {latest_run}")

    # 3. Load all compiled propositions
    prop_files = glob.glob(os.path.join(latest_run, "propositions", "*.json"))
    if not prop_files:
        print("Error: No proposition snapshots found.")
        return
    print(f"Found {len(prop_files)} proposition files.")

    engine = ValidationEngine()
    stats = {
        "UNTRIGGERED": 0,
        "TRIGGERED": 0,
        "SUPPORTED": 0,
        "CONTRADICTED": 0,
        "PARTIALLY_SUPPORTED": 0,
        "GROUNDED": 0,
    }

    evaluated_count = 0
    for prop_file in prop_files:
        with open(prop_file, "r") as f:
            prop_data = json.load(f)

        # Parse into Pydantic model
        compiled_prop = CompiledProposition(**prop_data)
        replay_step = compiled_prop.replay_step

        # We perform two evaluations:
        # A. Live Slice Evaluation (simulation of the live loop where the future is unknown)
        # B. Retrospective Evaluation (where the full history is known)

        # Live slice
        slice_df = history_df.iloc[: replay_step + 1]
        rec_live = engine.validate(
            compiled_prop,
            slice_df,
            current_step=replay_step,
            confidence_before=0.5,
            confidence_after=0.5,
        )

        # Retrospective (lookahead step is now within bounds)
        rec_retro = engine.validate(
            compiled_prop,
            history_df,
            current_step=replay_step,
            confidence_before=0.5,
            confidence_after=0.5,
        )

        stats[rec_retro.validation_state] += 1
        evaluated_count += 1

        print(f"\nProposition {compiled_prop.id[:8]} at Step {replay_step}:")
        print(f"  Live State:  {rec_live.validation_state}")
        print(f"  Retro State: {rec_retro.validation_state}")
        if rec_retro.validation_state == "SUPPORTED":
            print(f"  Evidence:    {rec_retro.supporting_evidence}")
        elif rec_retro.validation_state == "CONTRADICTED":
            print(f"  Evidence:    {rec_retro.contradicting_evidence}")
        else:
            print(
                f"  Trace:       {rec_retro.validation_trace.get('status') or rec_retro.validation_trace.get('trigger_evaluated')}"
            )

    print("\n==========================================================")
    print("EXPERIMENTAL COVERAGE STATISTICS (RETROSPECTIVE)")
    print("==========================================================")
    for state, count in stats.items():
        print(f"  • {state:20}: {count}")
    print("==========================================================")


if __name__ == "__main__":
    run_experiment()
