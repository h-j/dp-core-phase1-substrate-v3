# EKAMNET SCIENTIFICALLY NEUTRAL CAUSAL-INFLUENCE AUDIT
## DP / EKAMNET RESEARCH PROGRAM

This document reports the findings of a read-only forensic architecture and scientific validity audit.

---

### 1. Executive Summary

This audit evaluates the feasibility of testing longitudinal cognitive lifecycle loop closure using a minimal deterministic causal-influence mechanism without introducing epistemic contamination. 

The audit concludes that **a scientifically neutral causal-influence mechanism is feasible only under strict constraints**. By utilizing purely structural parameters (such as Evaluation Order or Routing Decisions between identical execution paths) and verifying them through deterministic A/B counterfactual runs, the program can prove structural lifecycle closure without claiming or validating epistemic learning performance.

**Final Verdict**: `NEUTRAL_CAUSAL_INFLUENCE_FEASIBLE_WITH_STRICT_CONSTRAINTS`

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

The active repository files (`replay_engine.py`, `theory_generation_flow.py`) and database schemas were traced to identify existing data retrieval paths and verify if their execution alters downstream computations. Candidate neutral mechanisms were evaluated against mathematical constraints to ensure they do not introduce LLM-based semantic interpretations.

---

### 4. Persistence-to-Learning Conceptual Ladder

To ensure scientific hygiene, the audit establishes five distinct levels of system maturity:

1. **A. DATA PERSISTENCE**: Information from step $t$ is successfully serialized and stored in a database or local file such that it exists at step $t+n$.
2. **B. RETRIEVAL**: Persisted information from step $t$ is successfully loaded and accessed by the orchestrator at step $t+n$.
3. **C. COMPUTATIONAL INFLUENCE**: Injecting or modifying the retrieved state changes a downstream prompt or variable.
4. **D. ARCHITECTURAL CAUSAL INFLUENCE**: A controlled A/B counterfactual experiment demonstrates that the retrieved state is *causally responsible* for a downstream computational difference (e.g. execution path taken) at step $t+n$.
5. **E. EPISTEMIC LEARNING**: The causal influence produces a justified improvement or adaptation in belief accuracy, decision quality, or prediction performance.

This audit establishes that **Level D (Architectural Causal Influence) can be verified and demonstrated independently of Level E (Epistemic Learning).**

---

### 5. Necessary vs Sufficient Analysis

- **Necessary**: Yes. For a system to demonstrate that it learns over time, it is necessary that past cognitive states causally influence future computations. Without this link, the system is memory-blind and incapable of longitudinal adaptation.
- **Sufficient**: No. A hardcoded step counter or a static date filter retrieved from disk causally changes future computations, but it does not represent learning. Learning requires that the causal changes represent an adaptive model of the environment.

*Verdict*: The proposition “Demonstrating that past state causally changes future computation is necessary but not sufficient evidence that the system learns” is **scientifically and architecturally defensible for DP/EkamNet**.

---

### 6. Repository-Native Influence Path Inventory

Three native paths through which retrieved state propagates in the backtester were traced:

1. **Regime Continuity Memory Retrieval**:
   - Source state: Abstraction/Observation text.
   - Persistence: Local snapshot directories.
   - Retrieval function: `self.regime_continuity_memory.summary(regime_subtype)` (`replay_engine.py:1404`).
   - Downstream consumer: LLM theory generation prompt.
   - Computational effect: Bypassed (causally silent; predictions default to experience-only).
   - Influence type: `RETRIEVAL_WITHOUT_CAUSAL_INFLUENCE`.
2. **Theory Lineage Retrieval**:
   - Source state: Parent theory details (`confidence_state`).
   - Persistence: Local `theory_lineage.json`.
   - Retrieval function: `self.theory_lineage.evolve_theory` (`replay_engine.py:2018`).
   - Downstream consumer: Novelty gate branch checker.
   - Computational effect: Directs decision branch between mutate and reuse.
   - Active in Replay: Yes.
   - Influence type: `LONGITUDINAL_BELIEF_EVOLUTION` (LLM-mediated inputs, deterministic code branch).
