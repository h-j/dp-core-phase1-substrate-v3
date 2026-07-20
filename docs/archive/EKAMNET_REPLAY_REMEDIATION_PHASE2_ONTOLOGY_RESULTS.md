# EKAMNET REPLAY INTEGRITY REMEDIATION PHASE 2 RESULTS
## DEFECT 3 ONTOLOGY CONTRACT RECONCILIATION AND COGNITIVE DELTA CHARACTERIZATION
## DP / EKAMNET RESEARCH PROGRAM

---

### 1. Executive Summary

This phase resolved **Defect 3 (Ontology Contract Mismatch)** involving `SECTOR_ZSCORE` by validating its originating observable path, executing matched-state baseline and treatment runs, and mapping the resulting downstream cognitive deltas. 

Under equivalent starting states (0 pre-existing database rows, identical seeds and model configurations), the correction of the ontology registry allowed candidate theories containing `SECTOR_ZSCORE` to survive on the first attempt without validation retry fallbacks. 
* The baseline run had 6 GENERATE decisions vs. 5 in the treatment run (n=10, not a generalizable frequency claim).
* The average contradiction pressure was 0.5491 in baseline vs. 0.1311 in the treatment run (n=10, not a generalizable frequency claim).
* This contract resolution propagated a clear, traceable cognitive divergence that altered downstream trading actions on steps 3, 4, 5, 7, and 9.

---

### 2. Scope and Prohibitions

This implementation was strictly bounded to Defect 3.
* No Candidate F composition experiments were initiated.
* S4-E0 and Milestone 8 work remain untouched.
* P1-P6 scientific validation gates were not altered.
* Full cognitive-behavior preservation is explicitly not claimed, as correcting the ontology contract was expected to (and did) introduce a significant cognitive delta.
* No prompt configurations were modified.

---

### 3. Pre-Implementation Ontology Contract Trace

| Component | File / Function | Accepts SECTOR_ZSCORE? | Generates SECTOR_ZSCORE? | Rejects SECTOR_ZSCORE? | Transforms SECTOR_ZSCORE? | Runtime Consequence | Authoritative Role? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Originating Observable** | `market/replay/run.py` | Yes | Yes | No | No | Numeric feature values calculated and parsed. | Yes (observable source) |
| **Generation Prompt** | `flows/theory_flow/theory_generation_flow.py` | Yes | Yes | No | No | Displays `sector_zscore` as available for use. | No |
| **Extraction Prompt** | `market/replay/replay_engine.py` | Yes | Yes | No | No | Directs LLM to choose from `CORE_CONCEPTS`. | No |
| **TheoryStructured Schema** | `cognition/schemas/theory/theory.py` | Yes | Yes | No | No | String concept tags container. | No |
| **OntologyRegistry** | `cognition/schemas/knowledge/ontology.py` | **No** | No | **Yes** | No | Lacks `SECTOR_ZSCORE` in whitelist. | Yes (contract definer) |
| **Validators** | `flows/theory_flow/theory_generation_flow.py` | **No** | No | **Yes** | No | Throws tag validation failure and triggers retry loop. | Yes (contract validator) |
| **Persistence Path** | `TheoryRepository` | Yes | Yes | No | No | Serialized structured JSON stored in DB. | No |
| **Retrieval Path** | `TheoryRepository` | Yes | Yes | No | No | Relational data reconstituted. | No |
| **REVISE Path** | `replay_engine.py` | Yes | Yes | No | No | Modifies components without validating tags. | No |
| **Contradiction/Evidence** | `ContradictionDetector` | Yes | Yes | No | No | Evaluates observations against component expected behavior. | No |

---

### 4. Authoritative Contract Decision

* **Pre-Implementation Classification**: `ONTOLOGY_REGISTRY_OMISSION_CONFIRMED`
* **Justification**: The prompt correctly lists `sector_zscore` as an available observable variable, but `SECTOR_ZSCORE` is omitted from `OntologyRegistry.CORE_CONCEPTS`. No changes to the prompt templates were required or implemented.

---

### 5. Matched-State Baseline Manifest

```json
{
  "timestamp": "2026-07-14T10:28:48.539218+00:00",
  "commit_hash": "2159672a0063a23f6884dbf5ff67e054ae0e5db6",
  "ollama": {
    "model": "llama3.2",
    "configuration": {
      "temperature": 0.0,
      "seed": 42
    }
  },
  "database": {
    "row_counts": {
      "abstractions": 0,
      "confidence_states": 0,
      "market_observations": 0,
      "market_outcomes": 0,
      "observations": 0,
      "prediction_probes": 0,
      "prediction_results": 0,
      "reflections": 0,
      "reflective_memory_states": 0,
      "strategic_memory": 0,
      "theories": 0,
      "transition_pressure_events": 0,
      "validations": 0
    },
    "is_clean": true
  },
  "lineage_state": {
    "exists": false,
    "path": "/Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/data/replay_snapshots/reliance/theory_lineage.json"
  },
  "input_data": {
    "path": "/Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/data/reliance_daily_3y.csv",
    "md5_checksum": "9d44a48f935e2181ee35826907e3a377"
  },
  "replay_command": "POSTGRES_HOST=127.0.0.1 poetry run python -m market.replay.run --days 10 --restart --reset"
}
```

