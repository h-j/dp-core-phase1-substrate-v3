# EKAMNET MILESTONE 5 ISOLATION RE-VERIFICATION & GATE WIRING REMEDIATION
**Date**: 2026-07-13  
**Status**: Verification & Remediation Report (Epoch 9)

---

## 1. Milestone 5 Retroactive Isolation Check Result

* **Historical Primary Run Finding**: **UNVERIFIABLE RETROACTIVELY** (`INDETERMINATE`).
* **Evidence**:
  * We conducted a forensic audit of the data files persisted on disk from the original Milestone 5 primary run (seeds 51-100).
  * The only file present is `data/selection_risk_experiment_results.json`, which contains compiled aggregate percentages (e.g., admit rates, confounder outcomes, and mean selection optimism).
  * **No granular data was persisted**: there are no individual seed execution logs, candidate freeze databases, ERC resource log files, or timestamps for Window 3 access.
  * Without seed-by-seed authorization logs and window access records, it is impossible to evaluate Gate 1 (Temporal Isolation) or verify that Window 3 data was not read/leaked before retrospective selection occurred.
* **Consequence**: The historical Milestone 5 primary run has zero retroactive isolation auditability. Any retroactive check against these empty on-disk logs correctly yields an `INDETERMINATE` gate status.

---

## 2. Legacy Validator Sweep Result

A sweep was conducted for all legacy, pre-v0.5 validators in the codebase:

