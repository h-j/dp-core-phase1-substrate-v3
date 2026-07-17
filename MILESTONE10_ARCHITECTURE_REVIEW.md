# Milestone 10 Architecture Review
## DP / EKAMNET RESEARCH PROGRAM

This document evaluates the architectural design of **Milestone 10: Closed-Loop Belief Update**, with a focus on cognitive correctness, mathematical stability, and research invariants.

---

## 1. Executive Assessment

**FINAL RATING: APPROVE_WITH_MINOR_REFINEMENTS**

The Milestone 10 draft design establishes a solid, deterministic, and replay-reproducible foundation for learning. However, to prevent local optimization bias and ensure cognitive rigor under context shifts, we recommend several minor refinements before implementation. Specifically, we introduce a deterministic **Evidence-Weight Model**, add **Temporal & Variance constraints** to promotion criteria, establish the **Pattern Consolidation Engine** as a first-class component, and expand the active scope of **World Model Constraints**.

---

## 2. Strengths of Current Design

1.  **Strict Boundary Separation**: The `ValidationEngine` serves as the deterministic, non-LLM gate. The complete decoupling of LLM processing from belief state updates ensures that the core learning loop remains mathematical, transparent, and reproducible.
2.  **Uncertainty-Modulated Belief Updates**: The mathematical update equations scale confidence changes by the inverse of uncertainty ($1 - U_t$). This is cognitively sound: the system avoids making volatile belief updates in high-uncertainty regimes.
3.  **Immutability and Auditability**: Treating validation records as write-once and capturing lineage updates in transition ledgers ensures 100% auditability and eliminates trace corruption.

---

## 3. Recommended Refinements (To Incorporate Now)

### 3.1 Part 1: Deterministic Evidence-Weight Model
We reject the assumption that every `SUPPORTED` validation record should carry equal weight. A prediction made with high conviction, representing a rare market tail-event, provides stronger empirical evidence than a low-conviction prediction during flat market conditions.

We introduce a deterministic **Evidence Weight** $w_V$ for each validation record $V$:
$$w_V = C_{\text{pred}} \cdot M_V \cdot R_V$$
Where:
*   **$C_{\text{pred}}$ (Prediction Conviction)**: The conviction score $\in [0.40, 1.0]$ assigned by the model at prediction time.
*   **$M_V$ (Outcome Magnitude)**: Weights validation by actual price return:
    $$M_V = 1.0 + \min\left(2.0, \beta \cdot |r_{\text{actual}}|\right)$$
    where $\beta = 10.0$ and $r_{\text{actual}}$ is the return on the lookahead step.
*   **$R_V$ (Statistical Rarity)**: A rarity multiplier. If the trigger features fall in extreme percentiles ($< 10\%$ or $> 90\%$), $R_V = 1.5$; otherwise $R_V = 1.0$.

In the update equations, the effective learning rate is scaled:
$$\eta_{\text{effective}} = \min\left(\eta_{\text{max}}, \eta \cdot w_V\right)$$
where $\eta = 0.15$ and $\eta_{\text{max}} = 0.40$ (capping the maximum single-step update to prevent whiplash). All parameters ($C_{\text{pred}}$, $r_{\text{actual}}$, trigger percentiles) are stored immutably in prediction/validation records, ensuring 100% replay reproducibility.

### 3.2 Part 2: Multidimensional Promotion Criteria
Fixed thresholds (e.g. $N \ge 5$ validations and $SR \ge 70\%$) are susceptible to local sample clustering (a theory matching a temporary market trend). We refine the promotion criteria:
*   **Transient Belief $\rightarrow$ Stabilized Lesson**:
    *   *Add Temporal Span*: The validations must span at least $\Delta t \ge 10$ backtest steps to ensure persistence over time.
    *   *Add Regime Diversity*: Must be validated on at least two distinct steps that have opposite market return signs.
*   **Stabilized Lesson $\rightarrow$ Canonical Principle**:
    *   *Add Contradiction Contiguity Gate*: Any sequence of 3 consecutive `CONTRADICTED` validations triggers an immediate demotion/retirement, regardless of the lifetime success rate.

