# DP/EKAMNET COGNITIVE ARCHITECTURE v2.0
**EkamNet Research Program | Canonical Architecture Consolidation**  
*Document Status: CANONICAL DESIGN REFERENCE*  

---

## Executive Summary

This document consolidates and formalizes the canonical design reference for the **DP/EkamNet Cognitive Architecture v2.0**. Over the past epochs, various cognitive components (including Candidate F, Replay Integrity Remediation, the Minimal Learning Cycle, and the Theory $\rightarrow$ Proposition boundary) developed along distinct research paths. This synthesis unifies these efforts into a single, cohesive, scientifically grounded reference architecture.

The core design of DP/EkamNet v2.0 establishes a strict compilation boundary between human-like semantic reasoning (Theories) and formal, machine-verifiable operational logic (Propositions). Key subsystems (such as lineage engines, prospective validation gates, and competition models) are organized into a unified, feedback-driven pipeline designed to govern longitudinal learning while preventing negative memory overgeneralization.

---

## Part 1: Architectural Timeline

The evolution of the DP/EkamNet substrate is characterized by four primary architectural epochs:

```
                  ┌───────────────────────────────┐
                  │            EPOCH 1            │
                  │   Direct SQL-Theory Pipeline  │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │           EPOCHS 2-4          │
                  │  Strategy B Sequential Extr.  │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │           EPOCHS 5-7          │
                  │     Minimal Learning Cycle    │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │           EPOCHS 8-9          │
                  │  Integrity & Gov. Remediation │
                  └───────────────────────────────┘
```

### Epoch 1: Direct SQL-Theory Pipeline (Legacy Loop)
* **Pipeline Structure**:  
  `Observation` $\rightarrow$ `Experience` $\rightarrow$ `Theory`
* **Purpose**: Establish an asset-native backtesting simulation that evaluates daily market indicators and prompts the LLM to generate predictive theories directly.
* **Scientific Question**: Can an LLM-driven agent generate directional predictions directly from market indicators and persist daily records?
* **Outcome**: A functional, single-candidate backtest loop that stores raw observation, abstraction, and theory objects in a PostgreSQL database.
* **Surviving Concepts**: Daily ingestion loops, LLM-based single-candidate theory generation, and Postgres persistence backends.

### Epochs 2-4: Strategy B Sequential Extraction
* **Pipeline Structure**:  
  `Observation` $\rightarrow$ `Abstraction` $\rightarrow$ `Strategy B (Call 1/2)` $\rightarrow$ `Theory`
* **Purpose**: Introduce structure to the raw theory prompts, separating reasoning into a 2-stage call (Call 1: extraction of indicators; Call 2: causal claim and mechanism components).
* **Scientific Question**: Does structured sequential extraction reduce semantic claim drift and LLM hallucination?
* **Outcome**: Strategy B passed the pre-registered integration gates with 100.0% schema compliance and semantic preservation.
* **Surviving Concepts**: Call 1 & 2 sequential extraction pipelines, structured mechanism components (`MechanismComponent`), and the `OntologyRegistry` constraint checking.

### Epochs 5-7: Minimal Learning Cycle (MLC) pilots
* **Pipeline Structure**:  
  `Theory` $\rightarrow$ `Proposition Compilation` $\rightarrow$ `Prospective Validation (P1-P6)` $\rightarrow$ `Belief Memory` $\rightarrow$ `Trigger Pruning`
* **Purpose**: Research longitudinal learning, candidate competition, and closed-loop feedback in isolation.
* **Scientific Question**: Can past validation experience dynamically alter future candidate selection via memory-driven feedback?
* **Outcome**: Causal learning loop demonstrated with a +53.85% selection accuracy boost in stable environments (Family A), but collapsed to 0.0% under context shifts (Family B) due to negative memory overgeneralization.
* **Surviving Concepts**: Prospective validation gates, pairwise competition engines (`MLCCompetitionEngine`), belief lifecycles (`ADMITTED`, `WEAKENED`, `RETIRED`), and trigger-field pruning.

### Epochs 8-9: Integrity & Governance Remediation
* **Purpose**: Reconcile and fix discrepancies at the boundary of replay persistence and scientific gate checks.
* **Scientific Question**: Do relational schemas and validators accurately reflect the state of the cognitive pipeline?
* **Outcome**: Relational lineage propagation, nested structured ID unique generation, and `SECTOR_ZSCORE` ontology checking successfully verified and fixed. Automated completion gates were structured but remained scientifically `UNVERIFIED` due to undefined MME thresholds.
* **Surviving Concepts**: Stable UUID generation on theory revisions, lineage graph persistence, and formal claim-consistency checks.