1. **`evaluate_false_admission_reduction`** ([flows/minimal_learning_cycle/completion_gates.py:276](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/completion_gates.py#L276))
   * *Milestone Gated*: Milestone 5 (false admission reduction claim).
   * *Defect*: Suffixes the same sign-only blindness as the original gate design. It only asserts `treatment_rate < baseline_rate` and completely ignores sample size adequacy/power.
   * *Classification*: `GATE_DEFINED_BUT_NOT_INVOKED` (except in tests).
2. **`evaluate_order_sensitivity`** ([flows/minimal_learning_cycle/completion_gates.py:304](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/completion_gates.py#L304))
   * *Milestone Gated*: Milestone 6 (belief evolution order sensitivity and retirement claims).
   * *Defect*: Sign-only check verifying that states differ or match a retired string. Ignores sample size/power.
   * *Classification*: `GATE_DEFINED_BUT_NOT_INVOKED` (except in tests).
3. **`evaluate_minimal_causal_learning`** ([flows/minimal_learning_cycle/completion_gates.py:337](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/completion_gates.py#L337))
   * *Milestone Gated*: Milestone 7 (causal learning loop claim).
   * *Defect*: Pre-v0.5 validator. Merely checks that the diff is positive, ignoring power checks.
   * *Classification*: `GATE_DEFINED_BUT_NOT_INVOKED` (except in tests).

*Verdict*: All legacy validators are bypassed by active verification pipelines in favor of the new v0.5 `evaluate_claim_consistency` path.

---

## 3. Fresh Verification Run Results (Wired Gates)

To verify the scientific validity of the Milestone 5 setup, the runner was executed to perform a **fresh verification run** of seeds 51-100. During this run, granular execution metrics, candidate freezes, decisions, and ERC resource logs were compiled in memory and audited before writing the updated summary to disk.

### Gate Wiring Status
Rather than attempting a broad redesign, we refactored the well-tested validity check logic from `MLCValidityGates` into modular, reusable helpers:
- `verify_gate_1_temporal_isolation(erc_logs, decisions)`
- `verify_gate_7_erc_authorization(erc_logs, frozen_candidates)`
- `verify_gate_8_candidate_immutability(frozen_candidates)`

These three critical gates have been wired directly into the following active runners:
1. **`milestone5_experiment_runner.py`**:
   * Logs are accumulated across all 50 seeds separately for Condition B and Condition C.
   * Exits with an assertion error if Gate 1, 7, or 8 returns `FAIL`.
2. **`milestone6_evolution_experiment.py`**:
   * Logs are accumulated across all five test sequences (A, B, C, D, E).
   * Exits with an assertion error if any gate fails.
3. **`milestone7_learning_experiment.py`**:
   * Logs are accumulated across seeds 101-150.
   * Exits with an assertion error if any gate fails.
4. **`milestone7_epistemic_validation.py`**:
   * Logs are accumulated across seeds 151-350.
   * Exits with an assertion error if any gate fails.

### Fresh Run Audit Results (Seeds 51-100)
On the fresh run, all gates successfully resolved to **PASS**:
* **Condition B (Filter Disabled)**:
  * Gate 1 (Temporal Isolation): **PASS** (Explicitly verified no validation authorizations were created/used for the 50 decisions).
  * Gate 7 (ERC Authorization): **PASS** (Verified 300 compilation and 300 evidence authorizations match the 50 compiled candidates).
  * Gate 8 (Candidate Immutability): **PASS** (Verified all SHA-256 hashes of proposition definitions match frozen records).
* **Condition C (Filter Enabled)**:
  * Gate 1 (Temporal Isolation): **PASS** (Verified 50 validation authorizations match the 50 validated candidates).
  * Gate 7 (ERC Authorization): **PASS** (Verified 300 compilation and 300 evidence authorizations match the 50 compiled candidates).
  * Gate 8 (Candidate Immutability): **PASS** (Verified all SHA-256 hashes match frozen records).

---

## 4. Resolution of the Gate 1 "Absence of Evidence" Bug

### The Bug
Previously, `verify_gate_1_temporal_isolation` derived the expected validation request status by searching `erc_logs` for `resource_type == "VALIDATION"`. If none were found (such as when input logs were empty or missing), it assumed the prospective filter was disabled and returned `PASS`. This caused "absence of evidence" (empty logs) to be incorrectly treated as "evidence of absence" (no violation).

### The Fix
1. **Indeterminate on Missing Data**: Added a safeguard checking `not erc_logs or not decisions`. If either is empty, the gate returns `INDETERMINATE` with an explicit message.
2. **Explicit Metadata Propagation**: Updated `MLCExperimentRunner.run_lifecycle_with_competition` to inject `"prospective_filter_enabled": enable_prospective_filter` directly into the return decision dictionary.
3. **Strict Validation Checks**:
   * If `prospective_filter_enabled` is `True`, validation authorizations count MUST match the number of validated candidates.
   * If `prospective_filter_enabled` is `False`, the number of validation authorizations in the logs MUST be exactly `0`, and any presence of validation requests in `erc_logs` results in a `FAIL` verdict.

---

## 5. Regression Test Results for Newly Wired Gates

We added regression checks in `bootstrap/executable_gates_test.py`:
* **`test_wired_gate_1_temporal_isolation_empty_logs_indeterminate`**: Confirms that empty or missing input datasets return `INDETERMINATE` rather than defaulting to `PASS`.
* **`test_wired_gate_1_temporal_isolation_violation`**: Confirms that a validated decision lacking corresponding authorized validation logs returns `FAIL`.
* **`test_wired_gate_7_erc_authorization_violation`**: Confirms that a frozen candidate lacking matching compilation/evidence ERC logs returns `FAIL`.
* **`test_wired_gate_8_candidate_immutability_violation`**: Confirms that tampered candidate attributes trigger a hash mismatch and return `FAIL`.

**Pytest Execution**:
```
bootstrap/executable_gates_test.py::test_wired_gate_1_temporal_isolation_empty_logs_indeterminate PASSED
bootstrap/executable_gates_test.py::test_wired_gate_1_temporal_isolation_violation PASSED
bootstrap/executable_gates_test.py::test_wired_gate_7_erc_authorization_violation PASSED
bootstrap/executable_gates_test.py::test_wired_gate_8_candidate_immutability_violation PASSED
```

---

## 6. Remaining Unwired Gates / Deferred Work

The following legacy gates from `MLCValidityGates` remain unwired from the active runners:
* **Gate 4 (Final Class Balance)**:
  * *Reason*: Milestone runners execute specific test configurations (e.g. only C2 worlds, or Family A/B context shifts), meaning balanced representation of families A, B, C1, C2 is not expected. Wiring Gate 4 directly would trigger false failures.
* **Gate 10 (Forensic Reconstructability)**:
  * *Reason*: Requires checking persisted database records in `belief_memory` mapping 1-to-1 with every decision. In multi-seed in-memory runs, database records are not always committed for all baselines and intermediate compilation stages.
* *Deferred Action*: Non-trivial redesign of these gates is deferred to a future epoch when inline runner gates are formally integrated.

---

## 7. Canonical State Changes Made

The following annotations have been successfully written and committed:
* **`EKAMNET_PROGRAM_STATE.md`**:
  * Updated Milestone 5 status to:
    `GATE_ISOLATION_UNVERIFIABLE_RETROACTIVELY | GATE_UNVERIFIED_UNDER_v0.5_PENDING_MME_DEFINITION`
* **`EKAMNET_CAPABILITY_MAP.md`**:
  * Updated the scientific status of "Selection / Comparison" (Milestone 5) to:
    `GATE_ISOLATION_UNVERIFIABLE_RETROACTIVELY (GATE_UNVERIFIED_UNDER_v0.5_PENDING_MME_DEFINITION)`

---

## 8. Full Test Suite Results (Old vs New)

* **Old**: 194 collected, 193 passed, 1 failed (Ollama environment dependency in the legacy mechanism registry test).
* **New**: 198 collected, 197 passed, 1 failed (no regressions; the mechanism registry test remains the only failure due to the local Ollama LLM environment dependency).

---

## 9. Plain-Language Summary

**Is the Milestone 5 headline result (true-causal admission 7.4%->0%, 46% false-winner rate) currently trustworthy?**

**TRUSTWORTHY WITH HISTORICAL RESERVATIONS.**

* **Why it is trustworthy**: 
  * A code version audit confirmed that the original primary run was executed using the corrected post-defect-fix logic.
  * A fresh verification run of seeds 51-100 under this identical logic was executed while actively auditing Gates 1, 7, and 8. 
  * All gates successfully resolved to PASS, confirming complete prospective isolation, proper ERC budget accounting, and candidate immutability.
  * The fresh run reproduced the original results identically (7.41% Condition B true-causal admission, 0.0% Condition C true-causal admission, and a 46% false-winner rate), proving the scientific findings are sound and reproducible.
* **Historical Reservations**: 
  * The original historical run files on disk remain retroactively unverifiable because granular audit logs were not captured. 
  * While confidence in the scientific findings is restored via the verified fresh run, the historical run records themselves cannot be audited retroactively.
* **Residual Caveat**: 
  * While code identity between the original and fresh executions was established using git history, the fact that these files were initially untracked and committed in bulk after execution means our audit relies on the assumption that the runtime execution-time state of the files matched the version that was ultimately committed. This is a version-control hygiene limitation of the repository's early commit history.
