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
| **Confidence Evolution Engine (PROMPT R1)** | Keyword-based confidence updates allowed LLM prose text to influence belief update path. | Replaced `ConfidenceEvolutionEngine` with `ScoredConfidenceEngine` (Beta posterior on predicate validation outcomes). Downgraded prior confidence-evolution scientific results as superseded. | Eliminates text keyword leakage into live confidence path; belief state is now driven purely by resolved predicate validation states, staleness decay, and contradiction counts. |


---

## 2. System Operational Maturity (Engineering Status)

*   **Milestone 1 (Replay Integrity)**: `100.0% Complete`. Repaired defects 1, 2, and 3. Verified database SQL ↔ JSON lineage propagation.
*   **Milestone 2 (Candidate F Counterfactual)**: `100.0% Complete`. Matured counterfactual logging and matching mechanisms.
*   **Milestone 3 (Epistemic Plurality)**: `100.0% Complete`. Prompt-decomposed Calls 1 & 2 sequential structured formation successfully integrated. Unit tested sibling multiplicity.
*   **Milestone 5 (Selection Engine)**: `OPEN (Operational 100%, Scientific Closure: INSUFFICIENT EVIDENCE)`. Deterministic pairwise competition engine integrated. Scientific gate status `INSUFFICIENT_EVIDENCE` (sample size 13 < min_sample 50 required for pre-registered MME threshold +10pp).
*   **Milestone 6 (Belief State Transitions)**: `OPEN (Operational 100%, Scientific Closure: INSUFFICIENT EVIDENCE)`. Integrated `WEAKENED` and `RETIRED` belief state schema models. Scientific gate status `INSUFFICIENT_EVIDENCE` (synthetic planted regime flip artifact pending).
*   **Milestone 7 (Learning Loop Pruning)**: `OPEN (Operational 100%, Scientific Closure: FAILED)`. Active candidate pruning hooks verified. Scientific gate status `FAIL` (Family B context-shift degradation -76.92pp fails pre-registered MME threshold >= -0.10).
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

---

## 7. Phase 1C Scientific Progress & Experimental Findings

### 7.1 EXP-1C.1 Diagnostic Replay (10-Day Reliance Window)
*   **Status**: COMPLETED (`commit 56dd7dd`)
*   **Execution Integrity**: 0 degraded steps across 10 matched seed runs (Control $C_0$ vs Intervention $I_1$, $k=5$).
*   **Finding**: $D_{\text{epistemic}} = 0.0$. On short single-regime 10-day windows, zero theory falsification events occur naturally.

### 7.2 EXP-1C_60D Multi-Regime Replay (60-Day Reliance Window)
*   **Status**: COMPLETED (`commit e4d25fa`)
*   **Execution Integrity**: 0 degraded steps across 60 steps $\times$ 10 runs (100% operational reliability).
*   **Finding**: $D_{\text{epistemic}} = 0.0$. In un-perturbed market replays, theories remain within valid bounds ($\text{score} \ge 0.5$). `LessonExtractor` requires $\ge 2$ recurring falsification instances to persist a lesson. Without falsifications, no lessons accumulate naturally.

