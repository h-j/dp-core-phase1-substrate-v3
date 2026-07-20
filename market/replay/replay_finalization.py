"""
Finalization, reporting, and manifest generation module for ReplayExecutor.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger("replay_engine.finalization")


def emit_cognitive_summary(executor: Any):
    """Logs post-replay cognitive metrics and summary."""
    if not executor.quiet:
        print("\n======================================================================")
        print("REPLAY COGNITIVE SUMMARY REPORT")
        print("======================================================================\n")

    if executor.lineage_audit_table and not executor.quiet:
        print("\nLineage Evolution Audit Table:")
        print(
            f"{'Day':<12} | {'Lineage ID':<36} | {'Created':<7} | {'Mutated':<7} | "
            f"{'Merged':<6} | {'Revived':<7} | {'Exp Action':<10}"
        )
        print("-" * 105)
        for row in executor.lineage_audit_table:
            print(
                f"{row['day']:<12} | {row['lineage_id']:<36} | "
                f"{str(row['created']):<7} | {str(row['mutated']):<7} | "
                f"{str(row['merged']):<6} | {str(row['revived']):<7} | "
                f"{row['experience_action']:<10}"
            )

    try:
        from market.replay.replay_analysis import ReplayAnalysisEngine
        from market.replay.replay_analysis_metrics import print_milestone10_metrics

        analysis_engine = ReplayAnalysisEngine(base_path=executor.run_dir)
        print_milestone10_metrics(analysis_engine, quiet=executor.quiet)
    except Exception as e:
        logger.warning(f"Failed to generate Milestone 10 cognitive metrics: {e}")

    save_manifest(executor)
    generate_v1_report(executor)


def save_manifest(executor: Any):
    """Generates and persists the replay manifest JSON."""
    manifest = {
        "run_id": getattr(executor, "run_id", "run_unknown"),
        "symbol": executor.engine.market_name or "RELIANCE",
        "downloaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "data_sources": [
            "yfinance (Stock & Index)",
            "NSE Security Delivery %",
            "Moneycontrol FII/DII Flows",
        ],
        "feature_versions": [
            "sector_zscore",
            "sector_percentile",
            "delivery_pct_5d",
            "fii_net",
            "dii_net",
        ],
        "replay_version": "v3.0PersistentReflective",
        "llm_version": "llama3.2",
        "git_commit": getattr(executor, "git_commit_hash", "unknown"),
        "execution_hash": hashlib.sha256(
            f"{getattr(executor, 'run_id', '')}{len(executor.engine)}".encode()
        ).hexdigest(),
    }

    manifest_run_path = executor.run_dir / "replay_manifest.json"
    with open(manifest_run_path, "w") as f:
        json.dump(manifest, f, indent=2)

    manifest_out_path = executor.base_output_dir / "replay_manifest.json"
    with open(manifest_out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    if not executor.quiet:
        print("\n======================================================================")
        print("REPLAY MANIFEST (REPRODUCIBILITY)")
        print("======================================================================")
        print(json.dumps(manifest, indent=2))
        print(f"✓ Saved manifest to run snapshot directory: {manifest_run_path}")
        print(f"✓ Saved manifest to outputs folder: {manifest_out_path}")


def generate_v1_report(executor: Any):
    """Generates JSON and HTML report artifacts for replay."""
    try:
        from market.replay.replay_report_generator import ReplayReportGenerator

        if not executor.quiet:
            print("\n--- REPLAY REPORT V1 GENERATION ---")

        report_gen = ReplayReportGenerator(base_path=executor.run_dir)
        report_data = report_gen.build_report_data()

        run_json_path = executor.run_dir / "report.json"
        with open(run_json_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        run_html_path = executor.run_dir / "report.html"
        report_gen.render_html_report(report_data, run_html_path)

        out_json_path = executor.base_output_dir / "report.json"
        with open(out_json_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        out_html_path = executor.base_output_dir / "report.html"
        report_gen.render_html_report(report_data, out_html_path)

        if not executor.quiet:
            print(f"✓ Saved structured report data to run snapshot: {run_json_path}")
            print(f"✓ Rendered interactive HTML report to run snapshot: {run_html_path}")
            print(f"✓ Saved structured report data to output folder: {out_json_path}")
            print(f"✓ Rendered interactive HTML report to output folder: {out_html_path}\n")

    except Exception as e:
        logger.error(f"Failed to generate Replay Report v1: {e}", exc_info=True)
