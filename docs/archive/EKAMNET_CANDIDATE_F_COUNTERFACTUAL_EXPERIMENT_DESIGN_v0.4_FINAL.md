# EKAMNET CANDIDATE F COUNTERFACTUAL EXPERIMENT DESIGN v0.4 FINAL
## DP / EKAMNET RESEARCH PROGRAM

---

### 1. Executive Summary

This document establishes the final counterfactual experiment design for Candidate F (Provenance-Driven Novelty Routing). This specification normalized control/treatment semantics, resolved and incorporated the prompt-layout residual confound, traced and verified root-node identity semantics, and restructured the outcomes hierarchy to prioritize the theory-evidence-state lifecycle loop over downstream trading performance. 

The pre-execution checklist in Section 20 provides the exact steps, definitions, and stop conditions required to execute this counterfactual validation.

---

### 2. Scope and Prohibitions

This is a **design-only specification**:
* No production source code was modified.
* No experiments were executed.
* S4-E0 and Milestone 8 remain queued.
* P1-P6 gates remain untouched.

---

### 3. Prior Selection Rationale Reconciliation

* **Superseded Claims**: The claim that the semantic-context confound can be completely eliminated through controls is superseded. Because the `REVISE` prompt receives structured JSON components while the `GENERATE` prompt receives claim summaries (or no context when retired), the prompt layouts differ.
* **Selection Status**: We classify this status as:
  **ORIGINAL_SELECTION_RATIONALE_PARTIALLY_SUPERSEDED_BUT_SELECTION_STILL_SUPPORTED**
* **Corrected Rationale**: Candidate F remains preferred to Candidates A-E because those neutral candidates are cognitively inert (modifying only metadata stage names or evaluation categories) and fail to test if prior history affects future cognitive content. Candidate F is the only candidate that exercises the native learning loop closure. However, we acknowledge that the epistemic status transition and prompt layout changes are jointly tested and cannot be isolated.

---

### 4. Corrected Candidate F Selection Decision

Candidate F is selected for counterfactual experiment design under the corrected joint-influence framework:

**CANDIDATE_F_SELECTED_FOR_COUNTERFACTUAL_EXPERIMENT_DESIGN**

---

### 5. Complete Identity / Provenance Chain Trace

We trace the exact identity mapping for the Step 1 theory (`d07f94a5-5308-4620-8699-ae7dec4a4631`) in run `run_20260714_155858`:

1. **Originating Theory $\rightarrow$ Persisted TheoryModel Row**:
   - *Source Object*: `Theory` (Pydantic model)
   - *Source ID Type*: `str` (UUID4)
   - *Source ID Value*: `"d07f94a5-5308-4620-8699-ae7dec4a4631"`
   - *Lookup*: `TheoryRepository.create(theory)` sets `TheoryModel.id = theory.id`.
   - *Target Object*: `TheoryModel` (relational row)
   - *Target ID Type*: `str` (primary key)
   - *Target ID Value*: `"d07f94a5-5308-4620-8699-ae7dec4a4631"`
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `TheoryRepository.create()` mapping logic.

2. **TheoryModel Row $\rightarrow$ Lineage-Family Assignment**:
   - *Source Object*: `TheoryModel`
   - *Source ID Type*: `str` (UUID4)
   - *Source ID Value*: `"d07f94a5-5308-4620-8699-ae7dec4a4631"`
   - *Lookup*: `evolve_theory()` generates a 16-character hex string hash from abstraction + step.
   - *Target Object*: `TheoryModel.lineage_id`
   - *Target ID Type*: `str` (16-char hex)
   - *Target ID Value*: `"5f33fb88966dd952"`
   - *Equality Required / Confirmed*: Yes / Yes. (Defect 1 fix resolved this).
   - *Evidence*: `replay_engine.py` line 2054.

