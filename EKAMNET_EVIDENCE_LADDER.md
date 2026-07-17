# EKAMNET EVIDENCE LADDER
## DP / EKAMNET RESEARCH PROGRAM

This document establishes the canonical scientific verification ladder for the EkamNet research program. Progression through the ladder ensures that architectural claims are backed by rigorous, repeatable empirical evidence.

---

### 1. Definition of Evidence Levels (L0–L5)

* **L0: Described / Designed**
  * *Definition*: The capability or mechanism is conceptually described in design documentation, settings, or instructions, but no runnable implementation exists in the codebase.
* **L1: Implemented**
  * *Definition*: Code for the capability exists in the repository and runs without syntax errors, but has not undergone formal unit testing or simulation validation.
* **L2: Verified (Unit Tested)**
  * *Definition*: The capability has passing unit tests that validate core invariants and state transitions in isolation, independent of model outputs or longitudinal simulation runs.
* **L3: Demonstrated (Single Run)**
  * *Definition*: The capability has been executed in a full longitudinal simulation or replay run, with logs and database dumps archived, demonstrating operational viability.
* **L4: Validated (Controlled Backtest)**
  * *Definition*: The capability's causal effect is confirmed through controlled, matched-state counterfactual simulations ($k \ge 3$ matched replication pairs) over a backtest period.
* **L5: Generalized**
  * *Definition*: The causal effect is validated across multiple distinct regime classes, datasets, and model seeds with zero falsifications of the core hypothesis.

---

### 2. Promotion Criteria

* **L0 → L1 Promotion**: Merge runnable, syntactically correct code into the package.
* **L1 → L2 Promotion**: Implement unit tests covering state validation and edge cases, achieving a successful passing suite run (`poetry run pytest`).
* **L2 → L3 Promotion**: Complete a 10-day backtest simulation run, saving all snapshots, and generating an HTML/JSON analysis report.
* **L3 → L4 Promotion**: Execute a pre-registered counterfactual experiment runner script that passes all pre-execution isolation checks, dynamically implements the target intervention, and archives all control vs treatment run outputs.
* **L4 → L5 Promotion**: Replicate the counterfactual backtest across 3 different asset datasets or regime classes without triggering stop conditions.

---

### 3. Completed Experiment Mapping

The table below maps all completed experiments to their highest verified evidence level:

| Experiment ID | Experiment Name | Highest Level Achieved | Supporting Artifacts |
| :--- | :--- | :--- | :--- |
| **EX-001** | Candidate F Controlled Counterfactual Experiment | **L4 (Validated)** | [all_results.json](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/data/archive/counterfactual_experiment/all_results.json) |
| **EX-002** | Phase 1 Lineage and Nested ID Remediation | **L3 (Demonstrated)** | [Phase 1 Results](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_REPLAY_REMEDIATION_PHASE1_RESULTS.md) |
| **EX-003** | Phase 2 Registry Contract Remediation | **L3 (Demonstrated)** | [Phase 2 Results](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_REPLAY_REMEDIATION_PHASE2_ONTOLOGY_RESULTS.md) |
