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
| **EVD-006** | Level L3 (System) | PROMPT E0a | Read-side provenance substrate (`ConsultationLedger`), 100% byte-stability, and `influence_trace`. | `tests/test_consultation_ledger.py` |
| **EVD-007** | Level L2 (Component) | PROMPT E0b | Synthworld benchmark port, `TrivialTheoryGenerator`, `DPAdapter`, and 200-step smoke run (Brier 0.0074). | `tests/test_synthworld_benchmark.py` |
| **EVD-008** | Level L4 (Governance) | PROMPT E1 | Counterfactual ablation replay engine (`ablation_replay.py`) — **UNUSABLE AS EVIDENCE** pending re-run (missing cache counts; target at prior). | `tests/test_ablation_replay.py` |
| **EVD-009** | Level L4 (Governance) | PROMPT E2 | 20-seed synthetic battery — **VOID** (criteria not pre-registered; non-conformant benchmark). | `tests/test_run_e2.py` |
| **EVD-010** | Level L4 (Governance) | PROMPT E1_v2 | Counterfactual Ablation Protocol: Positive Control PASSED (verified_influence=17); Market Run REFUSED (precondition evidence_count 1.0 < 5.0). | `tests/test_ablation_protocol.py` |
| **EVD-011** | Level L4 (Governance) | PROMPT C3 / E2_v2 | 20-Seed Reference Synthetic Battery: Gate A Branch [AMBIGUOUS] (DP 0 decoy claims vs Flat 1.05; S3 recovery 292.5 vs 1873.8 steps; ECE 0.1630). | `bench/results/e2_v2_results.md` |

---

## Detailed Evidence Records

### EVD-011: 20-Seed Reference Synthetic Battery & Gate A Evaluation (PROMPT C3 / E2_v2)

* **Date**: 2026-07-24
* **Status**: `ACTIVE`
* **Target Milestone**: PROMPT C3 / E2_v2
* **Verification Level**: `Level L4 (Governance & Benchmark Battery Verification)`
* **Findings**:
  1. Executed 20-seed battery (4 scenarios $\times$ 20 seeds $\times$ 5 learners) at default scenario horizons on verified reference benchmark (`commit dc5502d`).
  2. **S2 Decoy Resistance**: DP/EkamNet achieved **0.0000 decoy claims** and **100% precision** vs FlatBayesian's 1.05 decoy claims and 65.8% precision.
  3. **S3 Recovery Speed**: DP/EkamNet recovered from regime flip in **292.5 steps** vs FlatBayesian's **1873.8 steps** (6.4x faster unlearning).
  4. **Calibration**: DP/EkamNet Expected Calibration Error across all 20 seeds = `0.1630`.
* **Gate Verdict**: **`AMBIGUOUS`** per `gate_a.yaml` three-branch table (outperformed baselines on decoy resistance and recovery speed, but paid static stream regret penalty on S1).


---

## Detailed Evidence Records

### EVD-010: Counterfactual Ablation Protocol & Registered Preconditions (PROMPT E1_v2)

* **Date**: 2026-07-24
* **Status**: `ACTIVE`
* **Target Milestone**: PROMPT E1_v2
* **Verification Level**: `Level L4 (Governance & Counterfactual Validation)`
* **Findings**:
  1. **Positive Control**: `DPAdapter` on scenario S1 promoted `c1 -> e1` to established tier ($E[\text{Beta}]=0.9595$, evidence count $13.34 \ge 5$). Counterfactual ablation produced 17 output divergences out of 50 predictions ($P_{\text{trace}} \cap D_{\text{obs}} = 17$, $D_{\text{obs}} \setminus P_{\text{trace}} = \emptyset$). Positive control **PASSED**.
  2. **Market Precondition Gate**: 35-day baseline market replay (`run_20260724_120559`) evaluated lineage confidence states. Highest confidence lineage `10:theory:0` reached confidence $0.6667 > 0.65$, but evidence count sat at **1.0 < 5.0**.
* **Gate Verdict**: **`REFUSED / BLOCKED ✗`** per `gate_a.yaml` pre-registered criteria. Market run refused due to insufficient evidence accumulation in the 35-day window.


---

## Detailed Evidence Records

### EVD-008: Counterfactual Ablation Protocol & Registered Verdict (PROMPT E1) — [UNUSABLE AS EVIDENCE]

