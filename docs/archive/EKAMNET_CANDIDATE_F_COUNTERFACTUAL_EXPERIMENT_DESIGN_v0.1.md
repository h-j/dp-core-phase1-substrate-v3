# EKAMNET CANDIDATE F COUNTERFACTUAL EXPERIMENT DESIGN v0.1
## MINIMUM COGNITIVE LOOP COMPOSITION TEST
## DP / EKAMNET RESEARCH PROGRAM

---

### 1. Executive Summary

This document presents the counterfactual experiment design to test whether accumulated epistemic history causally influences future cognitive content through Candidate F (Provenance-Driven Novelty Routing). 

To isolate this influence from the **CONTEXT_REMOVAL_CONFOUND**, we design a **Semantic-Context-Preserving Epistemic Ablation**. 
* The **Treatment Group** executes normal Candidate F, where a theory whose contradiction score exceeds the threshold is retired and filtered out of subsequent retrieval, forcing a `GENERATE` route.
* The **Control Group** retrieves the exact same prior theory as context, but suppresses the epistemic retirement transition (forcing its status to remain `"active"`), thereby routing the novelty gate to `REVISE` (or `REINFORCE`).
* Comparing these matched-state runs will prove whether the epistemic status transition itself causally alters the downstream cognitive trajectory.

---

### 2. Scope and Prohibitions

This is a **design-only specification**.
* No production source code was modified.
* No experiments were executed.
* S4-E0 and Milestone 8 remain queued.
* P1-P6 gates remain untouched.
* Lifecycle closure is explicitly not claimed.

---

### 3. Candidate F Executable Causal Chain

The entire Candidate F path is natively active in the repository:

1. **Originating Experience / Abstraction**:
   - *Source State*: Market raw inputs and text abstractions.
   - *Producer*: `MarketObservationSynthesizer` & `TheoryGenerationFlow`.
   - *Persistence Location*: PostgreSQL tables `observations` and `abstractions`.
   - *Retrieval*: `session.query(Observation)` / `session.query(Abstraction)`.
   - *Decision*: Orchestrator loop.
   - *Downstream Consumer*: LLM context.
   - *Observable Output*: Saved db rows.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

2. **Theory Generation**:
   - *Source State*: Abstraction text and active principles.
   - *Producer*: `TheoryGenerationFlow`.
   - *Persistence Location*: PostgreSQL `theories` table and local experience JSON files under `data/experiences/`.
   - *Retrieval*: `session.query(Theory)` / `TheoryRepository.get()`.
   - *Decision*: Orchestrator branch selector.
   - *Downstream Consumer*: `TheoryLineageEngine.evolve_theory()`.
   - *Observable Output*: Relational theory row.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

3. **Evidence / Contradiction Update**:
   - *Source State*: Prediction probes and actual market outcomes.
   - *Producer*: `ContradictionDetector.detect()`.
   - *Persistence Location*: PostgreSQL `transition_pressure_events`.
   - *Retrieval*: `session.query(PredictionResult)` / `session.query(Validation)`.
   - *Decision*: Triggered at end of step inside `replay_engine.py`.
   - *Downstream Consumer*: `TheoryLineageEngine.record_contradictions()`.
   - *Observable Output*: Contradiction score calculation.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

4. **TheoryRecord Status Change**:
   - *Source State*: Calculated contradiction score.
   - *Producer*: `TheoryLineageEngine.retire_stale_theories()`.
   - *Persistence Location*: Local `theory_lineage.json` snap.
   - *Retrieval*: `self.theory_lineage.active_theories()`.
   - *Decision*: Evaluates if contradiction score exceeds threshold (`0.50`).
   - *Downstream Consumer*: Novelty check prior theory query.
   - *Observable Output*: `"status": "retired"` in JSON.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

5. **Persistence**:
   - *Source State*: Lineage state object.
   - *Producer*: `self.theory_lineage._persist()`.
   - *Persistence Location*: `data/replay_snapshots/reliance/<run_id>/theory_lineage.json`.
   - *Retrieval*: `TheoryLineageEngine.load_from_snapshot()`.
   - *Decision*: End-of-step trigger.
   - *Downstream Consumer*: Analysis and subsequent steps.
   - *Observable Output*: Saved `theory_lineage.json`.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

