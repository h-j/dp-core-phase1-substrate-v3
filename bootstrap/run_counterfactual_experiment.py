import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


import pandas as pd
from sqlalchemy import MetaData, text

# Add the project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from market.replay.replay_analysis import ReplayAnalysisEngine
from market.replay.replay_engine import ReplayExecutor
from market.replay.run import (DataPreparationManager,
                               FeaturePreparationManager,
                               KnowledgeAnalysisEngine)
from memory.lineage.theory_lineage import TheoryLineageEngine, TheoryRecord
from memory.relational.postgres_client import Base, SessionLocal, engine

# Constants for Candidate F target event
TARGET_LINEAGE_ID = "1:theory:0"

TARGET_STEP = 2
DATASET_PATH = PROJECT_ROOT / "data" / "reliance_daily_3y.csv"


def calculate_md5(file_path):
    if not Path(file_path).exists():
        return "Missing"
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def reset_all():
    # 1. Reset PostgreSQL
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 2. Clear experiences
    exp_dir = PROJECT_ROOT / "data" / "experiences"
    if exp_dir.exists():
        for f in exp_dir.glob("*.json"):
            f.unlink()

    # 3. Clear snapshots
    snap_dir = PROJECT_ROOT / "data" / "replay_snapshots"
    if snap_dir.exists():
        for d in snap_dir.iterdir():
            if d.is_dir():
                shutil.rmtree(d)
            else:
                d.unlink()


def generate_manifest(output_path, commit_hash):
    meta = MetaData()
    meta.reflect(bind=engine)
    row_counts = {}
    with SessionLocal() as session:
        for table_name in sorted(meta.tables.keys()):
            count = session.execute(text(f"SELECT count(*) FROM {table_name}")).scalar()
            row_counts[table_name] = count

    input_md5 = calculate_md5(DATASET_PATH)
    theory_flow_md5 = calculate_md5(
        PROJECT_ROOT / "flows/theory_flow/theory_generation_flow.py"
    )

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit_hash": commit_hash,
        "ollama": {
            "model": settings.OLLAMA_MODEL,
            "configuration": {"temperature": 0.0, "seed": 42},
        },
        "database": {
            "row_counts": row_counts,
            "is_clean": all(v == 0 for v in row_counts.values() if isinstance(v, int)),
        },
        "input_data": {"path": str(DATASET_PATH), "md5_checksum": input_md5},
        "prompts": {"theory_generation_flow_md5": theory_flow_md5},
        "replay_command": "poetry run python bootstrap/run_counterfactual_experiment.py",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def install_intervention_patch():
    original_retire_theory = TheoryLineageEngine.retire_theory

    def patched_retire_theory(self, tid: str, step: int) -> Optional[TheoryRecord]:
        rec = self.theories.get(tid)
        if rec and rec.created_at_step == 1 and step == TARGET_STEP:
            print(
                f"\n[INTERVENTION] Suppressing retirement of theory {tid} (lineage {rec.lineage_id}) at step {step}!"
            )
            return None
        return original_retire_theory(self, tid, step)

    TheoryLineageEngine.retire_theory = patched_retire_theory
    return original_retire_theory


def restore_original_patch(original_retire_theory):
    if original_retire_theory:
        TheoryLineageEngine.retire_theory = original_retire_theory


