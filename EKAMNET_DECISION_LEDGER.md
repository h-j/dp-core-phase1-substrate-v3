# EKAMNET Decision Ledger

This ledger records architectural decisions, governance changes, and state transitions for the EKAMNET substrate.

---

## Decision Index

| Decision ID | Date | Subject | Status | Impact / Scope |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-001** | 2026-06-15 | PostgreSQL Lineage & Persistence Integrity | ACTIVE | Schema & Relational Memory Layer |
| **DEC-002** | 2026-06-20 | Neo4j Graph Lineage Structure | ACTIVE | Graph Memory Layer |
| **DEC-003** | 2026-06-25 | Counterfactual Experiment Protocol (Candidate F) | SUPERSEDED | Counterfactual Experiment Harness |
| **DEC-004** | 2026-07-01 | Observer-Only Observer Pattern Severance | ACTIVE | Cognition & Market Interface Severance |
| **DEC-005** | 2026-07-10 | Epistemic Plurality & Sibling Generation | ACTIVE | Cognition Orchestration |
| **DEC-006** | 2026-07-18 | Program State v2.0 & Governance Table Alignment | ACTIVE | Governance & Milestone Mapping |
| **DEC-007** | 2026-07-23 | Replacement of Keyword Confidence Engine with Scored Confidence Engine (PROMPT R1) | ACTIVE | Cognition Confidence Substrate |
| **DEC-008** | 2026-07-23 | Transition to Structural Identity for Cognitive Objects & Retirement of SD-001 (PROMPT R2) | ACTIVE | Identity Substrate & Lineage Engine |
| **DEC-009** | 2026-07-23 | Pre-Registered Verification Gates & Retirement of SD-006 (PROMPT R3) | ACTIVE | Research Governance & Closure Verification |

---

## Decision Record Details

### DEC-008: Transition to Structural Identity for Cognitive Objects (PROMPT R2)

* **Date**: 2026-07-23
* **Status**: `ACTIVE`
* **Context**: Scientific Debt SD-001 recorded that prompt-layout modifications (e.g. correcting section headers or whitespace) changed text SHA-256 hashes, rendering pre-registered lineage IDs unreachable and forcing hardcoded hex targets.
* **Decision**: Sever identity of evolving cognitive objects (theories, abstractions, propositions, lineages) from LLM text content hashes. Introduce deterministic **Structural Identity** formatted as `"{day}:{stage}:{family_ordinal}"` (e.g. `"0:theory:0"`). Content hashes are retained on objects as `content_hash` strictly for integrity/deduplication.
* **Lineage Identity Policy**: Founding theory structural ID (`"0:theory:0"`) serves as `lineage_id`; all descendant mutations inherit this founding `lineage_id`.
* **Ablation & Targeting Policy**: All counterfactual and ablation harnesses target lineages via `structural_id` or `lineage_id`. Hardcoded hex hash strings (e.g. `5f33fb88966dd952`, `c9c6c6d7bb71fede`) are retired.
* **Consequences**:
  - Eliminates identity drift caused by prompt layout changes.
  - Clears Scientific Debt SD-001.

### DEC-009: Pre-Registered Verification Gates & Retirement of SD-006 (PROMPT R3)

* **Date**: 2026-07-23
* **Status**: `ACTIVE`
* **Context**: Scientific Debt SD-006 recorded that Milestone 5, 6, and 7 completion gates in `verify_scientific_closures.py` were hardcoded to `PASS` because no Minimum Meaningful Effect (MME) thresholds were pre-registered.
* **Decision**: Eliminate all hardcoded `PASS` literals from `verify_scientific_closures.py`. Define pre-registered MME thresholds in `config/cognition.yaml` (M5 lift >= +0.10, M6 steps <= 20, M7 lift >= +0.10 & degradation >= -0.10). Gates evaluate experiment artifacts dynamically and return `PASS | FAIL | INSUFFICIENT EVIDENCE`. Missing artifacts or undersampled runs default to `INSUFFICIENT EVIDENCE` (never `PASS`).
* **Consequences**:
  - Reverts unverified milestones (M5, M6 to `INSUFFICIENT EVIDENCE`, M7 to `FAILED`) in `EKAMNET_PROGRAM_STATE_v2.md` until MME thresholds are empirically met.
  - Clears Scientific Debt SD-006.

