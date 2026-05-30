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
            self.CSV_PATH = Path(__file__).parent.parent.parent / "data" / self.DEFAULT_CSV_NAME

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
            raise ValueError(
                f"No date column found. Columns: {list(data.columns)}"
            )

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

        required_cols = ["date", "open", "high", "low", "close", "adjusted_close", "volume", "source", "downloaded_at"]
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

        data["daily_return_pct"] = ((data["close"] - data["open"]) / data["open"] * 100).round(4)
        data["return_3d"] = ((data["close"] - data["close"].shift(3)) / data["close"].shift(3) * 100).round(4)
        data["return_5d"] = ((data["close"] - data["close"].shift(5)) / data["close"].shift(5) * 100).round(4)
        data["return_10d"] = ((data["close"] - data["close"].shift(10)) / data["close"].shift(10) * 100).round(4)

        data["avg_5d_volume"] = data["volume"].rolling(window=5, min_periods=1).mean().round(0)
        data["avg_20d_volume"] = data["volume"].rolling(window=20, min_periods=1).mean().round(0)
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
        data["range_pct"] = ((data["high"] - data["low"]) / data["close"] * 100).round(4)

        prior_close = data["close"].shift(1)
        data["gap_points"] = (data["open"] - prior_close).round(2)
        data["gap_pct"] = ((data["open"] - prior_close) / prior_close * 100).round(4)

        tr = pd.concat([
            data["high"] - data["low"],
            (data["high"] - prior_close).abs(),
            (data["low"] - prior_close).abs(),
        ], axis=1).max(axis=1)
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


class NIFTYHistoryDownloader(HistoricalMarketDownloader):
    TICKER = "^NSEI"
    DEFAULT_CSV_NAME = "nifty_daily_3y.csv"


class RelianceHistoryDownloader(HistoricalMarketDownloader):
    TICKER = "RELIANCE.NS"
    DEFAULT_CSV_NAME = "reliance_daily_3y.csv"
