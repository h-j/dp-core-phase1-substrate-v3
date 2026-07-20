# EKAMNET REPLAY CLOSURE AND CANDIDATE F SELECTION
## DP / EKAMNET RESEARCH PROGRAM

---

### 1. Executive Summary

This document concludes the Replay Integrity Remediation process and characterizes the selection of Candidate F (Provenance-Driven Novelty Routing) as the flagship target for the upcoming counterfactual composition experiment. By resolving the three core database integrity defects (Lineage Propagation, Nested ID Regeneration, and Ontology Whitelisting), the system has established matched-state initial conditions. Comparative evaluations demonstrate that while structurally neutral mechanisms exist, Candidate F is the only candidate that directly tests whether accumulated epistemic history causally influences future cognitive content. Therefore, Candidate F is selected for the subsequent experiment design phase.

---

### 2. Scope and Prohibitions

In accordance with program directives, the following boundaries were strictly observed:
* No experiment design was executed.
* Candidate F was not implemented or modified.
* No further Replay runs were executed.
* S4-E0 and Milestone 8 work remain queued and untouched.
* P1-P6 scientific validation gates were not modified.
* No search for additional Replay defects was conducted.

---

### 3. Replay Integrity Remediation Closure

The Replay Integrity Remediation is officially complete. All three targeted defects have been repaired and verified:
* **DEFECT 1 (Lineage Propagation)**: Restored database lineage propagation write-backs, ensuring SQL $\leftrightarrow$ JSON consistency.
* **DEFECT 2 (Nested ID Collision)**: Enforced deepcopy-nested ID and timestamp regeneration on `REVISE` operations, preventing primary key collisions while preserving identity on `REINFORCE`.
* **DEFECT 3 (Ontology Omission)**: Added `"SECTOR_ZSCORE"` to `CORE_CONCEPTS` in the ontology registry. 

---

### 4. Corrected Phase 2 Claim Boundary

The Phase 2 results claim boundary is canonically recorded as:

**ONTOLOGY_CONTRACT_CORRECTION_CONFIRMED_WITH_TRACEABLE_EXPECTED_COGNITIVE_DELTA**

*Interpretation Limits*:
1. The ontology registry defect was successfully demonstrated;
2. The minimum repair was implemented;
3. Matched initial states were established between baseline and treatment;
4. The intervention successfully removed the identified ontology rejection and validation retry path;
5. The resulting cognitive trajectories diverged downstream;
6. The broad trajectory divergence is consistent with downstream propagation of the contract correction;
7. The exact causal ancestry of every individual downstream delta was not independently established, and we do not claim that every individual downstream delta was independently causally proven.

---

### 5. Canonical Program-State Update

The canonical program-state artifact, [EKAMNET_PROGRAM_STATE.md](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_PROGRAM_STATE.md), has been updated under Section 12 to record the status `REPLAY_INTEGRITY_REMEDIATION_COMPLETE`, alongside the repaired defects list, claim boundaries, and next steps.

---

### 6. Prior Neutral-Candidate Artifact Provenance

* **Artifact File**: [EKAMNET_MINIMUM_COGNITIVELY_MEANINGFUL_CAUSAL_INFLUENCE_AUDIT.md](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_MINIMUM_COGNITIVELY_MEANINGFUL_CAUSAL_INFLUENCE_AUDIT.md)
* **Provenance**: Originally generated under Epoch 9 / Iteration 1 to inventory and classify native candidate mechanisms (Sections 6–13, 20).
* **Identified Neutral Candidates**: 
  - **Candidate A (Lineage Revisit)**: Classifying a new related theory as a lineage revisit rather than a new object.
  - **Candidate B (Additional Evidence)**: Routing theories with unresolved contradictions to require more validation.
  - **Candidate C (Re-Evaluation Scheduling)**: Queueing retired theories for future evaluation.
  - **Candidate D (Lifecycle Stage Routing)**: Routing theory nodes to `FIRST_EVALUATION` vs `RECONSIDERATION`.
  - **Candidate E (Provenance Relationship)**: Associating mutated theories with parent lineages.

---

### 7. Candidate F Mechanism Trace

* **Mechanism**: **Provenance-Driven Novelty Routing**
* **Trace Path**:
  1. **Source State**: `TheoryRecord.status` is tracked inside `theory_lineage.json`.
  2. **Evidence Input**: Validation contradictions at step $t$ trigger `retire_stale_theories()`, transitioning status to `"retired"`.
  3. **Retrieval**: `active_theories()` filters on step $t+n$, omitting `"retired"` records.
  4. **Causal Influence**: If the parent theory is retired, `replay_engine.py:1453` sets `prior_theory = None`, forcing the novelty branch to execute `GENERATE` rather than `REVISE`.
  5. **Cognitive Consequence**: `REVISE` deepcopies and mutates the parent theory (retaining core mechanisms), whereas `GENERATE` compiles a completely new theory structure from scratch.

---

### 8. Strongest Neutral Candidate Mechanism Trace

