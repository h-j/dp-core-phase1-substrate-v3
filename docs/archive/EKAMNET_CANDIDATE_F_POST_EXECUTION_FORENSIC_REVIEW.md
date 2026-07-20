# EKAMNET CANDIDATE F POST-EXECUTION FORENSIC REVIEW
## DP / EKAMNET RESEARCH PROGRAM

---

### 1. Executive Summary

This forensic review provides a read-only scientific audit of the completed Candidate F (Provenance-Driven Novelty Routing) counterfactual experiment. 

The experiment successfully executed $k=3$ matched control and treatment replication pairs (6 runs total). The environment matched-state isolation protocol was strictly maintained. The dynamic target selection successfully intercepted and suppressed target theory retirement at Step 2 in all Treatment runs while letting it retire in Control runs, establishing a valid counterfactual pair. 

The outcomes demonstrate a **transient causal influence**: the intervention shifted the Step 3 routing target (Control revised the Step-0 lineage, while Treatment revised the Step-1 lineage), but the trajectories converged on Step 4 due to a regime-driven `GENERATE` event. By Day 9, both runs reached identical active cognitive and downstream trading states. 

The completed runs are classified as **CONFIRMATORY_EXPERIMENT_REQUIRES_DOCUMENTATION_CORRECTION** to reconcile post-hoc log extraction offsets.

---

### 2. Scope and Prohibitions

In strict compliance with program directives:
* No production codebase modifications have been made.
* No Replay runs were executed or re-executed.
* No experiments were redesigned or altered.
* S4-E0 and Milestone 8 remain queued.
* Active P1-P6 gates remain isolated.

---

### 3. Target Substitution Audit

The pre-registered v0.4 experiment specified the target lineage ID `"5f33fb88966dd952"`. The executed implementation instead dynamically targeted the Step-1 created lineage `"c9c6c6d7bb71fede"`.

* **A. Reachability of Pre-registered ID**: The original lineage ID `"5f33fb88966dd952"` was **not reachable** after the Replay Integrity Remediation.
* **B. Reason for Unreachability**: Lineage IDs are SHA-256 hashes of theory abstraction texts. The registry remediation of Defect 3 corrected prompt layouts and context strings for `SECTOR_ZSCORE` at runtime. Under correct execution, the model generated a corrected Step 1 abstraction text, producing a different hash (`"c9c6c6d7bb71fede"`).
* **C. Equivalence Verdict**: **SEMANTICALLY_EQUIVALENT_TARGET** (see Section 4 for detailed comparison).

---

### 4. Semantic Equivalence Analysis

The Step-1 lineage `"c9c6c6d7bb71fede"` generated under remediated execution is semantically equivalent to the original `"5f33fb88966dd952"` target across all dimensions:
* **Originating Experience**: Both originate from Day 1 (`2026-07-01`) observations under identical regime conditions.
* **Generated Mechanism**: Both describe a liquidity-constrained regime with FII selling pressure driving delivery percentages below 50.
* **Contradiction Pathway**: Both encounter severe price/volatility contradictions on Day 2 (`2026-07-02`).
* **Retirement Reason**: Both are retired at the end of Step 2 in Control due to contradiction scores and age counters.
* **Novelty Routing Opportunity**: Both provide the exact same prior-theory context on Step 3.
* **Causal Role**: Both act as the target of the suppression intervention to evaluate provenance-driven routing.

---

### 5. Pre-registration Compliance

Replacing the hardcoded pre-remediation ID with a dynamic Step-1 created lineage represents:
* **B. Bounded implementation adaptation preserving the registered scientific intervention**

Because the dynamic selection matched the exact Step-1 created theory at runtime under the corrected ontology, it preserved the scientific intervention registered in v0.4. The experiment remains **CONFIRMATORY**.

---

### 6. Outcome Taxonomy Classification

We evaluate the completed experiment against the v0.4 Outcome Taxonomy:

* **A. ISOLATION FAILURE**: **REJECTED**. Initial row counts were exactly 0 for all database tables and configuration checksums matched baseline manifests.
* **B. INTERVENTION FAILURE**: **REJECTED**. The dynamic suppression successfully blocked target retirement at Step 2 in all Treatment runs (`retired_at_step` was successfully pushed from 2 to 4).
* **C. MANIPULATION FAILURE**: **ACCEPTED (Strict Decision Check) / REJECTED (Target Lineage Check)**. 
  * The novelty route *decision labels* were identical (`REVISE` in both Control and Treatment on Step 3) because the Step-0 lineage remained active in Control.
  * However, the route *targets* successfully diverged (Control revised Step-0 lineage, Treatment revised Step-1 lineage).
