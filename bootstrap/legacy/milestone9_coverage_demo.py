import os

import pandas as pd

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from flows.proposition_flow.validation_engine import ValidationEngine


def run_demo():
    print("==========================================================")
    print("MILESTONE 9 VALIDATION TERMINAL STATES DEMONSTRATION")
    print("==========================================================")

    # 1. Load full history data
    data_path = "data/reliance_daily_3y.csv"
    if not os.path.exists(data_path):
        print(f"Error: Data path {data_path} not found.")
        return
    history_df = pd.read_csv(data_path)
    print(f"Loaded history data: {len(history_df)} rows.")

    engine = ValidationEngine()

    # Let's find two steps in the data where we can demonstrate triggers:
    # We look for a step t where close[t] > close[t-1] and close[t+1] > close[t] (SUPPORTED)
    # And another step where close[t] > close[t-1] but close[t+1] < close[t] (CONTRADICTED)

    supported_step = None
    contradicted_step = None

    for t in range(1, len(history_df) - 1):
        close_prev = history_df["close"].iloc[t - 1]
        close_curr = history_df["close"].iloc[t]
        close_next = history_df["close"].iloc[t + 1]

        if close_curr > close_prev:
            # Trigger met: close went up today
            if close_next > close_curr:
                # Target met: close went up tomorrow too
                if supported_step is None:
                    supported_step = t
            else:
                # Target not met: close went down tomorrow
                if contradicted_step is None:
                    contradicted_step = t

        if supported_step is not None and contradicted_step is not None:
            break

    print(f"Selected Step {supported_step} for SUPPORTED demonstration.")
    print(f"Selected Step {contradicted_step} for CONTRADICTED demonstration.")

    # Define trigger: close[t] > close[t-1]
    trigger = {
        "operand_left": {"field": "close", "time_offset": 0},
        "operator": ">",
        "operand_right": {"field": "close", "time_offset": -1},
    }

    # Define target: close[t+1] > close[t] (Outcome == 'up')
    target = {"field": "outcome", "operator": "==", "value": "up"}

    # A. SUPPORTED CASE
    prop_supported = CompiledProposition(
        id="prop-demo-supported",
        theory_id="t-demo-supported",
        lineage_id="l-demo-supported",
        replay_step=supported_step,
        compilation_status="SUCCESS",
        trigger_definition=trigger,
        target_definition=target,
        scope_definition=[],
    )

    rec_supported = engine.validate(
        prop_supported, history_df, current_step=supported_step
    )

    print("\n----------------------------------------------------------")
    print("DEMONSTRATION 1: SUPPORTED STATE")
    print("----------------------------------------------------------")
    print(f"Replay Step:      {supported_step}")
    print(f"Trigger:          close[t] > close[t-1]")
    print(f"Target:           outcome == 'up'")
    print(f"Validation State: {rec_supported.validation_state}")
    print(f"Evidence:         {rec_supported.supporting_evidence}")
    print(f"Trace:            {rec_supported.validation_trace}")

    # B. CONTRADICTED CASE
    prop_contradicted = CompiledProposition(
        id="prop-demo-contradicted",
        theory_id="t-demo-contradicted",
        lineage_id="l-demo-contradicted",
        replay_step=contradicted_step,
        compilation_status="SUCCESS",
        trigger_definition=trigger,
        target_definition=target,
        scope_definition=[],
    )

    rec_contradicted = engine.validate(
        prop_contradicted, history_df, current_step=contradicted_step
    )

    print("\n----------------------------------------------------------")
    print("DEMONSTRATION 2: CONTRADICTED STATE")
    print("----------------------------------------------------------")
    print(f"Replay Step:      {contradicted_step}")
    print(f"Trigger:          close[t] > close[t-1]")
    print(f"Target:           outcome == 'up'")
    print(f"Validation State: {rec_contradicted.validation_state}")
    print(f"Evidence:         {rec_contradicted.contradicting_evidence}")
    print(f"Trace:            {rec_contradicted.validation_trace}")


if __name__ == "__main__":
    run_demo()
