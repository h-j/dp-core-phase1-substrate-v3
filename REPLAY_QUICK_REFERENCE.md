# NIFTY Replay System - Quick Reference Guide

## Installation & Setup

### 1. Install Dependencies
```bash
cd dp-core-phase1-substrate-v3
poetry lock
poetry install
```

### 2. Download Dataset
```bash
poetry run python -m market.data.download_nifty_history
```

Output: `data/nifty_daily_3y.csv` (829 trading days)

### 3. Validate Dataset
```bash
poetry run python -m market.data.dataset_validator
```

Expected output:
```
✓ Dataset validation PASSED (829 rows, 2023-01-02 to 2026-05-15)
```

---

## Quick Demo

### Run Demonstration
```bash
poetry run python -m bootstrap.replay_demo
```

Shows:
- Dataset loading
- Scenario definitions (30/90/365-day)
- Observation synthesis samples
- Determinism verification

---

## Python API Usage

### Using the Replay Engine

```python
from market.replay.replay_engine import ReplayEngine
import pandas as pd

# Initialize engine
engine = ReplayEngine(max_days=30)  # 30-day replay

# Iterate through trading days
for day_idx in range(len(engine)):
    day_data = engine.get_observation_for_day(day_idx)
    
    print(f"Date: {day_data['date']}")
    print(f"OHLCV: {day_data['ohlcv']}")
    print(f"Return: {day_data['derived']['daily_return_pct']:.2f}%")
    
    # Log entry for determinism tracking
    engine.log_entry(
        day_idx,
        day_data['date'],
        obs_hash="...",
        theory_hash="...",
        conf_hash="..."
    )

# Finalize and get execution hash
execution_hash = engine.finalize_execution()
print(f"Execution hash: {execution_hash}")
```

### Using Observation Synthesizer

```python
from market.replay.market_observation_synthesizer import MarketObservationSynthesizer
import pandas as pd

# Load data
data = pd.read_csv("data/nifty_daily_3y.csv")
synthesizer = MarketObservationSynthesizer(data)

# Generate observation for specific day
observation = synthesizer.synthesize(day_index=100)

print(f"Text: {observation.observation_text}")
print(f"Trend: {observation.trend_state}")
print(f"Volatility: {observation.volatility_state}")
print(f"Breadth: {observation.breadth_state}")
print(f"Contradictions: {observation.contradiction_markers}")
```

### Using Analysis Engine

```python
from market.replay.replay_analysis import ReplayAnalysisEngine

analysis = ReplayAnalysisEngine()

# Record cognition state for each day
for day in days:
    analysis.record_day(
        day_index=day['idx'],
        date=day['date'],
        confidence_state={
            'empirical_confidence': 0.65,
            'regime_confidence': 0.72,
            'reflection_confidence': 0.58,
            'theoretical_coherence': 0.61,
            'contradiction_pressure': 0.42
        },
        contradiction_result={
            'score': 0.42,
            'contradictions': ['price_up_breadth_down']
        },
        theory_summary="Market structure supports continuation...",
        reflection_summary="Observation of weak breadth suggests...",
        market_regime="uptrend"
    )

# Analyze
results = analysis.analyze()

# Print summary
analysis.print_summary()
```

---

## Dataset Structure

### CSV Format
```csv
date,open,high,low,close,volume,daily_return_pct,rolling_volatility_10d,rolling_volatility_30d
2023-01-02,18131.70,18215.15,18086.50,18197.45,256100,0.3626,,
2023-01-03,18163.20,18251.95,18149.80,18232.55,208700,0.3818,0.0136,0.0136
...
2026-05-15,23731.40,23839.30,23610.30,23643.50,408900,-0.3704,0.6344,0.7051
```

### Columns
- **date**: Trading date (YYYY-MM-DD)
- **open**: Opening price
- **high**: Highest price of the day
- **low**: Lowest price of the day
- **close**: Closing price
- **volume**: Trading volume
- **daily_return_pct**: (close - open) / open * 100
- **rolling_volatility_10d**: 10-day rolling volatility (std dev)
- **rolling_volatility_30d**: 30-day rolling volatility (std dev)

---

## Observation Synthesis Rules

### Trend States
| State | Condition |
|-------|-----------|
| `extended_higher` | +1% return over 2+ days |
| `closed_higher` | +0.5% intraday close |
| `extended_lower` | -1% return over 2+ days |
| `closed_lower` | -0.5% intraday close |
| `range_bound` | <0.3% intraday movement |

### Volatility States
| State | Condition |
|-------|-----------|
| `expanded` | 30d vol >2% or intraday range >1.5% |
| `high` | 30d vol 1-2% |
| `moderate` | 30d vol 0.5-1% or range 0.8-1% |
| `stable` | 30d vol <1% |
| `compressed` | Intraday range <0.8% |

