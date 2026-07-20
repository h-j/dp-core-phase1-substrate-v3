# EKAMNET EXPERIMENTAL FINDINGS LEDGER
## DP / EKAMNET RESEARCH PROGRAM

This document serves as the canonical repository-native findings ledger. All claims must correspond to a stable identifier (`EF-xxx`) and follow strict claim-licensing limits.

---

### EF-001: Provenance-Driven Novelty Routing (Candidate F)

* **Research Question**: `EQ-001` (Does accumulated epistemic history causally change later DP cognition?)
* **Experiment Reference**: `EX-001` (Controlled Counterfactual Experiment, $k=3$ matched replication pairs)
* **Evidence Level**: **L3 (Reproduced)**
* **Current Status**: `ROBUSTNESS_THRESHOLD_UNRESOLVED`

#### Licensed Claims
1. Epistemic suppression of target retirement successfully kept the target lineage `"c9c6c6d7bb71fede"` active at Step 2 in all Treatment runs.
2. The active target lineage shifted the Step 3 routing targets dynamically: Control runs revised the Step-0 lineage, while Treatment runs revised the Step-1 lineage. This indicates a **local causal effect on intermediate routing**.
3. Eventual convergence occurred: by Day 9, both Control and Treatment converged to identical active theory states, predictions, and conviction scores.
4. Downstream trading actions and performance delta was exactly `0.00` cumulative PnL difference at step 9.

#### Not Licensed (Prohibited Claims)
1. Claiming that Provenance-Driven Novelty Routing has no causal impact on trading performance in other regime classes or over longer backtest horizons.
2. Claiming that the entire cognitive loop is universally convergent.

* **Confidence**: High (100% deterministic matching across all 3 matched replication pairs).
* **Stability**: High (selection convergence triggered at Step 4 by a regime-driven `GENERATE` event).
* **Residual Confounds**: Prompt Layout Confound (differing prompt layouts between `REVISE` and `GENERATE` loops).
* **Future Work**: `EQ-003` (Determine if local divergence propagates persistently in other regime environments without Step 4 `GENERATE` resets).

---

### EF-002: Lineage and Nested Identity Remediation (Defects 1 & 2)

* **Research Question**: `EQ-005` (Do lineage IDs and nested structures propagate correctly?)
* **Experiment Reference**: `EX-002` (Phase 1 Remediation validation runs)
* **Evidence Level**: **L3 (Demonstrated)**

#### Licensed Claims
1. Lineage-family identity propagation is SQL ↔ JSON consistent.
2. `REVISE` actions correctly regenerate nested structures; `REINFORCE` actions correctly preserve them.

#### Not Licensed (Prohibited Claims)
1. Trajectory preservation claims across arbitrary prompt modifications.

---

### EF-003: Registry Contract Remediation (Defect 3)

* **Research Question**: `EQ-002` (Does registry schema correctness affect cognitive trajectory?)
* **Experiment Reference**: `EX-003` (Phase 2 Remediation validation runs)
* **Evidence Level**: **L3 (Demonstrated)**

#### Licensed Claims
1. Omission of `SECTOR_ZSCORE` registry contract corrected.
2. Remediated ontology alters LLM output abstraction strings, introducing a localized cognitive trajectory divergence (e.g. lineage ID hashes).

---

## Evidence Debt Register

This section tracks the remaining empirical validation required before findings can be promoted to higher evidence levels.

### EF-001 (Provenance-Driven Novelty Routing)
* **Current Evidence**: Local suppression intervention successfully executed dynamically in 3 matched runs on Reliance daily dataset. Local routing shift at Step 3 observed; downstream cognitive and financial convergence on Day 9.
* **Evidence Debt**:
  1. *Cross-regime replication*: Testing under trending vs range-bound regimes.
  2. *Cross-asset replication*: Testing on Nifty index or other sector assets.
  3. *Longer replay horizons*: Extending backtest from 10 days to 30 or 100 days.
  4. *Robustness characterization*: Temperature and prompt variation sensitivity analysis.

### EF-002 (Lineage and Nested Identity Remediation)
* **Current Evidence**: Verified invariants on isolated mock inputs.
* **Evidence Debt**: Longitudinal verification under full multi-agent replay runs.

### EF-003 (Registry Contract Remediation)
* **Current Evidence**: Verified on a single Reliance 10-day backtest.
* **Evidence Debt**: Verification across all standard benchmark sets to confirm zero regression.
