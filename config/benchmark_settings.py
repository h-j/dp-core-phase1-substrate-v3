from pathlib import Path

# Standard benchmark asset registry and characteristics classification map.
# Supports adding new assets simply by adding entries to this dictionary.
BENCHMARK_ASSETS = {
    "RELIANCE": {
        "sector_index": "^CNXENERGY",
        "category": "Stable Large Cap",
        "volatility": "moderate",
        "trend_persistence": "high",
        "participation_profile": "high",
        "sector": "Energy",
        "liquidity": "extremely_high",
    },
    "TCS": {
        "sector_index": "^CNXIT",
        "category": "Trending Technology",
        "volatility": "low",
        "trend_persistence": "moderate",
        "participation_profile": "high",
        "sector": "Technology",
        "liquidity": "high",
    },
    "ADANIENT": {
        "sector_index": "^CNXINFRA",
        "category": "High Volatility",
        "volatility": "high",
        "trend_persistence": "high",
        "participation_profile": "speculative",
        "sector": "Infrastructure",
        "liquidity": "high",
    },
    "ONGC": {
        "sector_index": "^CNXENERGY",
        "category": "Commodity / Macro Sensitive",
        "volatility": "moderate",
        "trend_persistence": "moderate",
        "participation_profile": "institutional",
        "sector": "Energy",
        "liquidity": "moderate",
    },
    "NIFTY": {
        "sector_index": "^NSEI",
        "category": "Index",
        "volatility": "low",
        "trend_persistence": "moderate",
        "participation_profile": "broad",
        "sector": "Index",
        "liquidity": "maximum",
    },
}
