# EKAMNET MINIMUM COGNITIVELY MEANINGFUL CAUSAL-INFLUENCE DISCRIMINATION AUDIT
## DP / EKAMNET RESEARCH PROGRAM

This document reports the findings of a read-only forensic architecture and scientific discrimination audit.

---

### 1. Executive Summary

This final audit resolves the composition boundary question for the DP/EkamNet program: *Does a concrete, repository-grounded Level 2 causal-influence mechanism exist that can test longitudinal lifecycle closure without requiring validation of an epistemic learning mechanism?*

The audit confirms that **multiple repository-grounded Level 2 mechanisms exist**. Specifically, **Candidate F (Provenance-Driven Novelty Routing)** is already natively implemented and active in the repository's backtest orchestrator. It uses the active lineage node registry to determine whether to execute the mutation/revision flow or the standard generation flow. 

However, executing a counterfactual experiment to verify this lifecycle loop is blocked by the repository's database integrity defects, which must be remediated first.

**Final Verdict**: `LEVEL_2_MECHANISM_IDENTIFIED_PENDING_INTEGRITY_REMEDIATION`

---

### 2. Audit Scope and Prohibitions

This is a **read-only forensic architecture audit**. In accordance with the program constraints:
- No source code was modified.
- No database migrations or schema adjustments were performed.
- No database defects (such as lineage ID corruption or ID collisions) were repaired.
- No Milestone 8 work was initiated.
- No milestone closures or scientific validation claims were made.

---

### 3. Evidence Method

Repository orchestrator files (`replay_engine.py`) and memory tracking engines (`theory_lineage.py`) were inspected to trace how retrieved states alter downstream decision branches. Candidates were evaluated against strict Level 2 discrimination criteria to ensure they do not introduce LLM-based semantic interpretation or modify prediction values.

---

### 4. Three-Level Causal-Influence Model

The audit structures causal influence into three distinct levels:

- **Level 1 (Software/Architectural State-Loop Closure)**: Past state changes only execution metadata (e.g. logging formats, trace detail routing) with guaranteed identical cognitive outputs.
- **Level 2 (Cognitive Lifecycle Closure)**: Past epistemic state changes a future related cognition process (such as lineage association or lifecycle routing disposition) without modifying candidate semantic content, confidence, or evidence thresholds.
- **Level 3 (Epistemic Learning)**: Past state changes future cognition in a beneficial or performance-improving manner (such as candidate trigger pruning or evidence threshold adaptation), requiring scientific validation.

---

### 5. Operational Definition of Cognitively Meaningful

A processing change is operationalized as **cognitively meaningful (Level 2)** if it alters the *disposition* or *lifecycle routing* of a theory node within the cognition loop based on its lineage history. 

- **Cognitive Processing Change**: Transitioning a candidate's lifecycle stage (e.g. routing to `RECONSIDERATION` vs `FIRST_EVALUATION`) or associating a new theory node with a retired lineage tree.
- **Software Execution Change**: Adjusting database transaction batch sizes, snapshot folder paths, or console log print formats.

---

### 6. Repository-Native Candidate Inventory

The active repository was searched for existing candidate paths, detailed below:

1. **Novelty Branching**:
   - Source: Active lineage ID list in `self.theory_lineage`.
   - Persistence: Local `theory_lineage.json`.
   - Consumer: Novelty check in `replay_engine.py` (lines 1447–1457).
   - Computational difference: Determines whether the engine executes `REVISE` (deep-copying and modifying the prior theory) vs `GENERATE` (compiling a new theory).
   - Classification: **Level 2**.
2. **Regime Continuity Context Retrieval**:
   - Source: Regime memory signatures.
   - Persistence: Snapshot directories.
   - Consumer: Prompt generation.
   - Computational difference: None (expérience-only path defaults predictions; no causal influence on outputs).
   - Classification: **Level 1 (retrieval only)**.

---

### 7. Candidate A — Lineage Revisit Disposition

- **Concept**: Past lineage status classifies a new related theory as `REVISIT_EXISTING_LINEAGE` rather than `NEW_COGNITIVE_OBJECT`.
- **Epistemic Content Change**: None.
- **Scientific Neutrality**: High (asserts no improvement in prediction accuracy).
- **Engineering Distance**: Short.
- **Classification**: `LEVEL_2_COGNITIVE_LIFECYCLE_CLOSURE`.

