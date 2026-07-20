# EKAMNET PROGRAM STATE v2.0
## DP / EKAMNET RESEARCH PROGRAM

* **Last Updated**: 2026-07-20T16:05:00Z
* **Program North Star**: Build and scientifically validate an EkamNet v0.1 in which past epistemic experience causally changes future cognitive behavior.
* **Current Epoch**: 10
* **Current Iteration**: 4
* **Current Milestone**: Milestone 10 & 10-Phase Stabilization Remediation — Closed-Loop Belief Update & Substrate Stabilization Complete

---

## 1. Governance Migration & Correction Table
This table outlines the corrections applied to the program state to eliminate claim drift and separate operational implementation from scientific maturity.

| Old State Element | Identified Inconsistency / Claim Drift | Corrective Action in State v2.0 | Scientific Justification |
| :--- | :--- | :--- | :--- |
| **Milestone Mapping** | Milestone 4 was missing from the state logs. Milestone 8 was placed ahead of Milestone 9 despite requiring it as a block dependency. | Reorganized milestones in `EKAMNET_MILESTONE_MAP.md`. Documented the merge of Milestone 4 into Milestone 3. Postponed Milestone 8 to follow Milestone 9. | Establishes internal consistency and correct capability ordering. |
| **Candidate F (EF-001)** | Historically referred to as "validated novelty routing," implying a performance lift. | Downgraded claim maturity. Licensed only local trajectory shifts at Step 3; explicitly noted that final step (Day 9) converged back to control with exact 0.00 PnL delta. | Prevents strengthening the scientific claim beyond empirical data boundaries. |
| **MLC (EF-004)** | Historically described as a "complete causal learning loop," masking performance degradation. | Reclassified learning loop behavior as a double-edged sword that degrades performance under context-shift (-76.92% selection rate). | Captures context-dependent risks and prevents false-admission optimism. |
| **Decision Logging** | Sibling generation decisions (DEC_003, DEC_005) were modified and overwritten over time. | Transitioned to a dedicated, versioned `EKAMNET_DECISION_LEDGER.md` preserving all status changes (ACTIVE, SUPERSEDED, etc.). | Preserves decision history and research path auditability. |
| **Trade Feedback Loop** | Downstream paper trader sizer/PnL mutated cognition confidence states directly. | Severed trade feedback (Phase 0 remediation). Re-enforced strict observer-only contract in `AGENTS.md` and AST regression tests. | Preserves pure reflective cognition; prediction must remain indirect and non-optimized for. |

---

## 2. System Operational Maturity (Engineering Status)

*   **Milestone 1 (Replay Integrity)**: `100.0% Complete`. Repaired defects 1, 2, and 3. Verified database SQL ↔ JSON lineage propagation.
*   **Milestone 2 (Candidate F Counterfactual)**: `100.0% Complete`. Matured counterfactual logging and matching mechanisms.
*   **Milestone 3 (Epistemic Plurality)**: `100.0% Complete`. Prompt-decomposed Calls 1 & 2 sequential structured formation successfully integrated. Unit tested sibling multiplicity.
*   **Milestone 5 (Selection Engine)**: `100.0% Complete`. Deterministic pairwise competition engine integrated.
*   **Milestone 6 (Belief State Transitions)**: `100.0% Complete`. Integrated `WEAKENED` and `RETIRED` belief state schema models.
*   **Milestone 7 (Learning Loop Pruning)**: `100.0% Complete`. Active candidate pruning hooks verified.
*   **Milestone 9 (Two-Stage Proposition Compiler)**: `100.0% Complete`. Integrated `SemanticCompiler` flow, `ParameterGrounder` code calculations, and database repository tables.
*   **Milestone 9 (Validation Engine & Records)**: `100.0% Complete`. Code implementation completed, type-sanitized, and Postgres/JSON persistence verified. Immutability contract verified. Section O scorecard printing integrated.
*   **Milestone 10 (Closed-Loop Belief Update)**: `100.0% Complete`. Integrated Validation Records with active theory belief states, empirical confidence evolution, and lineage survival/retirement dynamics without trade-sourced feedback.
*   **10-Phase Stabilization Remediation**: `100.0% Complete`.
    - Phase 0: Severed trade feedback & documented observer-only contract (`a61349f`).
    - Phase 1: Pruned 8 orphaned/duplicate files across `flows/theory_flow/` and `market/replay/` (`5559ce0`).
    - Phase 2: Implemented JSON list serialization & relational FK constraints (`4bf33d5`).
    - Phase 3: Added `telemetry/logging_config.py`, gated debug traces, triaged exceptions with `_degraded_steps` tracking (`00eaa24`).
    - Phase 4: Created unit test suite (`tests/`, 23 tests, 0.44s runtime) & GitHub Actions CI (`d4c6184`).
    - Phase 5: Centralized parameters to `config/cognition_tuning.yaml` & `CHANGELOG_tuning.md` (`7baacbb`).
    - Phase 6: Added SHA-256 LLM prompt cache (`data/llm_cache/`) & `--offline` replay flag (`e6f3337`).
    - Phase 7: Verified structured output `json_format=True` migration.
    - Phase 8: Annotated stub infra with `# STUB` headers and created `docs/planned_infra.md` (`5533a01`).
    - Phase 9: Untracked `.env`, created `.env.example`, updated `.gitignore`, and archived root docs (`30d5ca7`).

