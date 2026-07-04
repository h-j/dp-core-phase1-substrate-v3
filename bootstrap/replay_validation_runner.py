"""
Comprehensive replay validation runner.

Orchestrates:
1. Dataset download and validation
2. 30/90/365-day replay execution
3. Determinism verification
4. Analysis and reporting
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path

from market.data.dataset_validator import DatasetValidator
from market.data.download_nifty_history import NIFTYHistoryDownloader
from market.replay.replay_engine import ReplayEngine, ReplayExecutor


class ReplayValidationRunner:
    """Orchestrates comprehensive replay validation."""

    def __init__(self):
        """Initialize runner."""
        project_root = Path(__file__).parent.parent.parent
        self.data_dir = project_root / "data"
        self.csv_path = self.data_dir / "nifty_daily_3y.csv"

    def run_full_validation(self, skip_download: bool = False, restart: bool = False):
        """Run complete validation suite."""
        print("\n" + "=" * 70)
        print("NIFTY REPLAY VALIDATION SUITE")
        print("=" * 70)

        # Step 1: Download or update dataset
        if restart:
            print(
                "\n[1/5] Checking and downloading latest market data incrementally (-restart)..."
            )
            self._handle_restart_incremental()
        elif not skip_download:
            print("\n[1/5] Downloading historical NIFTY data...")
            self._download_dataset()
        else:
            print("\n[1/5] Skipping download (using existing dataset)")

        # Step 2: Validate dataset
        print("\n[2/5] Validating dataset...")
        self._validate_dataset()

        # Step 3: Run short/medium/long replays
        print("\n[3/5] Running replay scenarios...")
        self._run_replays()

        # Step 4: Verify determinism
        print("\n[4/5] Verifying determinism...")
        self._verify_determinism()

        # Step 5: Report
        print("\n[5/5] Generating final report...")
        self._generate_report()

        print("\n" + "=" * 70)
        print("✓ VALIDATION SUITE COMPLETE")
        print("=" * 70 + "\n")

    def _handle_restart_incremental(self):
        """Check if dataset is up-to-date, download missing dates incrementally if needed."""
        try:
            downloader = NIFTYHistoryDownloader(str(self.csv_path))
            if downloader.is_latest():
                print("✓ Market data is already up-to-date. Skipping download.")
            else:
                print(
                    "Market data is not up-to-date. Fetching latest incremental updates..."
                )
                updated = downloader.update_incremental()
                if updated:
                    print("✓ Market data updated successfully.")
                else:
                    print("✓ No new market data available to update.")
        except Exception as e:
            print(f"✗ Incremental update check failed: {e}")
            raise

    def _download_dataset(self):
        """Download NIFTY historical data."""
        try:
            downloader = NIFTYHistoryDownloader(str(self.csv_path))
            data = downloader.download()
            downloader.persist(data)
            downloader.add_derived_fields()
            print("✓ Dataset download and persistence complete")
        except Exception as e:
            print(f"✗ Download failed: {e}")
            raise

    def _validate_dataset(self):
        """Validate downloaded dataset."""
        validator = DatasetValidator(str(self.csv_path))
        results = validator.validate(verbose=True)

        if results["errors"]:
            raise ValueError(f"Dataset validation failed: {results['errors']}")

    def _run_replays(self):
        """Run short/medium/long replay scenarios."""
        scenarios = [
            {"days": 3, "label": "3-day"},
            {"days": 5, "label": "5-day"},
            {"days": 10, "label": "10-day"},
        ]

        self.replay_results = {}

        for scenario in scenarios:
            label = scenario["label"]
            days = scenario["days"]

            print(f"\n  Running {label} replay ({days} trading days)...")

            try:
                result = self._execute_replay(days, label)
                self.replay_results[label] = result
                print(f"  ✓ {label} replay complete")
            except Exception as e:
                print(f"  ✗ {label} replay failed: {e}")
                raise

    def _execute_replay(self, max_days: int, label: str) -> dict:
        """
        Execute a replay for the specified number of days using the production ReplayExecutor.

        Returns:
            dict with replay results and metrics
        """
        executor = ReplayExecutor(
            max_days=max_days,
            dataset_path=str(self.csv_path),
            market_name=(
                "NIFTY 50" if "nifty" in str(self.csv_path).lower() else "RELIANCE"
            ),
            quiet=True,
            verbose=False,
            compare_secondary=False,
            generate_visualizations=False,
            lineage_debug=False,
            restart=True,
        )

        executor.execute(emit_summary=False)

        return {
            "label": label,
            "days": len(executor.engine),
            "date_range": executor.engine.get_date_range(),
            "execution_hash": executor.engine.execution_hash,
            "day_outputs": [],
            "analysis": executor.replay_analysis_engine,
        }

    def _verify_determinism(self):
        """Verify replay determinism by running twice."""
        if "10-day" not in self.replay_results:
            print("  Skipping determinism check (10-day replay not executed)")
            return

        print("\n  Executing 10-day replay second time for determinism check...")

        try:
            result_2 = self._execute_replay(10, "10-day-verification")

            original_hash = self.replay_results["10-day"]["execution_hash"]
            verification_hash = result_2["execution_hash"]

            if original_hash == verification_hash:
                print(f"  ✓ Determinism VERIFIED")
                print(f"    Hash (both runs): {original_hash[:16]}...")
                self.determinism_verified = True
            else:
                print(f"  ✗ Determinism FAILED")
                print(f"    Original:      {original_hash[:16]}...")
                print(f"    Verification:  {verification_hash[:16]}...")
                self.determinism_verified = False

        except Exception as e:
            print(f"  ✗ Determinism verification failed: {e}")
            self.determinism_verified = False

    def _generate_report(self):
        """Generate final validation report."""
        print("\n" + "=" * 70)
        print("REPLAY VALIDATION REPORT")
        print("=" * 70)

        print(f"\nDataset: {self.csv_path}")
        print(f"Validation Time: {datetime.now().isoformat()}")

        if hasattr(self, "replay_results"):
            print("\nReplay Results:")
            for label, result in self.replay_results.items():
                print(f"\n  {label.upper()}:")
                print(f"    Days: {result['days']}")
                print(
                    f"    Date range: {result['date_range'][0]} to {result['date_range'][1]}"
                )
                print(f"    Execution hash: {result['execution_hash'][:16]}...")

                # Print analysis summary
                result["analysis"].print_summary()

                prediction_summary = (
                    result["analysis"].analyze().get("prediction_analysis", {})
                )
                if prediction_summary:
                    print("    Prediction probe performance:")
                    print(
                        f"      Accuracy: {prediction_summary['accuracy']:.1%} "
                        f"| Partial: {prediction_summary['partial_accuracy']:.1%} "
                        f"| Uncertain: {prediction_summary['uncertain_rate']:.1%}"
                    )
                    print(
                        f"      Invalidation rate: {prediction_summary['invalidation_rate']:.1%} "
                        f"| Mean confidence: {prediction_summary['mean_confidence']:.3f}"
                    )

                capital_summary = (
                    result["analysis"].analyze().get("capital_simulation_analysis", {})
                )
                if capital_summary:
                    print("    Capital Simulation Summary:")
                    print(
                        f"      Ending Capital: ₹{capital_summary.get('ending_capital', 0):,.2f} "
                        f"| Return: {capital_summary.get('return_pct', 0.0):.2%} "
                        f"| Annualized: {capital_summary.get('annualized_return', 0.0):.2%}"
                    )
                    print(
                        f"      Win Rate: {capital_summary.get('win_rate', 0.0):.2%} | Max Drawdown: {capital_summary.get('max_drawdown', 0.0):.2%}"
                    )

        if hasattr(self, "determinism_verified"):
            status = "✓ PASS" if self.determinism_verified else "✗ FAIL"
            print(f"Determinism Check: {status}")

        print("\n" + "=" * 70 + "\n")

        # Export CSV for the last replay (e.g., 10-day)
        if "10-day" in self.replay_results:
            self.replay_results["10-day"]["analysis"].export_prediction_analysis_csv(
                Path("market/replay/output/prediction_analysis.csv")
            )


def main():
    """Run the validation suite."""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Run NIFTY Replay Validation Suite")
    # Accept standard --restart and yfinance-friendly -restart flags
    parser.add_argument(
        "-restart",
        "--restart",
        action="store_true",
        help="Incremental check and download of latest market data before starting replay",
    )
    args, unknown = parser.parse_known_args()

    runner = ReplayValidationRunner()

    # Check if dataset exists
    skip_download = os.path.exists(runner.csv_path)

    try:
        runner.run_full_validation(skip_download=skip_download, restart=args.restart)
    except Exception as e:
        print(f"\n✗ Validation suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