### Breadth States (5-day rolling)
| State | Condition |
|-------|-----------|
| `strongly_participatory` | ≥80% up days |
| `strengthened` | 60-80% up days |
| `mixed` | 40-60% up days |
| `weakened` | 20-40% up days |
| `deteriorated` | <20% up days |

### Auto-Detected Contradictions
- `price_up_breadth_down`: Higher close + weak breadth
- `momentum_with_volatility_expansion`: Extended trend + expanded volatility
- `liquidity_concentration_weak_breadth`: Concentrated liquidity + weak breadth
- `range_bound_volatility_expansion`: Range-bound + expanded volatility

---

## Analysis Outputs

### Confidence Metrics
```python
results['confidence_analysis'] = {
    'empirical_confidence': {
        'initial': 0.50,
        'final': 0.62,
        'max': 0.75,
        'mean': 0.58,
        'trajectory': 'rising'
    },
    'theoretical_coherence': {
        'initial': 0.61,
        'final': 0.54,
        'mean': 0.58,
        'trend': 'degrading'
    }
}
```

### Contradiction Dynamics
```python
results['contradiction_analysis'] = {
    'total_days_with_contradictions': 45,
    'persistence_ratio': 0.54,
    'score_trend': 'increasing',
    'mean_contradiction_score': 0.42
}
```

### Detected Risks
```python
results['risks'] = [
    {
        'type': 'overconfidence_drift',
        'severity': 'high',
        'description': 'Confidence increasing despite outcome validation'
    },
    {
        'type': 'theory_rigidity',
        'severity': 'high',
        'description': 'Very limited theory diversity; potential rigidity'
    }
]
```

---

## Common Tasks

### Run 30-Day Replay
```python
from market.replay.replay_engine import ReplayEngine

engine = ReplayEngine(max_days=30)
print(f"Replaying {len(engine)} days from {engine.get_date_range()[0]}")
```

### Verify Determinism
```python
from market.replay.market_observation_synthesizer import MarketObservationSynthesizer
import pandas as pd
import hashlib

data = pd.read_csv("data/nifty_daily_3y.csv")
synth = MarketObservationSynthesizer(data)

# Generate twice
obs1 = synth.synthesize(100)
obs2 = synth.synthesize(100)

hash1 = hashlib.sha256(obs1.observation_text.encode()).hexdigest()
hash2 = hashlib.sha256(obs2.observation_text.encode()).hexdigest()

print(f"Deterministic: {hash1 == hash2}")
```

### Get Date Range
```python
from market.replay.replay_engine import ReplayEngine

engine = ReplayEngine()
start, end = engine.get_date_range()
print(f"Replay range: {start} to {end}")
```

---

## Troubleshooting

### Dataset Not Found
```
ValueError: Dataset not found: /path/to/data/nifty_daily_3y.csv
```

**Solution:**
```bash
poetry run python -m market.data.download_nifty_history
```

### Validation Failed
```
ValueError: Dataset validation failed: ['Found X NaN values in OHLCV']
```

**Solution:**
Re-download the dataset:
```bash
rm data/nifty_daily_3y.csv
poetry run python -m market.data.download_nifty_history
```

### MultiIndex Error (yfinance)
This is handled automatically in the download script. If you encounter issues, ensure yfinance is up-to-date:
```bash
poetry update yfinance
```

---

## Performance Notes

- **Engine load time**: ~100ms for 829 days
- **Observation synthesis**: ~0.5ms per day
- **Analysis computation**: ~10ms for 100+ days
- **Memory footprint**: ~5MB for CSV + runtime state

---

## Documentation

Full documentation available in:
- [HISTORICAL_DATASET_INTEGRATION.md](HISTORICAL_DATASET_INTEGRATION.md)

Python docstrings available in:
- `market/replay/replay_engine.py`
- `market/replay/market_observation_synthesizer.py`
- `market/replay/replay_analysis.py`
- `market/data/download_nifty_history.py`
- `market/data/dataset_validator.py`

---

## Architecture

```
Historical NIFTY Data
        ↓
    CSV File (829 days)
        ↓
    ReplayEngine (deterministic navigator)
        ↓
    MarketObservationSynthesizer (rule-based)
        ↓
    MarketObservation Events
        ↓
    [Cognition Loop: Abstraction → Theory → Validation → Reflection]
        ↓
    ReplayAnalysisEngine (metrics & risks)
        ↓
    Cognition Insights
```

---

## Philosophy

The replay system is designed for **studying cognition**, not predicting markets:

- ✓ Deterministic (reproducible)
- ✓ Inspectable (all rules documented)
- ✓ Longitudinal (continuous over time)
- ✓ Offline-first (no real-time feeds)
- ✓ Integrity-preserving (no temporal leakage)

Focus: How does reflective cognition evolve? When does it degrade? How does it handle contradictions?