---

## 3. Scientific Verification Maturity (Claims Status)

*   **Candidate F Causal Influence (EQ-001 / EF-001)**: `LOCAL_ROUTING_SHIFT_VALIDATED_BUT_LONGITUDINAL_CONVERGENT`. Matches matched treatment runs (L4). Causal trajectory shift is local to Step 3. EVENTUAL CONVERGENCE observed on Day 9 with exactly 0.00 PnL difference. Reconciled as Outcome Category D (Empirical Propagation Failure / NO_CAUSAL_INFLUENCE_DETECTED_IN_BOUNDED_EXPERIMENT).
*   **MLC Pairwise Competition (EF-004)**: `HIGH_SELECTION_RISK_AND_WEAK_SIGNAL_DEFERRAL_DEMONSTRATED`. False winner rate is 46.0% (L3). Safeguard does not reduce false-admissions on primary false-admission metrics, but rejects 13.04% of confounding winners. Deferral rate of weak causal signals is 100% (reducing true causal admission from 7.41% to 0.0%).
*   **MLC Minimal Learning Loop (Milestone 7 / EF-004)**: `CONTEXT_DEPENDENT_LOOP_INTERVENTION_DEMONSTRATED`. Pruning trigger fields improves causal selection by +53.85 percentage points in stable environments, but collapses selection by -76.92 percentage points in context-shift environments (L3 demonstrated). Negative memory trigger overgeneralization is a proven risk.
*   **Two-Stage Proposition Compilation (Phase 1.7 / EF-005)**: `COMPILER_CONVERGENCE_VERIFIED_BUT_OBSERVATIONAL_ONLY`. Eliminates threshold hallucinations and relative reference fumbles (L2/L3). Replay decisions remain unchanged.
*   **Proposition Validation Engine (Milestone 9 / EF-006)**: `VALIDATION_ENGINE_AND_IMMUTABILITY_VERIFIED`. Conceptually and code-verified. Runs deterministically, records observations, and persists immutable validation outcomes. Retrospective validation terminal states verified.
*   **Closed-Loop Belief Update & Stabilization (Milestone 10 / Remediation)**: `VERIFIED & STABILIZED`. Verified confidence evolution, contradiction zone mapping, theory survival tracking, and experience loop attribution without trade-sourced feedback loops. 243/243 total suite tests pass cleanly.

---

## 4. Governing Principles
1. DP may imagine freely.
2. EkamNet may believe only through evidence.
3. No architecture without evidence.
4. No evidence without architectural consequence when action is justified.
5. Architecture may advance only as far as evidence justifies.
6. Negative results are valid results.
7. Absence of evidence is acceptable.
8. A governing hypothesis may fail.
9. Implementation momentum must not override scientific validity.
10. Scientific caution must not become an excuse for engineering stagnation.

---

## 5. Active Frontiers
*   **Scientific Frontier**: Phase 1C — Longitudinal Reflective Cognition & Contradiction-Aware Theory Lineage Evolution over extended multi-month market datasets.
*   **Engineering Frontier**: Scaling offline cached replay validation and lineage visualization over multi-symbol market datasets.

---

## 6. Program Risk Register
1.  **`CANONICAL_STATE_DRIFT_RISK`**: The risk that scientific interpretations become stronger in canonical state files than underlying code and execution evidence supports. Mitigated by this governance v2.0 package.
2.  **`EVIDENCE_TO_ARCHITECTURE_INFERENCE_RISK`**: The risk of concluding that one architecture option is correct/superior solely because a different option is shown to be strained, without directly testing the proposed option.
3.  **`EPISTEMIC_RECALL_CYCLE`**: The risk of reviving a previously refuted candidate from dormancy due to truncation of historical validation records. Mitigated by enforcing 100% validation log preservation in dormancy.
4.  **`P1-P6_BOUNDARY_CONTRACTS_BYPASS`**: Milestone 5, 6, and 7 verification completion check gates are bypassed (hardcoded to `PASS`) in the validator script `verify_scientific_closures.py`, rendering the scientific closures unverified in automated checks.
5.  **`UNCONTAINED_FEEDBACK_LOOP_RISK`**: The risk of downstream decision/sizing components mutating cognition confidence states. Mitigated by Phase 0 explicit observer-only contract in `AGENTS.md` and AST regression tests (`tests/test_no_trade_feedback.py`).
6.  **`SILENT_COGNITION_FAILURE_RISK`**: The risk of silent exception suppression corrupting cognition state. Mitigated by Phase 3 exception triage and `_degraded_steps` tracking in `replay_engine.py`.
