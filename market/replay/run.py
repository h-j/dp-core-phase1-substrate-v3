import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from config.settings import settings
from market.data.download_history import (STOCK_SECTOR_MAP,
                                          GenericHistoryDownloader)
from market.data.moneycontrol_fetcher import MoneycontrolFetcher
from market.data.nse_fetcher import NSEFetcher
from market.replay.replay_analysis import ReplayAnalysisEngine
from market.replay.replay_engine import ReplayExecutor
from memory.knowledge.knowledge_repository import KnowledgeRepository


class DataPreparationManager:
    """
    Stage 1: Data Preparation
    Responsible for fetching/checking all raw market history, indexes,
    and scraping auxiliary data (Delivery %, FII/DII Net Flows),
    intelligently resolving against existing Evidence Gaps.
    """

    def __init__(
        self, symbol: str, force_refresh: bool = False, dataset_path: str = None
    ):
        self.symbol = symbol
        self.force_refresh = force_refresh
        self.dataset_path = (
            Path(dataset_path)
            if dataset_path
            else Path(__file__).parent.parent.parent / "data" / "reliance_daily_3y.csv"
        )

    def prepare(self, start_date: str = "2023-01-01", end_date: str = None):
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        print("[DataPreparationManager] Preparing Replay...")

        # Check active evidence gaps to align acquisition
        knowledge_repo = KnowledgeRepository()
        evidence_gaps = knowledge_repo.list_evidence_gaps()

        print("Checking Evidence Gaps Registry:")
        relevant_gaps = [
            g
            for g in evidence_gaps
            if any(
                term in g.missing_evidence.lower()
                for term in ["volume", "delivery", "sector", "fii", "dii"]
            )
        ]
        if relevant_gaps:
            print(
                f"  -> Found {len(relevant_gaps)} unresolved volume-related evidence gap(s):"
            )
            for g in relevant_gaps:
                print(
                    f"     • Gap: {g.missing_evidence} (Candidate: {g.candidate_data_source})"
                )
        else:
            print("  -> No unresolved volume-related evidence gaps found.")

        # 1. Primary Ticker
        primary_ticker = self.symbol
        if "NIFTY" not in primary_ticker.upper() and "." not in primary_ticker:
            primary_ticker = f"{primary_ticker.upper()}.NS"

        stock_cached = self.dataset_path.exists()
        if stock_cached and not self.force_refresh:
            try:
                df_temp = pd.read_csv(self.dataset_path)
                if "date" in df_temp.columns and len(df_temp) > 0:
                    max_date = pd.to_datetime(df_temp["date"]).max().date()

                    # Compute last working day (preceding Friday for weekends, or today/yesterday for weekdays depending on market close hour)
                    now = datetime.now()
                    last_wd = now
                    if last_wd.weekday() == 5:  # Saturday
                        last_wd -= timedelta(days=1)
                    elif last_wd.weekday() == 6:  # Sunday
                        last_wd -= timedelta(days=2)
                    elif last_wd.weekday() < 5 and now.hour < 18:
                        # Weekday before 6 PM local time: use previous weekday
                        last_wd -= timedelta(days=1)
                        while last_wd.weekday() >= 5:
                            last_wd -= timedelta(days=1)

                    last_wd_date = last_wd.date()
                    if max_date < last_wd_date:
                        print(
                            f"• Latest cached data ({max_date}) is older than last working day ({last_wd_date}). Force refreshing..."
                        )
                        self.force_refresh = True
            except Exception as e:
                print(
                    f"⚠ Failed reading cached file to check latest date: {e}. Force refreshing..."
                )
                self.force_refresh = True

        if stock_cached and not self.force_refresh:
            print(f"✓ {primary_ticker} price history: Already available (Skipping)")
        else:
            status_str = "Updating" if self.force_refresh else "Missing -> Downloading"
            print(f"• {primary_ticker} price history: {status_str}...")
            primary_downloader = GenericHistoryDownloader(
                primary_ticker, str(self.dataset_path)
            )
            try:
                p_data = primary_downloader.download(
                    start_date=start_date, end_date=end_date
                )
                primary_downloader.persist(p_data)
                primary_downloader.add_derived_fields()
                print(f"  ✓ Downloaded and saved {primary_ticker} price history.")
            except Exception as e:
                print(
                    f"  ⚠ Failed downloading {primary_ticker} data: {e}. Attempting cache fallback."
                )

        # Resolve actual date ranges from stock CSV
        if self.dataset_path.exists():
            df = pd.read_csv(self.dataset_path)
            df["date"] = pd.to_datetime(df["date"])
            actual_start_date = df["date"].min().strftime("%Y-%m-%d")
            actual_end_date = df["date"].max().strftime("%Y-%m-%d")
        else:
            actual_start_date = start_date
            actual_end_date = end_date
            df = None

        # 2. Sector Index Strength
        sector_ticker = STOCK_SECTOR_MAP.get(
            self.symbol.upper(),
            STOCK_SECTOR_MAP.get(primary_ticker.upper(), "^CNXENERGY"),
        )
        sector_cache_dir = self.dataset_path.parent / "market_data" / "sector_rs"
        sector_cache_dir.mkdir(parents=True, exist_ok=True)
        safe_sector_ticker = sector_ticker.replace("^", "")
        sector_cache_path = sector_cache_dir / f"{safe_sector_ticker}.parquet"

        sector_cached = sector_cache_path.exists()
        if sector_cached and not self.force_refresh:
            print(f"✓ Sector strength ({sector_ticker}): Cached (Skipping)")
        else:
            status_str = "Updating" if self.force_refresh else "Missing -> Downloading"
            print(f"• Sector strength ({sector_ticker}): {status_str}...")
            try:
                sector_downloader = GenericHistoryDownloader(
                    sector_ticker, str(sector_cache_dir / f"{safe_sector_ticker}.csv")
                )
                sec_data = sector_downloader.download(
                    start_date=actual_start_date, end_date=actual_end_date
                )
                sec_data = sec_data.reset_index()
                if isinstance(sec_data.columns, pd.MultiIndex):
                    sec_data.columns = [col[0] for col in sec_data.columns]
                date_col = next(
                    (c for c in sec_data.columns if "date" in c.lower()),
                    sec_data.columns[0],
                )
                sec_data = sec_data.rename(columns={date_col: "date"})
                sec_data.columns = sec_data.columns.str.lower()
                sec_data["date"] = pd.to_datetime(sec_data["date"])
                sec_data = sec_data[["date", "close"]].rename(
                    columns={"close": "sector_close"}
                )
                sec_data.to_parquet(sector_cache_path, index=False)
                print(f"  ✓ Cached sector index data.")
            except Exception as e:
                print(f"  ⚠ Failed fetching live sector data: {e}.")
                if not sector_cached and df is not None:
                    print("  -> Generating simulated sector index fallback.")
                    temp_df = df[["date", "close"]].copy()
                    temp_df["sector_close"] = temp_df[
                        "close"
                    ] * 15.0 + np.random.normal(0, temp_df["close"] * 0.2)
                    temp_df[["date", "sector_close"]].to_parquet(
                        sector_cache_path, index=False
                    )

        # 3. Delivery Percentage
        delivery_cache_dir = self.dataset_path.parent / "market_data" / "delivery"
        delivery_cache_path = (
            delivery_cache_dir / f"{primary_ticker.replace('.NS', '')}_delivery.parquet"
        )
        delivery_cached = delivery_cache_path.exists()
        if delivery_cached and not self.force_refresh:
            print(f"✓ Delivery % data: Cached (Skipping)")
        else:
            status_str = "Updating" if self.force_refresh else "Missing -> Downloading"
            print(f"• Delivery % data: {status_str}...")
            try:
                nse_fetcher = NSEFetcher(cache_dir=delivery_cache_dir)
                nse_fetcher.fetch_delivery_data(
                    symbol=primary_ticker,
                    start_date=actual_start_date,
                    end_date=actual_end_date,
                    force_refresh=self.force_refresh,
                )
                print(f"  ✓ Cached delivery % data.")
            except Exception as e:
                print(f"  ⚠ Failed fetching live delivery %: {e}.")
                if not delivery_cached:
                    print("  -> Will generate simulated delivery fallback in Stage 2.")

        # 4. FII/DII Net Flows
        fii_dii_cache_dir = self.dataset_path.parent / "market_data" / "fii_dii"
        fii_dii_cache_path = fii_dii_cache_dir / "fii_dii_flows.parquet"
        fii_dii_cached = fii_dii_cache_path.exists()
        if fii_dii_cached and not self.force_refresh:
            print(f"✓ FII/DII Net Flows data: Cached (Skipping)")
        else:
            status_str = "Updating" if self.force_refresh else "Missing -> Downloading"
            print(f"• FII/DII Net Flows data: {status_str}...")
            try:
                fii_dii_fetcher = MoneycontrolFetcher(cache_dir=fii_dii_cache_dir)
                fii_dii_fetcher.fetch_fii_dii_data(
                    start_date=actual_start_date,
                    end_date=actual_end_date,
                    force_refresh=self.force_refresh,
                )
                print(f"  ✓ Cached FII/DII flows data.")
            except Exception as e:
                print(f"  ⚠ Failed fetching live FII/DII flows: {e}.")
                if not fii_dii_cached:
                    print("  -> Will generate simulated FII/DII fallback in Stage 2.")

        print("✓ Data Preparation complete.")


