# EKAMNET 10-DAY DIAGNOSTIC REPLAY REPORT
## DP / EKAMNET RESEARCH PROGRAM

This document reports the findings of a bounded, observation-only diagnostic replay of the current repository-native DP/EkamNet system.

---

### 1. Executive Summary

This diagnostic run executed a 10-day RELIANCE replay using the native execution engine. While the pipeline completed successfully and generated all expected report files, a detailed inspection of database states and JSON traces reveals significant architectural divergence between local files (JSON snapshots) and the PostgreSQL persistence layer. Specifically:
- **Relational lineage drift**: PostgreSQL SQL tables record a single static lineage ID for all theories, failing to reflect the parent-child mutations and branch splits tracked in `theory_lineage.json`.
- **Inner object ID collisions**: mutated theories duplicate the `id` and `created_at` fields of their nested `TheoryStructured` sub-objects, violating uniqueness principles.
- **Dormant cognitive memory layers**: relational tables for reflective and strategic memory remain completely empty, and the system relies entirely on experience-only prediction paths, exercising no actual cognitive memory influence on predictions.

**Verdict**: `DIAGNOSTIC_REPLAY_COMPLETED_ROADMAP_RELEVANT_FINDINGS_REQUIRE_REVIEW`

---

### 2. Pre-Execution Record

Before execution, the configuration and environment were recorded as follows:

1. **Exact repository commit**: `08b7a036b26bd6aba6d58769d266a276ca9f6e2f` (branch `main`).
2. **Exact replay command**: `POSTGRES_HOST=127.0.0.1 poetry run python -m market.replay.run --days 10 --restart --reset`
3. **Replay date range**: `2026-06-29` to `2026-07-10` (last 10 trading days in the dataset).
4. **Number of replay days**: 10
5. **Model configuration**: Ollama model `llama3.2` (resolved to local model `llama3.2:latest`).
6. **Random seed/configuration**: Seed `42` set for Ollama client initialization.
7. **Relevant feature flags**: `EKAMNET_STRATEGY_B_SPIKE` = `"1"` (active default), `LLM_AUDIT_ENABLED` = `True`.
8. **Starting database/memory state**: 5 pre-existing entries in postgres relational memory tables.
9. **Clean-state vs Inherits memory**: Clean-state. The `--restart` and `--reset` flags dropped/recreated all database tables and cleared snapshot directories.
10. **Exact files expected to contain replay outputs**:
    - `market/replay/output/report.json` and `report.html`
    - `market/replay/output/reliance/cognitive_decision_trace.json`
    - `market/replay/output/reliance/knowledge_graph.json`
    - Snapshot folder `data/replay_snapshots/reliance/run_20260713_205553/` containing `theory_lineage.json`, `observability_metrics.json`, and sequential day logs `day_0000.json` to `day_0009.json`.

---

### 3. Replay Execution Status

- **Status**: Completed successfully without crashes.
- **Start Time**: 2026-07-13T20:55:53+05:30.
- **Completion Time**: 2026-07-13T21:10:47+05:30.
- **Failures/Errors Intercepted**: NSE API returned 503 errors during initial delivery data fetch. The pipeline handled this gracefully by falling back to simulated features generated in Stage 2.

---

### 4. Lifecycle Reconstruction

Based on the artifacts generated, the EkamNet cognitive loop stages were analyzed:

