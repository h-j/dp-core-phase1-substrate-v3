# DP / EkamNet Agent Guide

## Project Purpose

Drishti Pragya (DP) / EkamNet is a reflective cognition substrate validated through deterministic market replay.

This is not a trading bot, signal generator, or prediction optimizer.

Market data is the first validation domain for contradiction-aware evolving cognition.

## Architecture Map

```text
market/replay/       deterministic replay engine and market observation synthesis
dp/theory/           theory lineage, mutation, retirement, revival
dp/memory/           reflective and historical memory surfaces
dp/observability/    metrics, contradiction registry, replay summaries
dp/reflection/       reflective cognition semantics when present
docs/                persistent repo guidance and release notes
```

## Core Principles

- Deterministic replay only.
- No future leakage.
- Preserve contradiction.
- Prefer epistemic compression over prose expansion.
- Prediction is indirect only.
- Keep fixes minimal and deterministic.
- Restore disconnected behavior before extending it.
- Preserve theory mutation, retirement, revival, and lineage.
- Ground reflection in actual theories and contradictions.

## Codex Workflow

Before coding:

- Audit the existing path.
- Identify root cause.
- Restore if behavior is disconnected.
- Extend only after restoration is clear.

After coding, return:

- Files changed.
- Behavior changed.
- Replay summary or focused verification.
- Risks and assumptions.

## Replay Commands

Run from repo root:

```bash
poetry run python market/replay/replay_engine.py --days 5 --restart
poetry run python market/replay/replay_engine.py --days 15 --restart
poetry run python market/replay/replay_engine.py --days 30 --restart
```

## Guardrails

Do not:

- Optimize prediction directly.
- Add trade logic.
- Add buy/sell/return optimization.
- Rewrite modules unnecessarily.
- Introduce random behavior.
- Inflate finance prose.

Prefer:

- Observability.
- Lineage preservation.
- Deterministic replay validation.
- Contradiction-aware lifecycle repair.
- Small changes with explicit cognition semantics.

## Observer-Only Modules

`DecisionPolicyEngine`, `CapitalSimulator`, `ConvictionSizer`, and `PaperTrader` are downstream observers only.
They read prediction probes, transition pressure, and market outcomes to simulate paper trading performance.
Nothing produced by these modules (decisions, trade logs, PnL, conviction scores) may ever feed back into cognition-state-mutating methods (`ConfidenceEvolutionEngine.evolve`, `TheoryLineageEngine.evolve_theory`, `ContradictionRegistry`, or `RegimeMemoryStore`).

## Forensic Audit Governance Rule

Every forensic audit must end in exactly one of the following outcomes:
- **Evidence Ledger Entry**: For verified scientific findings and empirical claims.
- **Decision Ledger Entry**: For versioned architectural and design decisions.
- **Rejected Finding**: For refuted candidate claims.

No forensic audit may remain unattached or unmapped.

## Edge Test Pre-Registration Freeze

`experiments/edge_test/PREREGISTRATION.md` is frozen after commit. Agents must never modify thresholds, constants, or rule logic in `experiments/edge_test/` in response to observed results. Any optimization of the trading rule against test outcomes is prohibited.