class FeaturePreparationManager:
    """
    Stage 2: Feature Preparation
    Generates rolling Relative Strength, percentiles,
    averages, and merges cached auxiliary features into the final CSV.
    """

    def __init__(self, symbol: str, dataset_path: str = None):
        self.symbol = symbol
        self.dataset_path = (
            Path(dataset_path)
            if dataset_path
            else Path(__file__).parent.parent.parent / "data" / "reliance_daily_3y.csv"
        )

    def prepare(self) -> pd.DataFrame:
        print(
            "[FeaturePreparationManager] Generating derived features and regime labels..."
        )
        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Primary stock file missing at {self.dataset_path}"
            )

        df = pd.read_csv(self.dataset_path)
        df["date"] = pd.to_datetime(df["date"])

        # Drop pre-existing columns to avoid merge suffixes
        for col in [
            "sector_close",
            "sector_rs_ratio",
            "sector_zscore",
            "sector_percentile",
            "delivery_pct",
            "delivery_pct_5d",
            "fii_net",
            "dii_net",
        ]:
            if col in df.columns:
                df = df.drop(columns=[col])

        # 1. Merge Sector data
        primary_ticker = self.symbol
        if "NIFTY" not in primary_ticker.upper() and "." not in primary_ticker:
            primary_ticker = f"{primary_ticker.upper()}.NS"
        sector_ticker = STOCK_SECTOR_MAP.get(
            self.symbol.upper(),
            STOCK_SECTOR_MAP.get(primary_ticker.upper(), "^CNXENERGY"),
        )
        safe_sector_ticker = sector_ticker.replace("^", "")
        sector_cache_path = (
            self.dataset_path.parent
            / "market_data"
            / "sector_rs"
            / f"{safe_sector_ticker}.parquet"
        )

        if sector_cache_path.exists():
            sector_df = pd.read_parquet(sector_cache_path)
            sector_df["date"] = pd.to_datetime(sector_df["date"])
            df = pd.merge(
                df, sector_df[["date", "sector_close"]], on="date", how="left"
            )
            print("✓ Merged Sector Relative Strength close.")
        else:
            print("⚠ Sector cache missing! Generating simulated fallback.")
            df["sector_close"] = df["close"] * 15.0 + np.random.normal(
                0, df["close"] * 0.2
            )

        df["sector_close"] = df["sector_close"].ffill().bfill()
        df["sector_rs_ratio"] = df["close"] / df["sector_close"]

        # Rolling Z-score
        rolling_mean_20 = df["sector_rs_ratio"].rolling(window=20, min_periods=1).mean()
        rolling_std_20 = (
            df["sector_rs_ratio"].rolling(window=20, min_periods=1).std().fillna(1.0)
        )
        df["sector_zscore"] = (df["sector_rs_ratio"] - rolling_mean_20) / rolling_std_20
        df.loc[rolling_std_20 == 0.0, "sector_zscore"] = 0.0

        # Percentile rank
        df["sector_percentile"] = (
            df["sector_rs_ratio"]
            .rolling(window=20, min_periods=1)
            .apply(
                lambda x: pd.Series(x).rank(pct=True).iloc[-1] if len(x) > 0 else 0.5
            )
        )
        print("✓ Computed sector relative strength Z-score and percentile.")

        # 2. Merge Delivery %
        delivery_cache_path = (
            self.dataset_path.parent
            / "market_data"
            / "delivery"
            / f"{primary_ticker.replace('.NS', '')}_delivery.parquet"
        )
        if delivery_cache_path.exists():
            deliv_df = pd.read_parquet(delivery_cache_path)
            deliv_df["date"] = pd.to_datetime(deliv_df["date"])
            df = pd.merge(df, deliv_df[["date", "delivery_pct"]], on="date", how="left")
            print("✓ Merged delivery %.")
        else:
            df["delivery_pct"] = np.nan

        if df["delivery_pct"].isna().all():
            print("⚠ Generating simulated delivery % fallback.")
            np.random.seed(42)
            df["delivery_pct"] = np.clip(
                np.random.normal(loc=48.0, scale=8.0, size=len(df)), 15.0, 85.0
            )
        else:
            df["delivery_pct"] = df["delivery_pct"].ffill().bfill().fillna(45.0)

        df["delivery_pct_5d"] = (
            df["delivery_pct"].rolling(window=5, min_periods=1).mean()
        )

        # 3. Merge FII/DII Net Flows
        fii_dii_cache_path = (
            self.dataset_path.parent
            / "market_data"
            / "fii_dii"
            / "fii_dii_flows.parquet"
        )
        if fii_dii_cache_path.exists():
            flow_df = pd.read_parquet(fii_dii_cache_path)
            flow_df["date"] = pd.to_datetime(flow_df["date"])
            df = pd.merge(
                df, flow_df[["date", "fii_net", "dii_net"]], on="date", how="left"
            )
            print("✓ Merged FII/DII Net Flows.")
        else:
            df["fii_net"] = np.nan
            df["dii_net"] = np.nan

        if df["fii_net"].isna().all() or df["dii_net"].isna().all():
            print("⚠ Generating simulated FII/DII flows fallback.")
            np.random.seed(100)
            df["fii_net"] = df["fii_net"].fillna(
                pd.Series(np.random.normal(loc=200.0, scale=1000.0, size=len(df)))
            )
            df["dii_net"] = df["dii_net"].fillna(
                pd.Series(np.random.normal(loc=150.0, scale=800.0, size=len(df)))
            )
        else:
            df["fii_net"] = df["fii_net"].ffill().bfill().fillna(0.0)
            df["dii_net"] = df["dii_net"].ffill().bfill().fillna(0.0)

        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df.to_csv(self.dataset_path, index=False)
        print(
            f"✓ Validated and saved enriched dataset to {self.dataset_path} ({len(df)} rows)"
        )
        return df