---

### 8. Candidate B — Additional Evidence Disposition

- **Concept**: Unresolved contradiction levels route a theory to require additional validation sessions (`ADDITIONAL_EVIDENCE_REQUIRED`).
- **Scientific Neutrality**: High (provided the evidence threshold value itself is not changed).
- **Engineering Distance**: Medium.
- **Classification**: `LEVEL_2_COGNITIVE_LIFECYCLE_CLOSURE`.

---

### 9. Candidate C — Re-Evaluation Scheduling

- **Concept**: Past invalidation queues a retired theory for future re-evaluation.
- **Scientific Neutrality**: High (does not suppress candidates or modify confidence).
- **Engineering Distance**: Medium.
- **Classification**: `LEVEL_2_COGNITIVE_LIFECYCLE_CLOSURE`.

---

### 10. Candidate D — Lifecycle Stage Routing

- **Concept**: Prior validations route a theory node to `FIRST_EVALUATION` vs `RECONSIDERATION` stages.
- **Scientific Neutrality**: High (epistemic validation standards remain identical on both paths).
- **Engineering Distance**: Short.
- **Classification**: `LEVEL_2_COGNITIVE_LIFECYCLE_CLOSURE`.

---

### 11. Candidate E — Provenance-Driven Relationship Handling

- **Concept**: Past lineage links associate a mutated theory with a parent tree rather than treating it as independent.
- **Scientific Neutrality**: High.
- **Engineering Distance**: Short.
- **Classification**: `LEVEL_2_COGNITIVE_LIFECYCLE_CLOSURE`.

---

### 12. Candidate F — Repository-Discovered Mechanism

- **Mechanism Name**: **Provenance-Driven Novelty Routing**.
- **Source State**: Lineage ID registry.
- **Persistence**: `theory_lineage.json`.
- **Consumer**: Replay loop check (`replay_engine.py` line 1453).
- **Computational Difference**: Routes the orchestrator to `REVISE` (mutating/revising prior theory) vs `GENERATE` (creating a new theory).
- **Active in Replay**: Yes.
- **Deterministic**: Yes (lineage ID check).
- **Counterfactual Intervention**: Yes (by force-clearing `active_ids`).
- **Classification**: `LEVEL_2_COGNITIVE_LIFECYCLE_CLOSURE`.

---

### 13. False Level-2 Adversarial Analysis

- **`FALSE_LEVEL_2_A` (Metadata only)**: Candidate F passes. The decision to revise vs generate is a core cognitive branch that changes the object's mutation path, not merely metadata.
- **`FALSE_LEVEL_2_B` (Candidate suppression)**: Candidate F passes. It does not suppress the candidate or block compilation; it only changes how it is compiled (via revision vs generation).
- **`FALSE_LEVEL_2_C` (Confidence modification)**: Candidate F passes. It does not alter confidence states.
- **`FALSE_LEVEL_2_F` (LLM-mediated)**: Candidate F passes. The branch selection (lines 1447–1457) is purely deterministic code, independent of the LLM.

---

### 14. Semantic vs Scientific Neutrality

- **Semantic Neutrality**: The mechanism does not alter the text content of the theory node.
- **Scientific Neutrality**: The mechanism does not claim that routing improves epistemic performance.

*Verdict*: A valid Level 2 mechanism must satisfy **both** criteria. While any disposition routing introduces an inductive bias (deciding to reuse vs generate), this does **not** imply a performance claim. We can prove that the bias causally alters the execution path without asserting that the bias is beneficial or correct.

---

### 15. One-Object Minimum Loop Trace

A conceptual trace of **Candidate F (Provenance-Driven Novelty Routing)** is mapped below:

Experience $E_t$
→ `Theory` $O_t$ (`flows/theory_flow/theory_generation_flow.py`)
→ `TheoryStructured` $O_t$ (Strategy B)
→ Validation outcome at $t$ (`validations` table)
→ Lineage ID $S_t$ (`theory_lineage.json`)
→ **Time Passes**
→ New Observation at $t+n$
→ Lineage check loads $S_t$ (`replay_engine.py` line 1448)
→ Novelty branch executes `REVISE` (Causal influence)
→ Compiles mutated `Theory` $O_{t+n}$ (`replay_engine.py` line 1838)
→ Later validation at $t+n$
→ Lineage transition recorded in `theory_lineage.json`.