3. **Lineage-Family Assignment $\rightarrow$ TheoryRecord Node**:
   - *Source Object*: `TheoryModel.lineage_id`
   - *Source ID Type*: `str` (16-char hex)
   - *Source ID Value*: `"5f33fb88966dd952"`
   - *Lookup*: Registry map lookup `self.theory_lineage.theories[lineage_id]`.
   - *Target Object*: `TheoryRecord`
   - *Target ID Type*: `str` (16-char hex)
   - *Target ID Value*: `"5f33fb88966dd952"`
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `theory_lineage.py:333`: `lineage_id` returned in evolution results.

4. **TheoryRecord Node $\rightarrow$ Contradiction Accumulation**:
   - *Source Object*: `TheoryRecord`
   - *Source ID Type*: `str` (16-char hex)
   - *Source ID Value*: `"5f33fb88966dd952"`
   - *Lookup*: `record_contradictions(tid=lineage_record.id, ...)` uses lineage hex ID.
   - *Target Object*: `TheoryRecord.contradictions` (list)
   - *Target ID Type*: `str` (16-char hex)
   - *Target ID Value*: `"5f33fb88966dd952"`
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `replay_engine.py` line 2206.

5. **Contradiction Accumulation $\rightarrow$ Retirement Transition**:
   - *Source Object*: `TheoryRecord`
   - *Source ID Type*: `str` (16-char hex)
   - *Source ID Value*: `"5f33fb88966dd952"`
   - *Lookup*: `retire_stale_theories()` checks contradiction score on Step 2.
   - *Target Object*: `TheoryRecord.status`
   - *Target ID Type*: `str`
   - *Target ID Value*: `"retired"`
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `theory_lineage.py` retirement loops.

6. **Retirement Transition $\rightarrow$ active_theories() Filtering**:
   - *Source Object*: `TheoryRecord.status`
   - *Source ID Type*: `str`
   - *Source ID Value*: `"retired"`
   - *Lookup*: `active_theories()` excludes records where `status == "retired"`.
   - *Target Object*: `active_records` (list)
   - *Target ID Type*: `List[TheoryRecord]`
   - *Target ID Value*: `[]` (empty list if single record)
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `theory_lineage.py` filter loop.

7. **active_theories() Filtering $\rightarrow$ active_ids Representation**:
   - *Source Object*: `active_records`
   - *Source ID Type*: `List[TheoryRecord]`
   - *Source ID Value*: `[]`
   - *Lookup*: Constructs set `{t.id for t in active_records}`.
   - *Target Object*: `active_ids` (set)
   - *Target ID Type*: `Set[str]`
   - *Target ID Value*: `{}` (empty set)
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `replay_engine.py` line 1449.

8. **active_ids Representation $\rightarrow$ last_theory.id Membership Check**:
   - *Source Object*: `active_ids`
   - *Source ID Type*: `Set[str]`
   - *Source ID Value*: `{}`
   - *Lookup*: `if last_theory.id in active_ids or last_theory.lineage_id in active_ids`.
   - *Target Object*: Boolean match outcome
   - *Target ID Type*: `bool`
   - *Target ID Value*: `False`
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `replay_engine.py` line 1453.

9. **last_theory.id Membership Check $\rightarrow$ prior_theory Assignment**:
   - *Source Object*: Boolean match outcome
   - *Source ID Type*: `bool`
   - *Source ID Value*: `False`
   - *Lookup*: Skips assignment, leaving `prior_theory = None`.
   - *Target Object*: `prior_theory` variable
   - *Target ID Type*: `NoneType`
   - *Target ID Value*: `None`
   - *Equality Required / Confirmed*: Yes / Yes.
   - *Evidence*: `replay_engine.py` lines 1453-1457.

10. **prior_theory Assignment $\rightarrow$ Novelty Routing Consequence**:
    - *Source Object*: `prior_theory`
    - *Source ID Type*: `NoneType`
    - *Source ID Value*: `None`
    - *Lookup*: Orchestrator defaults route to `GENERATE`.
    - *Target Object*: `decision` routing label
    - *Target ID Type*: `str`
    - *Target ID Value*: `"GENERATE"`
    - *Equality Required / Confirmed*: Yes / Yes.
    - *Evidence*: `replay_engine.py` line 1936.

