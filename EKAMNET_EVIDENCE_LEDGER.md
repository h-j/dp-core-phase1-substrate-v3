# EKAMNET EVIDENCE LEDGER
## DP / EKAMNET RESEARCH PROGRAM

This document consolidates the canonical Evidence Levels and Experimental Findings of the EkamNet program. It separates engineering implementation status from scientific claim maturity and lists remaining evidence debts.

---

## 1. Definition of Evidence Levels (L0–L5)

*   **L0: Described / Designed**: Conceptualized in design specifications or prompts; no codebase implementation.
*   **L1: Implemented**: Runnable code exists in the repository, but has zero unit testing or simulation validation.
*   **L2: Verified (Unit Tested)**: isolated unit tests pass, verifying data models, invariants, and state transitions.
*   **L3: Demonstrated (Single Run)**: Run successfully in a single longitudinal simulation or replay backtest; snapshots generated.
*   **L4: Validated (Controlled Backtest)**: Causal effect is confirmed through controlled, matched-state counterfactual simulations ($k \ge 3$ matched replication pairs) over a backtest period.
*   **L5: Generalized**: Counterfactual validation completed across multiple distinct regime classes, datasets, and seeds with zero falsifications.

---

## 2. Experimental Findings Ledger

### EF-001: Provenance-Driven Novelty Routing (Candidate F)
*   **Engineering Status**: `IMPLEMENTATION_COMPLETE` (Code in `replay_engine.py` is fully operational).
*   **Scientific Claim Maturity**: `TRAJECTORY_DIVERGENCE_LOCAL_BUT_LONGITUDINAL_CONVERGENCE_OBSERVED`
*   **Evidence Maturity**: **L4 (Validated)** (on Reliance daily dataset).
*   **Licensed Claims**:
    1.  Epistemic suppression successfully kept the target lineage active at Step 2 in all Treatment runs.
    2.  Active target lineage dynamically shifted Step 3 routing targets (Control revised Step-0; Treatment revised Step-1), proving local causal impact.
    3.  Eventual convergence occurs: by Day 9, treatment and control converge to identical theory states, predictions, and conviction scores.
    4.  Downstream trading actions show exactly `0.00` cumulative PnL difference at Step 9.
*   **Prohibited Claims**:
    1.  Claiming that Candidate F increases overall trading performance/returns.
    2.  Claiming that the cognitive loop is universally divergent.
*   **Remaining Evidence Debt**:
    *   Replication on other sector assets or indices (e.g. Nifty).
    *   Testing on longer backtest horizons (30 to 100 days) to see if convergence holds.
*   **Open Review Items**:
    *   Investigate the Prompt Layout Confound (differing prompts between `REVISE` and `GENERATE` loops).

---

### EF-002: Lineage and Nested Identity Remediation
*   **Engineering Status**: `IMPLEMENTATION_COMPLETE` (Invariants enforced in relational model layers).
*   **Scientific Claim Maturity**: `RELATIONAL_PROPAGATION_CORRECTNESS_VERIFIED`
*   **Evidence Maturity**: **L3 (Demonstrated)**
*   **Licensed Claims**:
    1.  Lineage-family identity propagation is SQL ↔ JSON consistent.
    2.  `REVISE` actions correctly regenerate nested structures; `REINFORCE` actions preserve them.
*   **Prohibited Claims**:
    1.  Claiming trajectory stability across arbitrary prompt modifications.
*   **Remaining Evidence Debt**:
    *   Longitudinal validation under complex multi-agent execution runs.

---

### EF-003: Registry Contract Remediation
*   **Engineering Status**: `IMPLEMENTATION_COMPLETE` (Ontology configuration updated).
*   **Scientific Claim Maturity**: `ONTOLOGY_COMPLIANCE_RESTORED`
*   **Evidence Maturity**: **L3 (Demonstrated)**
*   **Licensed Claims**:
    1.  Omission of `SECTOR_ZSCORE` contract corrected.
    2.  Remediated ontology alters LLM output abstraction strings, shifting cognitive trajectories.