| Stage | Executed? | Artifact/Event Count | Evidence in Repository | Provenance Reconstructable? |
| :--- | :--- | :--- | :--- | :--- |
| **Experience** | Yes | 4 JSON files | `data/replay_snapshots/reliance/run_20260713_205553/experiences/` | **Partially**. Only lineage-root experiences are created as JSON files; they are completely absent from relational tables. |
| **Formation** | Yes | 10 abstractions | SQL `abstractions` table (10 rows); `day_0000.json` to `day_0009.json` `"abstraction"` field. | **Yes**. `source_observation_id` links the abstraction to the source observation record in PostgreSQL. |
| **Compilation** | Yes | 10 theories | SQL `theories` table (10 rows); `theory_lineage.json` graph nodes. | **Partially**. The Pydantic object `Theory` has a randomly generated `lineage_id` in SQL, breaking mapping to the real lineage tree in JSON. |
| **Evidence** | Yes | 10 validations | SQL `validations` table (10 rows); `prediction_results` (9 rows). | **Yes**. `validations.theory_id` and `prediction_probes.theory_id` correctly reference `theories.id`. |
| **Decision** | Yes | 10 decisions | `decision_journal.json` (10 rows); `paper_trade_log.csv`. | **Yes**. Mapped step-by-step in local files. |
| **Memory** | No | 0 rows | SQL `reflective_memory_states` and `strategic_memory` are empty. | **No**. Persistence is not operationalized. |
| **Later Retrieval / Influence** | Partially | 29 retrieval events | `cognitive_decision_trace.json` `"memory_retrieved"` list. | **No**. Memories were retrieved but had **zero downstream influence** (0 guided predictions). |

---

### 5. Boundary Diagnostic

1. **Theories generated**: 10.
2. **Reached compilation**: 10 (successfully instantiated as Pydantic objects and written to SQL).
3. **Failed before/during compilation**: 0.
4. **Fields in generated `TheoryStructured`**: `mechanism`, `claim`, `if_branch`, `else_branch`, `unless`, `falsified_if`, `forbidden_state`, `mechanism_components`, `falsification_conditions`, `reuse_decision`, and Strategy B fields (`trigger_definition`, `target_definition`, `scope_definition`, `expected_direction`, `contradiction_definition`, `mechanism_type`, `causal_direction`, `driver`, `mediator_or_process`, `target_effect`).
5. **Fields surviving in compiled propositions**: In PostgreSQL, the `summary_structured` text column stores the complete serialized `TheoryStructured` JSON, meaning all fields technically survive. However, in `prediction_probes`, only the `direction` and `confidence` fields are extracted and linked to `theories.id`.
6. **P1/P2/P5 violations**:
    - **P1/P5 Identity Collision**: Mutated child theories generated in the `REVISE` and `REINFORCE` paths of the replay engine copy the parent `TheoryStructured` sub-object in-place. The child does not regenerate a new `id` or `created_at` for the inner Pydantic object, resulting in duplicate structured identifiers (e.g. ID `"5cb3bc75-f0b9-4883-928e-0736d01c715e"` duplicated across days 1–9) in the SQL database.

---

### 6. Plurality Diagnostic

1. **Originating experiences producing multiple candidates**: 0.
2. **Generation mechanism**: Sibling generation code exists (`TheoryGenerationFlow.process_multiple`), but it is `CODE_PATH_NOT_EXECUTED_IN_THIS_REPLAY` because the replay engine calls only `process` (single candidate path).
3. **Sibling relationships reconstructable**: No.
4. **`alternative_group_id` presence**: Present in `Theory` model but remains `null` in all database rows and JSON snapshots.
5. **Observable competing explanations in evidence evaluation**: None.

---

### 7. Recovery / Reentry Opportunity Diagnostic

- **Rejected beliefs/propositions**: 0 in lineage graph. (1 `"REJECTED"` flag exists on step 0 in raw LLM JSON output, but was not registered as a state transition).
- **Deferred beliefs/propositions**: 0.
- **Later relevance/reconsideration**: Not attempted.
- **Verdict**: `NO_REENTRY_EVIDENCE_AVAILABLE`. (No reentry or recovery mechanism was executed or attempted during the 10-day run).

---

### 8. Memory Influence Diagnostic