---

### 6. Identity Chain Verdict

**CANDIDATE_F_ROOT_IDENTITY_SEMANTICS_VERIFIED**

*Repository Evidence*: 
When a new lineage is created by `evolve_theory()`, `TheoryLineageEngine.create_theory(tid, step, ...)` (line 95) is invoked with an identical hex ID string `tid = lineage_id`. Thus, for a root node of a lineage family, `TheoryRecord.id` and `TheoryRecord.lineage_id` are identical (`5f33fb88966dd952`). For subsequent mutations, `mutate_theory()` generates a new unique `child_id` while inheriting `lineage_id = parent.lineage_id` (line 186). This maps lineage-node ID vs. lineage-family ID correctly.

---

### 7. Corrected Experiment Classification

**PARTIAL_COGNITIVE_LIFECYCLE_COMPOSITION_EXPERIMENT**

*Justification*: The experiment does not isolate the pure "epistemic state" alone, since changes in routing eligibility alter prompt layouts and semantic context formats. Instead, it tests the integrated composition of the native learning loop (Experience $\rightarrow$ Theory $\rightarrow$ Contradiction $\rightarrow$ State $\rightarrow$ Retrieval $\rightarrow$ Routing $\rightarrow$ Mutation).

---

### 8. Control and Treatment Definitions

* **CONTROL (Unmodified Production)**: Normal Candidate F. Theory `5f33fb88966dd952` is retired on Step 2 due to contradiction. On Step 3, it is filtered out of `active_ids`, setting `prior_theory = None` $\rightarrow$ routes to `GENERATE`.
* **TREATMENT (Ablation)**: Epistemic suppression active. Retirement for lineage `5f33fb88966dd952` is suppressed at Step 2. On Step 3, the lineage remains `"active"` and is retrieved as `prior_theory` $\rightarrow$ routes to `REVISE`.

---

### 9. Targeted Intervention Decision

We select **B: Targeted Suppression of the pre-registered theory lineage family** (`5f33fb88966dd952` on Step 2). 

Targeted suppression minimizes unrelated state drift. Any observed downstream trajectory divergence is attributable to the targeted Candidate F intervention and its inseparable associated semantic-context and prompt-layout consequences, subject to the documented residual confound.

---

### 10. Manipulation Checks

* **Intervention Integrity Check**: Lineage status is `"retired"` in Control vs. `"active"` in Treatment at the end of Step 2.
* **Manipulation Check 1**: `prior_theory` is `None` in Control vs. populated with `last_theory` in Treatment at Step 3.
* **Manipulation Check 2**: Novelty gate routes to `GENERATE` in Control vs. `REVISE` (or `REINFORCE`) in Treatment at Step 3.
* *Note*: These checks are mechanically guaranteed by repository logic. They do not constitute independent scientific evidence of cognitive change.

---

### 11. Primary Scientific Outcomes

* **PRIMARY_SCIENTIFIC_OUTCOME**: 
  Persistent divergence in the subsequent repository-native **theory $\rightarrow$ evidence $\rightarrow$ epistemic-state trajectory** following the targeted Candidate F intervention and its inseparable semantic-context / prompt-layout consequences.
* **SECONDARY OUTCOMES**:
  - Prediction direction divergence.
  - Conviction score divergence.
  - Trading-execution divergence.
  - Other downstream behavioral/financial effects.
* **DIAGNOSTIC OBSERVABLES**:
  - Prompt differences.
  - Generated theory text differences.
  - Intermediate routing metadata.

---

### 12. Lifecycle Completion Outcomes

* **LIFECYCLE_COMPLETION_OUTCOME**: Validations and contradiction scores at Step 5 and beyond link directly to the child theory node, and it eventually transitions to a new retired/contradicted state, completing the cognitive lifecycle feedback loop.