*   **Prohibited Claims**:
    1.  Claiming that correcting ontology tags universally improves decision accuracy.
*   **Remaining Evidence Debt**:
    *   Regression testing across all historical snapshot folders.

---

### EF-004: MLC Competition & Selection (Milestone 5)
*   **Engineering Status**: `IMPLEMENTATION_COMPLETE` (`MLCCompetitionEngine` fully unit-tested and integrated).
*   **Scientific Claim Maturity**: `SELECTION_RISK_AND_SAFEGUARD_INEFFICIENT_SIGNAL_DEFERRAL_CHARACTERIZED`
*   **Evidence Maturity**: **L3 (Demonstrated)** (on seeds 51-100).
*   **Licensed Claims**:
    1.  Pairwise competition engine runs successfully and debits ERC budgets for all compiled candidates.
    2.  Selection risk is high: false winner rate is 46.0%, mean selection optimism is +0.0531.
    3.  Safeguards fail to reduce primary false-admissions (0.0 percentage point reduction) but reject 13.04% of confounding winners while deferring weak causal signals (reducing true causal admission from 7.41% to 0.0%).
*   **Prohibited Claims**:
    1.  Claiming the competition engine solves selection risk or guarantees true causal candidate survival.
*   **Remaining Evidence Debt**:
    *   Testing with larger models (8B, 70B) to verify if compliance and selection optimism risks decrease.

---

### EF-005: Two-Stage Proposition Compilation (Phase 1.7)
*   **Engineering Status**: `IMPLEMENTATION_COMPLETE` (`SemanticCompiler` & `ParameterGrounder` implemented and verified).
*   **Scientific Claim Maturity**: `COMPILER_CONVERGENCE_STABILIZED_BUT_OBSERVATIONAL_ONLY`
*   **Evidence Maturity**: **L2 (Verified)** (100% pytest green) / **L3 (Demonstrated)** (on 10-day backtest).
*   **Licensed Claims**:
    1.  Separating semantic compiler from parameter grounder resolves relative comparisons and eliminates threshold hallucinations.
    2.  Observation loop executes successfully and writes snapshots without altering legacy replay metrics.
*   **Prohibited Claims**:
    1.  Claiming that compiled propositions change replay decision paths (execution remains observational only).
*   **Remaining Evidence Debt**:
    *   Characterizing compiler drift under sudden regime shifts.
    *   Testing grounding thresholds over longer backtest horizons (60+ days).

---

### EF-006: Proposition Validation Engine (Milestone 9)
*   **Engineering Status**: `IMPLEMENTATION_COMPLETE` (Deterministic Validation Engine, Pydantic schemas, relational model mapping, and repository storage fully implemented and verified).
*   **Scientific Claim Maturity**: `VALIDATION_ENGINE_AND_IMMUTABILITY_VERIFIED`
*   **Evidence Maturity**: **L3 (Demonstrated)** (observational execution in daily replay) / **L4 (Validated)** (retrospective outcome resolution).
*   **Licensed Claims**:
    1.  The `ValidationRecord` is conceptually and code-verified as the atomic unit of learning (encounter point with external reality).
    2.  The `ValidationEngine` deterministically resolves trigger, scope, and lookahead target conditions against history.
    3.  Database persistence is write-once, append-only; attempts to overwrite records trigger an immutability ValueError.
    4.  Numpy and pandas data types are recursively sanitized to Python native scalar types to prevent database JSON serialization KeyErrors.
    5.  Retrospective validation successfully resolves trigger-met propositions to `SUPPORTED` and `CONTRADICTED` outcomes.
*   **Prohibited Claims**:
    1.  Claiming validation records change live replay decisions (live loop remains observational-only).
    2.  Claiming `PARTIALLY_SUPPORTED` is assigned by the current atomic logic.
*   **Remaining Evidence Debt**:
    - Implementation of closed-loop updates applying validation feedback to active theories (Milestone 10).
    - Resolution of LLM variable hallucinations (e.g. `volatility_regime` and `liquidity_absorption_rate`) which do not exist in the raw dataset, leading to runtime KeyErrors (evaluated as `GROUNDED`).
