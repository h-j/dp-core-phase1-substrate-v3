# Milestone 10: Belief Dynamics Design Spec
## DP / EKAMNET RESEARCH PROGRAM

This document outlines the architecture, data models, update mechanics, and graduation criteria for **Milestone 10: Closed-Loop Belief Update**.

---

## 1. Overview & Architectural Role

Milestone 10 establishes the first closed-loop learning feedback cycle in EkamNet. It bridges the gap between speculative cognition (generated theories and grounded propositions) and durable world-model adaptation. 

The `ValidationRecord` is the atomic evidence block. The **Belief Update Engine** consumes validation records at Step $t+1$ to update the confidence, uncertainty, and active status of all corresponding lineages created at Step $t$. Stable lineages are gradually graduated into **Lessons**, **Principles**, and eventually **World Model Constraints** using strict mathematical criteria.

```
                    [ Speculative Theories ]
                              │
                              ▼
                   [ Grounded Propositions ]
                              │
                              ▼
                         [ Replay ]
                              │
                              ▼
                     [ Validation Engine ]
                              │
                              ▼
                      [ ValidationRecord ]
                              │
                              ▼
                  [ Belief Dynamics Engine ]
                              │
                              ├──> Updates [Transient Belief States]
                              ├──> Extracts [Stabilized Lessons]
                              ├──> Promotes [Canonical Principles]
                              └──> Axiomatizes [World Model Constraints]
```

---

## 2. Relational Schema Data Models

To ensure strict relational alignment and lineage tracking, the following models are designed:

### 2.1 Level 1: Transient Beliefs (`theory_lineage_states`)
Tracks step-specific confidence and uncertainty values for active theory lineages.
```sql
CREATE TABLE theory_lineage_states (
    id UUID PRIMARY KEY,
    lineage_id VARCHAR(64) NOT NULL REFERENCES theory_lineages(id),
    active_theory_id UUID NOT NULL REFERENCES theories(id),
    confidence DOUBLE PRECISION DEFAULT 0.50,
    uncertainty DOUBLE PRECISION DEFAULT 0.50,
    status VARCHAR(32) NOT NULL, -- 'ACTIVE', 'WEAKENED', 'RETIRED', 'DORMANT'
    last_validation_id UUID REFERENCES validation_records(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 Level 2: Stabilized Lessons (`stabilized_lessons`)
Represents localized, contextual rules verified across a series of steps.
```sql
CREATE TABLE stabilized_lessons (
    id UUID PRIMARY KEY,
    lesson_text TEXT NOT NULL,
    originating_lineage_id VARCHAR(64) REFERENCES theory_lineages(id),
    regime_context VARCHAR(64) NOT NULL,
    evidence_count INT NOT NULL,
    success_rate DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    status VARCHAR(32) NOT NULL, -- 'CANDIDATE', 'ACTIVE', 'RETIRED'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 Level 3: Canonical Principles (`canonical_principles`)
Global, cross-regime rules whitelisted from contradiction.
```sql
CREATE TABLE canonical_principles (
    id UUID PRIMARY KEY,
    originating_lesson_id UUID REFERENCES stabilized_lessons(id),
    formal_invariant TEXT NOT NULL, -- logic constraint string
    tested_regimes JSONB NOT NULL, -- list of subtypes
    generalization_score DOUBLE PRECISION NOT NULL,
    falsification_count INT DEFAULT 0,
    status VARCHAR(32) NOT NULL, -- 'ACTIVE', 'CHALLENGED', 'RETIRED'
    promoted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2.4 Level 4: World Model Constraints (`world_model_constraints`)
Axioms injected directly into LLM prompts to bound future theory generation.
```sql
CREATE TABLE world_model_constraints (
    id UUID PRIMARY KEY,
    originating_principle_id UUID REFERENCES canonical_principles(id),
    constraint_axiom TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    revision_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Mathematical Update Engine

Belief updates occur at the boundary of each simulation day. 

Let $C_t \in [0, 1]$ and $U_t \in [0, 1]$ represent confidence and uncertainty at step $t$.
Let $\eta = 0.15$ be the learning rate, $\gamma = 0.10$ be the uncertainty update rate, and $\lambda = 0.01$ be the decay coefficient.

### 3.1 Validation Record is SUPPORTED
$$C_{t+1} = C_t + \eta \cdot (1 - C_t) \cdot (1 - U_t)$$
$$U_{t+1} = U_t - \gamma \cdot U_t$$
*Confidence increases asymptotically toward 1.0; uncertainty decreases toward 0.0.*

### 3.2 Validation Record is CONTRADICTED
$$C_{t+1} = C_t - \eta \cdot C_t \cdot (1 - U_t)$$
$$U_{t+1} = U_t + \gamma \cdot (1 - U_t)$$
*Confidence drops; uncertainty increases toward 1.0.*

### 3.3 Validation Record is UNTRIGGERED (Decay)
Lineages that remain untested drift back toward the uninformative center:
$$C_{t+1} = C_t - \lambda \cdot (C_t - 0.5)$$
$$U_{t+1} = U_t + \lambda \cdot (1 - U_t)$$

---

## 4. Contradiction Shocks and State Transitions

### 4.1 Transition Pressure
If the daily `ContradictionDetector` outputs a score $S_{\text{contra}} \ge 0.50$, it triggers a transition pressure event, inducing an uncertainty shock:
$$U_{t+1} = \min(1.0, U_{t+1} + \kappa \cdot S_{\text{contra}})$$
where $\kappa = 0.20$ is the shock multiplier.

### 4.2 State Transition Logic
*   **`ACTIVE` $\rightarrow$ `WEAKENED`**: Triggered if $C_t < 0.40$ and $U_t > 0.70$.
*   **`WEAKENED` $\rightarrow$ `RETIRED`**: Triggered if $C_t < 0.30$.
*   **`RETIRED` $\rightarrow$ `ACTIVE` (Revival)**: Occurs only if the retired lineage's regime signature matches the current market context, and the system records a subsequent prediction error reduction of $\ge 20\%$ using the candidate's core features.

---

## 5. Graduation & Promotion Framework

To transition up the cognitive hierarchy, beliefs must cross pre-registered **Evidence Level** gates:

### 5.1 Step 1: Transient Belief $\rightarrow$ Stabilized Lesson (L3 Demonstration)
*   **Gate**: Local empirical verification.
*   **Criteria**:
    *   $N_{\text{validations}} \ge 5$ (on the specific target regime).
    *   Success rate $SR \ge 70\%$ (propositions supported).
    *   Mean confidence $\bar{C} \ge 0.70$.
    *   Mean uncertainty $\bar{U} < 0.40$.

### 5.2 Step 2: Stabilized Lesson $\rightarrow$ Canonical Principle (L4 Validation)
*   **Gate**: Cross-regime generalization testing.
*   **Criteria**:
    *   $N_{\text{validations}} \ge 20$ total.
    *   Validation across $\ge 2$ different regime subtypes.
    *   Falsification rate $< 5\%$ (maximum 1 contradicted outcome).

### 5.3 Step 3: Canonical Principle $\rightarrow$ World Model Constraint (L5 Generalization)
*   **Gate**: Long-term axiomatic survival.
*   **Criteria**:
    *   Survival time $N_{\text{steps}} \ge 100$ steps.
    *   Zero contradiction pressure spikes during active period.
    *   Axiomatization: The principle is translated into a logical constraint and appended to the LLM system prompt context, strictly preventing the generation of future theories that contradict this axiom.

---

## 6. Verification and Auditability Guarantees

1.  **Replay Invariance**: All updates to confidence ($C$) and uncertainty ($U$) are calculated deterministically in python float math. There are no stochastic paths or LLM calls in the update loop, ensuring identical state propagation across replays.
2.  **Audit Trail Ledger**: Updates to lineage states are persisted in `belief_transition_events` database records containing the originating `validation_record_id`, ensuring full scientific provenance.
3.  **Traceable Logic Constraints**: Prompt-injected world model constraints are printed in the final manifests (`replay_manifest.json`), mapping each active prompt axiom to its parent principle ID and evidence records.