---

### 6. Baseline 10-Day Replay Results

* **Run ID**: `run_20260714_155858`
* **Final Capital**: `₹995,936.34`
* **Total Return**: `-0.41%`
* **Ontology Compliance**: 22.2% valid (9 checked, 2 valid).
* **Unknown Taxonomy Value**: `RANGE_PERSISTENCE` (generated as a retry fallback when the original `SECTOR_ZSCORE` tag was rejected).

---

### 7. Minimum Defect 3 Implementation

The repair adds `"SECTOR_ZSCORE"` directly to the ontology whitelist:

```diff
--- a/cognition/schemas/knowledge/ontology.py
+++ b/cognition/schemas/knowledge/ontology.py
@@ -68,6 +68,7 @@ class OntologyRegistry:
         "BREAKOUT_VALIDATION",
         "BREAKOUT_FAILURE",
         "DELIVERY_EXHAUSTION",
+        "SECTOR_ZSCORE",
     ]
```

---

### 8. Defect 3 Test Results

| Test Name | Setup | Expected Result | Actual Result | Pass / Fail |
| :--- | :--- | :--- | :--- | :--- |
| **test_generate_contract_consistency** | Check `"SECTOR_ZSCORE"` presence in `CORE_CONCEPTS`. | True | True | **PASS** |
| **test_revise_contract_consistency** | Validate mock component using `"SECTOR_ZSCORE"`. | True | True | **PASS** |
| **test_persistence_retrieval_consistency** | Serialize and deserialize component with `"SECTOR_ZSCORE"`. | Tag is preserved. | Tag is preserved. | **PASS** |
| **test_unknown_value_policy** | Validate `"FAKE_UNSUPPORTED_METRIC_XYZ"`. | Disallowed, tracked in metrics. | Disallowed, tracked. | **PASS** |
| **test_no_unrelated_ontology_expansion** | Verify core concepts count is exactly 11. | 11 core concepts. | 11 core concepts. | **PASS** |
| **test_existing_regression** | Run the complete repository test suite. | All tests pass. | 206 tests passed. | **PASS** |

---

### 9. Matched-State Treatment Manifest

```json
{
  "timestamp": "2026-07-14T11:49:49.403118+00:00",
  "commit_hash": "804dfc881f2ed786ddec754c1851eead70dfa208",
  "ollama": {
    "model": "llama3.2",
    "configuration": {
      "temperature": 0.0,
      "seed": 42
    }
  },
  "database": {
    "row_counts": {
      "abstractions": 0,
      "confidence_states": 0,
      "market_observations": 0,
      "market_outcomes": 0,
      "observations": 0,
      "prediction_probes": 0,
      "prediction_results": 0,
      "reflections": 0,
      "reflective_memory_states": 0,
      "strategic_memory": 0,
      "theories": 0,
      "transition_pressure_events": 0,
      "validations": 0
    },
    "is_clean": true
  },
  "lineage_state": {
    "exists": false,
    "path": "/Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/data/replay_snapshots/reliance/theory_lineage.json"
  },
  "input_data": {
    "path": "/Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/data/reliance_daily_3y.csv",
    "md5_checksum": "9d44a48f935e2181ee35826907e3a377"
  },
  "replay_command": "POSTGRES_HOST=127.0.0.1 poetry run python -m market.replay.run --days 10 --restart --reset"
}
```

---

### 10. Treatment 10-Day Replay Results

* **Run ID**: `run_20260714_171958`
* **Final Capital**: `₹994,003.72`
* **Total Return**: `-0.60%`
* **Ontology Compliance**: 100.0% valid (3 checked, 3 valid).
* **Unknown Taxonomy Value**: `None`

---

### 11. Stepwise Cognitive Delta Comparison

| Step | Date | Base Route | Treat Route | Base Action | Treat Action | Base PnL | Treat PnL | Base Tags | Treat Tags | Delta Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | 2026-06-30 | GENERATE | GENERATE | `hold` | `hold` | 0.00 | 0.00 | `[RANGE_PERSISTENCE...]` | `[SECTOR_ZSCORE...]` | `EXPECTED_DELTA_FROM_CONTRACT_CORRECTION` |
| **1** | 2026-07-01 | GENERATE | GENERATE | `short` | `short` | -857.88 | -857.88 | `[VOLATILITY...]` | `[SECTOR_ZSCORE...]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **2** | 2026-07-02 | REINFORCE | REINFORCE | `long` | `long` | -614.00 | -639.42 | `[LIQUIDITY...]` | `[SECTOR_ZSCORE...]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **3** | 2026-07-03 | REVISE | REVISE | `hold` | `short` | 0.00 | 0.00 | `[LIQUIDITY...]` | `[SECTOR_ZSCORE]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **4** | 2026-07-06 | GENERATE | GENERATE | `hold` | `short` | 0.00 | 0.00 | `[LIQUIDITY...]` | `[]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **5** | 2026-07-07 | GENERATE | GENERATE | `hold` | `long` | 0.00 | -1123.17 | `[CONDITIONAL...]` | `[TREND...]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **6** | 2026-07-08 | GENERATE | GENERATE | `long` | `long` | -1248.36 | -1624.83 | `[CONDITIONAL...]` | `[TREND...]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **7** | 2026-07-09 | REVISE | REVISE | `short` | `hold` | -320.69 | 0.00 | `[MOMENTUM...]` | `[BREAKOUT...]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **8** | 2026-07-10 | REVISE | REVISE | `short` | `short` | -1022.73 | -1316.19 | `[MOMENTUM...]` | `[BREAKOUT...]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |
| **9** | 2026-07-13 | GENERATE | REVISE | `hold` | `long` | 0.00 | -434.79 | `[LIQUIDITY...]` | `[BREAKOUT...]` | `DOWNSTREAM_PROPAGATED_EXPECTED_DELTA` |

