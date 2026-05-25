"""
Dataset validation for historical NIFTY replay integrity.

Ensures:
- no duplicate dates
- no future dates
- no missing required columns
- no NaN OHLCV values
- chronological ordering
- minimum replayable size
"""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd


class DatasetValidator:
    """
    Validates historical NIFTY dataset for replay integrity.
    """

    REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
    MIN_ROWS = 250  # ~1 year of trading days

    def __init__(self, csv_path: str = None):
        """Initialize validator with optional custom CSV path."""
        if csv_path:
            self.CSV_PATH = csv_path
        else:
            # Default path: data/ directory at project root
            self.CSV_PATH = Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"

    def validate(self, verbose: bool = True) -> dict:
        """
        Run comprehensive validation.
        
        Returns:
            dict with validation results and summary
        """
        results = {
            "file_exists": False,
            "columns_valid": False,
            "no_duplicates": False,
            "no_future_dates": False,
            "no_nan_ohlcv": False,
            "chronological_order": False,
            "minimum_size": False,
            "errors": [],
            "warnings": [],
            "summary": "",
            "row_count": 0,
            "date_range": None
        }

        # Check file exists
        if not os.path.exists(self.CSV_PATH):
            results["errors"].append(
                f"CSV file not found: {self.CSV_PATH}"
            )
            if verbose:
                self._print_results(results)
            return results

        results["file_exists"] = True

        try:
            data = pd.read_csv(self.CSV_PATH)
        except Exception as e:
            results["errors"].append(f"Failed to read CSV: {e}")
            if verbose:
                self._print_results(results)
            return results

        results["row_count"] = len(data)

        # Check columns
        missing_cols = [
            col for col in self.REQUIRED_COLUMNS
            if col not in data.columns
        ]

        if missing_cols:
            results["errors"].append(
                f"Missing required columns: {missing_cols}"
            )
        else:
            results["columns_valid"] = True

        # Check for duplicates
        duplicate_count = data.duplicated(subset=["date"]).sum()
        if duplicate_count > 0:
            results["errors"].append(
                f"Found {duplicate_count} duplicate dates"
            )
        else:
            results["no_duplicates"] = True

        # Check for future dates
        data["date"] = pd.to_datetime(data["date"])
        today = datetime.now().date()
        future_dates = (data["date"].dt.date > today).sum()

        if future_dates > 0:
            results["errors"].append(
                f"Found {future_dates} future dates (after today)"
            )
        else:
            results["no_future_dates"] = True

        # Check for NaN in OHLCV
        ohlcv_cols = ["open", "high", "low", "close", "volume"]
        present_ohlcv = [col for col in ohlcv_cols if col in data.columns]

        nan_count = data[present_ohlcv].isna().sum().sum()
        if nan_count > 0:
            results["errors"].append(
                f"Found {nan_count} NaN values in OHLCV"
            )
        else:
            results["no_nan_ohlcv"] = True

        # Check chronological order
        is_sorted = data["date"].is_monotonic_increasing
        if not is_sorted:
            results["errors"].append("Data is not sorted chronologically")
        else:
            results["chronological_order"] = True

        # Check minimum size
        if len(data) < self.MIN_ROWS:
            results["warnings"].append(
                f"Dataset has {len(data)} rows; "
                f"recommended minimum is {self.MIN_ROWS}"
            )
        else:
            results["minimum_size"] = True

        # Capture date range
        if len(data) > 0:
            start_date = data["date"].min().strftime("%Y-%m-%d")
            end_date = data["date"].max().strftime("%Y-%m-%d")
            results["date_range"] = (start_date, end_date)

        # Generate summary
        all_passed = all([
            results["file_exists"],
            results["columns_valid"],
            results["no_duplicates"],
            results["no_future_dates"],
            results["no_nan_ohlcv"],
            results["chronological_order"],
            results["minimum_size"]
        ])

        if all_passed:
            results["summary"] = (
                f"✓ Dataset validation PASSED "
                f"({len(data)} rows, {results['date_range'][0]} to "
                f"{results['date_range'][1]})"
            )
        else:
            results["summary"] = (
                f"✗ Dataset validation FAILED "
                f"({len(results['errors'])} errors, "
                f"{len(results['warnings'])} warnings)"
            )

        if verbose:
            self._print_results(results)

        return results

    def _print_results(self, results: dict):
        """Print validation results in human-readable format."""
        print("\n" + "=" * 60)
        print("DATASET VALIDATION RESULTS")
        print("=" * 60)

        print(f"File: {self.CSV_PATH}")
        print(f"File exists: {results['file_exists']}")
        print(f"Rows: {results['row_count']}")

        if results["date_range"]:
            print(
                f"Date range: {results['date_range'][0]} to "
                f"{results['date_range'][1]}"
            )

        print("\nValidation Checks:")
        print(f"  Columns valid:         {results['columns_valid']}")
        print(f"  No duplicates:         {results['no_duplicates']}")
        print(f"  No future dates:       {results['no_future_dates']}")
        print(f"  No NaN in OHLCV:       {results['no_nan_ohlcv']}")
        print(f"  Chronological order:   {results['chronological_order']}")
        print(f"  Minimum size:          {results['minimum_size']}")

        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")

        if results["warnings"]:
            print("\nWarnings:")
            for warning in results["warnings"]:
                print(f"  - {warning}")

        print(f"\n{results['summary']}")
        print("=" * 60 + "\n")


def main():
    """Validate the NIFTY dataset."""
    validator = DatasetValidator()
    results = validator.validate(verbose=True)
    return results


if __name__ == "__main__":
    main()
