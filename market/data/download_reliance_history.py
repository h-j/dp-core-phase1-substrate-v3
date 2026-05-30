"""
Historical RELIANCE.NS dataset downloader.

Downloads daily OHLCV data from Yahoo Finance and persists in the same schema
as NIFTY historical data.
"""

from market.data.download_history import RelianceHistoryDownloader


def main():
    """Download and persist RELIANCE historical data."""
    downloader = RelianceHistoryDownloader()

    try:
        data = downloader.download()
        downloader.persist(data)
        downloader.add_derived_fields()
        print("✓ RELIANCE historical dataset ready for replay")

    except Exception as e:
        print(f"✗ Download failed: {e}")
        raise


if __name__ == "__main__":
    main()