---

## Part 2: Canonical Cognitive Pipeline

The canonical cognitive pipeline representing the unified DP/EkamNet v2.0 architecture operates as follows:

1. **Ingestion**: Daily market price and indicator data are retrieved by the simulation loop.
2. **Abstraction**: Raw metrics are consolidated into semantic representations using the `AbstractionFlow`.
3. **Novelty Routing**: The `NoveltyDetectionGate` evaluates the abstraction against prior active theories.
   * If **`GENERATE`**, a new theory is drafted.
   * If **`REVISE`**, the prior theory's mechanisms are mutated, and nested structured IDs are regenerated.
   * If **`REINFORCE`**, the prior theory and its IDs are preserved.
4. **Lineage Propagation**: The `TheoryLineageEngine` records parent-child relationships and maps the theory to a stable family lineage ID.
5. **Proposition Compilation**: The semantic theory is compiled into a concrete, operational `Proposition` using the Closed Operational Grammar.
6. **Scientific Validation (P1-P6)**: The compiled proposition is passed through the P1–P6 validators to check for isolation, causal necessity, and resource limits.
7. **Candidate Competition**: Multiple propositions under the same `alternative_group_id` compete via the `MLCCompetitionEngine` on complexity, compliance, and prospective validation lift.
8. **Belief Lifecycle**: The selected winner enters `MLCBeliefMemory`, starting as an `ADMITTED_BELIEF` and transitioning to `WEAKENED_BELIEF` or `RETIRED_BELIEF` based on accumulated contradictions.
9. **Lesson Extraction**: Active and closed experiences are analyzed by the `LessonExtractor` to extract general rules.
10. **Principle Formation**: Highly stable mechanisms (`prediction_helped >= 3`) are promoted to formal `Principles`.
11. **World Model Synthesis**: Evolving principles are synthesized by the `WorldModelEngine` into a structured, unified narrative.
12. **Future Reasoning**: Validated belief states, lessons, and world model constraints are injected back as context to guide future LLM theory generation.

---

## Part 3: Component Inventory

| Component | Purpose | Status | Recommendation | Justification (Based on Evidence) |
| :--- | :--- | :--- | :--- | :--- |
| **Replay Engine** | Simulation loop coordinator | Production | **KEEP** | Core harness coordinating historical data feeds. |
| **Theory Gen.** | Semantic reasoning (Call 1/2) | Production | **KEEP** | Essential for generating hypothesis narratives and mechanisms. |
| **Novelty Routing** | Routes decision types | Production | **KEEP** | Correctly drives execution paths (`GENERATE`, `REVISE`, `REINFORCE`). |
| **Candidate F** | Counterfactual baseline reference | Experimental | **KEEP** | Core provenance primitive used to measure learning divergence. |
| **Lineage** | Tracks family histories | Production | **KEEP** | Restored relational lineage fixes map family trajectories correctly. |
| **Ontology** | Validates schema tokens | Production | **KEEP** | Essential for maintaining concept and indicator alignment. |
| **Prop. Compiler** | Converts Theories to Propositions | Experimental | **REPLACE** | Current implementation is synthetically mocked. Needs replacement with an LLM-driven compiler. |
| **Closed Grammar** | Defines proposition parameters | Experimental | **REPLACE** | Currently hardcoded for binary values (`[0, 1]`). Must be replaced with a generalized grammar supporting financial attributes. |
| **Prop. Schema** | Mappings for propositions | Experimental | **KEEP** | Schema fields are structurally complete. |
| **P1 Validator** | Isolation gate | Stub | **REPLACE** | Currently bypassed. Needs integration of real retrospective filters. |
| **P2 Validator** | Causal Necessity gate | Stub | **REPLACE** | Currently bypassed. Needs implementation of causal statistics. |
| **P3 Validator** | Mechanism Strength gate | Stub | **REPLACE** | Currently bypassed. |
| **P4 Validator** | Resource Contamination gate | Stub | **REPLACE** | Currently bypassed. |
| **P5 Validator** | Safeguard Benefit gate | Stub | **REPLACE** | Currently bypassed. |
| **P6 Validator** | Safeguard Cost gate | Stub | **REPLACE** | Currently bypassed. |
| **Competition** | Chooses winner among siblings | Experimental | **KEEP WITH MOD.** | Logical engine is complete, but must be wired to process continuous propositions. |
| **Belief Memory** | Manages proposition lifecycles | Experimental | **KEEP** | State transition logic is robustly tested and structurally complete. |
| **Lesson Extractor** | Generalizes experiences | Production | **KEEP WITH MOD.** | Logical engine is complete, but requires semantic abstraction rather than exact string matching for contradictions. |
| **Principle Engine** | Promotes stable mechanisms | Production | **KEEP** | Invariant discovery logic is robust, though requires more steps to trigger. |
| **World Model** | Cohesive narrative synthesis | Production | **KEEP** | Correctly compiles baseline models; will scale once principles exist. |
| **Reflection** | Computes tension metrics | Production | **KEEP** | Tracks contradiction severity and regime continuity successfully. |
| **Deferred Pool** | Holds candidates for reentry | Future | **REPLACE** | Currently a stub. Needs design of a reentry reevaluation hook. |

