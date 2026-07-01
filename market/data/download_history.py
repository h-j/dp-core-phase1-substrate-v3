"""
Shared historical market downloader utilities.

Provides a single deterministic downloader + persistence workflow
for both NIFTY and stock-specific datasets.
"""

import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from market.data.nse_fetcher import NSEFetcher
from market.data.moneycontrol_fetcher import MoneycontrolFetcher


class HistoricalMarketDownloader:
    """
    Shared downloader for historical OHLCV datasets.

    Subclasses should define:
    - TICKER
    - DEFAULT_CSV_NAME
    - DEFAULT_START_DATE
    """

    TICKER = ""
    DEFAULT_CSV_NAME = "dataset.csv"
    DEFAULT_START_DATE = "2023-01-01"
    CSV_PATH = None

    def __init__(self, csv_path: str = None):
        if csv_path:
            self.CSV_PATH = Path(csv_path)
        else:
            self.CSV_PATH = (
                Path(__file__).parent.parent.parent / "data" / self.DEFAULT_CSV_NAME
            )

    def download(self, start_date: str = None, end_date: str = None):
        start_date = start_date or self.DEFAULT_START_DATE
        end_date = end_date or datetime.now().strftime("%Y-%m-%d")

        print(f"Downloading {self.TICKER} data from {start_date} to {end_date}...")

        try:
            data = yf.download(
                self.TICKER,
                start=start_date,
                end=end_date,
                progress=True,
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
        sort_ascending: bool = True,
    ):
        data = data.reset_index()

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        date_col = None
        for col in data.columns:
            if "date" in col.lower():
                date_col = col
                break

        if date_col is None:
            raise ValueError(f"No date column found. Columns: {list(data.columns)}")

        if date_col != "date":
            data = data.rename(columns={date_col: "date"})

        data.columns = data.columns.str.lower()

        data["source"] = f"yfinance:{self.TICKER}"
        data["downloaded_at"] = datetime.now().isoformat()

        for old_col, new_col in {
            "adj close": "adjusted_close",
            "adjusted close": "adjusted_close",
        }.items():
            if old_col in data.columns:
                data = data.rename(columns={old_col: new_col})

        required_cols = [
            "date",
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
            "source",
            "downloaded_at",
        ]
        available_cols = [col for col in required_cols if col in data.columns]
        if not available_cols:
            raise ValueError(
                f"Required columns missing. Expected {required_cols}, got {list(data.columns)}"
            )

        data = data[available_cols]
        initial_len = len(data)
        data = data.dropna(subset=["open", "high", "low", "close", "volume"])
        if len(data) < initial_len:
            print(f"Removed {initial_len - len(data)} rows with NaN values")

        data["date"] = pd.to_datetime(data["date"])
        today = datetime.now()
        data = data[data["date"] <= today]

        if deduplicate:
            initial_len = len(data)
            data = data.drop_duplicates(subset=["date"], keep="first")
            if len(data) < initial_len:
                print(f"Removed {initial_len - len(data)} duplicate date rows")

        if sort_ascending:
            data = data.sort_values("date", ascending=True)

        data["date"] = data["date"].dt.strftime("%Y-%m-%d")
        self.CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(self.CSV_PATH, index=False)
        print(f"Persisted {len(data)} rows to {self.CSV_PATH}")
        return data

    def add_derived_fields(self):
        if not os.path.exists(self.CSV_PATH):
            print(f"CSV not found: {self.CSV_PATH}")
            return

        data = pd.read_csv(self.CSV_PATH)
        data["date"] = pd.to_datetime(data["date"])
        data = data.sort_values("date")

        data["daily_return_pct"] = (
            (data["close"] - data["open"]) / data["open"] * 100
        ).round(4)
        data["return_3d"] = (
            (data["close"] - data["close"].shift(3)) / data["close"].shift(3) * 100
        ).round(4)
        data["return_5d"] = (
            (data["close"] - data["close"].shift(5)) / data["close"].shift(5) * 100
        ).round(4)
        data["return_10d"] = (
            (data["close"] - data["close"].shift(10)) / data["close"].shift(10) * 100
        ).round(4)

        data["avg_5d_volume"] = (
            data["volume"].rolling(window=5, min_periods=1).mean().round(0)
        )
        data["avg_20d_volume"] = (
            data["volume"].rolling(window=20, min_periods=1).mean().round(0)
        )
        data["volume_ratio_5d"] = (data["volume"] / data["avg_5d_volume"]).round(4)
        data["volume_ratio_20d"] = (data["volume"] / data["avg_20d_volume"]).round(4)

        conditions = [
            data["volume_ratio_5d"] > 1.5,
            data["volume_ratio_5d"] > 1.1,
            data["volume_ratio_5d"] < 0.9,
        ]
        choices = ["spike", "elevated", "dry"]
        data["volume_state"] = np.select(conditions, choices, default="normal")

        data["range_points"] = (data["high"] - data["low"]).round(2)
        data["range_pct"] = ((data["high"] - data["low"]) / data["close"] * 100).round(
            4
        )

        prior_close = data["close"].shift(1)
        data["gap_points"] = (data["open"] - prior_close).round(2)
        data["gap_pct"] = ((data["open"] - prior_close) / prior_close * 100).round(4)

        tr = pd.concat(
            [
                data["high"] - data["low"],
                (data["high"] - prior_close).abs(),
                (data["low"] - prior_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        data["atr_5"] = tr.rolling(window=5).mean().round(2)
        data["atr_14"] = tr.rolling(window=14).mean().round(2)

        data["rolling_volatility_10d"] = (
            data["daily_return_pct"].rolling(window=10, min_periods=1).std()
        ).round(4)
        data["rolling_volatility_30d"] = (
            data["daily_return_pct"].rolling(window=30, min_periods=1).std()
        ).round(4)

        data["date"] = data["date"].dt.strftime("%Y-%m-%d")
        data.to_csv(self.CSV_PATH, index=False)
        print(f"Added derived fields. Updated: {self.CSV_PATH}")

    def is_latest(self) -> bool:
        """
        Check if the local dataset is already up-to-date.
        Considers weekends and intra-day trading hours (assuming market close at 16:00).
        """
        if not self.CSV_PATH.exists():
            return False

        try:
            df = pd.read_csv(self.CSV_PATH)
            if df.empty or "date" not in df.columns:
                return False

            df["date"] = pd.to_datetime(df["date"])
            latest_date = df["date"].max()

            now = datetime.now()
            # If latest date in CSV is today or in the future, it is up-to-date
            if latest_date.date() >= now.date():
                return True

            # Adjust check based on weekends and active trading hours
            weekday = now.weekday()
            delta_days = (now.date() - latest_date.date()).days

            if weekday == 5:  # Saturday
                # If latest date is Friday (1 day ago), it's latest
                if delta_days <= 1:
                    return True
            elif weekday == 6:  # Sunday
                # If latest date is Friday (2 days ago), it's latest
                if delta_days <= 2:
                    return True
            elif weekday == 0 and now.hour < 16:  # Monday before 16:00
                # If latest date is Friday (3 days ago), it's latest
                if delta_days <= 3:
                    return True
            else:
                # If it's a weekday after 16:00, we expect today's data.
                # If before 16:00, yesterday's data (1 day ago) is acceptable.
                if now.hour < 16:
                    if delta_days <= 1:
                        return True

            return False
        except Exception as e:
            print(f"Error checking if dataset is latest: {e}")
            return False

    def update_incremental(self) -> bool:
        """
        Incrementally download missing latest market data,
        merge with existing dataset, and update derived fields.
        Returns True if new rows were added, False otherwise.
        """
        if not self.CSV_PATH.exists():
            print(f"No existing dataset at {self.CSV_PATH}. Performing full download.")
            data = self.download()
            self.persist(data)
            self.add_derived_fields()
            return True

        try:
            existing_df = pd.read_csv(self.CSV_PATH)
            if existing_df.empty or "date" not in existing_df.columns:
                print(
                    f"Dataset at {self.CSV_PATH} is empty or invalid. Performing full download."
                )
                data = self.download()
                self.persist(data)
                self.add_derived_fields()
                return True

            # Get latest date in string format
            existing_df["date"] = pd.to_datetime(existing_df["date"])
            latest_date = existing_df["date"].max()
            latest_date_str = latest_date.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"Error reading existing dataset: {e}. Performing full download.")
            data = self.download()
            self.persist(data)
            self.add_derived_fields()
            return True

        today_str = datetime.now().strftime("%Y-%m-%d")
        if latest_date_str >= today_str:
            print(
                f"Dataset already includes today's date ({latest_date_str}). No update needed."
            )
            return False

        print(
            f"Dataset latest date: {latest_date_str}. Fetching updates from yfinance..."
        )
        try:
            # yfinance start_date is inclusive. We start from latest_date_str to ensure overlapping
            # boundary rows are cleanly updated/deduplicated.
            new_data = self.download(start_date=latest_date_str)
            if new_data.empty:
                print("No new data returned from yfinance.")
                return False

            new_data = new_data.reset_index()
            if isinstance(new_data.columns, pd.MultiIndex):
                new_data.columns = [col[0] for col in new_data.columns]

            date_col = None
            for col in new_data.columns:
                if "date" in col.lower():
                    date_col = col
                    break

            if date_col is None:
                print(
                    f"No date column found in downloaded data. Columns: {list(new_data.columns)}"
                )
                return False

            if date_col != "date":
                new_data = new_data.rename(columns={date_col: "date"})

            new_data.columns = new_data.columns.str.lower()
            new_data["source"] = f"yfinance:{self.TICKER}"
            new_data["downloaded_at"] = datetime.now().isoformat()

            for old_col, new_col in {
                "adj close": "adjusted_close",
                "adjusted close": "adjusted_close",
            }.items():
                if old_col in new_data.columns:
                    new_data = new_data.rename(columns={old_col: new_col})

            required_cols = [
                "date",
                "open",
                "high",
                "low",
                "close",
                "adjusted_close",
                "volume",
                "source",
                "downloaded_at",
            ]
            available_cols = [col for col in required_cols if col in new_data.columns]
            new_data = new_data[available_cols]
            new_data = new_data.dropna(
                subset=["open", "high", "low", "close", "volume"]
            )

            new_data["date"] = pd.to_datetime(new_data["date"])
            existing_df["date"] = pd.to_datetime(existing_df["date"])

            # Merge and deduplicate
            initial_row_count = len(existing_df)
            combined_df = pd.concat([existing_df, new_data])
            combined_df = combined_df.drop_duplicates(subset=["date"], keep="last")
            combined_df = combined_df.sort_values("date", ascending=True)

            # Ensure we don't leak future dates
            today = datetime.now()
            combined_df = combined_df[combined_df["date"] <= today]

            # Write back to CSV
            combined_df["date"] = combined_df["date"].dt.strftime("%Y-%m-%d")
            self.CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
            combined_df.to_csv(self.CSV_PATH, index=False)

            new_rows_count = len(combined_df) - initial_row_count
            if new_rows_count > 0:
                print(
                    f"✓ Added {new_rows_count} new trading days incrementally. Total: {len(combined_df)} rows."
                )
                self.add_derived_fields()
                return True
            else:
                print("No new trading days were added after deduplication.")
                return False

        except Exception as e:
            print(f"Failed to incrementally update market data: {e}")
            raise


class NIFTYHistoryDownloader(HistoricalMarketDownloader):
    TICKER = "^NSEI"
    DEFAULT_CSV_NAME = "nifty_daily_3y.csv"


class RelianceHistoryDownloader(HistoricalMarketDownloader):
    TICKER = "RELIANCE.NS"
    DEFAULT_CSV_NAME = "reliance_daily_3y.csv"


class GenericHistoryDownloader(HistoricalMarketDownloader):
    """
    A generic downloader that lets us fetch any arbitrary ticker dynamically.
    """
    def __init__(self, ticker: str, csv_path: str):
        self.TICKER = ticker
        super().__init__(csv_path=csv_path)


STOCK_SECTOR_MAP = {
    "RELIANCE": "^CNXENERGY",
    "RELIANCE.NS": "^CNXENERGY",
    "NIFTY 50": "^NSEI",
    "NIFTY": "^NSEI",
    "TCS": "^CNXIT",
    "TCS.NS": "^CNXIT",
    "ADANIENT": "^CNXINFRA",
    "ADANIENT.NS": "^CNXINFRA",
    "ONGC": "^CNXENERGY",
    "ONGC.NS": "^CNXENERGY",
}


def ensure_data(
    symbol: str,
    start_date: str = "2023-01-01",
    end_date: str = None,
    force_refresh: bool = False,
    dataset_path: str = None
) -> pd.DataFrame:
    """
    Ensures that the primary dataset is prepared and enriched by delegating to the 
    DataPreparationManager and FeaturePreparationManager stages.
    """
    from market.replay.run import DataPreparationManager, FeaturePreparationManager
    
    # 1. Run Data Preparation Stage
    prep_manager = DataPreparationManager(
        symbol=symbol,
        force_refresh=force_refresh,
        dataset_path=dataset_path
    )
    prep_manager.prepare(start_date=start_date, end_date=end_date)
    
    # 2. Run Feature Preparation Stage
    feature_manager = FeaturePreparationManager(
        symbol=symbol,
        dataset_path=dataset_path
    )
    return feature_manager.prepare()
