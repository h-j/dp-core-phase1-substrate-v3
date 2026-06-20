"""
Historical NIFTY 50 dataset downloader.

Downloads daily OHLCV data from Yahoo Finance.
Range: Jan 2023 to current date
Deterministic, replayable, offline-first storage.
"""

from market.data.download_history import NIFTYHistoryDownloader


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