6. **active_theories() Filtering**:
   - *Source State*: In-memory `theories` list registry.
   - *Producer*: `TheoryLineageEngine.active_theories()`.
   - *Persistence Location*: None (in-memory).
   - *Retrieval*: `active_theories()`.
   - *Decision*: Filters out records where `status == "retired"`.
   - *Downstream Consumer*: `replay_engine.py` active ID check.
   - *Observable Output*: Active theories list.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

7. **prior_theory Selection**:
   - *Source State*: `active_ids` set.
   - *Producer*: Novelty check block in `replay_engine.py` (lines 1447–1457).
   - *Persistence Location*: None (in-memory assignment).
   - *Retrieval*: Checks if `last_theory.id in active_ids`.
   - *Decision*: Assigns `prior_theory = last_theory` if present.
   - *Downstream Consumer*: `self.novelty_gate.is_novel()`.
   - *Observable Output*: Assigned `prior_theory` reference.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

8. **REVISE / GENERATE Routing**:
   - *Source State*: `prior_theory` availability.
   - *Producer*: `self.novelty_gate.is_novel()`.
   - *Persistence Location*: Saved in `decision_journal.json`.
   - *Retrieval*: Novelty gate logic.
   - *Decision*: Determines route (`REVISE` vs `GENERATE`).
   - *Downstream Consumer*: Orchestrator execution branch.
   - *Observable Output*: Route logs.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

9. **Later Theory Formation**:
   - *Source State*: Route decision.
   - *Producer*: `TheoryGenerationFlow` / `TheoryRevisionFlow`.
   - *Persistence Location*: PostgreSQL `theories` table.
   - *Retrieval*: `TheoryRepository.get()`.
   - *Decision*: Revision prompt vs. generation prompt.
   - *Downstream Consumer*: Relational memory.
   - *Observable Output*: Revised theory (inheriting lineage) vs. a new theory.
   - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

10. **Later Evidence**:
    - *Source State*: Child predictions and market outcomes.
    - *Producer*: `ContradictionDetector.detect()`.
    - *Persistence Location*: PostgreSQL `transition_pressure_events`.
    - *Retrieval*: validations query.
    - *Decision*: validation check.
    - *Downstream Consumer*: `record_contradictions()`.
    - *Observable Output*: Child contradiction score.
    - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

11. **Further Epistemic State Transition**:
    - *Source State*: Child contradiction score.
    - *Producer*: `TheoryLineageEngine.retire_stale_theories()`.
    - *Persistence Location*: `theory_lineage.json`.
    - *Retrieval*: subsequent step retrieval.
    - *Decision*: Transitions child status to `"retired"`.
    - *Downstream Consumer*: Future novelty gate check.
    - *Observable Output*: child theory retired in registry.
    - *Classification*: `REPOSITORY_NATIVE_ACTIVE_PATH`

---

### 4. Operational Causal Claim

**Causal Claim**:
Holding originating experiences, model configurations, initial database states, prompt templates, and semantic historical theory contexts controlled, changing the epistemic status/provenance state (retired vs. active) of prior theories causes a difference in later repository-native cognitive operation (REVISE vs. GENERATE routing) and subsequent theory trajectory (semantic/logical components of the generated theory).

* **Independent Variable**: Epistemic status/provenance state of the prior theory (`"retired"` vs. `"active"`).
* **Dependent Variable**: Novelty routing decision (`GENERATE` vs. `REVISE`) on step $t+n$, and the resulting semantic/logical content of the generated theory.
* **Control Variables**: Database starting state (0 rows), input dataset, model settings (llama3.2, temp=0, seed=42), prompt templates, and the presence of the prior theory's semantic text in the workspace.
* **Mediator**: `TheoryLineageEngine.active_theories()` filtration and `prior_theory` assignment in `replay_engine.py`.
* **Expected Causal Path**: 
  Validation contradiction $\rightarrow$ status becomes `"retired"` $\rightarrow$ excluded from `active_ids` $\rightarrow$ `prior_theory` is `None` $\rightarrow$ Novelty gate executes `GENERATE` $\rightarrow$ new independent theory compiled $\rightarrow$ trajectory divergence.
