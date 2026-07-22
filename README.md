# DP Core - Phase1 Substrate V3

Production-grade foundational substrate for reflective cognition experimentation, longitudinal memory study, and deterministic epistemic evolution.

## Features

- **Reflective Cognition Loop**: Observation → Abstraction → Theory → Predicate Validation → Epistemic Confidence → Contradiction Graphing → Reflection
- **Deterministic LLM I/O Ledger**: Reproducible replay without live LLM calls (`LIVE`, `REPLAY`, `AUTO` modes)
- **Decoupled Event Bus**: Strongly-typed Pydantic domain events (`ObservationCreated`, `MechanismGenerated`, `TheoryCreated`, etc.)
- **Theory Lifecycle State Machine**: Authoritative states (`DRAFT`, `CANDIDATE`, `ACTIVE`, `WEAKENING`, `RETIRED`, `ARCHIVED`)
- **Epistemic Confidence Engine**: Interpretable, deterministic confidence evolution producing structured `ConfidenceReport`s
- **Predicate Validation Framework**: Falsifiable hypothesis testing with `CONFIRMED`, `PARTIALLY_CONFIRMED`, `REJECTED`, `INSUFFICIENT_EVIDENCE` outcomes
- **Memory Retrieval Quality & Provenance**: Explainable memory ranking metrics and theory `ReasoningProvenance` lineage
- **Contradiction Graph & Resolver**: Multi-signal epistemic conflict resolution across competing hypotheses
- **Research Diagnostics & Reporting**: Comprehensive 9-domain diagnostic collection exporting to **JSON** (`data/research_report.json`) and **Markdown** (`data/research_report.md`)

## Environment Setup

```bash
poetry install
```

## Supported Replay Datasets

The reflective cognition replay engine supports three historical daily OHLCV datasets:
- **`data/reliance_daily_3y.csv`** (Default Primary Asset: Reliance Industries 3-year daily OHLCV)
- **`data/tcs_daily_3y.csv`** (Secondary Asset: Tata Consultancy Services 3-year daily OHLCV)
- **`data/nifty_daily_3y.csv`** (Benchmark Index: NIFTY 50 Index 3-year daily OHLCV)

## Running Deterministic Replay

```bash
# Run replay simulation using default primary dataset (Reliance) in REPLAY mode
poetry run python -m market.replay.run --llm-mode REPLAY

# Run replay simulation using a custom dataset path
poetry run python -m market.replay.run --csv-path data/tcs_daily_3y.csv --llm-mode REPLAY
```

## Verification & Testing

```bash
# Run full unit test suite
poetry run pytest

# Run replay determinism test
poetry run pytest tests/test_replay_determinism.py
```

## Documentation

- [Architecture Overview](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/docs/ARCHITECTURE_OVERVIEW.md)
- [Docs Index](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/docs/README.md)


