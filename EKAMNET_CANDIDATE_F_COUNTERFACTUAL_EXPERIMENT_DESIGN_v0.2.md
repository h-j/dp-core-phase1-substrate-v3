# EKAMNET CANDIDATE F COUNTERFACTUAL EXPERIMENT DESIGN v0.2
## DP / EKAMNET RESEARCH PROGRAM

---

### 1. Executive Summary

This document refines the counterfactual experiment design for Candidate F (Provenance-Driven Novelty Routing). 

This version establishes correct control and treatment definitions, traces prompt layout semantics to identify a residual context confound, documents the exact step and ID details of a native retirement opportunity, and narrows the claim licensing rules. 

We select **Semantic-Context-Preserving Epistemic Ablation** as the preferred design, acknowledging that due to layout differences between `REVISE` and `GENERATE` prompt templates, semantic context is not strictly preservable in the native path. The design incorporates this limitation directly into the claim scope.

---

### 2. Scope and Prohibitions

This is a **design-only specification**:
* No production code was modified.
* No experiments were executed.
* S4-E0 and Milestone 8 remain queued.
* P1-P6 gates remain untouched.
* No claims of lifecycle closure are made.

---

### 3. Corrected Control and Treatment Definitions

To ensure scientific correctness, we define the experimental groups as:
* **CONTROL GROUP**: Unmodified repository-native Candidate F behavior. Theories whose contradiction scores exceed the threshold are transitioned to `"retired"`, filtered out by `active_theories()`, resulting in `prior_theory = None` $\rightarrow$ routing to `GENERATE` on subsequent steps.
* **TREATMENT GROUP**: The pre-registered epistemic ablation/intervention. The retirement transition is suppressed at runtime. Theories remain `"active"`, are retrieved by `active_theories()`, resulting in `prior_theory` being available $\rightarrow$ routing to `REVISE` (or `REINFORCE`).

---

### 4. Candidate F Semantic Context Trace

We traced how prior theory information is supplied to the LLM:
1. **GENERATE Path**:
   - If `prior_theory` is `None` (Control on step $t+n$), no prior theory text or component details enter the prompt.
   - If `prior_theory` is provided (e.g. during a non-retired generation branch), the prompt in `flows/theory_flow/theory_generation_flow.py` appends only a flat text description of the thesis (`prior_theory.summary_structured.claim`).
2. **REVISE Path**:
   - The orchestrator in `replay_engine.py:1578` converts the structured mechanisms list into a JSON block (`prior_mechs_str`) and appends it under `=== CURRENT MECHANISM COMPONENTS ===`. It also details failed components, passed components, and attribution reasoning.
3. **Prompt Layout Contrast**:
   - The `REVISE` prompt is structured to guide the LLM through in-place component mutations, while the `GENERATE` prompt compiles a thesis from scratch.
   - We cannot supply the full structured components JSON block to the `GENERATE` prompt without modifying production prompt templates (which is prohibited).

---

### 5. Semantic Context Preservation Verdict

**SEMANTIC_CONTEXT_NOT_PRESERVABLE_IN_NATIVE_CANDIDATE_F_PATH**

*Justification*: Because the two pathways use completely different prompt layouts and consume different slices of semantic information, it is impossible to strictly preserve the exact same prior-theory semantic context. Bypassing retirement to select `REVISE` vs. `GENERATE` inherently changes the prompt layout. This means the context-removal confound remains a residual confound that cannot be completely neutralized without mutating production prompts.

---

### 6. Refined Operational Causal Claim

**Operational Claim**:
Holding initial database state, model configurations, input data, and prompt layouts controlled, changing the epistemic status of prior theories (retired vs. active) in the native Candidate F path alters both the semantic context format in the prompts and the subsequent novelty routing decision, which downstream causes a traceable divergence in the subsequent cognitive trajectory.

* **Independent Variable (IV)**: Epistemic status of the prior theory (`"retired"` vs. `"active"`).
* **Dependent Variable (DV)**: Novelty routing decision (`GENERATE` vs. `REVISE`) and the resulting semantic/logical content of the generated theory.
* **Control Variables**: Database initial state (0 rows), input data checksum, model configurations (llama3.2, temp=0, seed=42), and prompt templates.
* **Mediator**: `TheoryLineageEngine.active_theories()` filtration and `prior_theory` assignment in `replay_engine.py`.
* **Expected Causal Path**: 
  Validation contradiction $\rightarrow$ status becomes `"retired"` $\rightarrow$ excluded from `active_ids` $\rightarrow$ `prior_theory` is `None` $\rightarrow$ Novelty gate executes `GENERATE` $\rightarrow$ new independent theory compiled $\rightarrow$ trajectory divergence.
* **Falsification Condition**: 
  If the retirement state is ablated (forcing status to remain `"active"`), the system continues to retrieve the prior theory and routes to `REVISE` (or `REINFORCE`), compiling a revised theory child that retains parent components, and the subsequent trajectory matches the active control run.

---

### 7. Candidate F Opportunity Provenance