* **Falsification Condition**: 
  If the retirement state is ablated (forcing status to remain `"active"`), the system continues to retrieve the prior theory and routes to `REVISE` (or `REINFORCE`), compiling a revised theory child that retains parent components, and the subsequent trajectory matches the active control run.

---

### 5. Counterfactual Alternatives

| Dimension | A: Naive Retrieval Ablation | B: Semantic-Context-Preserving Epistemic Ablation | C: Contradiction Threshold Shift |
| :--- | :--- | :--- | :--- |
| **Causal Strength** | Weak (fails to isolate epistemic status from context removal) | **Strong** (isolates epistemic status while keeping context constant) | Strong (isolates threshold transition) |
| **Context Confound** | High | **Zero** | Zero |
| **Contamination** | Low | **Low** | Medium |
| **Nativeness** | High | **High** | High |
| **Distance** | Zero | **Short** (runtime monkeypatch of status check) | Minimal |
| **Reversibility** | High | **High** | High |
| **Observability** | High | **High** | High |
| **Falsification Value**| Low | **High** | High |

---

### 6. Preferred Intervention Design

We select **B: Semantic-Context-Preserving Epistemic Ablation** as the preferred design. It provides complete isolation of the epistemic status variable without confounding results through context removal.

---

### 7. Epistemic Ablation Semantics

The control run will override `TheoryLineageEngine.retire_stale_theories()` at runtime so that:
- It records contradiction scores but **never** transitions a theory's status to `"retired"`. All records remain `"active"`.
- As a result, `active_theories()` continues to retrieve the prior theory on step $t+n$, assigning it to `prior_theory`.
- The novelty gate receives the prior theory as context and executes `REVISE` or `REINFORCE`.
- This holds all semantic context constant while removing the causal influence of the retirement event.

---

### 8. Experimental Unit and Replay Window

* **Experimental Unit**: One complete 10-day Replay simulation run.
* **Replay Window**: The 10-day RELIANCE window is **sufficient**. Prior runs verified that this window contains multiple contradiction events (spiking on Day 2 and 3 at 0.78), a native retirement transition on Day 2, and retrieval checks on subsequent steps, leading to routing divergences (Step 9 routed to `GENERATE` in baseline vs. `REVISE` in treatment).
* **MME Necessity**: No Micro-Market-Environment is required, as the native RELIANCE backtest captures all necessary nodes.

---

### 9. Elicitation and Execution Controls

* **Starting State**: Executing the manifest utility to guarantee 0 database rows and empty snapshots.
* **Configurations**: Model `llama3.2`, Temperature `0.0`, Seed `42`, and checksum-verified `reliance_daily_3y.csv`.
* **Determinism Safeguard**: Paired runs alone are vulnerable to concurrency fluctuations. We implement a **replication strategy**: execute $k=3$ identical runs for both control and treatment. If any replication shows divergence within its group, the run is marked as non-deterministic and the result is discarded.

---

### 10. Pre-Registered Observables

* **Primary Causal Outcome**: Novelty routing decision (`GENERATE` vs. `REVISE` vs. `REINFORCE`) at step $t+n$.
* **Mediators**: `prior_theory` assignment in `replay_engine.py` (None vs. theory object).
* **Secondary Outcomes**: Semantic content (text characters, mechanism components list) of the compiled theory at step $t+n$.
* **Diagnostic Observables**:
  - TheoryRecord status (`active` vs. `retired`) in `theory_lineage.json`.
  - Contradiction pressure score.
  - Database row counts.

---

### 11. Success and Failure Taxonomy

