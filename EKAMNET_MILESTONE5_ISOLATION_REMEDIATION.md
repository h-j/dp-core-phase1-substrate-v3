# EKAMNET MILESTONE 5 ISOLATION RE-VERIFICATION & GATE WIRING REMEDIATION
**Date**: 2026-07-13  
**Status**: Verification & Remediation Report (Epoch 9)

---

## 1. Milestone 5 Retroactive Isolation Check Result

* **Finding**: **UNVERIFIABLE RETROACTIVELY**.
* **Evidence**:
  * We conducted a forensic audit of all data files persisted on disk from the Milestone 5 primary run (seeds 51-100).
  * The only file present is `data/selection_risk_experiment_results.json`, which contains compiled aggregate percentages (e.g., admit rates, confounder outcomes, and mean selection optimism).
  * **No granular data was persisted**: there are no individual seed execution logs, candidate freeze databases, ERC resource log files, or timestamps for Window 3 access.
  * Without seed-by-seed authorization logs and window access records, it is impossible to evaluate Gate 1 (Temporal Isolation) or verify that Window 3 data was not read/leaked before retrospective selection occurred.
* **Consequence**: The Milestone 5 primary run has zero retroactive isolation auditability. Re-establishing full scientific confidence in its results requires running a fresh experiment with runtime logging and inline gate checkers enabled.

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

## 3. Gate Wiring Status per Runner

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

---

## 4. Regression Test Results for Newly Wired Gates

We added regression checks in `bootstrap/executable_gates_test.py`:
* **`test_wired_gate_1_temporal_isolation_violation`**: Constructs a validated decision but fails to write the validation authorization log to ERC. Verifies that the checker correctly returns `FAIL`.
* **`test_wired_gate_7_erc_authorization_violation`**: Constructs a frozen candidate lacking matching compilation/evidence ERC logs. Verifies that the checker returns `FAIL`.
* **`test_wired_gate_8_candidate_immutability_violation`**: Modifies the fields of a frozen candidate after hash generation. Verifies that the checker catches the content hash discrepancy and returns `FAIL`.

**Pytest Execution**:
```
bootstrap/executable_gates_test.py::test_wired_gate_1_temporal_isolation_violation PASSED
bootstrap/executable_gates_test.py::test_wired_gate_7_erc_authorization_violation PASSED
bootstrap/executable_gates_test.py::test_wired_gate_8_candidate_immutability_violation PASSED
```

---

## 5. Remaining Unwired Gates / Deferred Work

The following legacy gates from `MLCValidityGates` remain unwired from the active runners:
* **Gate 4 (Final Class Balance)**:
  * *Reason*: Milestone runners execute specific test configurations (e.g. only C2 worlds, or Family A/B context shifts), meaning balanced representation of families A, B, C1, C2 is not expected. Wiring Gate 4 directly would trigger false failures.
* **Gate 10 (Forensic Reconstructability)**:
  * *Reason*: Requires checking persisted database records in `belief_memory` mapping 1-to-1 with every decision. In multi-seed in-memory runs, database records are not always committed for all baselines and intermediate compilation stages.
* *Deferred Action*: Non-trivial redesign of these gates is deferred to a future epoch when inline runner gates are formally integrated.

---

## 6. Canonical State Changes Made

The following annotations have been successfully written and committed:
* **`EKAMNET_PROGRAM_STATE.md`**:
  * Updated Milestone 5 status to:
    `GATE_ISOLATION_UNVERIFIABLE_RETROACTIVELY | GATE_UNVERIFIED_UNDER_v0.5_PENDING_MME_DEFINITION`
* **`EKAMNET_CAPABILITY_MAP.md`**:
  * Updated the scientific status of "Selection / Comparison" (Milestone 5) to:
    `GATE_ISOLATION_UNVERIFIABLE_RETROACTIVELY (GATE_UNVERIFIED_UNDER_v0.5_PENDING_MME_DEFINITION)`

---

## 7. Full Test Suite Results (Old vs New)

* **Old**: 194 collected, 193 passed, 1 failed (Ollama environment dependency in the legacy mechanism registry test).
* **New**: 197 collected, 196 passed, 1 failed (no regressions; the mechanism registry test remains the only failure due to the local Ollama LLM environment dependency).

---

## 8. Plain-Language Summary

**Is the Milestone 5 headline result (true-causal admission 7.4%->0%, 54% false-winner rate) currently trustworthy?**

**PARTIALLY TRUSTWORTHY.**

* **Why it is trustworthy**: The mathematical and statistical outcomes (mean selection optimism, false-winner rate, admission rates) are correctly computed from the raw outputs of the experiment execution. The code structure for pairwise selection logic (`MLCCompetitionEngine`) is validated by unit tests and passes successfully.
* **Why it is untrustworthy**: The primary claim of **temporal isolation** (no leakage of Window 3 outcomes into retrospective candidate selection) **has not been verified by code and cannot be verified retroactively** due to a complete lack of persisted execution logs. While the mathematical logic is correct, the empirical foundation of the run remains exposed to unlogged side-channel/leakage risks.
