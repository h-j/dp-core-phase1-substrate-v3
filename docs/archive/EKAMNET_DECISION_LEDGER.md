# EKAMNET DECISION LEDGER
## DP / EKAMNET RESEARCH PROGRAM

This document serves as the versioned and historically traceable record of all architectural and scientific decisions of the program.

---

## 1. Decision Status Overview

*   **ACTIVE**: Decision governs the current codebase and research lifecycle.
*   **SUPERSEDED**: Decision was historically valid but has been replaced by a newer decision.
*   **REJECTED**: Proposed path was evaluated and explicitly turned down due to scientific or engineering constraints.
*   **DEPRECATED**: Decision is no longer active and has no active successor.

---

## 2. Decision Log

### DEC_001: ERC Budget Override Reconciliation
*   **Date**: 2026-07-11
*   **Type**: SCIENTIFIC
*   **Status**: `ACTIVE`
*   **Decision**: Reconciled ERC budget depletion and pilot results: budgets were overridden to 10,000 units in the pilot orchestrator, so the 100-world pilot completed successfully without truncation.
*   **Rationale**: Trace verified that cumulative consumption was 5,400 units, which is below the 10,000 override but above the default 1000.
*   **Falsification Trigger**: Evidence of actual execution failure or halts under the override.
*   **Authority**: AG

---

### DEC_002: Phase 0 Diagnostic Protocol Freeze
*   **Date**: 2026-07-11
*   **Type**: METHODOLOGICAL
*   **Status**: `ACTIVE`
*   **Decision**: Freezing the Phase 0 Formation Boundary Diagnostic v0.1 protocol before execution.
*   **Rationale**: We must characterize the source-to-target semantic representability gap before optimizing handoff adapters or structured generation prompts.
*   **Falsification Trigger**: Inability to extract representative theory snapshots.
*   **Authority**: AG

---

### DEC_003: Strategy B Spike Authorization
*   **Date**: 2026-07-11
*   **Type**: HUMAN
*   **Status**: `SUPERSEDED` by **DEC_007**
*   **Decision**: AUTHORIZE_REVERSIBLE_STRATEGY_B_ENGINEERING_SPIKE with PERMANENT_STRATEGY_B_ADOPTION_DEFERRED.
*   **Rationale**: Bounded experimental spike was authorized to test for structure-induced formation distortion.

---

### DEC_004: Strategy B Conditional Integration Authorization
*   **Date**: 2026-07-11
*   **Type**: HUMAN
*   **Status**: `SUPERSEDED` by **DEC_007**
*   **Decision**: AUTHORIZE_AUTONOMOUS_STRATEGY_B_EVIDENCE_EXPANSION_WITH_CONDITIONAL_INTEGRATION.
*   **Rationale**: Empowers the loop to integrate Strategy B and enter Milestone 3 autonomously if it passes the pre-registered multi-case comparison compliance gate.

---

### DEC_005: Strategy B 3B Compliance Rejection
*   **Date**: 2026-07-11
*   **Type**: SCIENTIFIC
*   **Status**: `SUPERSEDED` by **DEC_007**
*   **Decision**: REJECT_STRATEGY_B_INTEGRATION_DUE_TO_LLM_COMPLIANCE_FAILURE. Permanent integration was rejected because the 6-case multi-context comparison run demonstrated only 33.3% schema compliance on the llama3.2 3B model.
*   **Rationale**: Bounded comparison showed that the 3B model fails to consistently generate the ten structured Proposition fields in complex contexts.

---

### DEC_006: Strategy B 8B Configuration Scaling Authorization
*   **Date**: 2026-07-11
*   **Type**: HUMAN
*   **Status**: `ACTIVE`
*   **Decision**: AUTHORIZE_AUTONOMOUS_FORMATION_HANDOFF_RESOLUTION by testing Strategy B under the llama3 8B model configuration. Rejection is scoped to the llama3.2 3B current prompt configuration.
*   **Rationale**: Scaled model test isolates model capacity limits from architectural limits.
*   **Authority**: HUMAN

---

### DEC_007: Sequential Handoff Integration & Milestone 3 Entry
*   **Date**: 2026-07-11
*   **Type**: SCIENTIFIC
*   **Status**: `ACTIVE`
*   **Decision**: INTEGRATE_SEQUENTIAL_STRUCTURED_FORMATION_AND_ENTER_MILESTONE_3. Integrated the new sequential extraction architecture as standard, which achieved 100% schema compliance and 100% semantic preservation. Entered Milestone 3 autonomously and implemented sibling multiplicity/preservation.
*   **Rationale**: Decomposing prompt into sequential Calls 1 & 2 resolves model formatting capacity constraints without inducing prompt congestion or semantic claims distortion.
*   **Authority**: AG