---

## Part 4: Candidate F Position

### Architectural Definition
Candidate F is a **provenance-driven cognitive primitive**. It represents a specific, targeted lineage history (`5f33fb88966dd952`) designated to serve as the baseline state in counterfactual experiments.

### permanent Placement
Candidate F lives inside the **Lineage Subsystem** and is managed by `TheoryLineageEngine`. 
* **Role**: It acts as a counterfactual reference anchor. 
* **Mechanism**: By programmatically suppressing its retirement during controlled validation runs, the system can measure downstream routing shifts, prediction divergence, and financial performance deltas against the control baseline. This determines if past experience has a causally measurable impact on cognitive convergence.

---

## Part 5: MLC v1 Concept Inventory

* **Proposition Lifecycle**: **KEEP**. The states (`ADMITTED`, `WEAKENED`, `RETIRED`) and allowed transitions are logically sound and verified by automated tests.
* **Competition Framework**: **KEEP WITH MODIFICATION**. The concept of comparing sibling candidates under a shared group ID to limit selection bias is essential. However, the engine must compare real market propositions instead of synthetic binary tokens.
* **Belief Memory**: **KEEP**. Retaining longitudinal records in `reflective_memory_states` prevents the system from suffering from immediate-term regime amnesia.
* **Binary Grammar**: **RETIRE**. Restricting operators to `==` and values to binary `[0, 1]` or `"VAL_A"` outcomes is incompatible with financial time-series.
* **Trigger Pruning**: **REPLACE**. Static global trigger pruning must be replaced with **context-aware pruning**. Pruning must depend on regime similarity to prevent negative memory overgeneralization during context shifts.
* **Synthetic Schemas**: **RETIRE**. Hardcoded schemas used to validate mock parameters must be graduated to support real feature indicators.

---

## Part 6: Theory $\rightarrow$ Proposition Architecture

The Theory $\rightarrow$ Proposition compilation boundary acts as the gateway between unstructured human-like abstraction and formal, machine-verifiable operational logic.

```
                    ┌────────────────────────────┐
                    │           THEORY           │
                    │ Unstructured LLM Narrative │
                    └──────────────┬─────────────┘
                                   │
                                   ▼ [COMPILATION BOUNDARY]
                    ┌────────────────────────────┐
                    │        PROPOSITION         │
                    │   Strict Machine Schema    │
                    └────────────────────────────┘
```

### 1. Responsibilities
* Parse the semantic claim text of the generated `Theory`.
* Compile the claim into a structured operational proposition conforming to the Generalized Operational Grammar.
* Enforce type constraints and schema compliance.

### 2. Inputs
* `Theory` object containing the `summary`, `thesis`, and unstructured `MechanismComponent` list.
* Current `ObservationEvent` and active `OntologyRegistry` tokens.

### 3. Outputs
* Compiled `Proposition` object containing:
  * `proposition_id`: Unique generated identifier.
  * `trigger_definition`: Grounded market indicator condition (e.g., `delivery_pct > 80`).
  * `target_definition`: Expected market outcome (e.g., `close_direction == 'up'`).
  * `scope_definition`: Applicability filters (e.g., `volatility_state == 'compressed'`).
  * `complexity_cost`: Count of variables and conditional clauses.

### 4. Invariants
* **Claim Identity**: The compiled trigger and target conditions must preserve 100% semantic claim identity with the original theory text (zero hallucination).
* **Deterministic Evaluation**: Given a specific observation day, the trigger condition must evaluate deterministically to `True` or `False`.

### 5. Failure Modes
* **Compilation Rejection**: If the theory text cannot be translated into valid indicators, the compiler outputs `COMPILATION_REJECTED`.
* **Out-of-Vocabulary indicator**: If the LLM generates a trigger condition using indicator tokens not registered in the `OntologyRegistry`, it fails compliance validation.

---