* **Strongest Neutral Candidate**: **Candidate D (Lifecycle Stage Routing)**
* **Trace Path**:
  1. **Source State**: Theory node evaluation count and history.
  2. **Evidence Input**: Accumulation of validation runs.
  3. **Retrieval**: Prior evaluations are queried from the database.
  4. **Causal Influence**: The system routes the theory node through different lifecycle tags (e.g., `FIRST_EVALUATION` vs `RECONSIDERATION` stages) during the validation pipeline.
  5. **Cognitive Consequence**: Epistemic validation rules remain identical; the routing only alters metadata labels or stage categorizations without modifying the theory's semantic assertions or logical mechanisms.

---

### 9. Comparative Discrimination Matrix

| Evaluation Dimension | Candidate F (Novelty Routing) | Strongest Neutral Candidate (Candidate D) |
| :--- | :--- | :--- |
| **1. Cognitive Necessity** | **Yes**. Tests if past history alters the generated theory content. | **No**. Only shifts categorization labels or evaluation stage tags. |
| **2. Causal Intervention Clarity** | **Yes**. Retrieval can be disabled countersignaled (`active_ids` cleared). | **Yes**. Labels or stages can be counterfactually bypassed. |
| **3. Lifecycle Coverage** | **Complete**. Spans experience, theory, validation, persistence, retrieval, revision. | **Incomplete**. Fails to close Standard C (does not alter future theory compilation). |
| **4. Semantic Activity Risk** | **High**. Reorganizing revision changes textual content and logic. | **None**. Semantically neutral; text content remains untouched. |
| **5. Structural Neutrality** | **No**. Directly mutates cognitive representation paths. | **Yes**. Preserves structural/scientific representation. |
| **6. Scientific Claim Value** | **High**. Proves history causally changes cognitive behavior. | **Low**. Only proves history alters metadata classification. |
| **7. Falsification Value** | **High**. Failure proves the system's theory generation is history-insensitive. | **Low**. Failure only indicates categorization adapters are broken. |
| **8. Repository Nativeness** | **Yes**. Production code path already natively executes this logic. | **Partial**. Conceptual framework exists but requires integration code. |
| **9. Experimental Distance** | **Zero**. Fully implemented in `replay_engine.py`. | **Short/Medium**. Requires creating database/pipeline adapters. |
| **10. Relation to Open Question** | **Direct**. Tests causal impact of history on later cognition. | **Indirect**. Succeeds without demonstrating changes in future thinking. |

---

### 10. Strongest Argument Against Candidate F

* **Objection**: Candidate F's `REVISE` vs `GENERATE` branch selection is semantically active. Disabling lineage retrieval removes historical theory context from the LLM prompt. Consequently, any observed downstream trajectory divergence in backtests might be caused by a simple loss of semantic context (forcing the LLM to generate from scratch) rather than by a lack of structured cognitive lifecycle closure. A positive result (divergence) establishes that the LLM behaves differently when context is withheld, but does not prove the complete longitudinal cognitive loop is closed.
* **Classification**: **REQUIRE_EXPERIMENT_DESIGN_CONTROLS**
* **Justification**: This risk can be managed by applying strict controls to the counterfactual experiment (e.g., matching model parameters, seeds, temperature, and checking that the semantic content is generated under controlled, predictable pathways).

---

### 11. Strongest Argument Against Neutral Candidate

* **Objection**: The strongest neutral candidate (Candidate D) achieves its neutrality by stripping the mechanism of any cognitive impact. If the experiment succeeds (showing different lifecycle stage tags), it proves only that the system updates metadata fields correctly. The core learning loop remains open because the accumulated epistemic history has **zero** causal influence on future cognitive content or decisions; the LLM would continue to compile the exact same theories.
* **Falsification Verdict**: **YES**. The experiment could succeed cleanly while the core hypothesis—that past epistemic history changes later cognition—remains false. This makes the neutral candidate scientifically insufficient for testing the open question.

---

### 12. Selection Logic Evaluation

Repository evidence supports all selection criteria:
1. **Direct Test**: Candidate F directly tests whether prior theory success/failure changes subsequent theory compilation.
2. **Neutral Sufficiency**: A neutral candidate could pass (e.g., changing metadata) while leaving future cognition completely unchanged.
3. **Control Feasibility**: Candidate F's semantic activity risk is mitigable via prompt/seed controls and matching initial db conditions.
4. **Nativeness**: Candidate F is natively active and executed in the main replay pipeline.
5. **Claim Strength**: Candidate F licenses a claim about cognitive behavior alteration, whereas the neutral candidate only licenses a claim about metadata propagation.

---

### 13. Remaining Experimental Risks

* **LLM Non-Determinism**: Minor fluctuations in token generation due to hardware concurrency could simulate trajectory divergence. Strict execution constraints are required.
* **State Pollution**: Intermediate database states must be completely cleared between control and treatment runs to prevent cross-contamination.

---

### 14. Candidate F Status

**CANDIDATE_F_SELECTED_FOR_COUNTERFACTUAL_EXPERIMENT_DESIGN**

---

### 15. Final Recommendation

**REPLAY_CLOSURE_COMPLETE_PROCEED_TO_CANDIDATE_F_DESIGN**
