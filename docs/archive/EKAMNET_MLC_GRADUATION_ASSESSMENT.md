# EKAMNET MLC SCIENTIFIC GRADUATION ASSESSMENT
**EkamNet Research Program | Minimal Learning Cycle (MLC) Evaluation**  
*Document Status: CONFIRMED READ-ONLY AUDIT*

---

## Executive Summary

This graduation assessment evaluates whether the **Minimal Learning Cycle (MLC)** framework is scientifically mature enough to graduate from its isolated experimental harness into the production `market.replay` loop. 

Based on repository evidence, the MLC has successfully demonstrated key logical capabilities (including structured belief transitions, prospective validation, and candidate competition) inside a synthetic sandbox. However, the framework's operational grammar is currently hardcoded for a binary synthetic world (limiting trigger inputs to `[0, 1]` and target outcomes to `["VAL_A", "VAL_B"]`), making it syntactically incapable of representing or processing real-world financial variables. 

Furthermore, the scientific completion closures for Milestones 5, 6, and 7 remain `UNVERIFIED` because the Minimum Meaningful Effect (MME) thresholds were left undefined (`None`), and trigger pruning under context-shifts (Family B) resulted in a catastrophic collapse in selection accuracy (from 76.92% down to 0.0%) due to negative memory overgeneralization. 

Consequently, the final scientific verdict is:
`MLC_NOT_READY_FOR_GRADUATION`

Graduation requires expanding the proposition grammar to support real financial attributes, formally pre-registering MME thresholds, and implementing safeguards against negative memory overgeneralization in dynamic context environments.

---

## Original Scientific Intent

Reconstructing the historical files (specifically [EKAMNET_PROGRAM_STATE.md](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_PROGRAM_STATE.md) and [EKAMNET_ARCHITECTURE_TO_REPLAY_INTEGRATION_FORENSIC_AUDIT.md](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_ARCHITECTURE_TO_REPLAY_INTEGRATION_FORENSIC_AUDIT.md)):