---

### DEC_008: Pairwise Epistemic Competition Engine (Milestone 5)
*   **Date**: 2026-07-11
*   **Type**: SCIENTIFIC
*   **Status**: `ACTIVE`
*   **Decision**: IMPLEMENT_PAIRWISE_EPISTEMIC_SELECTION_ENGINE_FOR_COMPETING_SIBLINGS. Designed and implemented the pairwise selection engine (Milestone 5) based on compliance, validation lift, and complexity tie-breakers.
*   **Rationale**: Using a clean, deterministic pairwise selection avoids prompt congestion and ensures resource-awareness.
*   **Authority**: AG

---

### DEC_009: Longitudinal Belief State Transitions (Milestone 6)
*   **Date**: 2026-07-11
*   **Type**: SCIENTIFIC
*   **Status**: `ACTIVE`
*   **Decision**: IMPLEMENT_LONGITUDINAL_BELIEF_EVOLUTION_STATE_TRANSITIONS. Added new WEAKENED_BELIEF and RETIRED_BELIEF states to minimal learning cycle schemas, and extended belief memory to preserve transition histories and track provenance.
*   **Rationale**: Prevents arbitrary belief mutation while maintaining auditable state change pathways.
*   **Authority**: AG

---

### DEC_010: Two-Stage Proposition Compilation Architecture (Phase 1.7)
*   **Date**: 2026-07-15
*   **Type**: SCIENTIFIC
*   **Status**: `ACTIVE`
*   **Decision**: DECOUPLE_SEMANTIC_COMPILATION_FROM_PARAMETER_GROUNDING. Bifurcated the compilation logic into a Semantic Compiler flow and a deterministic Parameter Grounder. Exposes `compile_theory()` returning both `CanonicalSemanticProposition` and `CompiledProposition`.
*   **Rationale**: Separates high-level textual parsing from database-driven percentile/offset calculations, eliminating threshold hallucinations and fumbles (like `high > null`).
*   **Authority**: AG

---

### DEC_011: Validation Record Epistemic Primitive (Milestone 9)
*   **Date**: 2026-07-15
*   **Type**: SCIENTIFIC
*   **Status**: `ACTIVE`
*   **Decision**: FREEZE_VALIDATION_RECORD_AS_CANONICAL_LEARNING_PRIMITIVE. Approved the ValidationRecord schema, lifecycle states, and temporal/regime evidence accumulation formulas.
*   **Rationale**: Establishes that the ValidationRecord is the true atomic unit of learning (where speculative hypothesis collides with reality). This serves as the direct input to Belief Updates, Lesson Extraction, and Dormancy Reactivations.
*   **Authority**: AG

---

### DEC_012: Implementation and Verification of the Validation Engine (Milestone 9)
*   **Date**: 2026-07-16
*   **Type**: ENGINEERING / SCIENTIFIC
*   **Status**: `ACTIVE`
*   **Decision**: IMPLEMENT_VALIDATION_ENGINE_AND_RELATIONAL_STORAGE. Implemented the `ValidationEngine` class (resolving triggers, scope, and lookahead targets deterministically), relational mapping tables, repository storage layers, snapshot exports, and type-sanitization checks.
*   **Rationale**: Establishes the concrete validation infrastructure, enforcing append-only database immutability.
*   **Authority**: AG

---

### DEC_013: Forensic Audit Governance Rule and Documentation Reconciliation
*   **Date**: 2026-07-16
*   **Type**: METHODOLOGICAL
*   **Status**: `ACTIVE`
*   **Decision**: ADOPT_FORENSIC_AUDIT_CLOSURE_RULE_AND_RECONCILE_MILESTONES. Mandated that every forensic audit must end in exactly one of: Evidence Ledger Entry, Decision Ledger Entry, or Rejected Finding. Reconciled Candidate F target lineage hash changes as a semantically equivalent consequence of the corrected ontology, and verified that Milestone 3/S4-E0 forensic findings remain valid.
*   **Rationale**: Eliminates documentation ambiguity and closes the loop on historical audit results.
*   **Authority**: AG
