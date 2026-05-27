"""
Historical NIFTY 50 dataset downloader.

Downloads daily OHLCV data from Yahoo Finance.
Range: Jan 2023 to current date
Deterministic, replayable, offline-first storage.
"""

import os
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf


class NIFTYHistoryDownloader:
    """
    Downloads and persists historical NIFTY 50 data from Yahoo Finance.
    
    Ensures:
    - deterministic output
    - clean data integrity
    - chronological ordering
    - duplicate detection
    """

    TICKER = "^NSEI"
    DEFAULT_START_DATE = "2023-01-01"
    CSV_PATH = None

    def __init__(self, csv_path: str = None):
        """Initialize downloader with optional custom CSV path."""
        if csv_path:
            self.CSV_PATH = csv_path
        else:
            # Default path: data/ directory at project root
            self.CSV_PATH = Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"

    def download(self, start_date: str = None, end_date: str = None):
        """
        Download NIFTY historical data.
        
        Args:
            start_date: Start date (default: 2023-01-01)
            end_date: End date (default: today)
            
        Returns:
            DataFrame with OHLCV data
        """
        start_date = start_date or self.DEFAULT_START_DATE
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")

        print(f"Downloading NIFTY data from {start_date} to {end_date}...")

        try:
            data = yf.download(
                self.TICKER,
                start=start_date,
                end=end_date,
                progress=True
            )

            if data.empty:
                raise ValueError(
                    f"No data available for {self.TICKER} "
                    f"between {start_date} and {end_date}"
                )

            print(f"Downloaded {len(data)} trading days")
            return data

        except Exception as e:
            print(f"Error downloading data: {e}")
            raise

    def persist(
        self,
        data,
        deduplicate: bool = True,
        sort_ascending: bool = True
    ):
        """
        Persist data to CSV with validation and normalization.
        
        Args:
            data: DataFrame from download()
            deduplicate: Remove duplicate dates
            sort_ascending: Sort chronologically ascending
        """
        # Reset index to make date a column
        data = data.reset_index()

        # Handle MultiIndex columns (flatten them)
        if isinstance(data.columns, pd.MultiIndex):
            # Flatten to just the first part of the tuple
            data.columns = [col[0] for col in data.columns]

        # Find date column (could be 'Date', 'date', etc.)
        date_col = None
        for col in data.columns:
            if 'date' in col.lower():
                date_col = col
                break

        if date_col is None:
            raise ValueError(
                f"No date column found. Columns: {list(data.columns)}"
            )

        # Rename date column to lowercase 'date'
        if date_col != 'date':
            data = data.rename(columns={date_col: 'date'})

        # Normalize column names to lowercase
        data.columns = data.columns.str.lower()

        # Add metadata
        data["source"] = f"yfinance:{self.TICKER}"
        data["downloaded_at"] = datetime.now().isoformat()

        # Rename yfinance columns to standard names
        column_mapping = {
            "adj close": "adjusted_close",
            "adjusted close": "adjusted_close"
        }

        for old_col, new_col in column_mapping.items():
            if old_col in data.columns:
                data = data.rename(columns={old_col: new_col})

        # Select required columns
        required_cols = ["date", "open", "high", "low", "close", "adjusted_close", "volume", "source", "downloaded_at"]

        available_cols = [col for col in required_cols if col in data.columns]
        if not available_cols:
            raise ValueError(
                f"Required columns missing. Expected {required_cols}, "
                f"got {list(data.columns)}"
            )

        data = data[available_cols]

        # Remove rows with NaN in OHLCV
        initial_len = len(data)
        data = data.dropna(subset=["open", "high", "low", "close", "volume"])
        if len(data) < initial_len:
            print(f"Removed {initial_len - len(data)} rows with NaN values")

        # Remove future dates
        data["date"] = pd.to_datetime(data["date"])
        today = datetime.now()
        data = data[data["date"] <= today]

        # Deduplicate dates
        if deduplicate:
            initial_len = len(data)
            data = data.drop_duplicates(subset=["date"], keep="first")
            if len(data) < initial_len:
                print(
                    f"Removed {initial_len - len(data)} duplicate date rows"
                )

        # Sort chronologically
        if sort_ascending:
            data = data.sort_values("date", ascending=True)

        # Format date as YYYY-MM-DD string
        data["date"] = data["date"].dt.strftime("%Y-%m-%d")

        # Ensure output directory exists
        self.CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV
        data.to_csv(self.CSV_PATH, index=False)
        print(f"Persisted {len(data)} rows to {self.CSV_PATH}")

        return data

    def add_derived_fields(self):
        """
        Add optional derived fields:
        - daily_return_pct
        - rolling_volatility_10d
        - rolling_volatility_30d
        """
        if not os.path.exists(self.CSV_PATH):
            print(f"CSV not found: {self.CSV_PATH}")
            return

        data = pd.read_csv(self.CSV_PATH)
        # Ensure date is datetime for gap calculations if re-reading
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date")

        # 1. Momentum Metrics
        data["daily_return_pct"] = ((data["close"] - data["open"]) / data["open"] * 100).round(4)
        data["return_3d"] = ((data["close"] - data["close"].shift(3)) / data["close"].shift(3) * 100).round(4)
        data["return_5d"] = ((data["close"] - data["close"].shift(5)) / data["close"].shift(5) * 100).round(4)
        data["return_10d"] = ((data["close"] - data["close"].shift(10)) / data["close"].shift(10) * 100).round(4)

        # 2. Volume Metrics
        data["avg_5d_volume"] = data["volume"].rolling(window=5, min_periods=1).mean().round(0)
        data["avg_20d_volume"] = data["volume"].rolling(window=20, min_periods=1).mean().round(0)
        data["volume_ratio_5d"] = (data["volume"] / data["avg_5d_volume"]).round(4)
        data["volume_ratio_20d"] = (data["volume"] / data["avg_20d_volume"]).round(4)
        
        # Add volume_state label
        conditions = [
            data["volume_ratio_5d"] > 1.5,  # Spike
            data["volume_ratio_5d"] > 1.1,  # Elevated
            data["volume_ratio_5d"] < 0.9   # Dry
        ]
        choices = ["spike", "elevated", "dry"]
        data["volume_state"] = np.select(conditions, choices, default="normal")


        # 3. Volatility & Range Metrics
        data["range_points"] = (data["high"] - data["low"]).round(2)
        data["range_pct"] = ((data["high"] - data["low"]) / data["close"] * 100).round(4)
        
        prior_close = data["close"].shift(1)
        data["gap_points"] = (data["open"] - prior_close).round(2)
        data["gap_pct"] = ((data["open"] - prior_close) / prior_close * 100).round(4)

        # ATR Calculation (True Range)
        tr = pd.concat([
            data["high"] - data["low"],
            (data["high"] - prior_close).abs(),
            (data["low"] - prior_close).abs()
        ], axis=1).max(axis=1)
        data["atr_5"] = tr.rolling(window=5).mean().round(2)
        data["atr_14"] = tr.rolling(window=14).mean().round(2)

        # Legacy Volatility Metrics (Backward Compatibility)
        data["rolling_volatility_10d"] = (
            data["daily_return_pct"]
            .rolling(window=10, min_periods=1)
            .std()
        ).round(4)
        data["rolling_volatility_30d"] = (
            data["daily_return_pct"]
            .rolling(window=30, min_periods=1)
            .std()
        ).round(4)

        # Re-format date to string for CSV
        data["date"] = data["date"].dt.strftime("%Y-%m-%d")
        data.to_csv(self.CSV_PATH, index=False)
        print(f"Added derived fields. Updated: {self.CSV_PATH}")


def main():
    """Download and persist NIFTY historical data."""
    downloader = NIFTYHistoryDownloader()

    try:
        # Download data
        data = downloader.download()

        # Persist with validation
        downloader.persist(data)

        # Add derived fields
        downloader.add_derived_fields()

        print("✓ NIFTY historical dataset ready for replay")

    except Exception as e:
        print(f"✗ Download failed: {e}")
        raise


if __name__ == "__main__":
    import pandas as pd
    main()