### 1. Why was the MLC created?
The MLC was created to study and validate longitudinal, reflective learning in a controlled, low-noise environment before introducing the complexity of real-world asset trading data. According to the Program North Star, the objective was to:
> "Build and scientifically validate an EkamNet v0.1 in which past epistemic experience causally changes future cognitive behavior." ([EKAMNET_PROGRAM_STATE.md:L4](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_PROGRAM_STATE.md#L4))

### 2. What hypotheses was it intended to validate?
The MLC aimed to validate five primary hypotheses (H1 to H5):
* **H1 (Lifecycle Fidelity)**: "Did MLC v0.1 execute the intended epistemic lifecycle without violating architectural validity gates?" ([mlc_v0_1_scientific_verdict_protocol.md:L7-L8](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/artifacts/experiments/mlc_v0_1/run_20260710_100104_d08f2b85/mlc_v0_1_scientific_verdict_protocol.md#L7-L8))
* **H2 (Above-Random Decision Value)**: "Does MLC v0.1 provide decision value above the matched random baseline?" ([mlc_v0_1_scientific_verdict_protocol.md:L13-L14](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/artifacts/experiments/mlc_v0_1/run_20260710_100104_d08f2b85/mlc_v0_1_scientific_verdict_protocol.md#L13-L14))
* **H3 (Prospective Accuracy Value)**: "Does prospective validation improve decision accuracy over the matched retrospective-only B2 ablation?" ([mlc_v0_1_scientific_verdict_protocol.md:L18-L20](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/artifacts/experiments/mlc_v0_1/run_20260710_100104_d08f2b85/mlc_v0_1_scientific_verdict_protocol.md#L18-L20))
* **H4 (Safety Value)**: "Does prospective validation reduce catastrophic false admission relative to B2?" ([mlc_v0_1_scientific_verdict_protocol.md:L23-L24](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/artifacts/experiments/mlc_v0_1/run_20260710_100104_d08f2b85/mlc_v0_1_scientific_verdict_protocol.md#L23-L24))
* **H5 (Defer Calibration)**: "Does MLC correctly identify propositions that should remain deferred?" ([mlc_v0_1_scientific_verdict_protocol.md:L31-L32](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/artifacts/experiments/mlc_v0_1/run_20260710_100104_d08f2b85/mlc_v0_1_scientific_verdict_protocol.md#L31-L32))

### 3. Which scientific risks justified isolating it from replay?
The isolation was justified by three key risks:
* **The danger of negative memory overgeneralization**: In context-shifting environments (Family B), enabling trigger pruning caused the selection rate of true causal candidates to collapse to 0.0% ([EKAMNET_PROGRAM_STATE.md:L102](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_PROGRAM_STATE.md#L102)). 
* **Selection-risk / Winner's Curse**: The risk of false winner selection under high variance, where prospective validation safeguards had to be calibrated before exposure to noisy financial signals.
* **Canonical state drift and inference inflation**: Preventing the deployment of architectures before their underlying mathematical and empirical evidence was established.

### 4. Which milestones does it support?
* **Milestone 5**: Epistemic Selection & Candidate Competition.
* **Milestone 6**: Longitudinal Belief Memory and State Transitions.
* **Milestone 7**: Closed-loop Causal Learning (pruning and feedback).

---

## Capability Assessment Matrix

Based on direct source code audit of [flows/minimal_learning_cycle/](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/):

| Capability | Implemented | Tested | Scientifically Validated | Production Ready | Evidence / Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Theory $\rightarrow$ Proposition compilation** | **Yes** | **Yes** | **Synthetic Only** | **No** | Defined in [experiment.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/experiment.py) and [pilot.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/pilot.py). Only generates mock propositions. |
| **Proposition schema** | **Yes** | **Yes** | **Synthetic Only** | **No** | `PropositionSchema` defined in [schemas.py:L61](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/schemas.py#L61). |
| **Closed Operational Grammar** | **Yes** | **Yes** | **Synthetic Only** | **No** | Checked in [schemas.py:L82-L138](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/schemas.py#L82-L138). Restricts triggers and outcomes to binary state values. |
| **Trigger extraction** | **Yes** | **Yes** | **Synthetic Only** | **No** | Parses `trigger_definition` fields restricted to `[0, 1]` values in [schemas.py:L94](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/schemas.py#L94). |
| **Target extraction** | **Yes** | **Yes** | **Synthetic Only** | **No** | Parses `target_definition` fields restricted to `"VAL_A"` or `"VAL_B"` outcomes in [schemas.py:L110](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/schemas.py#L110). |
| **Scope extraction** | **Yes** | **Yes** | **Synthetic Only** | **No** | Parses `scope_definition` arrays checking binary list variables in [schemas.py:L125](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/schemas.py#L125). |
| **Competition framework** | **Yes** | **Yes** | **Synthetic Only** | **No** | `MLCCompetitionEngine` comparing candidates on complexity, lift, and compliance in [competition.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/competition.py). |
| **Belief memory** | **Yes** | **Yes** | **Synthetic Only** | **No** | `MLCBeliefMemory` managing in-memory active and retired states in [belief_memory.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/belief_memory.py). |
| **Proposition lifecycle** | **Yes** | **Yes** | **Synthetic Only** | **No** | States like `ADMITTED_BELIEF`, `WEAKENED_BELIEF` defined in [schemas.py:L5-L17](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/schemas.py#L5-L17). |
| **Proposition retirement** | **Yes** | **Yes** | **Synthetic Only** | **No** | Retires beliefs based on contradiction counts in [belief_memory.py:L88](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/belief_memory.py#L88). |
| **Proposition revision** | **Yes** | **Yes** | **Synthetic Only** | **No** | Mutates trigger parameters of rejected propositions to find valid parameters in [experiment.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/experiment.py). |
| **P1 Gate (Isolation)** | **No** | **Yes** | **No** | **No** | Bypassed; hardcoded to `PASS` in [verify_scientific_closures.py:L16](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py#L16). |
| **P2 Gate (Causal Necessity)** | **No** | **Yes** | **No** | **No** | Bypassed; hardcoded to `PASS` in [verify_scientific_closures.py:L17](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py#L17). |
| **P3 Gate (Mechanism Strength)** | **No** | **Yes** | **No** | **No** | Bypassed; hardcoded to `PASS` in [verify_scientific_closures.py:L18](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py#L18). |
| **P4 Gate (Resource Contamination)** | **No** | **Yes** | **No** | **No** | Bypassed; hardcoded to `PASS` in [verify_scientific_closures.py:L20](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py#L20). |
| **P5 Gate (Safeguard Benefit)** | **No** | **Yes** | **No** | **No** | Bypassed; hardcoded to `PASS` in [verify_scientific_closures.py:L21](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py#L21). |
| **P6 Gate (Safeguard Cost)** | **No** | **Yes** | **No** | **No** | Bypassed; hardcoded to `PASS` in [verify_scientific_closures.py:L22](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py#L22). |

---

## Scientific Evidence Review

### 1. Demonstrated (In Production Replay)
* **Theory lineage tracking**: Proved to trace parent-child mutations and generate correct lineages in Postgres and `theory_lineage.json`.
* **Structured identity preservation**: Checked under the revised mutation path, correctly regenerating nested structured IDs.
* **Ontology compliance**: Validated concept tags and relation types against the taxonomy during backtest runs.

### 2. Partially Demonstrated (In isolated experiments)
* **Belief transitions (Milestone 6)**: Verified that ordered sequences of evidence events move belief records from `ADMITTED` to `WEAKENED` and `RETIRED` states, conforming to transition invariants.
* **Prospective validation (Milestone 5)**: Candidate selection with retrospective validation lift was run on seeds 51-100, showing a benefit in rejecting some confounding candidates.

### 3. Synthetic Only (Restricted to MLC sandbox)
* **Theory $\rightarrow$ Proposition compilation**: Only executed with synthetic inputs, where theory outputs are compiled into binary triggers and outcomes.
* **Closed Operational Grammar**: Verified only against the binary operators and values of [schemas.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/schemas.py#L61).
* **Causal learning loop / trigger pruning (Milestone 7)**: Run on seeds 151-350 using simulated worlds. Demonstrated a +53.85% lift in true causal selection for stable environments (Family A), but a -76.92% collapse under context-shifts (Family B) due to negative memory overgeneralization.

### 4. Untested / Unknown
* **Deferred candidate reentry**: The logic for re-admitting a previously deferred proposition under new supportive evidence is absent and remains un-implemented ([EKAMNET_ARCHITECTURE_TO_REPLAY_INTEGRATION_FORENSIC_AUDIT.md:L86](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_ARCHITECTURE_TO_REPLAY_INTEGRATION_FORENSIC_AUDIT.md#L86)).
* **Real-world causal learning performance**: How the learning loop behaves in noisy market environments remains completely unknown.

---

## Replay Gap Analysis

If the production `market.replay` loop were to adopt these MLC capabilities, the theoretical improvements and their scientific justifications are analyzed below:

### 1. Fewer False Propositions / Candidates
* **Adopted MLC Capability**: `MLCCompetitionEngine` & Prospective Validation.
* **Expected Improvement**: Reduced false-admission of confounding theories that show short-term correlation but lack predictive strength.
* **Replay Justification**: Under volatile market environments, selecting only the "winner" of a sibling group based on a retrospective window should filter out short-term noise. However, the synthetic baseline cost showed it also deferred weak true causal signals, meaning it may reduce overall prediction activity (a trade-off of precision vs. recall).

### 2. Better Lesson Quality & Principle Stability
* **Adopted MLC Capability**: Longitudinal Belief Memory (`MLCBeliefMemory`).
* **Expected Improvement**: Lessons and principles would be formed from *admitted beliefs* rather than raw, unvalidated experiences.
* **Replay Justification**: Currently, lessons are extracted from experiences using raw validation counts. If it integrated belief memory, lessons would only form when a proposition passes its prospective validation gate and achieves `ADMITTED_BELIEF` status. This would prevent volatile, transient correlations from polluting the world model, improving principle stability.

### 3. Reduced Contradiction Debt
* **Adopted MLC Capability**: Closed-loop memory feedback (trigger-field pruning).
* **Expected Improvement**: Skipping the generation of theories whose underlying triggers have already been falsified and retired in belief memory.
* **Replay Justification**: This should save LLM token usage and prevent the creation of repetitive, contradicted theories (reducing contradiction debt). But if context-shifts occur (like Family B), it runs the risk of completely shutting down correct predictions.

---

## Graduation Criteria

To justify integrating the MLC into the production replay loop, the system must meet these evidence-based gates:

### Gate 1: Operational Grammar Generalization
* **Threshold**: The `PropositionSchema` must support continuous, numeric, and text-based values matching actual market features (e.g., net flows, sector Z-scores) rather than hardcoded binary variables (`[0, 1]` and `"VAL_A"`/`"VAL_B"`).
* **Verification Method**: Pass 100% of schema validation checks on a standard 10-day market feature set.

### Gate 2: Pre-Registered Minimum Meaningful Effect (MME)
* **Threshold**: The claims in [verify_scientific_closures.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py) must be updated with non-null MMEs based on synthetic baseline variances.
* **Verification Method**: `verify_scientific_closures.py` must run and successfully output `CLAIM_SUPPORTED` for all evaluated closures, without raising `ValueError` or falling back to hardcoded `PASS` overrides.

### Gate 3: Context-Shift Safeguard (Family B Resilience)
* **Threshold**: Causal selection rate under Family B context-shifts must not fall below a baseline rate (e.g., must be $\ge 20\%$, compared to the current 0.0% collapse). This requires implementing context-aware trigger pruning that distinguishes between stable regimes and regime shifts.
* **Verification Method**: Evaluate on seeds 151-350 with learning enabled, achieving positive lift on Family A without collapsing Family B to zero.

---

## Counterfactual Assessment

### Scenario A: Replay is Left Unchanged
If the replay pipeline does not adopt the MLC, the following scientific capabilities remain permanently impossible:
* **True Epistemic Learning**: The system cannot perform true continuous learning. It will generate the same falsified theories repeatedly when similar regime conditions recur because it lacks a persistent negative memory to prune failed triggers.
* **Longitudinal Belief Evolvability**: The database tables `reflective_memory_states` and `strategic_memory` will remain permanently empty, and the world model will never build upon structured, validated beliefs.

### Scenario B: Replay Adopts the MLC
If the replay pipeline successfully integrates the MLC, the following new scientific experiments become possible:
* **Regime Reentry Experiments**: Testing if a previously retired or deferred trigger-field proposition can be revived when regime dynamics return to the baseline state.
* **Epistemic vs. Experience Trading Comparisons**: Comparing the capital returns of a trader guided strictly by *admitted longitudinal principles* against a trader guided by *immediate experience metrics*.
* **Safeguard Calibration Under Market Noise**: Finding the optimal mathematical balance between false-admission safeguards and true causal signal detection on live market time-series.

---

## Risk Assessment (Argument Against Integration Today)

Integrating the MLC today introduces significant scientific and operational risks:
1. **Semantic Incompatibility**: The current `PropositionSchema` will reject any real-world market indicator generated by `market.replay`. Attempting integration would break the replay execution loop immediately.
2. **Unvalidated gates & Claim Inflation**: The P1–P6 validators are completely unverified on real data. Merging them into production now would create a false impression of scientific rigor (claim inflation) while hiding the fact that the underlying metrics are not validated.
3. **Negative Memory Overgeneralization**: In volatile financial markets, context shifts are frequent. Integrating global trigger pruning without context-aware safeguards would cause the system to lock up and defer all predictions (precision is high, but recall collapses to zero), destroying trading returns.
4. **Replay Instability**: Introducing complex, unvalidated state transitions and in-memory belief memory would make debugging database-backed replication runs extremely difficult.

These risks remain high and mathematically evidenced by the Family B collapse.

---

## Graduation Recommendation

```
MLC_REQUIRES_ADDITIONAL_EXPERIMENTS
```

### Justification
The Minimal Learning Cycle framework has successfully demonstrated the logic of longitudinal belief transitions and prospective validation. However, it is not ready for production because its operational grammar is confined to a synthetic binary sandbox, and its causal learning loop collapses under context shifts. Additional experiments are required to generalize the grammar to real market attributes and to develop context-aware safeguards against negative memory overgeneralization.

---

## Next Scientific Milestone

To prepare the MLC for a future controlled pilot, the research program should prioritize:

### 1. Generalizing the Proposition Grammar
Expand `PropositionSchema.validate` to support continuous variables and a wider dictionary of operators (e.g., `>`, `<`, `in`) to allow real indicators (such as `fii_net` or `delivery_pct`) to be compiled as valid propositions.

### 2. Pre-Registering MME Values
Analyze the variance of the baseline run results to define explicit Minimum Meaningful Effect (MME) thresholds, ensuring that `verify_scientific_closures.py` can evaluate claim consistency without hardcoded gate overrides.

### 3. Success & Rollback Criteria for the Pilot
* **Success**: The integrated loop runs a 10-day backtest, compiling at least 5 real market propositions, validating them against incoming market returns, and achieving a $\ge 15\%$ reduction in false admissions without collapsing the total prediction count by more than $20\%$.
* **Rollback**: If the prediction rate collapses to 0.0% (total deferral), or if database primary key collisions occur on re-admission states, the system must automatically roll back to the `v3.0PersistentReflective` single-candidate theory pipeline.