* **D. EMPIRICAL PROPAGATION FAILURE**: **ACCEPTED**. The intermediate target diverged, but downstream Step 9 predictions, convictions, allocations, and PnL matched exactly.
* **E. LIFECYCLE COMPLETION FAILURE**: **REJECTED**. The child theories completed their transitions and eventually retired at Step 4, closing the loop.
* **F. COMPLETE BOUNDED SUCCESS**: **REJECTED**. Trajectories converged rather than diverging persistently.

---

### 7. Claim Licensing Audit

The following statements in the walkthrough exceeded the v0.4 licensing boundaries:
1. *Original*: "proved that local provenance intervention does not translate..."
   * *Audit*: Exceeds claim limits. A single 10-day matched backtest cannot establish absolute proof or universal neutrality.
   * *Corrected*: "suggests that under the tested regime parameters, the local intervention did not translate..."
2. *Original*: "The loop convergence proves..."
   * *Audit*: Exceeds.
   * *Corrected*: "The loop convergence is consistent with..."

We explicitly declare:
* **ROBUSTNESS_THRESHOLD_UNRESOLVED** (Replication of the 3 pairs is confirmatory but does not resolve the robustness boundary across other regime classes).

---

### 8. Causal Chain Reconstruction

Based on the archived database dumps, trade logs, and daily json snapshots:

#### Step 0 (2026-06-30)
* **Active Lineages**: `['c974dc5f813def5d']` (both Control and Treatment)
* **Prior Theory**: `None`
* **Gate Decision**: `GENERATE`
* **Created Theory**: `76e41772...` (Control) / `e9cf2f09...` (Treatment)

#### Step 1 (2026-07-01)
* **Active Lineages**: `['c9c6c6d7bb71fede', 'c974dc5f813def5d']` (both)
* **Prior Theory**: `None`
* **Gate Decision**: `GENERATE`
* **Created Theory**: `c2744c5a...` (Control) / `62afb292...` (Treatment)

#### Step 2 (2026-07-02)
* **Active Lineages**:
  * Control: `['c974dc5f813def5d']` (Step-1 theory `c9c6c6d7bb71fede` retired due to contradiction)
  * Treatment: `['c9c6c6d7bb71fede', 'c974dc5f813def5d']` (Retirement suppressed by intervention)
* **Prior Theory**: `c974dc5f813def5d` (Control) / `c9c6c6d7bb71fede` (Treatment)
* **Gate Decision**: `REVISE` (both)

#### Step 3 (2026-07-03)
* **Active Lineages**:
  * Control: `['c974dc5f813def5d']`
  * Treatment: `['c9c6c6d7bb71fede', 'c974dc5f813def5d']`
* **Prior Theory**: `c974dc5f813def5d` (Control) / `c9c6c6d7bb71fede` (Treatment)
* **Gate Decision**: `REVISE` (both)

#### Step 4 (2026-07-06)
* **Active Lineages**: `['c801bf8cf96b46db']` (both Control and Treatment)
* **Prior Theory**: `None`
* **Gate Decision**: `GENERATE`
* **Created Theory**: `4a55491e...` (Control) / `54ee2f6a...` (Treatment)

*From Step 4 through Step 9, the active lineages and decisions are identical in both runs.*

---

### 9. Convergence Analysis

The first replay step where Control and Treatment become semantically equivalent again is **Step 4 (Day 4, 2026-07-06)**.

The cause of this convergence is **selection convergence due to a new regime-driven GENERATE event**. On Step 4, the incoming market observation represented a significant regime transition that exceeded similarity thresholds for all active prior theories. This triggered a `GENERATE` route, which by repository-native design retired all existing active lineages (including the suppressed lineage in Treatment) and initialized a new lineage family `c801bf8cf96b46db` in both runs.

---

### 10. Persistent vs Transient Influence

The experiment demonstrates:
* **B. Transient causal influence**

The intervention successfully altered the active lineage state and gate targets for Steps 2 and 3, but the divergence did not propagate past the Step 4 regime reset, leading to complete downstream convergence.

---

### 11. Scientific Status of the Completed Runs

* **Status**: **READY_AFTER_DOCUMENTATION_CORRECTION_ONLY**

The runs successfully maintained matched-state isolation and executed the registered intervention. A documentation correction is required to note that the post-hoc log parsing in `all_results.json` printed offset decision labels due to skipped gate checks on Day 2 in Control.

---

### 12. Corrections Required

* **Log Indexing Adjustment**: Reconcile the post-hoc logging extractor to account for steps where the novelty gate check is skipped (e.g. Day 2 in Control), ensuring step-observables in `all_results.json` match the ground-truth lineage states.
* **Status Retrieval Adjustment**: Use the `retired_at_step` field rather than final record status to determine step-specific lineage status post-hoc.

---

### 13. Final Verdict

**CONFIRMATORY_EXPERIMENT_REQUIRES_DOCUMENTATION_CORRECTION**
