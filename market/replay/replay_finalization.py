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
        analysis_engine = getattr(executor, "replay_analysis_engine", None)
        if analysis_engine and not executor.quiet:
            analysis_engine.print_summary()
    except Exception as e:
        logger.warning(f"Failed to generate Milestone 10 cognitive metrics: {e}")

    save_manifest(executor)
    generate_v1_report(executor)


def save_manifest(executor: Any, manifest_path: Path = None):
    """Generates and persists the replay manifest JSON."""
    manifest = {
        "run_id": getattr(executor, "run_id", "run_unknown"),
        "symbol": getattr(executor.engine, "market_name", None) or "RELIANCE",
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

    target_file = manifest_path or (executor.run_dir / "replay_manifest.json")
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file, "w") as f:
        json.dump(manifest, f, indent=2)

    if not manifest_path and hasattr(executor, "base_output_dir"):
        manifest_out_path = executor.base_output_dir / "replay_manifest.json"
        manifest_out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_out_path, "w") as f:
            json.dump(manifest, f, indent=2)

    if not executor.quiet:
        print("\n======================================================================")
        print("REPLAY MANIFEST (REPRODUCIBILITY)")
        print("======================================================================")
        print(json.dumps(manifest, indent=2))
        print(f"✓ Saved manifest to target path: {target_file}")


def generate_v1_report(executor: Any):
    """Generates JSON and HTML report artifacts for replay."""
    try:
        from market.replay.report_renderer import ReplayReportModel, ReplayReportRenderer
        from market.replay.replay_analysis import ReplayAnalysisEngine

        if not executor.quiet:
            print("\n--- REPLAY REPORT V1 GENERATION ---")

        analysis_engine = getattr(executor, "replay_analysis_engine", None) or getattr(executor, "analysis_engine", None)
        if analysis_engine is None:
            analysis_engine = ReplayAnalysisEngine(market_name=getattr(getattr(executor, "engine", None), "market_name", "RELIANCE"))
        report_builder = ReplayReportModel(executor, analysis_engine)
        report_data = report_builder.build_model()

        if executor.run_dir:
            run_json_path = executor.run_dir / "report.json"
            with open(run_json_path, "w") as f:
                json.dump(report_data, f, indent=2, default=str)

            run_html_path = executor.run_dir / "report.html"
            ReplayReportRenderer.render(report_data, run_html_path)

        out_json_path = executor.base_output_dir / "report.json"
        with open(out_json_path, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        out_html_path = executor.base_output_dir / "report.html"
        ReplayReportRenderer.render(report_data, out_html_path)

        if not executor.quiet:
            print(f"✓ Saved structured report data to run snapshot: {executor.run_dir / 'report.json' if executor.run_dir else 'N/A'}")
            print(f"✓ Rendered interactive HTML report to run snapshot: {executor.run_dir / 'report.html' if executor.run_dir else 'N/A'}")
            print(f"✓ Saved structured report data to output folder: {out_json_path}")
            print(f"✓ Rendered interactive HTML report to output folder: {out_html_path}\n")

    except Exception as e:
        logger.error(f"Failed to generate Replay Report v1: {e}", exc_info=True)