---

### 13. Scientifically Meaningful Failure Points

After successful manipulation checks, the experiment fails scientifically at these points:
* `ROUTING_CHANGED_WITHOUT_THEORY_DELTA`: Novelty gate changed route but the LLM output identical claims/components.
* `THEORY_DELTA_WITHOUT_LATER_EVIDENCE`: Trajectories diverged but validations/predictions failed to register for the child theory, breaking downstream connection.
* `LATER_EVIDENCE_WITHOUT_STATE_TRANSITION`: Downstream validations were logged but failed to trigger subsequent retirement of the child theory.

---

### 14. Matched-State Isolation Protocol

The proven Phase 1 / Phase 2 matched-state protocol is reused:
- Before each run, execute `generate_manifest.py` to confirm:
  - 0 rows in all database tables.
  - Empty snapshots directories.
  - MD5 checksums of prompts match canonical files.
  - Seed, temperature, model, and dataset are equal.
- **`INITIAL_STATE_EQUIVALENCE_NOT_PROVEN`** invalidates experiment interpretation.

---

### 15. Corrected Outcome Taxonomy

| Outcome | Observed Condition | Scientific Interpretation | Licensed Claim |
| :--- | :--- | :--- | :--- |
| **A. ISOLATION FAILURE** | Initial row counts $\ne 0$ or config checksum mismatch. | Starting states were not matched; environmental contamination occurred. | **EXPERIMENT_NON_INTERPRETABLE** |
| **B. INTERVENTION FAILURE** | Target lineage retired in Treatment. | The monkeypatch/status override failed to execute. | **EXPERIMENT_NON_INTERPRETABLE** |
| **C. MANIPULATION FAILURE** | Routing identical in Control and Treatment on Step 3. | Hardcoded routing check failed or LLM generated a different route. | **EXPERIMENT_FAILED_TO_MANIPULATE** |
| **D. EMPIRICAL PROPAGATION FAILURE** | Routing diverged, but generated theory content or downstream actions match. | LLM ignored prompt context or outputs converged. | **NO_CAUSAL_INFLUENCE_DETECTED_IN_BOUNDED_EXPERIMENT** |
| **E. LIFECYCLE COMPLETION FAILURE** | Theories diverged, but validations/state transitions failed to complete. | Loop was broken at the evidence or transition node. | **CANDIDATE_F_CAUSAL_PROPAGATION_OBSERVED_WITHOUT_LIFECYCLE_COMPLETION** |
| **F. COMPLETE BOUNDED SUCCESS** | Causal chain completed from intervention to child retirement. | Epistemic status and layout changes jointly caused trajectory divergence. | **EPISTEMIC_STATUS_AND_ASSOCIATED_CONTEXT_CHANGE_JOINTLY_CAUSED_BOUNDED_TRAJECTORY_DIVERGENCE** |

---

### 16. Corrected Claim Licensing

* **Success Claim**:
  **EPISTEMIC_STATUS_AND_ASSOCIATED_CONTEXT_CHANGE_JOINTLY_CAUSED_BOUNDED_TRAJECTORY_DIVERGENCE**
* **Replication Boundary**: A single successful run does not prove system-wide closure. We record:
  **ROBUSTNESS_THRESHOLD_UNRESOLVED**
* **Negative Claim**:
  **NO_CAUSAL_INFLUENCE_DETECTED_IN_BOUNDED_EXPERIMENT**

---

### 17. Residual Confounds

* **Prompt Layout Confound**: Because `REVISE` prompts receive JSON mechanism components while `GENERATE` prompts receive only claim strings (or no context when retired), we cannot separate the effect of the epistemic status transition from the layout difference. This is a residual, non-eliminable confound.

---

### 18. Changes from v0.3