class KnowledgeAnalysisEngine:
    """
    Stage 4: Knowledge Analysis
    Uses the ReplayAnalysisEngine from ReplayExecutor to compute confidence statistics,
    contradiction resolutions, and knowledge health indices.
    """

    def __init__(self, market_name: str, executor: ReplayExecutor):
        self.market_name = market_name
        self.executor = executor
        self.analysis_engine = executor.replay_analysis_engine

    def analyze(self):
        # Configure outputs metrics safely on the executor's analysis engine
        if self.analysis_engine:
            base_output_dir = (
                Path(__file__).parent.parent.parent / "market" / "replay" / "output"
            )
            if "outputs" not in self.analysis_engine.external_metrics:
                self.analysis_engine.external_metrics["outputs"] = {}
            self.analysis_engine.external_metrics["outputs"].update(
                {
                    "prediction_csv": str(base_output_dir / "prediction_analysis.csv"),
                    "charts_dir": str(
                        base_output_dir / self.market_name.lower().replace(" ", "_")
                    ),
                }
            )


class ReportGenerator:
    """
    Stage 4: Report Generation
    Handles textual and console reporting, and exports
    the research-grade reproducibility Replay Manifest.
    """

    def __init__(
        self, executor: ReplayExecutor, analysis_engine: KnowledgeAnalysisEngine
    ):
        self.executor = executor
        self.analysis_engine = analysis_engine

    def generate(self):
        print("\n" + "=" * 70)
        print("REPORT GENERATION")
        print("=" * 70)

        # Trigger ReplayAnalysisEngine console prints
        if self.analysis_engine.analysis_engine:
            try:
                self.analysis_engine.analysis_engine.print_summary()
            except Exception as e:
                print(f"⚠ Failed to print summary report: {e}")
        else:
            print("⚠ ReplayAnalysisEngine was not initialized in ReplayExecutor.")

        # Reproducibility Manifest
        print("\n" + "=" * 70)
        print("REPLAY MANIFEST (REPRODUCIBILITY)")
        print("=" * 70)

        run_id = self.executor.run_dir.name if self.executor.run_dir else "run_unknown"
        symbol = self.executor.market_name
        downloaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_sources = [
            "yfinance (Stock & Index)",
            "NSE Security Delivery %",
            "Moneycontrol FII/DII Flows",
        ]
        feature_versions = [
            "sector_zscore",
            "sector_percentile",
            "delivery_pct_5d",
            "fii_net",
            "dii_net",
        ]
        replay_version = "v3.0PersistentReflective"
        llm_version = settings.OLLAMA_MODEL

        # Git commit SHA
        git_commit = "unknown"
        try:
            git_commit = (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
                )
                .decode("utf-8")
                .strip()
            )
        except Exception:
            pass

        manifest_dict = {
            "run_id": run_id,
            "symbol": symbol,
            "downloaded_at": downloaded_at,
            "data_sources": data_sources,
            "feature_versions": feature_versions,
            "replay_version": replay_version,
            "llm_version": llm_version,
            "git_commit": git_commit,
        }

        # Compute Execution Hash
        ordered_str = json.dumps(manifest_dict, sort_keys=True)
        execution_hash = hashlib.sha256(ordered_str.encode("utf-8")).hexdigest()
        manifest_dict["execution_hash"] = execution_hash

        print(json.dumps(manifest_dict, indent=2))

        # Save manifest files
        output_dir = (
            Path(__file__).parent.parent.parent / "market" / "replay" / "output"
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            if self.executor.run_dir:
                manifest_path = self.executor.run_dir / "replay_manifest.json"
                with open(manifest_path, "w") as f:
                    json.dump(manifest_dict, f, indent=2)
                print(f"✓ Saved manifest to run snapshot directory: {manifest_path}")

            output_manifest_path = output_dir / "replay_manifest.json"
            with open(output_manifest_path, "w") as f:
                json.dump(manifest_dict, f, indent=2)
            print(f"✓ Saved manifest to outputs folder: {output_manifest_path}")
        except Exception as e:
            print(f"⚠ Failed saving manifest file: {e}")

        # Render Replay Report V1 (report.json & report.html)
        print("\n--- REPLAY REPORT V1 GENERATION ---")
        try:
            from market.replay.report_renderer import (ReplayReportModel,
                                                       ReplayReportRenderer)

            # 1. Build structured JSON report model
            report_builder = ReplayReportModel(self.executor, self.analysis_engine)
            report_data = report_builder.build_model()

            # Save report.json
            if self.executor.run_dir:
                run_json_path = self.executor.run_dir / "report.json"
                with open(run_json_path, "w") as f:
                    json.dump(report_data, f, indent=2)
                print(
                    f"✓ Saved structured report data to run snapshot: {run_json_path}"
                )

                # Render report.html inside run folder
                run_html_path = self.executor.run_dir / "report.html"
                ReplayReportRenderer.render(report_data, run_html_path)
                print(
                    f"✓ Rendered interactive HTML report to run snapshot: {run_html_path}"
                )

            # Save report.json to output directory
            output_json_path = output_dir / "report.json"
            with open(output_json_path, "w") as f:
                json.dump(report_data, f, indent=2)
            print(
                f"✓ Saved structured report data to output folder: {output_json_path}"
            )

            # Render report.html to output directory
            output_html_path = output_dir / "report.html"
            ReplayReportRenderer.render(report_data, output_html_path)
            print(
                f"✓ Rendered interactive HTML report to output folder: {output_html_path}"
            )

        except Exception as e:
            print(f"⚠ Failed generating Replay Report v1: {e}")
            import traceback

            traceback.print_exc()


class ReplayPipeline:
    """
    Coordinates and executes the stages of the cognitive replay pipeline:
      Stage 1: Data Preparation
      Stage 2: Feature Preparation
      Stage 3: Replay Loop Execution
      Stage 4: Reporting and Manifest Exports
    """

    def __init__(self, args):
        self.args = args
        self.force_refresh = args.force_refresh
        self.restart = args.restart
        self.reset = args.reset

        if getattr(args, "symbol", None):
            self.symbol = args.symbol.upper()
        elif args.nifty:
            self.symbol = "NIFTY"
        else:
            self.symbol = "RELIANCE"

        if self.symbol == "NIFTY":
            self.market_name = "NIFTY 50"
            self.dataset_path = str(
                Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"
            )
        else:
            self.market_name = self.symbol
            csv_name = f"{self.symbol.lower()}_daily_3y.csv"
            self.dataset_path = str(
                Path(__file__).parent.parent.parent / "data" / csv_name
            )

    def run(self):
        print("=" * 80)
        print("              DP COGNITIVE REPLAY SYSTEM PIPELINE")
        print("=" * 80)

        # Stage 1: Data Preparation
        print("\n--- STAGE 1: DATA PREPARATION ---")
        data_prep = DataPreparationManager(
            symbol=self.symbol,
            force_refresh=self.force_refresh,
            dataset_path=self.dataset_path,
        )
        data_prep.prepare()

        # Stage 2: Feature Preparation
        print("\n--- STAGE 2: FEATURE PREPARATION ---")
        feat_prep = FeaturePreparationManager(
            symbol=self.symbol, dataset_path=self.dataset_path
        )
        feat_prep.prepare()

        # Stage 3: Cognition Replay Execution
        print("\n--- STAGE 3: COGNITION REPLAY ---")
        executor = ReplayExecutor(
            max_days=self.args.days,
            quiet=self.args.quiet,
            dataset_path=self.dataset_path,
            market_name=self.market_name,
            compare_secondary=self.args.cross_asset,
            generate_visualizations=self.args.visualize,
            lineage_debug=self.args.lineage_debug,
            restart=self.args.restart,
            verbose=self.args.verbose,
            force_refresh=self.args.force_refresh,
            data_prep_done=True,  # Instructs executor to skip inline data acquisition
        )

        # Isolate base_data_snap_dir per asset to prevent cross-asset deletion during restart
        executor.base_data_snap_dir = executor.base_data_snap_dir / self.symbol.lower()
        executor._create_snapshot_dirs()

        if self.reset:
            import shutil

            for sub in ["logs", "theories", "confidence", "observations"]:
                sub_dir = executor.replay_dir / sub
                if sub_dir.exists():
                    shutil.rmtree(sub_dir)
            executor._create_snapshot_dirs()

        if self.restart:
            executor.restart_clean()

        # Run replay loop without printing summary
        executor.execute(emit_summary=False)

        # Stage 4: Knowledge Analysis & Reporting
        print("\n--- STAGE 4: KNOWLEDGE ANALYSIS & REPORTING ---")
        analysis_engine = KnowledgeAnalysisEngine(
            market_name=self.market_name, executor=executor
        )
        analysis_engine.analyze()

        report_generator = ReportGenerator(
            executor=executor, analysis_engine=analysis_engine
        )
        report_generator.generate()

        return executor


def main():
    parser = argparse.ArgumentParser(
        description="Run modular stage-based DP Reflective Cognition replay pipeline"
    )
    parser.add_argument(
        "--days", type=int, default=None, help="Max number of trading days to replay"
    )
    parser.add_argument(
        "--nifty",
        action="store_true",
        help="Replay NIFTY 50 instead of RELIANCE (default)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Stock symbol to replay (e.g. TCS, ADANIENT, ONGC)",
    )
    parser.add_argument(
        "--restart", action="store_true", help="Restart replay (clear prior state)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset replay database tables and snapshots",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass caches and download/scrape fresh market data overlays",
    )
    parser.add_argument(
        "--cross-asset",
        action="store_true",
        help="Run optional cross-asset comparison",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate replay visualization images on demand",
    )
    parser.add_argument(
        "--lineage-debug",
        action="store_true",
        help="Enable verbose lineage carry-forward tracing",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug trace output",
    )

    args = parser.parse_args()

    try:
        pipeline = ReplayPipeline(args)
        pipeline.run()
    except Exception as e:
        print(f"\n✗ Replay pipeline execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
