# Milestone 9: Validation Engine & Validation Record Implementation
## DP / EKAMNET RESEARCH PROGRAM

This document outlines the design, implementation, and empirical verification of the Milestone 9 Validation Engine. The engine serves as the deterministic boundary between reasoning (hypothesis generation) and learning (empirical validation).

---

## 1. Executive Summary

Milestone 9 introduces the first cognitive learning primitives into the EkamNet substrate: the **Validation Engine** and the **Validation Record**. 
*   **Operational Validation**: Every grounded proposition generated during the daily replay loop is evaluated deterministically against realized future market metrics.
*   **Database Persistence**: Validation Records are saved in PostgreSQL as immutable, write-once, append-only entries, strictly preventing retroactive updates to historical experience.
*   **Backtest Verification**: Running a 10-day stock simulation demonstrates that the validation loop operates on a defensive observer-only pattern, recording empirical interaction statistics without altering replay decisions or price attributions.

---

## 2. Architecture & File Changes

We implemented a deterministic, non-LLM validation flow integrated within the existing daily replay cycle:

```
[Observation] ──> [Theory] ──> [Semantic Proposition] ──> [Grounded Proposition]
                                                                │
                                                                ▼
                                                        [Validation Engine]
                                                                │
                                                                ▼
                                                      [Validation Record] ──> [PostgreSQL / JSON]
```

### Files Added:
*   [validation_record.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/cognition/schemas/proposition/validation_record.py): Pydantic schema class specifying the validation attributes.
*   [validation_record_model.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/memory/relational/models/validation_record_model.py): SQLAlchemy mapping class for relational persistence in the `validation_records` table.
*   [validation_record_repository.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/memory/relational/repositories/validation_record_repository.py): DB repository enforcing the immutability constraint.
*   [validation_engine.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/proposition_flow/validation_engine.py): Deterministic evaluation engine mapping conditions, offsets, and rolling averages.
*   [milestone9_validation_test.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/milestone9_validation_test.py): Unit test suite verifying logic gates, repository queries, and immutability.

### Files Modified:
*   [models/__init__.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/memory/relational/models/__init__.py) / [repositories/__init__.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/memory/relational/repositories/__init__.py): Registered new ORM models and repository classes.
*   [replay_engine.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/market/replay/replay_engine.py): Instantiated repository and engine, created output subdirectories, and integrated daily validation execution.
*   [report_renderer.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/market/replay/report_renderer.py): Extended fallback dictionary with validation properties.
*   [replay_analysis_reporting.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/market/replay/replay_analysis_reporting.py): Added print scorecard blocks for the Validation stage.

---

## 3. Validation Engine Design

The `ValidationEngine` resolves grounded compiled proposition logic against the historical dataframe.
1.  **Trigger Evaluation**: Evaluates scalar and relative comparisons (e.g. `delivery_pct_5d > 60.0` or `volume[t] > rolling_mean(volume,20)`) at step `current_step`. If not met, state defaults to `UNTRIGGERED`.
2.  **Scope Evaluation**: Validates surrounding regime constraints. If mismatched, state transitions to `UNTRIGGERED`.
3.  **Target Evaluation (Lookahead)**: If trigger/scope are met, evaluates the target condition at step `current_step + 1` (representing subsequent outcome realization).
    *   If target is realized and matches, state transitions to `SUPPORTED`.
    *   If target is realized and fails, state transitions to `CONTRADICTED`.
    *   If target step is out of bounds (current day represents the backtest frontier), state transitions to `TRIGGERED` (pending).
4.  **Type Sanitization**: Automatically sanitizes all pandas/numpy int64 and float64 data types into native Python scalars before serialization, preventing JSON TypeErrors.

---

## 4. Empirical Validation Record Schema