### 7.3 EXP-1C.2 Controlled Epistemic Stress Experiment (60-Day Window)
*   **Status**: COMPLETED (`commit 72f099c`)
*   **Protocol**: [EXP_1C_2_CONTROLLED_EPISTEMIC_STRESS_PROTOCOL.md](file:///Users/hemantj/.gemini/antigravity-ide/brain/877ece6d-f299-4c12-b07c-dfc28f55cd90/EXP_1C_2_CONTROLLED_EPISTEMIC_STRESS_PROTOCOL.md)
*   **Three-Tier Evaluation Results**:
    1.  **Level 1 (Engineering Stability)**: `VERIFIED` (0 degraded steps across all runs).
    2.  **Level 2 (Learning Activation)**: `ACTIVATED` ($Y_{\text{lesson}} = 2.0$ active failure attribution lessons extracted and persisted into `LessonRepository` per run under regime shock mode $S_{\text{shock}}$, and $Y_{\text{lesson}} = 1.0$ under pre-warmed seeding mode $S_{\text{seed}}$).
    3.  **Level 3 (Causal Cognitive Adaptation)**: `INVARIANT` ($D_{\text{epistemic}} = 0.0$).
*   **Scientific Forensic Discovery**: `NoveltyDetectionGate` evaluates existing theories as `REINFORCE` or `REVISE` during replay steps, preserving structural theory component stability unless a full `GENERATE` decision is triggered.

---

## 8. Phase 1D Experience → Cognition Causal Bridge Validation

### 8.1 Candidate Alpha Implementation (Lesson-Aware Novelty Gate)
*   **Architecture**: Added `lesson_pressure` (Factor 5) to `NoveltyDetectionGate.compute_novelty_score` and passed active failure lessons into the Micro Reflection Critique prompt.
*   **Protocol**: [PHASE_1D_EPISTEMIC_BRIDGE_ARCHITECTURE_AND_PROTOCOL.md](file:///Users/hemantj/.gemini/antigravity-ide/brain/877ece6d-f299-4c12-b07c-dfc28f55cd90/PHASE_1D_EPISTEMIC_BRIDGE_ARCHITECTURE_AND_PROTOCOL.md)

### 8.2 EXP-1D.1 Scientific Validation Results
*   **Status**: COMPLETED & SCIENTIFICALLY VALIDATED (`commit d9f81a2`)
*   **Matched Seeds**: $k=5$ matched seed pairs ($\{42, 100, 200, 500, 777\}$) over 60 trading days under $S_{\text{shock}}$.
*   **Three-Tier Evaluation Results**:
    1.  **Level 1 (Engineering Stability)**: `VERIFIED` (0 degraded steps across all 60 steps $\times$ 10 runs).
    2.  **Level 2 (Learning Activation)**: `ACTIVATED` ($Y_{\text{lesson}} = 2.0$ lessons extracted and persisted).
    3.  **Level 3 (Causal Cognitive Adaptation)**: **`VALIDATED` ($D_{\text{epistemic}} = 0.4286 > 0.25$ threshold)**.
*   **Causal Mechanism**:
    *   Legacy Gate ($C_0$): Issued **0 GENERATE decisions** post-shock (stuck in `REINFORCE`).
    *   Candidate Alpha Gate ($I_1$): Issued **10 GENERATE decisions** post-shock, forcing full theory generation that actively consumes persisted failure lessons and mutates theory claims.
*   **North Star Verdict**: **VALIDATED** — Stored epistemic experience causally alters future cognitive behavior.

### 8.3 EXP-1D.2 Extended Replication (10 Seeds, 120 Days on Reliance)
*   **Status**: COMPLETED & GRADUATED TO LEVEL 4 REPLICATED EVIDENCE
*   **Scale**: 10 matched seed pairs ($k=10$, 20 full 120-day runs, 2,400 trading steps).
*   **Findings**:
    1.  **Level 1 Stability**: `VERIFIED` (0 degraded steps across 2,400 steps).
    2.  **Level 2 Activation**: $Y_{\text{lesson}} = 4.0$ active failure lessons extracted per run across 4 shock windows ($t \in \{15, 35, 75, 95\}$).
    3.  **Level 3 Adaptation**: **$D_{\text{epistemic}} = 0.4286 > 0.25$** ($C_0$: 0 GENERATE decisions vs $I_1$: 40 GENERATE decisions).

---

## 9. Phase 2A — Longitudinal Cognition & Trajectory Characterization

### 9.1 EXP-2.1 Longitudinal Experience Curve (360 Days on RELIANCE)
*   **Status**: COMPLETED & SCIENTIFICALLY CHARACTERIZED (`commit 30d5ca8`)
*   **Scale**: 10 full 360-day replays (5 matched seed pairs $k=5$, 3,600 total trading steps) across 12 monthly sampling checkpoints ($T_1 \dots T_{12}$) under 6 bi-monthly regime shocks ($t \in \{30, 90, 150, 210, 270, 330\}$).
*   **Findings**:
    1.  **Level 1 Stability**: `VERIFIED` (0 degraded steps across all 3,600 trading steps).
    2.  **Trajectory Classification**: **`ASYMPTOTE / STABLE EQUILIBRIUM`** ($D_{\text{epistemic}} = 0.4286$).
    3.  **Dynamic Profile**:
        *   **Shock Months (M1, M3, M5, M7, M9, M11):** $\pi_{\text{GENERATE}} = 0.0333$ (forces theory generation consuming active lessons).
        *   **Quiescent Months (M2, M4, M6, M8, M10, M12):** $\pi_{\text{REINFORCE}} = 1.0000$ (reuses failure-resilient theory).
    4.  **Verdict**: Cognition adapts rapidly to regime shocks and stabilizes into a resilient asymptotic equilibrium without over-falsification or epistemic collapse.

### 9.2 EXP-2.2 Adaptation Dynamics & REVISE Corridor Forensics
*   **Status**: COMPLETED & SCIENTIFICALLY CHARACTERIZED (`commit b68f12a`)
*   **Advanced Metric Profile**:
    *   **Text Epistemic Divergence ($D_{\text{epistemic}}$)**: $0.4286$
    *   **Mechanism Component Divergence ($D_{\text{mech}}$)**: $0.4000$
    *   **Theory Information Entropy ($H_{\text{theory}}$)**: $6.8920$ bits (rich vocabulary diversity)
    *   **Lesson Utilization Rate ($U_{\text{lesson}}$)**: $1.00$ under $S_{\text{shock}}$
*   **Dynamical Regime Classification**: **`RESILIENT ATTRACTOR / LIMIT CYCLE`** (true cognitive equilibrium).

### 9.3 Phase 2C Decision Surface Mapping & Cognitive Geometry (EXP-2C.1)
*   **Status**: COMPLETED & SCIENTIFICALLY CHARACTERIZED (`commit 38f9021`)
*   **Scale**: Full 6D continuous parameter grid sweep across 18,480 parameter coordinates ($S_{\text{val}} \times Sim \times F_{\text{ratio}} \times P_{\text{cov}} \times L_{\text{pres}} \times C$).
*   **Decision Surface Partitioning**:
    *   **Without Lessons ($L_{\text{pres}} = 0$)**: $\Omega_{\text{REINFORCE}} = 36.62\%$, $\Omega_{\text{REVISE}} = 59.47\%$, $\Omega_{\text{GENERATE}} = 3.91\%$ ($H_{\text{dec}} = 1.1594$ bits).
    *   **With Lessons ($L_{\text{pres}} = 1$)**: $\Omega_{\text{REINFORCE}} = 0.00\%$, $\Omega_{\text{REVISE}} = \mathbf{49.64\%}$, $\Omega_{\text{GENERATE}} = \mathbf{50.36\%}$ ($H_{\text{dec}} = 1.0000$ bits).
*   **Falsification Verdict**: **FALSIFIED** — The hypothesis that the `REVISE` corridor is "mathematically bypassed" is falsified. When active lessons exist, `REVISE` is not impossible or narrow; it occupies **49.64% of the continuous 6D parameter space volume**.
*   **Dynamical System Classification**: **Piecewise Continuous Threshold-Based Controller with Half-Space Bifurcation**.

---

## 10. Read-Side Provenance & Counterfactual Ablation Protocol (PROMPTS E0a, E0b, E1)

### 10.1 PROMPT E0a — Read-Side Provenance & Consultation Ledger
* **Status**: COMPLETED & VERIFIED (`commit c893628`)
* **Substrate**: Append-only `ConsultationLedger` (`dp/observability/consultation_ledger.py`) recording all cognitive consultations without wall-clock fields. 100% byte-stability verified across duplicate runs.
* **Analysis Tool**: `dp.observability.influence_trace` computing multi-hop transitive influence taints.

### 10.2 PROMPT E0b — Synthworld Benchmark Port & DPAdapter
* **Status**: COMPLETED & VERIFIED (`commit 3fbc8ea`)
* **Substrate**: Market-free configuration with deterministic `TrivialTheoryGenerator` and `DPAdapter` (`bench/synthworld/dp_adapter.py`) implementing 3-method `Learner` protocol (`observe`, `predict`, `beliefs`).
* **Hypothesis Space Equality**: Verified exact set equality `set(adapter.hypothesis_space) == set(baseline.hypothesis_space)`.
* **Smoke Run Performance**: 200-step S1 run completed with Brier Score **0.0074**, Discovery Rate **1.0** (100%), and 800 `role="gate"` consultation entries recorded.

### 10.3 PROMPT E1_v2 — Counterfactual Ablation Protocol & Precondition Gate Verdict
* **Status**: **`ACTIVE — POSITIVE CONTROL PASSED / MARKET RUN REFUSED`** (`commit eed6e72` / `experiments/run_e1_full_protocol.py`)
* **Positive Control Validation**:
  - `DPAdapter` on scenario S1 promoted `(c1, e1)` belief to established tier ($E[\text{Beta}]=0.9595$, evidence count $13.34 \ge 5$).
  - Ablating `(c1, e1)` produced 17 output divergences out of 50 predictions ($P_{\text{trace}} \cap D_{\text{obs}} = 17$, $D_{\text{obs}} \setminus P_{\text{trace}} = \emptyset$).
  - Positive control **PASSED**: verified influence set is non-empty and 100% predicted.
* **Market Replay Precondition Gate**:
  - 35-day baseline market replay (`run_20260724_120559`) evaluated lineage confidence states.
  - Highest confidence lineage `10:theory:0` reached confidence $0.6667 > 0.65$, but evidence count sat at **1.0 < 5.0**.
  - Market ablation run **`REFUSED / BLOCKED ✗`** per `gate_a.yaml` pre-registered criteria.
* **Reportable Scientific Unit**: The pairing ("Positive control proves instrument detects causal influence; 35-day market run refused due to evidence rate precondition") is the authoritative reportable scientific unit under repo governance (`DEC-012`).


---

## 11. Synthetic Benchmark Battery & Gate A Evaluation (PROMPT E2)

### 11.1 PROMPT E2 — 20-Seed Synthetic Battery & ECE Calibration (Initial Run)
* **Status**: **`VOID`** (`commit 50a7737` / `bench/run_e2.py`)
* **Governance Correction (PROMPT C1)**: Section 11.1 results declared **`VOID`** (criteria not pre-registered; non-conformant benchmark). Superseded by Section 11.2 (PROMPT C3 / E2_v2).

### 11.2 PROMPT C3 / E2_v2 — 20-Seed Reference Synthetic Battery & Gate A Branch Verdict
* **Status**: **`ACTIVE — GATE A VERDICT: [AMBIGUOUS]`** (`commit dc5502d` / `bench/run_e2_v2.py`)
* **Execution**: 20 seeds (0..19) $\times$ 4 scenarios ($T=3000, 3000, 4000, 4000$) $\times$ 5 learners on verified external reference benchmark (`commit dc5502d`).
* **Key Findings**:
  - **S2 Decoy Resistance (PASS)**: DP/EkamNet = `0.0000` decoy claims vs FlatBayesian = `1.0500` (100% precision vs 65.8%).
  - **S3 Recovery Speed (PASS)**: DP/EkamNet = `292.5 steps` vs FlatBayesian = `1873.8 steps` (unlearning died rules 6.4x faster).
  - **S3 Collateral Degradation (FAIL)**: DP/EkamNet = `0.0093` vs WindowedFrequency = `0.0079`.
  - **S1 Brier Regret (FAIL)**: DP/EkamNet = `0.0679` vs FlatBayesian = `0.0005` (static stream penalty due to promotion thresholding).
  - **Calibration**: DP/EkamNet ECE = `0.1630` across all scenarios $\times$ 20 seeds.
* **Registered Governance Consequence**: Per `gate_a.yaml` `AMBIGUOUS` branch, mixed results require registering an extension (longer horizons or higher seed counts) without modifying frozen parameters ($k_{\text{falsify}}=3.0, \lambda=0.01$, promotion tiers).










