# EKAMNET CANDIDATE F COUNTERFACTUAL EXPERIMENT DESIGN v0.3
## DP / EKAMNET RESEARCH PROGRAM

---

### 1. Executive Summary

This document presents the final reconciled counterfactual experiment design for Candidate F (Provenance-Driven Novelty Routing). 

Reconciliation of the prompt templates confirms that the semantic context format is not strictly preservable in the native Candidate F path because `REVISE` and `GENERATE` paths consume different prompt layouts. We narrow the experiment classification and claim licensing rules to carry this joint-influence limitation directly in their semantics. 

We choose a **Targeted Epistemic Suppression** of the pre-registered theory lineage family `5f33fb88966dd952` at Step 2 to surgically isolate the causal intervention. A sequence trace confirms that the relational-to-lineage identity chain is fully verified and correct.

---

### 2. Scope and Prohibitions

This is a **design-only specification**:
* No production code was modified.
* No experiments were executed.
* S4-E0 and Milestone 8 remain queued.
* P1-P6 gates remain untouched.

---

### 3. Prior Selection Rationale Reconciliation

The selection rationale in `EKAMNET_REPLAY_CLOSURE_AND_CANDIDATE_F_SELECTION.md` is reconciled as follows:
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

**CANDIDATE_F_IDENTITY_CHAIN_VERIFIED**

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

* **Specificity**: Surgical. Bypasses only the target lineage family's retirement path.
* **Contamination**: Extremely low. Normal retirement paths remain active for all other lineages.
* **Nativeness**: High. Suppresses state transition at the exact causal node.
* **Selection Rationale**: Option B prevents global state drift, ensuring that any downstream trajectory divergence is caused *only* by the status of the target lineage itself.

---

### 10. Manipulation Checks

* **Intervention Integrity Check**: Lineage status is `"retired"` in Control vs. `"active"` in Treatment at the end of Step 2.
* **Manipulation Check 1**: `prior_theory` is `None` in Control vs. populated with `last_theory` in Treatment at Step 3.
* **Manipulation Check 2**: Novelty gate routes to `GENERATE` in Control vs. `REVISE` (or `REINFORCE`) in Treatment at Step 3.
* *Note*: These checks are mechanically guaranteed by repository logic. They do not constitute independent scientific evidence of cognitive change.

---

### 11. Primary Scientific Outcomes

The genuinely empirical scientific outcomes begin after the manipulation checks:
* **EMPIRICAL_INTERMEDIATE_OUTCOME**: The semantic and logical components of the compiled theory at Step 3 (the text claim, mechanism components list, etc.) differ between Treatment and Control.
* **PRIMARY_SCIENTIFIC_OUTCOME**: Downstream predictions and trading execution actions at Step 4 and beyond diverge between Treatment and Control due to the different child theory.

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
| **E. LIFECYCLE COMPLETION FAILURE** | Theories diverged, but validations/state transitions failed to complete. | Loop was broken at the evidence or transition node. | **CANDIDATE_F_CAUSAL_CHAIN_EXISTENCE_VERIFIED** (Partial only) |
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

### 18. Changes from v0.2

1. **Selection Rationale Reconciliation**: Superseded the claim of complete context isolation.
2. **Targeted Intervention**: Selected a targeted suppression (Option B) rather than global suppression.
3. **Trace Verification**: Detailed the complete 10-step identity trace.
4. **Outcome Taxonomy**: Divided results into 6 specific failure/success categories.
5. **Claim Licensing**: Changed the licensed claim to represent the joint-influence confound directly in its semantics.

---

### 19. Final Design Verdict

**CANDIDATE_F_DESIGN_READY_FOR_EXECUTION**