1. **Memory retrieval events**: 10 (one for each trading day).
2. **Successful retrievals**: 29 records retrieved across the 10-day run (Step 0: 0, Step 1: 1, Step 2: 2, Step 3: 2, Step 4: 3, Step 5: 3, Step 6: 4, Step 7: 4, Step 8: 5, Step 9: 5).
3. **Contents of retrieved memory**: Local dictionaries containing `date`, `similarity`, and `actual_direction`.
4. **Causal downstream influence**: **None** (`MEMORY_RETRIEVED` but NOT `MEMORY_CAUSALLY_CHANGED_BEHAVIOR`). The replay report lists `"Knowledge Guided Predictions: 0"` and `"Experience Only Predictions: 10"`. No active principles or world model constraints were ever formulated or applied to guide predictions; hence, memory had zero causal impact on the predictions or decisions.

---

### 9. Provenance Diagnostic

Three representative lifecycle chains were tracked:

#### Chain 1: Step 0 (2026-06-29)
* **Experience ID**: None (JSON file `exp_bc43fedf5a8669e0_2026-06-29.json` exists in snapshots but is not represented in the database).
* **Theory ID**: `ef288966-78c9-4e11-b4d6-7334af61a325`.
* **Lineage ID**: Mismatch. SQL records `7c039bc0-3c76-46d2-bd4b-5692252341e2`, while local JSON records `bc43fedf5a8669e0`.
* **Proposition/Candidate ID**: Broken link. `theory_summary_structured` is `null` on step 0.
* **Evidence Record**: SQL `validations` ID `9815d73d-f403-44c8-8cb0-48d0c44c62f9`.
* **Prediction/Decision**: SQL `prediction_probes` ID 1 (`direction = lower`, `confidence = 0.55`).
* **Outcome**: SQL `prediction_results` ID 1 (`actual_direction = lower`, `direction_score = 1.0`).
* **Belief/Memory Record**: Broken link. SQL `reflective_memory_states` has 0 rows.
* **Later Retrieval**: Retrieved at Step 1, but with zero downstream cognitive effect.

#### Chain 2: Step 1 (2026-06-30)
* **Experience ID**: None.
* **Theory ID**: `c42b98d3-e0ad-494e-b410-bd52b6747ec6`.
* **Lineage ID**: Mismatch. SQL records `7c039bc0-3c76-46d2-bd4b-5692252341e2`, local JSON records `bc43fedf5a8669e0`.
* **Proposition/Candidate ID**: `"5cb3bc75-f0b9-4883-928e-0736d01c715e"`.
* **Evidence Record**: SQL `validations` ID `66fd7b09-5fce-42b0-91a3-be9b3c19c8d1`.
* **Prediction/Decision**: SQL `prediction_probes` ID 2 (`direction = lower`, `confidence = 0.615`).
* **Outcome**: SQL `prediction_results` ID 2 (`actual_direction = higher`, `direction_score = 0.0`).
* **Belief/Memory Record**: Broken link. SQL `reflective_memory_states` has 0 rows.

#### Chain 3: Step 2 (2026-07-01)
* **Experience ID**: None (JSON file `exp_825f24501c94113e_2026-07-01.json` exists).
* **Theory ID**: `0a4d6ba1-4e96-4471-8b4a-2389f530d08b`.
* **Lineage ID**: Mismatch. SQL records `7c039bc0-3c76-46d2-bd4b-5692252341e2`, local JSON records `825f24501c94113e`.
* **Proposition/Candidate ID**: Broken link due to ID collision. Inner structured object has duplicate ID `"5cb3bc75-f0b9-4883-928e-0736d01c715e"` copied from step 1.
* **Evidence Record**: SQL `validations` ID `5a6f4410-3213-40a5-82ee-a2745da8a211`.
* **Prediction/Decision**: SQL `prediction_probes` ID 3 (`direction = higher`, `confidence = 0.46`).
* **Outcome**: SQL `prediction_results` ID 3 (`actual_direction = range_bound`, `direction_score = 0.0`).
* **Belief/Memory Record**: Broken link (0 rows in SQL).

---

### 10. Existing Replay Metrics

`DESCRIPTIVE_REPLAY_METRIC_ONLY`

- **Paper Trading Performance**:
  - Total Return: `-0.37%`
  - Sharpe Ratio: `-10.17`
  - Max Drawdown: `0.43%`
  - Final Capital: `₹996,292.59`