---

### 12. Distribution Comparison

* **Ontology Acceptance Frequency**: The acceptance compliance rate was 22.2% valid in the baseline vs. 100.0% valid in the treatment run (n=10, not a generalizable frequency claim).
* **Ontology Rejection Frequency**: The validator rejected tags 7 times in the baseline run vs. 0 times in the treatment run (n=10, not a generalizable frequency claim).
* **Retry Frequency**: The retry loop was triggered 7 times in the baseline run vs. 0 times in the treatment run (n=10, not a generalizable frequency claim).
* **GENERATE count**: 6 in baseline vs. 5 in treatment (n=10, not a generalizable frequency claim).
* **REVISE count**: 3 in baseline vs. 4 in treatment (n=10, not a generalizable frequency claim).
* **REINFORCE count**: 1 in baseline vs. 1 in treatment (n=10, not a generalizable frequency claim).
* **Unique theory count**: 10 in baseline vs. 10 in treatment (n=10, not a generalizable frequency claim).
* **Unique lineage-family count**: 5 in baseline vs. 5 in treatment (n=10, not a generalizable frequency claim).
* **Average contradiction pressure**: The mean contradiction pressure was 0.5491 in baseline vs. 0.1311 in treatment (n=10, not a generalizable frequency claim).
* **Downstream execution distribution**: Baseline actions were 5 hold, 3 short, 2 long vs. Treatment actions of 2 hold, 4 short, 4 long (n=10, not a generalizable frequency claim).

---

### 13. Candidate F Impact Check

* **Classification**: `CANDIDATE_F_INPUT_DISTRIBUTION_CHANGE_ONLY`
* **Justification**: Defect 3 does not alter the execution path or logical schema of the Candidate F pipeline. It shifts the inputs (the accepted active theories pool and resulting contradiction scores) by allowing `SECTOR_ZSCORE` to compile successfully on its first try. 
* **Retirement Invariant**: Reusing the Phase 1 finding, theory retirement is governed exclusively by step counters (`last_seen_step`, `created_at_step`), not datetime fields. Correcting Defect 3 does not modify or introduce any new path into the retirement staleness logic in `TheoryLineageEngine.retire_stale_theories`.

---

### 14. Historical Artifact and Commit Record

* **Files Modified**:
  - `cognition/schemas/knowledge/ontology.py` (added tag `"SECTOR_ZSCORE"`)
  - `bootstrap/replay_integrity_remediation_test.py` (added Defect 3 unit tests A-E)
* **Git Commits**:
  - Commit `9906da7`: `hotfix/ontology-compliance: add SECTOR_ZSCORE to CORE_CONCEPTS`
  - Commit `804dfc8`: `test: add Defect 3 unit tests A-E`
* **Artifact Locations**:
  - Baseline run snapshots: `/Users/hemantj/.gemini/antigravity-ide/brain/b8b7aabc-30e0-440d-87e8-467c4024b9f4/scratch/baseline_run/`
  - Treatment run snapshots: `/Users/hemantj/.gemini/antigravity-ide/brain/b8b7aabc-30e0-440d-87e8-467c4024b9f4/scratch/treatment_run/`

---

### 15. Claim Boundary

* **Claim**: `ONTOLOGY_CONTRACT_CORRECTION_CONFIRMED_WITH_TRACEABLE_EXPECTED_COGNITIVE_DELTA`
* **Interpretation Limits**:
  - The ontology registry defect was successfully demonstrated;
  - The minimum repair was implemented;
  - Matched initial states were established between baseline and treatment;
  - The intervention successfully removed the identified ontology rejection and validation retry path;
  - The resulting cognitive trajectories diverged downstream;
  - The broad trajectory divergence is consistent with the downstream propagation of the contract correction;
  - The exact causal ancestry of every individual downstream delta was not independently established, and we do not claim that every individual downstream delta was independently causally proven.


---

### 16. Final Recommendation

**PHASE2_ACCEPTED_WITH_EXPECTED_COGNITIVE_DELTA**