3. **Contradiction Registry**:
   - Source state: Contradiction events.
   - Persistence: `contradiction_registry.json`.
   - Retrieval function: `self.contradiction_engine.detect()`.
   - Downstream consumer: `TransitionPressureEngine` and confidence calculators.
   - Computational effect: Updates pressure indicators.
   - Active in Replay: Yes.
   - Influence type: `LONGITUDINAL_BELIEF_EVOLUTION`.

---

### 7. Eligibility Flag Analysis

- **Mechanism**: Retrieved state changes whether a compiled theory is eligible for reinforcement vs mutation.
- **Observability**: High (logged in traces).
- **Counterfactual Intervention**: Yes (by force-clearing the flag).
- **Epistemic Content Change**: None (content is unchanged).
- **Epistemic Assumption**: Yes (assumes that ineligibility is "good" or "bad", implying preference).
- **Scientific Neutrality**: Conditional (neutral if used purely to route execution, contaminated if used to assert prediction quality).
- **Engineering Distance**: Short.
- **Strongest Contamination Argument**: Restricting eligibility suppresses hypotheses, which directly alters the candidate pool and introduces inductive bias.

---

### 8. Priority Score Analysis

- **Mechanism**: Retrieved state changes a priority score that determines logging or database persistence order.
- **Observability**: High.
- **Counterfactual Intervention**: Yes.
- **Epistemic Content Change**: None.
- **Epistemic Assumption**: Low.
- **Scientific Neutrality**: High (does not change predictions or decisions).
- **Engineering Distance**: Medium.
- **Strongest Contamination Argument**: If priority determines budget allocation (like ERC), it affects candidate survival and ceases to be neutral.

---

### 9. Routing Decision Analysis

- **Mechanism**: Retrieved state routes execution through Path X (e.g. logging detail level A) rather than Path Y (logging detail level B) of identical cognitive structures.
- **Observability**: High (verifiable via log output).
- **Counterfactual Intervention**: Yes.
- **Epistemic Content Change**: None.
- **Epistemic Assumption**: None (both paths execute identical cognitive logic).
- **Scientific Neutrality**: **Absolute** (purely structural).
- **Engineering Distance**: Short.
- **Strongest Contamination Argument**: None. It is a pure system-level tracing utility.

---

### 10. Evaluation Order Analysis

- **Mechanism**: Retrieved state changes the order in which candidates are evaluated, without changing the evaluation logic or candidate content.
- **Observability**: High.
- **Counterfactual Intervention**: Yes.
- **Epistemic Content Change**: None.
- **Epistemic Assumption**: None (provided no budget exhaustion occurs).
- **Scientific Neutrality**: **Absolute**.
- **Engineering Distance**: Medium.
- **Strongest Contamination Argument**: If the evaluation order changes under strict resource constraints, it can lead to starvation (ERC), which introduces bias.

---

### 11. Counterfactual Experiment Requirements

To demonstrate `PAST_STATE_CAUSED_FUTURE_COMPUTATIONAL_DIFFERENCE`:
- **Control Group**: Run a 10-day backtest with a mocked empty belief memory (or retrieval disabled).
- **Treatment Group**: Run the identical backtest with memory retrieval enabled.
- **Intervention variable**: The retrieved memory state from step $t$.
- **Controlled variables**: Initial assets, LLM seed, OHLCV data, prompt structures, and orchestrator configs.
- **Outcome variable**: The execution path (Path X vs Path Y) or logging output.
- **Sample size**: $N=1$ instance is sufficient (since the mechanism is deterministic, a single matched day is enough to prove existence). No statistical power or MME is required.

---

### 12. Scientific Claim Boundary

A successful counterfactual experiment licenses only a subset of claims:

- **Supported**:
  - `CLAIM_A`: Past information was persisted.
  - `CLAIM_B`: Past information was later retrieved.
  - `CLAIM_C`: Retrieved information was consumed downstream.
  - `CLAIM_D`: Retrieved information causally changed future computation.
  - `CLAIM_E`: The system demonstrated longitudinal cognitive lifecycle closure.
- **Not Supported / Requires Additional Evidence**:
  - `CLAIM_F`: The system learned (requires validation of adaptive logic).
  - `CLAIM_G`: The system improved epistemic performance (requires comparative effectiveness).

---

### 13. Epistemic Contamination Analysis

The risk of introducing epistemic assumptions through the influence mechanism is analyzed below:

- **Content changes**: `DISQUALIFYING`.
- **Hypothesis suppression**: `HIGH`.
- **Evidence threshold changes**: `HIGH`.
- **Prediction changes**: `DISQUALIFYING`.
- **LLM interpretation**: `DISQUALIFYING`.
- **Pure structural routing**: `LOW`.

*To remain neutral, the causal influence must be deterministic and structural, bypassing the LLM.*

---

### 14. Scientific Neutrality Criteria

A neutral causal-influence mechanism must satisfy these criteria:

- **Required**:
  1. Deterministic transformation (no LLM in the influence branch).
  2. No modification of epistemic content.
  3. No claim of performance improvement.
  4. Identical input conditions between control and treatment.
  5. Observable downstream execution difference.
- **Optional**:
  1. Reversible influence.
- **Unnecessary**:
  1. Improvement of prediction quality.

---

### 15. Strongest Falsification Argument

*The Inductive Bias Argument*: "Any downstream change caused by memory necessarily changes what the system does. If what the system does changes because of prior experience, then the system has implemented an inductive bias or policy. An inductive bias or policy is itself an epistemic mechanism. Therefore, no causal memory influence can be scientifically neutral."

*Audit Resolution*: The argument **fails** for pure structural routing. If the downstream change is restricted to system metadata (such as logging formats or evaluation ordering without resource limits), the system's epistemic outputs (predictions, trades, beliefs) remain identical. The change is computational but epistemically neutral, proving lifecycle closure without introducing bias.

---

### 16. Relationship to Milestone 7 and S4-E0

- **Milestone 7**: The proposed composition experiment does **not** duplicate trigger pruning. It uses a neutral routing flag rather than a candidate suppression filter, evading the overgeneralization harm of Milestone 7.
- **S4-E0 Plurality**: Lifecycle composition can scientifically precede S4-E0. Testing structural closure does not require multiple candidate theories; it can be validated using a single candidate family.

---

### 17. Four Decision Options and Recommendation

#### Option 1: A scientifically neutral causal-influence mechanism is feasible. Proceed after integrity repairs to Minimum Cognitive Loop Composition Experiment design.
- *Scientific benefit*: Speeds up design work.
- *Risk*: High risk of premature implementation.

#### Option 2: A neutral mechanism is feasible only with strict constraints. Resolve those constraints before experiment design. (Recommended)
- *Scientific benefit*: Prevents scientific contamination by establishing strict structural routing rules.
- *Risk*: Medium design cost.
- *Engineering cost*: Low.
- *Reversibility*: Fully reversible.

#### Option 3: Any causal influence necessarily embeds an epistemic mechanism. Complete additional mechanism validation before lifecycle composition.
- *Scientific benefit*: Ultra-conservative.
- *Risk*: Engineering stagnation.

#### Option 4: Repository evidence is insufficient to decide. Conduct a narrower forensic trace before roadmap selection.
- *Scientific benefit*: Delays decision.

---

### 18. Verdict Integrity Self-Check and Final Verdict

- Modifying code attempted? No.
- Canonical state modified? No.
- Implementation authorized? No.
- Retrieval mistaken for causal influence? No.
- Number of sections matches exactly 18? Yes.

**Final Verdict**:
`NEUTRAL_CAUSAL_INFLUENCE_FEASIBLE_WITH_STRICT_CONSTRAINTS`