An audit of the baseline run `run_20260714_155858` identifies the following native event sequence:
* **Theory Exists**: At Step 1 (2026-07-01), theory ID `d07f94a5-5308-4620-8699-ae7dec4a4631` (Lineage-family ID `5f33fb88966dd952`) was generated.
* **Contradiction Accumulates**: At Step 2 (2026-07-02), the retrospectively calculated contradiction score was `0.78` (exceeding the `0.50` threshold).
* **Retirement Transition**: At the end of Step 2 (2026-07-02), `TheoryLineageEngine.retire_stale_theories()` transitioned the lineage status to `"retired"`, persisting it in `theory_lineage.json`.
* **Retrieval Opportunity**: At Step 3 (2026-07-03), `active_theories()` was queried during the novelty check. Because `5f33fb88966dd952` was retired, it was excluded, setting `prior_theory = None`.
* **Causal Decision Point**: The novelty gate checked the step observation. Because `prior_theory` was `None`, it bypassed Revision and routed to `GENERATE` / `REINFORCE` fallback.
* **Counterfactual Opportunity**: If the retirement was suppressed (Treatment), the lineage would remain `"active"` at Step 3, providing the prior theory and forcing a `REVISE` routing.

*Classification*: **OBSERVED_NATIVE_EVENT** and **INFERRED_COUNTERFACTUAL_OPPORTUNITY**.

---

### 8. Replay Window Sufficiency Decision

The 10-day RELIANCE window is **sufficient**. As demonstrated in the baseline run, a native retirement occurs on Day 2, providing a retrieval opportunity on Day 3 and subsequent routing checks. No expanded window or Micro-Market-Environment is required.

---

### 9. Corrected Preferred Intervention

The intervention will be applied via a test harness wrapper:
* **Control**: Normal Candidate F execution (unmodified production status tracking).
* **Treatment**: Monkeypatch `TheoryLineageEngine.retire_stale_theories` at runtime to suppress retirement transitions (forcing records to remain `"active"`).
* All database, prompt, and execution configurations are kept identical.

---

### 10. Corrected Success and Failure Taxonomy

#### Success Condition (All 8 Required)
1. **Identical Pre-Intervention**: Control and Treatment are identical up to Step 2.
2. **Controlled Epistemic Difference**: Lineage is `"retired"` in Control vs. `"active"` in Treatment at the end of Step 2.
3. **Prior Retrieval Difference**: `prior_theory` is `None` in Control vs. populated in Treatment on Step 3.
4. **Changed Routing**: Control routes to `GENERATE` vs. Treatment routes to `REVISE` (or `REINFORCE`) on Step 3.
5. **Changed Cognitive Operation**: Control runs standard generation; Treatment runs revision compiler.
6. **Changed Trajectory**: The resulting child theory text/logic diverges.
7. **Later Evidence Attachment**: Validations attach to the child theory node.
8. **Further State Transition**: Child theory triggers subsequent retirement based on validations.

#### Failure Classifications
* `NO_ELIGIBLE_CANDIDATE_F_EVENT`: No theories retired in Control.
* `INTERVENTION_FAILED`: Retirement occurred in Treatment despite suppression.
* `CONTEXT_PRESERVATION_FAILED`: Runs diverged before Step 2.
* `ROUTING_UNCHANGED`: Novelty gate routed identically in both groups.
* `ROUTING_CHANGED_WITHOUT_THEORY_DELTA`: Routing changed but generated theory content was identical.
* `THEORY_DELTA_WITHOUT_LATER_EVIDENCE`: Trajectories diverged but validations failed to link to the new node.
* `LATER_EVIDENCE_WITHOUT_STATE_TRANSITION`: Validations recorded but failed to update status.
* `CAUSAL_CHAIN_COMPLETED`: Complete success.

---

### 11. Corrected Claim Licensing Rules

* **Event-Specific Success**: A single successful causal-chain event licenses only:
  `EPISTEMIC_STATE_CAUSAL_INFLUENCE_OBSERVED_FOR_BOUNDED_EVENT`
* **Lifecycle Closure**: A single successful 10-day Replay does not prove system-wide closure. We record:
  `ROBUSTNESS_THRESHOLD_UNRESOLVED`
  Lifecycle closure requires future replication across multiple assets/seeds.
* **Negative Result**: Identical trajectories in one run licenses only:
  `NO_CAUSAL_INFLUENCE_DETECTED_IN_BOUNDED_EXPERIMENT`

---

### 12. Isolation Gate Amendments

The pre-execution Isolation Gate requires:
1. Verification that lineage ID propagation and nested ID fixes are active.
2. MD5 checksum verification of prompt templates to guarantee no prompt modifications occur.
3. DB row counts manifest checks verifying a clean starting state.

---

### 13. Remaining Residual Confounds

* **Prompt Layout Confound**: Because `REVISE` prompts receive JSON mechanism components while `GENERATE` prompts receive only claim strings (or no context when `prior_theory` is None), we cannot separate the effect of the epistemic status transition from the layout difference. This is a residual, non-eliminable confound.

---

### 14. Changes from v0.1

1. **Normalized Definitions**: Swapped Control (native) and Treatment (epistemic ablation) definitions.
2. **Context Trace**: Discovered prompt layout differences between `REVISE` and `GENERATE` paths.
3. **Preservation Verdict**: Designated context as non-preservable in the native path.
4. **Opportunity Provenance**: Audited baseline run `run_20260714_155858` and documented Step 2/3 details.
5. **Narrowed Claims**: Restated success and negative licensing boundaries.

---

### 15. Final Design Verdict

**CANDIDATE_F_DESIGN_READY_FOR_ADVERSARIAL_REVIEW**
