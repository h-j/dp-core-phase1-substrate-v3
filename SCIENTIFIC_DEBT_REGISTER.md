# EkamNet Scientific Debt Register
## DP / EKAMNET RESEARCH PROGRAM

This register tracks "what remains unknown or unverified" in the substrate. It outlines the specific scientific and methodological debts that prevent strengthening empirical claims or block future milestones, serving as a permanent guide for research governance.

---

## 1. Active Scientific Debt Ledger

| ID | Scientific Debt | Description | Blocked Claims / Milestones | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **SD-001** | **Candidate F Lineage Substitution Reconciliation** | Correcting prompt layout defects (Defect 3) altered generated abstraction hashes, rendering the pre-registered lineage ID (`5f33fb88966dd952`) unreachable. Suppressing the dynamic target (`c9c6c6d7bb71fede`) at runtime validated the routing, but post-hoc log parsing encountered step-indexing offsets. | Strong counterfactual claims under EF-001 (requires automated index verification without log offset corrections). | Implement automated runtime lineage tracking that dynamically resolves the active family without hardcoded hex targets. |
| **SD-002** | **Live Validation Loop Target Boundary** | During live simulation, the lookahead target step `t+1` is in the future relative to the daily slice, meaning live validation records default to `UNTRIGGERED` or `TRIGGERED` (pending). Terminal states (`SUPPORTED`, `CONTRADICTED`) are only observable retrospectively. | Milestone 10 (Belief Update Engine cannot retrieve resolved terminal states during the current day's execution and must wait for subsequent step progression). | Design a retrospective evaluation buffer in the Milestone 10 orchestrator that pulls and resolves pending `TRIGGERED` records from step `t-1` as day `t` executes. |
| **SD-003** | **Cross-Regime Validation Coverage** | Replay executions are bounded to a single symbol (`RELIANCE`) over short horizons (10-30 days), which doesn't capture a broad spectrum of regime classes and market conditions. | Generalization claims (L5 verification) and system-wide lifecycle validation. | Execute longer simulation horizons (60-120 days) across indices (Nifty, Energy) and varying volatility regimes. |
| **SD-004** | **LLM Variable Hallucination (Compiler Leakage)** | Llama3.2 compiles theories containing variables that do not exist in the raw dataframe columns (e.g., `volatility_regime` and `liquidity_absorption_rate`), causing KeyErrors during validation engine checks and defaulting records to `GROUNDED`. | Clean/efficient validation coverage and noise reduction in learning. | Introduce a compiler-level ontology check or restrict prompt context to force LLM compilation to adhere to the whitelisted feature set. |
| **SD-005** | **Partially Supported Logic Constraints** | The current `ValidationEngine` evaluates atomic target conditions and only resolves binary states (`SUPPORTED` vs `CONTRADICTED`), lacking logic to compute `PARTIALLY_SUPPORTED` outcomes. | Multi-factor proposition validation (evaluating compound target definitions where some conditions are met and others fail). | Extend the `ValidationEngine` to parse compound target conditions (using AND/OR operators) and compute fractional support scores. |
| **SD-006** | **Bypassed Scientific Validation Gates** | Milestone 5, 6, and 7 verification check gates remain hardcoded to `PASS` in `verify_scientific_closures.py` due to the lack of pre-registered Minimum Meaningful Effect (MME) thresholds. | Automated full-system closure checks and production integration. | Define MME thresholds (such as minimum selection rate lift and maximum false-admission rates) and implement standard checks. |

---

## 2. Governance Invariant

No scientific debt entry may be cleared without:
1. An updated matched-state replication run proving the resolution of the debt.
2. An updated entry in the **EkamNet Evidence Ledger** showing progress to a higher Evidence Level ($L+1$).
3. A formal decision entry in the **EkamNet Decision Ledger**.
