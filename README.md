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

## Running Deterministic Replay

```bash
# Run replay simulation using LLM Ledger REPLAY mode (zero live LLM calls)
poetry run python -m market.replay.run --llm-mode REPLAY

# Run replay simulation in LIVE recording mode
poetry run python -m market.replay.run --llm-mode LIVE
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