### 3.3 Part 5: Active World Model Responsibilities (Adaptive Hybrid Exploration Safeguard)
Rather than treating World Model Constraints solely as static prompts (which risks severe confirmation bias under regime shifts), we implement an **Adaptive Hybrid Exploration Safeguard** based on the uncertainty ($U_p$) of the parent principle:

1.  **Axiomatic Gate (Hard Constraint)**: Active when $U_p < 0.30$. The theory generator is strictly prohibited from generating theories violating this axiom. This prunes the search space under verified, stable regimes.
2.  **Weak Prior (Soft Constraint)**: Active when $0.30 \le U_p < 0.60$. The prompt informs the generator of the principle's historical evidence but explicitly licenses generating counter-theories for exploratory validation.
3.  **Suspended (No Constraint)**: Active when $U_p \ge 0.60$ (due to local contradiction shocks). The constraint is completely removed, permitting full cognitive exploration to adapt to regime shifts.

Additional responsibilities:
*   **Retrieval Gate**: The orchestrator filters memory retrieval to prioritize historical days matching the world model's active regime constraints.
*   **Dormancy Reactivation**: A retired/dormant theory cannot be reactivated if it violates any active Axiomatic Gates.

### 3.4 Part 6: First-Class Pattern Consolidation Engine
We introduce the **Pattern Consolidation Engine** between Validation Records and Lessons:
*   *Role*: It acts as a batch processor at the end of each backtest block. Instead of promoting a single lineage directly, it clusters active lineages by semantic similarity and mechanism type.
*   *Outcome*: It nominates stable, consolidated clusters for lesson extraction, preventing noisy, redundant lineages from creating duplicate, narrow lessons.

### 3.5 Part 7: First-Class Belief Transition Schema
We adopt the immutable `BeliefTransitionEvent` database schema exactly as proposed. It acts as the audit ledger for the belief update loop.

---

## 4. Recommended Deferrals (To Defer to Phase 2)

1.  **Lesson Evolution (Part 3)**:
    *   *Decision*: **DEFER**.
    *   *Rationale*: Managing mutable, versioned lessons (Lesson v1 $\rightarrow$ Lesson v2) introduces topology churn and resets validation counts. In Milestone 10, lessons should remain read-only snapshots. If falsified, they should transition directly to `RETIRED`.
2.  **Principle Competition (Part 4)**:
    *   *Decision*: **DEFER**.
    *   *Rationale*: Before competing principles can be evaluated, we must verify that single principles update and guide predictions correctly. Competition adds premature complexity.

---

## 5. Updated Mathematical Model

The update equations are mathematically stable and exhibit asymptotic saturation. They are refined to incorporate the evidence-weight learning rate:

### 5.1 Supported Update
$$C_{t+1} = C_t + \eta_{\text{effective}} \cdot (1 - C_t) \cdot (1 - U_t)$$
$$U_{t+1} = U_t - \gamma \cdot U_t \cdot w_V$$

### 5.2 Contradicted Update
$$C_{t+1} = C_t - \eta_{\text{effective}} \cdot C_t \cdot (1 - U_t)$$
$$U_{t+1} = U_t + \gamma \cdot (1 - U_t) \cdot w_V$$

### 5.3 Decay Update (Untriggered Steps)
$$C_{t+1} = C_t - \lambda \cdot (C_t - 0.5)$$
$$U_{t+1} = U_t + \lambda \cdot (1 - U_t)$$

---

## 6. Scientific Risk Assessment & Invariant Check

*   **Auditability Violation Risk**: Real-world timestamps must never be used in calculating decay or updates.
    *   *Mitigation*: All temporal calculations (decay rates, stability age) must use step-based indices (backtest day count) to preserve replay determinism.
*   **Overgeneralization Risk**: A single rare event with high return magnitude could skew learning.
    *   *Mitigation*: The learning rate is capped by $\eta_{\text{max}} = 0.40$, ensuring no single validation can override accumulated history.

All core invariants (immutability, zero LLM belief influence, determinism) are preserved.