Every Validation Record preserves complete context and provenance:
```json
{
  "id": "117d3b84-01ed-49e8-8313-b8cc37a7a3a5",
  "created_at": "2026-07-16 05:09:16.766844+00:00",
  "proposition_id": "3abad088-1d41-419f-8cb1-11825c6fd8be",
  "canonical_proposition_id": "N/A",
  "theory_id": "b96a9155-e59e-4263-b669-44285f2215a3",
  "lineage_id": "e8d2f68a59b3752c",
  "mechanism_ids": [],
  "timestamp": "2026-07-16 05:09:16.766515+00:00",
  "replay_step": 2,
  "validation_state": "UNTRIGGERED",
  "supporting_evidence": null,
  "contradicting_evidence": null,
  "confidence_before": 0.1005,
  "confidence_after": 0.1005,
  "confidence_delta": 0.0,
  "uncertainty_before": 0.5,
  "uncertainty_after": 0.5,
  "uncertainty_delta": 0.0,
  "market_context": {
    "trend": "extended_higher"
  },
  "regime": "liquidity_constrained",
  "grounding_version": "1.7.0",
  "compiler_version": "1.7.0",
  "validation_engine_version": "1.0.0",
  "validation_trace": {
    "trigger_evaluated": "Field: delivery_pct_5d[t-1] (56.73048096475415) > 56.73048096475415",
    "trigger_val": 56.73048096475415,
    "status": "Trigger condition not met"
  },
  "notes": null
}
```

---

## 5. Verification & Test Results

### Automated Tests
Run unit tests:
```bash
poetry run pytest bootstrap/milestone9_validation_test.py
========================= 5 passed in 0.74s =========================
```
Run entire test suite:
```bash
poetry run pytest
====================== 217 passed, 48 warnings in 58.96s =======================
```

### Immutability Invariant Verification
The repository strictly prevents modifications to historical validation records. Attempting to save a record with an existing primary key ID throws a `ValueError` exception:
```python
with pytest.raises(ValueError, match="Immutability Contract Violation"):
    repo.save(record)
```

---

## 6. Replay Demonstration Statistics

A complete 10-day backtest simulation run on `RELIANCE` stock daily data:
```bash
poetry run python -m market.replay.run --days 10 --restart
```

### Scorecard (Section O printout)
```text
O. Proposition Compilation Statistics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Theories Processed (Generated):10
  • Propositions Compiled (Total):10
  • Compilation Success Rate:     100.0%
  • Success Count:                10
  • Partial Count:                0
  • Failed Count:                 0

  [Semantic Compilation stage]
  • Semantic Propositions Created: 10
  • Semantic Failures:            0
  • Ontology Mapping Failures:     0

  [Parameter Grounding stage]
  • Propositions Grounded:        10
  • Percentile Groundings Applied: 13
  • Relative References Resolved:  6
  • Grounding Failures:           0

  [Validation Engine stage]
  • Propositions Evaluated:        10
  • Validation Records Created:   10
  • Supported Records:            0
  • Contradicted Records:         0
  • Partially Supported Records:  0
  • Undecidable Records:          10
```

---

## 7. Philosophy & Readiness for Belief Update

Everything in the cognition loop prior to the Validation Engine represents internally generated reasoning (observations, theories, qualitative compiling, parameter grounding). Everything after it represents empirical knowledge shaped by reality.

The Validation Engine serves as this critical cognitive boundary. During this milestone, execution remains strictly observational to verify telemetry and persistence integrity. Now that Validation Records are stored as immutable, deterministic inputs, the substrate is fully prepared for Milestone 10: Closed-Loop Belief Update, enabling validation records to dynamically adjust theory confidence scores and guide future theory generation.

---

The Validation Engine should be treated as the boundary between reasoning and learning. Everything before it represents internally generated cognition (observations, theories, propositions). Everything after it represents knowledge that has been shaped by empirical interaction with reality. The Validation Engine must therefore remain deterministic, reproducible, and fully auditable, because it is the first point at which the system's internal hypotheses encounter external evidence.