1. **Category E Correction**: Changed Category E claim from `CANDIDATE_F_CAUSAL_CHAIN_EXISTENCE_VERIFIED` to `CANDIDATE_F_CAUSAL_PROPAGATION_OBSERVED_WITHOUT_LIFECYCLE_COMPLETION`.
2. **Intervention Claim Correction**: Clarified targeted suppression language to incorporate inseparable context and prompt-layout consequences.
3. **Identity Verification**: Confirmed root node ID semantics and identity chain validity.
4. **Outcomes Hierarchy Reorganization**: Placed theory-evidence-state trajectory as primary, prediction/trading execution as secondary, and prompt/text details as diagnostic.

---

### 19. Final Design Verdict

**CANDIDATE_F_FINAL_DESIGN_READY_FOR_EXECUTION**

---

### 20. Concise Execution Checklist

#### 1. Control Definition
Unmodified production Candidate F pipeline execution. Theories exceeding contradiction thresholds transition to `"retired"`, are filtered by `active_theories()`, leading to `prior_theory = None` and `GENERATE` routing.

#### 2. Treatment Definition
Epistemic suppression active. Retirement transition is blocked at runtime for the target lineage, leaving its status `"active"`, leading to `prior_theory` availability and `REVISE` (or `REINFORCE`) routing.

#### 3. Exact Target Lineage/Event
Lineage family ID `"5f33fb88966dd952"` created on Step 1 (2026-07-01), target retirement event at the end of Step 2 (2026-07-02) due to contradiction score `0.78`.

#### 4. Intervention Location
`TheoryLineageEngine.retire_stale_theories` or `record_contradictions` in [theory_lineage.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/memory/lineage/theory_lineage.py#L606) dynamically patched in `bootstrap/run_counterfactual_experiment.py`.

#### 5. Matched-State Manifest Requirements
* Output manifests `matched_state_baseline_manifest.json` and `matched_state_treatment_manifest.json`.
* Database row counts = 0 at startup for all tables.
* Clean/empty snapshot directories.
* Temperature=0.0, Seed=42, model="llama3.2".
* SHA-256 hash validation of prompt files.

#### 6. Pre-Execution Isolation Gate
Verify DB rows count, prompt SHA hash, settings, and input data checksum. Any mismatches abort the run.

#### 7. Manipulation Checks
* Status check at end of Step 2 (`"retired"` in Control vs `"active"` in Treatment).
* `prior_theory` assignment check at Step 3 (`None` in Control vs populated in Treatment).
* Novelty route decision at Step 3 (`GENERATE` in Control vs `REVISE` in Treatment).

#### 8. Primary Scientific Outcome
Divergence in the **theory $\rightarrow$ evidence $\rightarrow$ epistemic-state trajectory** starting at Step 3 and propagating downstream.

#### 9. Lifecycle Completion Outcome
Downstream validations/contradiction checks successfully attach to the child theory node, leading to child retirement.

#### 10. Secondary Outcomes
Downstream prediction directions, conviction scores, and trading-execution actions.

#### 11. Outcome Taxonomy
Evaluated across Categories A (Isolation Failure), B (Intervention Failure), C (Manipulation Failure), D (Empirical Propagation Failure), E (Lifecycle Completion Failure), and F (Complete Bounded Success).

#### 12. Licensed Claims
* Complete Success: `EPISTEMIC_STATUS_AND_ASSOCIATED_CONTEXT_CHANGE_JOINTLY_CAUSED_BOUNDED_TRAJECTORY_DIVERGENCE`.
* Lifecycle Failure: `CANDIDATE_F_CAUSAL_PROPAGATION_OBSERVED_WITHOUT_LIFECYCLE_COMPLETION`.
* System-wide loop claim: `ROBUSTNESS_THRESHOLD_UNRESOLVED` (requires replication).

#### 13. STOP Conditions
* Manifest checks or Isolation Gate check fails.
* Manipulation checks fail.
* Execution non-determinism detected across $k=3$ replication runs.
