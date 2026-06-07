"""Deterministic replay dataset navigation."""

import hashlib
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from market.data.dataset_validator import DatasetValidator


class ReplayEngine:
    """
    Deterministic replay of cognition loop over historical market data.
    """

    def __init__(
        self,
        dataset_path: str = None,
        market_name: str = "RELIANCE",
        validate: bool = True,
        max_days: int = None,
        verbose: bool = True,
    ):
        """
        Initialize replay engine.

        Args:
            dataset_path: Path to market CSV (default: data/reliance_daily_3y.csv)
            market_name: Label for the market or asset being replayed
            validate: Run validation on load
            max_days: Limit replay to N days (for testing)
            verbose: Print dataset load summary
        """
        if dataset_path:
            self.dataset_path = Path(dataset_path)
        else:
            # Default path: data/ directory at project root
            self.dataset_path = (
                Path(__file__).parent.parent.parent / "data" / "reliance_daily_3y.csv"
            )

        self.market_name = market_name
        self.validate_on_init = validate
        self.max_days = max_days
        self.verbose = verbose
        self.data = None
        self.replay_log = []
        self.execution_hash = None

        self._load_dataset()

    def _load_dataset(self):
        """Load and validate dataset."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        # Validate if requested
        if self.validate_on_init:
            validator = DatasetValidator(str(self.dataset_path))
            results = validator.validate(verbose=False)

            if results["errors"]:
                raise ValueError(f"Dataset validation failed: {results['errors']}")

        # Load dataset
        self.data = pd.read_csv(self.dataset_path)
        self.data["date"] = pd.to_datetime(self.data["date"])

        # Limit to max_days if specified
        if self.max_days:
            self.data = self.data.tail(self.max_days)

        if self.verbose:
            print(
                f"✓ Replay engine loaded {len(self.data)} trading days "
                f"({self.data['date'].min().date()} to "
                f"{self.data['date'].max().date()})"
            )

    def get_observation_for_day(self, day_index: int) -> dict:
        """
        Get deterministic market observation for a day.

        Args:
            day_index: 0-based index into replay dataset

        Returns:
            dict with OHLCV data and synthetic observation
        """
        if day_index < 0 or day_index >= len(self.data):
            raise IndexError(
                f"Day index {day_index} out of range " f"(0 to {len(self.data)-1})"
            )

        row = self.data.iloc[day_index]

        # Get prior day for trend comparison (if available)
        prior_row = self.data.iloc[day_index - 1] if day_index > 0 else None

        return {
            "day_index": day_index,
            "date": row["date"].strftime("%Y-%m-%d"),
            "ohlcv": {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            },
            "prior_ohlcv": (
                {"close": float(prior_row["close"])} if prior_row is not None else None
            ),
            "derived": (
                {
                    "daily_return_pct": float(
                        (row["close"] - row["open"]) / row["open"] * 100
                    ),
                    "volatility_10d": float(row.get("rolling_volatility_10d", 0.0)),
                    "volatility_30d": float(row.get("rolling_volatility_30d", 0.0)),
                    # v2.0 Enriched Metrics
                    "volume_state": row.get("volume_state", "normal"),
                    "volume_ratio_5d": float(row.get("volume_ratio_5d", 1.0)),
                    "volume_ratio_20d": float(row.get("volume_ratio_20d", 1.0)),
                    "range_pct": float(row.get("range_pct", 0.0)),
                    "gap_pct": float(row.get("gap_pct", 0.0)),
                    "atr_14": float(row.get("atr_14", 0.0)),
                    "return_3d": float(row.get("return_3d", 0.0)),
                    "return_5d": float(row.get("return_5d", 0.0)),
                }
                if "rolling_volatility_10d" in row
                else None
            ),
        }

    def get_date_range(self) -> tuple:
        """Return (start_date, end_date) as strings."""
        return (
            self.data["date"].min().strftime("%Y-%m-%d"),
            self.data["date"].max().strftime("%Y-%m-%d"),
        )

    def get_day_count(self) -> int:
        """Return total replaying days."""
        return len(self.data)

    def compute_execution_hash(self, log_entries: list) -> str:
        """
        Compute deterministic hash of replay execution.

        Used to verify determinism across runs.
        """
        combined = "\n".join(str(entry) for entry in log_entries)
        return hashlib.sha256(combined.encode()).hexdigest()

    def log_entry(
        self,
        day_index: int,
        date: str,
        observation_hash: str,
        theory_hash: str,
        confidence_hash: str,
    ):
        """Log a replay day entry for determinism validation."""
        entry = {
            "day_index": day_index,
            "date": date,
            "observation_hash": observation_hash,
            "theory_hash": theory_hash,
            "confidence_hash": confidence_hash,
            "timestamp": datetime.now().isoformat(),
        }
        self.replay_log.append(entry)

    def finalize_execution(self) -> str:
        """Finalize and return execution hash."""
        hashes = [
            entry["observation_hash"] + entry["theory_hash"] + entry["confidence_hash"]
            for entry in self.replay_log
        ]
        combined = "".join(hashes)
        self.execution_hash = hashlib.sha256(combined.encode()).hexdigest()
        return self.execution_hash

    def get_execution_log(self) -> list:
        """Return replay execution log."""
        return self.replay_log

    def __len__(self) -> int:
        """Return number of replay days."""
        return len(self.data) if self.data is not None else 0

    def __repr__(self) -> str:
        """String representation."""
        if self.data is None:
            return "<ReplayEngine: not loaded>"

        start, end = self.get_date_range()
        return f"<ReplayEngine: {len(self.data)} days, " f"{start} to {end}>"