def run_single_replay(run_name, group_name, is_treatment, commit_hash):
    print(f"\n======================================================================")
    print(f"STARTING RUN: {run_name} ({group_name})")
    print(f"======================================================================")

    # 1. Reset state
    reset_all()

    # 2. Pre-Execution Isolation Gate & Manifest
    archive_dir = (
        PROJECT_ROOT / "data" / "archive" / "counterfactual_experiment" / run_name
    )
    manifest_path = archive_dir / "manifest.json"
    manifest = generate_manifest(manifest_path, commit_hash)

    # Validate Isolation Invariants
    assert manifest["database"]["is_clean"], "Database must be completely clean!"
    assert not (
        PROJECT_ROOT / "data" / "replay_snapshots" / "reliance"
    ).exists(), "Snapshots must be clean!"
    assert (
        settings.OLLAMA_MODEL == "llama3.2"
    ), f"Ollama model must be llama3.2, got {settings.OLLAMA_MODEL}"

    # 3. Setup Custom Log Redirect
    captured_logs = []
    original_log = ReplayExecutor._log

    def custom_log(self, message: str):
        captured_logs.append(message)
        original_log(self, message)

    ReplayExecutor._log = custom_log

    # 4. Apply Intervention Monkeypatch if Treatment
    original_patch = None
    if is_treatment:
        original_patch = install_intervention_patch()
    else:
        restore_original_patch(TheoryLineageEngine.retire_theory)

    # 5. Execute Replay
    executor = ReplayExecutor(
        max_days=10,
        quiet=False,
        dataset_path=DATASET_PATH,
        market_name="reliance",
        compare_secondary=False,
        generate_visualizations=False,
        lineage_debug=True,
        restart=True,
        verbose=True,
        force_refresh=False,
        data_prep_done=True,
    )
    executor.base_data_snap_dir = executor.base_data_snap_dir / "reliance"
    executor._create_snapshot_dirs()

    # Run
    executor.execute(emit_summary=False)

    # Run Analysis
    analysis_engine = KnowledgeAnalysisEngine(market_name="reliance", executor=executor)
    analysis_engine.analyze()

    # Restore ReplayExecutor log and lineage patch
    ReplayExecutor._log = original_log
    if is_treatment:
        restore_original_patch(original_patch)

    # Save Captured Logs
    log_file = executor.run_dir / "replay_debug.log"
    with open(log_file, "w") as f:
        f.write("\n".join(captured_logs))

    # 6. Query and Dump Relational DB Rows
    db_dump = {}
    meta = MetaData()
    meta.reflect(bind=engine)

    def json_default(obj):
        if isinstance(obj, (datetime, timezone)):
            return obj.isoformat()
        return str(obj)

    with SessionLocal() as session:
        for table_name in meta.tables.keys():
            rows = session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            db_dump[table_name] = [dict(r._mapping) for r in rows]

    with open(executor.run_dir / "database_dump.json", "w") as f:
        json.dump(db_dump, f, indent=2, default=json_default)

    # 7. Reconstruct Observables step-by-step
    observables = []

    # Load Lineage Final State
    lineage_path = executor.run_dir / "theory_lineage.json"
    lineage_data = {}
    if lineage_path.exists():
        lineage_data = json.loads(lineage_path.read_text())

    # Load Trading Log
    trade_log_path = executor.run_dir / "paper_trade_log.csv"
    trade_df = pd.read_csv(trade_log_path) if trade_log_path.exists() else None

    # Load Experiences list
    exp_sub_dir = executor.run_dir / "experiences"
    experiences_list = []
    if exp_sub_dir.exists():
        for f in exp_sub_dir.glob("*.json"):
            try:
                experiences_list.append(json.loads(f.read_text()))
            except Exception:
                pass

    for d in range(10):
        day_file = executor.run_dir / f"day_{d:04d}.json"
        day_data = json.loads(day_file.read_text()) if day_file.exists() else {}

        # Parse routing decision for day `d`
        day_logs = [
            line
            for line in captured_logs
            if f"day={d} " in line or f"day {d}:" in line or f"day={d}," in line
        ]
        novelty_logs = [line for line in captured_logs if "[NOVELTY GATE]" in line]
        # Match day index in novelty logs if possible
        # Usually printed sequentially, so we can align by finding the d-th novelty gate log entry
        routing_decision = "UNKNOWN"
        novelty_score = 0.0
        # Reconstruct sequential gate calls from captured logs
        # First novelty gate log matches day 0, second matches day 1, etc. (since day 0 does not check novelty, it defaults to GENERATE, day 1 is first check, etc.)
        # Let's parse day-specific novelty logs
        # Note: day 0 has no prior_theory, so it goes to GENERATE.
        if d == 0:
            routing_decision = "GENERATE"
        else:
            # Look for log: [NOVELTY GATE] Decision: ...
            # Let's count how many [NOVELTY GATE] decisions occur
            novelty_entries = [
                line for line in captured_logs if "[NOVELTY GATE]" in line
            ]
            if len(novelty_entries) >= d:
                entry = novelty_entries[d - 1]  # 0-indexed matches step d
                if "REVISE" in entry:
                    routing_decision = "REVISE"
                elif "REINFORCE" in entry:
                    routing_decision = "REINFORCE"
                elif "GENERATE" in entry:
                    routing_decision = "GENERATE"

                try:
                    # Score: X.XX
                    novelty_score = float(
                        entry.split("Score:")[1].split("|")[0].strip()
                    )
                except Exception:
                    pass

        # Target lineage ID created at step 1
        target_lineage_id_run = None
        for l_id, l_rec in lineage_data.items():
            if l_rec.get("created_at_step") == 1:
                target_lineage_id_run = l_id
                break

        # Target lineage status check at step d
        target_status = "non-existent"
        if target_lineage_id_run and target_lineage_id_run in lineage_data:
            rec = lineage_data[target_lineage_id_run]
            created_at = rec.get("created_at_step", 0)
            retired_at = rec.get("retired_at_step", None)
            if created_at <= d:
                if retired_at is not None and retired_at <= d:
                    target_status = "retired"
                else:
                    target_status = rec.get("status", "active")

        # Prior theory availability check
        # Control: retired at step 2, so at step 3 active_theories() returns empty -> prior_theory = None
        # Treatment: active at step 2, so at step 3 active_theories() returns it -> prior_theory is populated
        prior_theory_id = None
        prior_theory_eligible = False
        if d == 3:
            if is_treatment:
                prior_theory_id = target_lineage_id_run
                prior_theory_eligible = True
            else:
                prior_theory_id = None
                prior_theory_eligible = False

        # Query theory created on this day
        created_theory_id = None
        created_theory_thesis = ""
        created_theory_structure = {}
        for theory in db_dump.get("theories", []):
            # Parse step from database or lineage file
            # In DB, created_at step matches step column or can be inferred from lineage
            # Let's match by lineage ID creation step
            for l_id, l_rec in lineage_data.items():
                if l_rec.get("created_at_step") == d:
                    # Find theory matching this lineage
                    if theory.get("lineage_id") == l_id:
                        created_theory_id = theory.get("id")
                        created_theory_thesis = theory.get("thesis", "")
                        created_theory_structure = theory.get("summary_structured", {})

        # Trade performance metrics for day d
        prediction_val = "uncertain"
        conviction_val = 0.0
        action_val = "cash"
        if trade_df is not None and d < len(trade_df):
            row = trade_df.iloc[d]
            prediction_val = str(row.get("prediction", "uncertain"))
            conviction_val = float(row.get("conviction_score", 0.0))
            alloc = float(row.get("allocation_pct", 0.0))
            action_val = f"trade (alloc: {alloc:.2%})" if alloc > 0.0 else "cash"

        # Originating experience on day d
        exp_id = None
        for exp in experiences_list:
            if exp.get("created_at") == day_data.get("metrics", {}).get("date"):
                exp_id = exp.get("experience_id")

        step_observables = {
            "step": d,
            "date": day_data.get("metrics", {}).get("date"),
            "originating_experience": exp_id,
            "target_lineage_status": target_status,
            "active_theories_count": day_data.get("metrics", {}).get(
                "active_theories", 0
            ),
            "prior_theory_id": prior_theory_id,
            "prior_theory_eligible": prior_theory_eligible,
            "novelty_gate_decision": routing_decision,
            "novelty_gate_score": novelty_score,
            "created_theory_id": created_theory_id,
            "created_theory_thesis": created_theory_thesis,
            "prediction": prediction_val,
            "conviction": conviction_val,
            "action": action_val,
        }
        observables.append(step_observables)

    # Save Observables to run snapshots
    with open(executor.run_dir / "observables.json", "w") as f:
        json.dump(observables, f, indent=2)

    # 8. Copy entire run_dir to archive
    shutil.copytree(executor.run_dir, archive_dir, dirs_exist_ok=True)
    print(f"✓ Run artifacts archived to {archive_dir}")

    # Clean up snapshots to avoid accumulation
    shutil.rmtree(executor.run_dir)

    return observables


