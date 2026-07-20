# EKAMNET REPLAY REMEDIATION PLAN ADDENDUM v0.2
## DP / EKAMNET RESEARCH PROGRAM

This addendum revises the EkamNet Replay Integrity Remediation Implementation Plan based on the adversarial review, establishing bounded corrections before any implementation begins.

---

### 1. Revised Implementation Sequence with Rationale

To prevent confounding downstream testing, the remediation sequence is reordered to isolate the non-neutral defect (Defect 3) from the two cognitive-neutral defects (Defects 1 and 2).

* **Revised Sequence**:
  1. **Step 1: Baseline Preservation Test Run**
     - Target Codebase: Baseline (unmodified).
     - Action: Run the full 10-day backtest replay window under seed 42 and record the cognitive decisions (`REVISE`/`GENERATE`/`REINFORCE`) for all 10 steps.
  2. **Step 2: Lineage ID Propagation Hotfix (Defect 1) + Preservation Test**
     - Target Codebase: Baseline + Defect 1 fix.
     - Files: `market/replay/replay_engine.py`.
     - Test: Verify correct parent-child lineage edges in PostgreSQL via `test_lineage_propagation`. Confirm 10-day replay decisions are identical to baseline.
  3. **Step 3: Nested ID Regeneration Hotfix (Defect 2) + Preservation Test**
     - Target Codebase: Baseline + Defects 1 & 2 fixes.
     - Files: `market/replay/replay_engine.py`.
     - Test: Verify unique `summary_structured.id` and updated `created_at` on `REVISE` mutations via `test_nested_id_regeneration`. Confirm 10-day replay decisions match baseline.
  4. **Step 4: Cognitive-Behavior Preservation Confirmation (Neutral Gate)**
     - Action: Byte-for-byte verification that the 10-step cognitive decisions of the Defects 1+2 code in isolation are identical to the baseline run.
  5. **Step 5: Ontology Registry Hotfix (Defect 3)**
     - Target Codebase: Baseline + Defects 1, 2, & 3 fixes.
     - Files: `cognition/schemas/knowledge/ontology.py`.
     - Test: Add `"SECTOR_ZSCORE"` to `CORE_CONCEPTS` and run `test_ontology_compliance`.
  6. **Step 6: Pre/Post Distribution Comparison for Defect 3**
     - Action: Run the new ontology distribution comparison test to characterize and document the non-neutral cognitive effect.

* **Rationale**: Defect 3 (`SECTOR_ZSCORE` validation omission) is classified as `POTENTIAL_COGNITIVE_EFFECT` because it triggers retries and LLM regenerations. If implemented first, it would be impossible to verify whether subsequent changes (Defects 1 & 2) are truly cognitive-neutral, as the baseline decisions would already have drifted due to the ontology change. Fixing Defects 1 & 2 first preserves the baseline cognitive trajectory, allowing clean validation of their neutrality in Step 4 before introducing the non-neutral taxonomy changes in Step 5.

---

### 2. Revised Cognitive-Behavior Preservation Test Specification

The mock 5-step loop is extended to the full 10-day diagnostic replay window under identical LLM seed/parameters to ensure subtle couplings are caught.

* **Test Specification**: `test_pre_post_cognitive_behavior_preservation`
  - **Setup**: Baseline and hotfixed code (Defects 1+2 only) run under identical LLM seed (`42`) and configuration (`llama3.2`).
  - **Input**: The full 10-day trading range (`2026-06-29` to `2026-07-10`) used in the diagnostic replay.
  - **Verification Method**: Extract and compare the exact cognitive decision sequence (`REVISE`, `GENERATE`, `REINFORCE`) at each of the 10 steps from the decision trace.
  - **Pass Criteria**: Byte-for-byte identity of the 10-step decision sequences. Any divergence in routing flags at any step constitutes a test failure.

---

### 3. New Pre/Post Distribution Comparison Test Specification (Defect 3)

Since the ontology fix allows previously rejected components to survive on first attempt, we must characterize the resulting cognitive delta.

* **Test Specification**: `test_ontology_cognitive_effect_distribution`
  - **Setup**: Run theory generation under identical prompts and seeds before and after the ontology registry fix.
  - **Input**: Standard theory generation prompts containing the concept `SECTOR_ZSCORE`.
  - **Measurements & Reporting**:
    1. **Survival Rate**: Count of theories featuring `SECTOR_ZSCORE` that triggered validation failures/retries pre-fix vs. those that survive on the first attempt post-fix.
    2. **Content Divergence Analysis**: Compare the semantic content, parameters, and branch logic of the surviving post-fix (first-attempt) theories against the pre-fix (retried/regenerated) versions for the same prompt.
  - **Acceptance Criteria**: Verify that post-fix, zero validation retries or failures occur due to the `SECTOR_ZSCORE` tag, and document the differences in the generated theories.