#### Success Condition (All 8 Required)
1. **Identical Pre-Intervention**: Equal state up to Step 2.
2. **Controlled Epistemic Difference**: Status is `"retired"` in Treatment vs. `"active"` in Control.
3. **Context Preservation**: Both runs retrieve equivalent semantic structures if available.
4. **Changed Routing**: Treatment selects `GENERATE` vs. Control selects `REVISE` (or `REINFORCE`).
5. **Changed Cognitive Operation**: Treatment runs standard compilation; Control runs revision compiler.
6. **Changed Trajectory**: The resulting child theory text/logic diverges.
7. **Later Evidence Attachment**: Validations attach to the child theory node.
8. **Further State Transition**: Child theory triggers subsequent retirement based on validations.

#### Failure Classifications
* `NO_ELIGIBLE_CANDIDATE_F_EVENT`: No theories reached the retirement threshold in the backtest.
* `INTERVENTION_FAILED`: Bypassing retirement failed (prior theory was not retrieved in control).
* `CONTEXT_PRESERVATION_FAILED`: The control run diverged before the retirement event occurred.
* `ROUTING_UNCHANGED`: Novelty gate routed identically in both control and treatment.
* `ROUTING_CHANGED_WITHOUT_THEORY_DELTA`: Routing changed but the generated theory text was identical.
* `THEORY_DELTA_WITHOUT_LATER_EVIDENCE`: Trajectories diverged but no validation probes linked to the new theory node.
* `LATER_EVIDENCE_WITHOUT_STATE_TRANSITION`: Validations recorded but failed to transition child status.
* `CAUSAL_CHAIN_COMPLETED`: Complete success.

---

### 12. Claim Licensing Rules

* **Existence Claim**: If a single Replay run achieves `CAUSAL_CHAIN_COMPLETED`, it licenses:
  `EPISTEMIC_STATE_CAUSAL_INFLUENCE_OBSERVED`
* **Lifecycle Claim**: If the complete loop is established, it licenses:
  `MINIMUM_COGNITIVE_LIFECYCLE_CLOSURE_ESTABLISHED`
* **No Influence Claim**: If routing/theory trajectories are identical, it licenses:
  `NO_CAUSAL_INFLUENCE_DETECTED`
* **Replication Threshold**: **ROBUSTNESS_THRESHOLD_UNRESOLVED** (requires multi-asset confirmation before a system-wide capability claim is licensed).

---

### 13. Isolation Gate

The pre-execution Isolation Gate fails if any of the following are true:
1. S4-E0 or Milestone 8 code is active.
2. P1-P6 gates are modified.
3. The ontology compliance fix is inactive.
4. Lineage and nested ID fixes are inactive.
5. Prompt configurations differ from master.
6. Control and Treatment differ by any parameter other than the retirement suppression patch.
7. Manifest verification fails (dirty database or incorrect input checksum).

---

### 14. Strongest False Positive

* **Scenario**: Trajectory divergence occurs on Step 3, but is caused by LLM token non-determinism rather than the retirement intervention.
* **Prevention**: Checked by running $k=3$ replications for both control and treatment and verifying zero intra-group variance.

---

### 15. Strongest False Negative

* **Scenario**: The system is history-sensitive, but the 10-day window contains no retirement events due to low contradiction scores.
* **Prevention**: The RELIANCE dataset has already been verified to contain a retirement event on Day 2 under default configurations.

---

### 16. Implementation Distance

We propose executing the intervention using a custom test runner script that dynamically overrides the registry status method, preventing any modifications to production files:

* custom runner script (`bootstrap/run_counterfactual_experiment.py`): `TEST_HARNESS_ONLY`
* logging metrics hook: `OBSERVATION_ONLY`
* production code changes: **None**

---

### 17. Remaining Scientific Unknowns

* The sensitivity of the LLM to semantic context changes when mutating theories under revision vs. generation.
* The long-term stability of the loop over larger (e.g. 100-day) horizons.

---

### 18. Final Design Verdict

**CANDIDATE_F_DESIGN_READY_FOR_ADVERSARIAL_REVIEW**