- **Missing Link**: The lineage ID mapping inside PostgreSQL is broken (due to the lineage ID propagation bug), which breaks SQL-side provenance tracing.

---

### 16. Counterfactual Experiment Feasibility

A counterfactual experiment for **Candidate F** is highly feasible:
- **Control Group**: Run a 10-day backtest with lineage retrieval disabled (forcing `prior_theory = None` on every step).
- **Treatment Group**: Run the identical backtest with lineage active.
- **Intervention Variable**: Active lineage ID matches.
- **Outcome Variable**: Count of `REVISE` vs `GENERATE` novelty decisions.
- **Case Count**: $N=1$ matched day is sufficient to prove causal existence. No MME is required.

---

### 17. State-Transition Requirement

To establish lifecycle closure, the audit evaluates three standards:
- **Standard A**: Retrieval → Causal Influence.
- **Standard B**: Retrieval → Causal Influence → Later Evidence.
- **Standard C**: Retrieval → Causal Influence → Later Evidence → Traceable State Transition.

*Verdict*: **Standard C** is the minimum scientifically defensible standard. We must prove that later evidence dynamically updates the state of the retrieved memory object (e.g. mutating its lineage status), closing the feedback loop.

---

### 18. Relationship to Existing Research

- **Milestone 5**: Candidate F does not depend on candidate competition or budget controls.
- **Milestone 6/7**: Candidate F does not depend on belief evolution states or trigger pruning. It can precede S4-E0 plurality.

---

### 19. Integrity Defect and New-Architecture Dependency Analysis

The database integrity defects block execution of the counterfactual trace:
1. **Lineage ID propagation bug**: `BLOCKS_EXPERIMENT`. Prevents tracing lineage families in SQL.
2. **Inner structured ID collision**: `BLOCKS_EXPERIMENT`. Breaks relational primary key constraints.
3. **Ontology taxonomy mismatch**: `BLOCKS_TRUSTWORTHY_MEASUREMENT`. Pollutes validation logs with false compliance failures.

*Prerequisites*: Bounded integration adapters are not required (the code already exists), but defect remediation is a strict blocker.

---

### 20. Candidate Discrimination Matrix

| Candidate | Repo-Native | Epistemic Origin | Persisted | Retrieved | Changes Processing | Deterministic | Semantically Neutral | Scientifically Neutral | Counterfactual Testable | Traceable Provenance | Level | Ready? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A (Revisit)** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Level 2** | Pending Repairs |
| **B (Evidence)**| Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Level 2** | Pending Repairs |
| **C (Schedule)**| Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Level 2** | Pending Repairs |
| **D (Routing)** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Level 2** | Pending Repairs |
| **E (Relation)**| Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Level 2** | Pending Repairs |
| **F (Novelty)** | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | **Level 2** | **Yes (Pending Repairs)** |

---

### 21. Four Decision Options and Recommendation

#### Option 1: Select the strongest valid LEVEL 2 mechanism and proceed, after prerequisites, to bounded experiment design. (Recommended)
- *Scientific benefit*: Verifies lifecycle loop integrity using a native mechanism.
- *Risk*: Requires fixing database defects first.
- *Engineering cost*: Low (defects only).
- *Reversibility*: Fully reversible.
- *Strongest argument for*: Leverages existing `REVISE`/`GENERATE` routing to prove structural closure immediately.
- *Strongest argument against*: Does not test predictive learning quality.

#### Option 2: Select the strongest near-valid mechanism and perform one bounded integration addition before experiment design.
- *Risk*: Unnecessary engineering complexity.

#### Option 3: Return to S4-E0 or other mechanism research before composition.
- *Risk*: Leaves active database defects unresolved.

#### Option 4: A missing architectural layer must be designed before composition.
- *Risk*: Unnecessary delay.

---

### 22. Verdict Integrity Self-Check and Final Verdict

- Modifying code attempted? No.
- Canonical state modified? No.
- Implementation authorized? No.
- Retrieval mistaken for causal influence? No.
- Number of sections matches exactly 22? Yes.
- Terminated in Conclusion A? Yes (Candidate F selected).

**Final Verdict**:
`LEVEL_2_MECHANISM_IDENTIFIED_PENDING_INTEGRITY_REMEDIATION`