---

### 4. Findings on summary_structured.created_at Usage in Staleness/Retirement Logic

A complete codebase audit was conducted to verify whether resetting the inner `summary_structured.created_at` timestamp on `REVISE` mutations (Defect 2 fix) would affect theory retirement timing or routing.

* **Audit Findings**:
  - The theory retirement logic resides in [TheoryLineageEngine.retire_stale_theories](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/memory/lineage/theory_lineage.py#L486-L530).
  - In `retire_stale_theories()`, staleness is calculated as:
    ```python
    stale_age = step - rec.last_seen_step
    ```
    where `step` is the current integer step index (day index), and `rec.last_seen_step` is the integer step index at which the theory record was last active.
  - The average retirement age calculation in `TheoryLineageEngine.retire_theory` also relies solely on step integers:
    ```python
    rec.retirement_ages.append(step - rec.created_at_step)
    ```
  - The audit confirmed that **no function in the codebase reads `summary_structured.created_at` or the outer `theory.created_at` datetime field to compute staleness, age, or retirement**. All retirement decisions are governed by step-based counters (`last_seen_step` and `created_at_step`) tracked inside `theory_lineage.json` as integers.
  - **Conclusion**: The `NO_CANDIDATE_F_EFFECT` claim for Defect 2 is fully evidenced. Resetting the datetime field `summary_structured.created_at` on `REVISE` will not change theory retirement behavior, keeping it completely isolated from Candidate F's routing mechanisms.

---

### 5. P1-P6 Gate Scope Classification

Row 38 of the Master Capability Traceability Table notes that the P1-P6 boundary contracts are hardcoded to `PASS` in [verify_scientific_closures.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py#L16).

* **Scope Classification**: **(b) Explicitly out of scope and deferred.**
* **Justification**:
  - The active project phase is Phase 1B (Persistent Reflective Cognition), focusing on PostgreSQL persistence integrity and historical cognition continuity.
  - The MLC (Minimal Learning Cycle) harness is an isolated experimental sandbox. Fixing the bypassed gate script `verify_scientific_closures.py` for Milestones 5/6/7 does not impact the database persistence defects of the active native replay engine.
* **Recording and Tracking**:
  - This has been logged in the program state as a known, tracked gap. Bypassing validation check gates will be addressed as part of the future S4-E0 integration design, rather than being hotfixed under the current replay integrity remediation effort.

---

### 6. Updated Candidate F Preservation Analysis Table

| Defect / Area | Contradiction Score Impact | TheoryRecord Status Impact | Retirement Behavior Impact | Active Theories Matching | Decision Routing (`REVISE` vs `GENERATE`) | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Defect 1: Relational Lineage** | `NO_CANDIDATE_F_EFFECT` | `NO_CANDIDATE_F_EFFECT` | `NO_CANDIDATE_F_EFFECT` | `TRACEABILITY_ONLY_EFFECT` | `NO_CANDIDATE_F_EFFECT` | Telemetry-only |
| **Defect 2: Nested ID Collision** | `NO_CANDIDATE_F_EFFECT` | `NO_CANDIDATE_F_EFFECT` | `NO_CANDIDATE_F_EFFECT` | `TRACEABILITY_ONLY_EFFECT` | `NO_CANDIDATE_F_EFFECT` | Telemetry-only |
| **Defect 3: Ontology Mismatch** | `POTENTIAL_COGNITIVE_EFFECT` | `POTENTIAL_COGNITIVE_EFFECT` | `POTENTIAL_COGNITIVE_EFFECT` | `POTENTIAL_COGNITIVE_EFFECT` | `POTENTIAL_COGNITIVE_EFFECT` | Cognitive Delta |

---

### 7. Execution and State Integrity Confirmation

We confirm that during this revision pass:
1. No source code files in `bootstrap/`, `cognition/`, `flows/`, `memory/`, `interfaces/`, or `market/` were modified.
2. No database migrations, schemas, or updates were executed.
3. No replay simulations (10-day or otherwise) were run.
4. No canonical or historical data state was altered.

---

This addendum has been completed under **PLAN REVISION ONLY** mode. Implementation is deferred until this addendum has been reviewed and authorized.