* **Date**: 2026-07-23 (Voided 2026-07-24)
* **Status**: `NULL - UNUSABLE AS EVIDENCE PENDING RE-RUN`
* **Target Milestone**: PROMPT E1
* **Verification Level**: `Level L4 (Governance & Counterfactual Validation)`
* **Voiding Rationale (PROMPT C1)**:
  1. Missing mandatory `substitution_count` and `reinvocation_count` in report.
  2. Ablation target `"0:theory:0"` sat at Beta prior 0.50 without resolved evidence ($E[\text{Beta}]=0.50$, `evidence_count=0`), violating the registered precondition requiring established lineage confidence $> 0.65$ with `evidence_count >= 5`.

### EVD-009: 20-Seed Synthetic Battery & Gate A Branch Registration (PROMPT E2) — [VOID]

* **Date**: 2026-07-24 (Voided 2026-07-24)
* **Status**: `VOID`
* **Target Milestone**: PROMPT E2
* **Verification Level**: `Level L4 (Governance & Benchmark Battery Verification)`
* **Voiding Rationale (PROMPT C1)**:
  1. Criteria were not pre-registered in `experiments/preregistration/gate_a.yaml` prior to execution.
  2. Benchmark environment was non-conformant (fabricated baseline name `"Elatraverian"`, missing required baseline `WindowedFrequency`, non-standard 200-step scenarios).
  3. Contradictory result sets between `bench/results/e2_results.md` and program state logs.
  4. Degenerate S3 recovery metrics.



---

## Detailed Evidence Records

### EVD-006: Read-Side Provenance Substrate & Influence Trace (PROMPT E0a)

* **Date**: 2026-07-23
* **Target Milestone**: PROMPT E0a
* **Verification Level**: `Level L3 (System Integration)`
* **Methodology**:
  1. Built append-only, 100% byte-stable `ConsultationLedger` without wall-clock fields.
  2. Instrumented read sites across theory generation, reflection, and gating rules. Enforced Boundary Rule (`CONSULTATION` vs `INSPECTION`).
  3. Built CLI tool `dp.observability.influence_trace` to compute multi-hop transitive influence taints.
* **Empirical Findings**:
  - Two identical 35-day replays produce 100% byte-identical `consultation_ledger.jsonl` files.
  - Multi-hop transitive chain resolution verified on synthetic and live replay ledgers.
* **Test Automation**: `poetry run pytest tests/test_consultation_ledger.py`

### EVD-007: Synthworld Benchmark Port & DPAdapter (PROMPT E0b)

* **Date**: 2026-07-23
* **Target Milestone**: PROMPT E0b
* **Verification Level**: `Level L2 (Component Integration)`
* **Methodology**:
  1. Created market-free substrate configuration and deterministic `TrivialTheoryGenerator` (zero LLM in evaluation path).
  2. Built `DPAdapter` (`bench/synthworld/dp_adapter.py`) adhering to 3-method `Learner` protocol (`observe`, `predict`, `beliefs`).
  3. Proved exact hypothesis space equality (`set(adapter.hypothesis_space) == set(baseline.hypothesis_space)`).
* **Empirical Findings**:
  - 200-step S1 smoke run completed with Brier Score = 0.0074 and Discovery Rate = 1.0 (100%).
  - 800 `role="gate"` consultation ledger entries recorded during `predict()`.
* **Test Automation**: `poetry run pytest tests/test_synthworld_benchmark.py`

### EVD-008: Counterfactual Ablation Protocol & Registered Verdict (PROMPT E1)

* **Date**: 2026-07-23
* **Target Milestone**: PROMPT E1
* **Verification Level**: `Level L4 (Governance & Counterfactual Validation)`
* **Methodology**:
  1. Built `market/replay/ablation_replay.py` and `dp/observability/divergence_analyzer.py`.
  2. Selected single highest-confidence established founding lineage `"0:theory:0"`.
  3. Executed 35-day counterfactual ablation replay with overlay LLM cache (`substitution_count=0`, `reinvocation_count=0`).
  4. Calculated Four-Way Sets: $P_{\text{trace}}$ (28 decision IDs), $D_{\text{obs}}$ ($\emptyset$), $V_{\text{influence}}$ ($\emptyset$), $U_{\text{unpredicted}}$ ($\emptyset$).
* **Empirical Findings**:
  - Baseline ledger MD5 checksum remained 100% byte-identical (non-mutation invariant verified).
  - $D_{\text{unpredicted}} = \emptyset$ (zero unpredicted decision divergences — confirms no uninstrumented consultation read sites exist).
  - Registered Verdict: **`NULL`** (`NULL: Divergence set D_obs is empty entirely — accumulated knowledge did not causally change reasoning in this bounded run.`).
* **Test Automation**: `poetry run pytest tests/test_ablation_replay.py`


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