- **Decision Intelligence**:
  - Directional Accuracy: `10.00%`
  - Commitment Accuracy: `12.50%`
  - Executed / Skipped Decisions: `8 / 2`
  - Decision Stability: `0.8605`
- **Ontology Compliance**:
  - Theory / Mechanism Components Valid: `0.0%`
  - Unknown Taxonomy Values: `SECTOR_ZSCORE`
- **Knowledge Formation**:
  - Validated Principles / Mechanisms Discovered: `0 / 0`
  - Compression Ratio: `10->10->0->0->0`

---

### 11. Surprises and Contradictions

1. **SQL vs. JSON Lineage Mismatch**: The lineage tracker properly evolves lineages in local JSON files (tracking merges, continuation, mutations), but `replay_engine.py` never updates the `Theory` object's `lineage_id` with `lineage_id_val`. As a result, all SQL theories are saved with the initial random lineage ID (`7c039bc0-3c76-46d2-bd4b-5692252341e2`), making PostgreSQL relational lineage queries useless.
2. **Inner Model ID Collisions**: Deep-copying `prior_theory` in `REVISE` and `REINFORCE` paths copies the inner `summary_structured` object without resetting its `id` and `created_at` fields. This creates database rows for distinct theories that share identical structured IDs and timestamps.
3. **Empty Memory and Strategy Tables**: Relational database tables `reflective_memory_states`, `strategic_memory`, and `market_observations` remain completely empty, indicating these modules are stubs or bypassed in the current execution flow.
4. **Total Default to Experience-Only Path**: Although regime memories are retrieved and similarity metrics are computed, no active principles or world models are created, defaulted to experience-only predictions across all 10 trading days.
5. **Ontology Taxonomies Out of Sync**: The system reported `0%` valid components because the LLM generated values (like `SECTOR_ZSCORE`) that were flagged as invalid against `OntologyRegistry` constraints.

---

### 12. Evidence Limitations

- The replay was restricted to a 10-day period. This is insufficient to observe long-term knowledge consolidation, maturation, or principle retirement.
- Fallback NSE Fetcher logic was triggered due to live API 503 response codes, substituting raw delivery values with simulated overlays.
- A single LLM model (`llama3.2`) was tested, which may exhibit model-specific parser quirks.

---

### 13. Questions This Replay Answers

* **What does the current lifecycle do?** It executes raw observation ingestion, LLM abstraction generation, LLM theory generation/revision, prediction generation, validation/invalidation, and decision logging.
* **Is lineage tracked in SQL?** No. SQL lineage IDs are static and corrupted due to missing propagation.
* **Are memories retrieved?** Yes, similarity matching is calculated and retrieved, but it does not feed forward into prediction rules.

---

### 14. Questions This Replay Cannot Answer

* Does the system actually learn over a 100-day or 1-year window?
* Does plurality generation (`process_multiple`) produce coherent competing theories when triggered under different runner configs?
* Does postgres recovery/reentry work when a deferred candidate is revived?

---

### 15. Recommended Implications for Current Roadmap

1. **Fix Lineage ID Propagation**: Modify `replay_engine.py` to assign the computed `lineage_id_val` to `theory.lineage_id` before persistence.
2. **Correct Inner ID Generation**: Ensure that deep-copying a theory object for revision/mutation explicitly resets `theory.summary_structured.id` and updates its `created_at` field.
3. **Operationalize SQL Memory Layer**: Connect the relational database models for `reflective_memory_states` and `strategic_memory` to the active query pathway so they are populated and used.
4. **Reconcile Ontology Constraints**: Update `OntologyRegistry` to allow valid indicators (e.g., `SECTOR_ZSCORE`) to prevent 0% compliance metrics.

---

## Verdict
`DIAGNOSTIC_REPLAY_COMPLETED_ROADMAP_RELEVANT_FINDINGS_REQUIRE_REVIEW`