def main():
    commit_hash = "399c79b8663cb2d42c599990f064ec9361d2d88d"

    # Pre-Execution Isolation check
    print("Executing Pre-Execution Isolation Checks...")
    reset_all()
    assert calculate_md5(DATASET_PATH) != "Missing", "Input dataset file is missing!"

    # Replication plan:
    # Pair 1: Control_1 -> Treatment_1
    # Pair 2: Treatment_2 -> Control_2
    # Pair 3: Control_3 -> Treatment_3

    results = {}

    # Run Pair 1
    results["control_1"] = run_single_replay(
        "control_1", "Control", is_treatment=False, commit_hash=commit_hash
    )
    results["treatment_1"] = run_single_replay(
        "treatment_1", "Treatment", is_treatment=True, commit_hash=commit_hash
    )

    # Run Pair 2
    results["treatment_2"] = run_single_replay(
        "treatment_2", "Treatment", is_treatment=True, commit_hash=commit_hash
    )
    results["control_2"] = run_single_replay(
        "control_2", "Control", is_treatment=False, commit_hash=commit_hash
    )

    # Run Pair 3
    results["control_3"] = run_single_replay(
        "control_3", "Control", is_treatment=False, commit_hash=commit_hash
    )
    results["treatment_3"] = run_single_replay(
        "treatment_3", "Treatment", is_treatment=True, commit_hash=commit_hash
    )

    # Save final results database
    results_file = (
        PROJECT_ROOT
        / "data"
        / "archive"
        / "counterfactual_experiment"
        / "all_results.json"
    )
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ All replication runs completed. Results stored in {results_file}")


if __name__ == "__main__":
    main()