## Part 7: Knowledge Lifecycle

The complete knowledge lifecycle of DP/EkamNet v2.0 represents the flow of information from raw observation to persistent cognitive memory:

```
Observation 
     │  (AbstractionFlow)
     ▼
Experience 
     │  (Novelty Gate & TheoryGen)
     ▼
Theory [Lineage & Ontology validated]
     │  (Compilation Boundary)
     ▼
Proposition [Closed Grammar & Schema checked]
     │  (P1-P6 Validation Gates & Competition Winner)
     ▼
Admitted Belief (reflective_memory_states)
     │  (Validation History: supported vs contradicted)
     ▼
Lesson (LessonExtractor generalizes patterns)
     │  (Invariant Discovery: prediction_helped >= 3)
     ▼
Principle (Stable invariant rule)
     │  (WorldModelEngine synthesis)
     ▼
World Model (System description & constraints)
     │  (Injected context)
     ▼
Future Reasoning (Guides next day's Theory)
```

### Participation of Governance Layers:
* **Contradiction**: Accumulates at the *Belief* stage. When contradictions cross the threshold, the belief transitions to `WEAKENED_BELIEF` and eventually `RETIRED_BELIEF`.
* **Confidence**: Evaluated at the *Theory* stage (e.g., empirical and theoretical confidence scores) and updated dynamically based on validation outcomes.
* **Evidence**: Injected at the *Validation* stage, comparing prediction probes against actual market outcomes to generate attributions.
* **Lineage**: Attaches to the *Theory* stage on creation, ensuring all mutated descendants carry the stable family ID.
* **Ontology**: Enforced at the *Theory* and *Proposition* compilation stages, ensuring indicator and concept tags conform to the registered taxonomy.

---

## Part 8: Deferred Candidate Re-entry (Milestone 8)

### Architectural Placement
Milestone 8 introduces the **Deferred Candidate Pool**, which acts as a staging queue for propositions that showed inconclusive evidence or weak causal strength during prospective validation.

```
                          ┌────────────────────────┐
                          │  Prospective Validator │
                          └───────────┬────────────┘
                                      │
                                      ▼ (Weak/Inconclusive)
                          ┌────────────────────────┐
                          │  Deferred Prop. Pool   │
                          └───────────┬────────────┘
                                      │
                                      ▼ (New Positive Evidence)
                          ┌────────────────────────┐
                          │   Re-entry Evaluator   │
                          └───────────┬────────────┘
                                      │
                                      ▼ (Re-admitted)
                          ┌────────────────────────┐
                          │    Admitted Belief     │
                          └────────────────────────┘
```

* **What becomes deferred?**: Only **Propositions** are deferred. Theories are high-level narratives; lessons and principles are generalizations of already validated beliefs. Deferral is applied strictly to compiled candidate propositions that fail to pass the prospective validation gate due to limited sample sizes or ambiguous causal effects.
* **Interaction with World Model**: Deferred candidates do not participate in the active world model. They remain isolated in the pool to prevent polluting the active system constraints.
* **Interaction with Lineage**: Deferred candidates preserve their original `lineage_id`, ensuring their validation history remains mapped to the correct theory family.
* **Interaction with Competition**: When new positive evidence accumulates in a regime, a re-entry evaluator checks if the deferred candidate can re-enter. Upon re-entry, it competes with active candidates for validation budgets.
* **Interaction with Memory**: Memory updates write historical transitions to `reflective_memory_states`, logging when a proposition shifts from `DEFERRED` to `ADMITTED`.

---

## Part 9: Architecture Diagram

This diagram represents the official reference architecture of the **DP/EkamNet v2.0 Cognitive Loop**:

```
                       ┌─────────────────────────┐
                       │   Raw Market Ingestion  │
                       └────────────┬────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │     AbstractionFlow     │
                       └────────────┬────────────┘
                                    │
                      Regime        ▼
                   ┌──────────> Novelty Routing 
                   │  Analog    (is_novel gate)
                   │  Memory        │
                   │                ├───────────────┬──────────────┐
                   │                ▼               ▼              ▼
                   │            GENERATE         REVISE        REINFORCE
                   │                │               │              │
                   │                └───────┬───────┘              │
                   │                        ▼                      │
                   │              Theory Lineage engine            │
                   │              (propagates stable ID)           │
                   │                        │                      │
                   │                        ▼                      │
                   │               Ontology Validator              │
                   │               (concept tag check)             │
                   │                        │                      │
                   │                        ▼                      │
                   │              Proposition Compiler             │
                   │              (translates to schema)           │
                   │                        │                      │
                   │                        ▼                      │
                   │              Scientific Gates (P1-P6)         │
                   │              (checks bounds & budget)         │
                   │                        │                      │
                   │                        ▼                      │
                   │              MLCCompetitionEngine             │
                   │              (picks winner among siblings)    │
                   │                        │                      │
                   │                        ▼                      │
                   │               MLCBeliefMemory                 │
                   │               (reflective_memory_states)      │
                   │                        │                      │
                   │                        ▼                      │
                   │                LessonExtractor                │
                   │                (extracts lessons)             │
                   │                        │                      │
                   │                        ▼                      │
                   │                 PrincipleEngine               │
                   │                (forms principles)             │
                   │                        │                      │
                   │                        ▼                      │
                   │                WorldModelEngine               │
                   │             (synthesizes narrative)           │
                   │                        │                      │
                   └────────────────────────┴──────────────────────┘
```

