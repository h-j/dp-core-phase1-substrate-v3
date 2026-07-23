# EKAMNET Evidence Ledger

This ledger records empirical evidence artifacts, replication run verifications, and closure proofs for the EKAMNET substrate.

---

## Evidence Summary Index

| Evidence ID | Verification Level | Target Milestone / Debt | Summary of Findings | Verification Artifact Path |
| :--- | :--- | :--- | :--- | :--- |
| **EVD-001** | Level L1 (Unit) | Milestone 1 | Replay execution determinism and SQL/JSON state logging. | `tests/` |
| **EVD-002** | Level L2 (Component) | Milestone 2 | Candidate F counterfactual ablation and state retirement. | `bootstrap/run_counterfactual_experiment.py` |
| **EVD-003** | Level L3 (System) | PROMPT R1 | Beta posterior scored confidence engine & severance of LLM text dampening. | `tests/test_scored_confidence.py` |
| **EVD-004** | Level L4 (Governance) | PROMPT R2 / SD-001 | Structural identity reachability across cosmetic prompt layout changes & retirement of SD-001. | `tests/test_structural_identity.py` |
| **EVD-005** | Level L4 (Governance) | PROMPT R3 / SD-006 | Pre-registered MME verification gates in `verify_scientific_closures.py` and SD-006 clearance. | `tests/test_closure_gates.py` |

---

## Detailed Evidence Records

### EVD-004: Structural Identity Verification for Cognitive Lineages & SD-001 Clearance

* **Date**: 2026-07-23
* **Target Debt**: Scientific Debt `SD-001` (Candidate F Lineage Substitution Reconciliation)
* **Verification Level**: `Level L4 (Governance & Replication Integrity)`
* **Methodology**:
  1. Executed theory lineage generation under prompt layout template A. Recorded structural ID (`"0:theory:0"`), lineage ID (`"0:theory:0"`), and content hash `hash1`.
  2. Modified prompt layout template cosmetically (added section delimiters and leading/trailing whitespace).
  3. Executed theory lineage generation under prompt layout template B. Recorded structural ID (`"0:theory:0"`), lineage ID (`"0:theory:0"`), and content hash `hash2`.
* **Empirical Findings**:
  - `rec1.id == rec2.id == "0:theory:0"` (Structural ID remains 100% reachable and identical).
  - `rec1.lineage_id == rec2.lineage_id == "0:theory:0"` (Founding Lineage ID remains 100% reachable and identical).
  - `rec1.content_hash != rec2.content_hash` (Content hash correctly captures text template variation for integrity/deduplication).
  - Counterfactual targeting for Candidate F (`TARGET_LINEAGE_ID = "0:theory:0"`) successfully resolves both runs without hardcoded hex targets.
* **Governing Decision**: `DEC-008` in `EKAMNET_DECISION_LEDGER.md`
* **Test Automation**: `poetry run pytest tests/test_structural_identity.py`

### EVD-005: Pre-Registered Verification Gates & SD-006 Clearance

* **Date**: 2026-07-23
* **Target Debt**: Scientific Debt `SD-006` (Bypassed Scientific Validation Gates)
* **Verification Level**: `Level L4 (Governance & Replication Integrity)`
* **Methodology**:
  1. Removed all hardcoded `PASS` literals from `bootstrap/verify_scientific_closures.py`.
  2. Defined MME thresholds in `config/cognition.yaml` for M5 (+10pp lift), M6 (<=20 steps to weaken), M7 (+10pp stable lift, >= -10pp context shift degradation).
  3. Executed dynamic gate evaluation against experiment artifacts.
* **Empirical Findings**:
  - Milestone 5 evaluates to `INSUFFICIENT_EVIDENCE` (sample size 13 < min_sample 50).
  - Milestone 6 evaluates to `INSUFFICIENT_EVIDENCE` (synthetic planted regime flip artifact pending).
  - Milestone 7 evaluates to `FAIL` (Family B context shift degradation -76.92pp fails pre-registered MME threshold >= -0.10).
  - Milestone statuses honestly updated in `EKAMNET_PROGRAM_STATE_v2.md`.
* **Governing Decision**: `DEC-009` in `EKAMNET_DECISION_LEDGER.md`
* **Test Automation**: `poetry run pytest tests/test_closure_gates.py`