---

## Part 10: Scientific Boundaries

To prevent future architectural drift, components are classified by their validation status:

### 1. Validated (Production Ready)
* **Sequential Extraction (Strategy B)**: Verified to compile structured theories with 100% semantic claim identity.
* **Lineage & Identity Engine**: Verified to preserve stable lineage families across SQL and JSON snapshot boundaries.
* **Ontology Registry Checks**: Verified to enforce concept and indicator taxonomy compliance.

### 2. Partially Validated (Harness Proven)
* **Belief Memory Transitions**: Logical transition sequences (`ADMITTED` $\rightarrow$ `WEAKENED` $\rightarrow$ `RETIRED`) verified under ordered evidence events in tests.
* **Pairwise Candidate Competition**: Demonstrated to compare candidates based on prospective validation lift in isolated MLC pilot runs.

### 3. Experimental (Concept Proof Only)
* **Closed Operational Grammar**: Proven only inside a binary mock sandbox; incapable of parsing actual financial indicators.
* **Trigger Pruning Feedback**: Demonstrated in synthetic worlds, but exhibits severe overgeneralization failure modes under context shifts.
* **P1–P6 Completion Gates**: Automated gate structures are defined, but hardcoded to `PASS` in validation scripts due to undefined MME thresholds.

### 4. Future Research (Aspirational)
* **Generalized Proposition Compiler**: LLM-guided parser to translate natural language claims into continuous mathematical indicators.
* **Deferred Candidate Re-entry**: Logic to re-evaluate and admit deferred propositions under fresh evidence.
* **Context-Aware Trigger Pruning**: Safeguards to prevent memory overgeneralization during regime transitions.

---

## Part 11: Future Milestone Roadmap

```
                    ┌───────────────────────────────┐
                    │          MILESTONE 8          │
                    │  Generalized Prop. Compiler   │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │          MILESTONE 9          │
                    │  Context-Aware trigger Pruning│
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │          MILESTONE 10         │
                    │   Deferred Candidate pool     │
                    └───────────────────────────────┘
```

### Milestone 8: Generalized Proposition Compiler
* **Objective**: Graduate the Proposition Compiler from binary mock schemas to a generalized, production-ready parsing engine.
* **Prerequisite**: Validated sequential extraction (Strategy B) and the updated `OntologyRegistry` containing real indicators.
* **Success Criteria**: 100% of generated market theories compile into schemas containing continuous indicator variables and operators.
* **Expected Scientific Contribution**: Establishes the mathematical framework to translate semantic claims into continuous, deterministic machine-verifiable expressions.

### Milestone 9: Context-Aware Trigger Pruning
* **Objective**: Solve the negative memory overgeneralization failure mode observed under context shifts.
* **Prerequisite**: Generalized Proposition Compiler and the active `RegimeMemoryStore`.
* **Success Criteria**: Enabling pruning under context shifts (Family B) achieves a true causal selection rate of $\ge 50\%$, preventing the 0.0% collapse.
* **Expected Scientific Contribution**: Demonstrates that epistemic learning loops can generalize negative experiences selectively based on regime similarity.

### Milestone 10: Deferred Candidate Pool & Re-entry
* **Objective**: Implement the staging pool and re-entry evaluation hooks for deferred candidates.
* **Prerequisite**: Context-Aware Trigger Pruning and generalized belief memory.
* **Success Criteria**: Deferred propositions are successfully re-admitted to the competition loop upon receiving supportive evidence, showing a $\ge 15\%$ accuracy improvement over permanent-deferral baselines.
* **Expected Scientific Contribution**: Validates the reentry pathway for weak or evidence-starved causal signals, completing the longitudinal belief lifecycle.
