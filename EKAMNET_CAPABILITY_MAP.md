# EKAMNET CAPABILITY MAP

This capability map defines the current state of the research program, separating architectural design from empirical validation, as mapped onto the EkamNet Evidence Ladder.

---

## Capability Status Ledger

| Capability | Architectural Capability | Experimentally Demonstrated Capability | Evidence Level | Known Risks | Current Blocker | Next Justified Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Observation** | Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | None | None | None |
| **Experience** | Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | None | None | None |
| **Pattern** | Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | None | None | None |
| **Mechanism** | Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | None | None | None |
| **Theory Formation**| Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | LLM non-determinism | None | None |
| **Formation Handoff**| Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | None | None | None |
| **Proposition** | Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | Binary schema limits | None | Validate in S4-E0 |
| **Compilation** | Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | Strict compiler gates | None | Validate in S4-E0 |
| **Readiness** | Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | Early-defer loops | None | Validate in S4-E0 |
| **Evidence** | Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | None | None | Validate in S4-E0 |
| **Measurement** | Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | None | None | Validate in S4-E0 |
| **Prospective Validation**| Implemented (Active)| Designed (Not Demonstrated)| `L2 (Verified)` | DGP non-stationarity | None | Validate in S4-E0 |
| **Epistemic Plurality**| Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | Starvation/collapse | None | Validate in plurality runs |
| **Selection / Comparison**| Implemented (Active)| Implemented & Observed | `L3 (Reproduced)` | Winner's Curse | None | None |
| **Belief Evolution**| Implemented (Active)| Implemented & Observed | `L3 (Reproduced)` | Arbitrary mutation | None | None |
| **Lesson Formation**| Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | Insufficient logging | None | Expand logger coverage |
| **Principle Formation**| Implemented (Active)| Designed (Not Demonstrated) | `L2 (Verified)` | None | None | None |
| **Longitudinal Memory**| Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | Memory leakage | None | None |
| **Retrieval** | Implemented (Active) | Implemented & Observed | `L3 (Reproduced)` | Selection bias | None | None |
| **Future Cognition**| Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | None | None | None |
| **Closed Learning Loop**| Implemented (Active) | Designed (Not Demonstrated) | `L2 (Verified)` | Overgeneralization | None | Run Milestone 7 loops |

---

## Program Risk Register

1. **`CANONICAL_STATE_DRIFT_RISK`**: The risk that scientific interpretations become stronger in canonical state files than underlying code and execution evidence supports.
2. **`EVIDENCE_TO_ARCHITECTURE_INFERENCE_RISK`**: The risk of concluding that one architecture option is correct/superior solely because a different option is shown to be strained, without directly testing the proposed option.
3. **`PREMATURE_HUMAN_GATE_RISK`**: The risk of stopping execution for a human decision when the current steering authorization already permits further bounded evidence generation, preventing the completion of an evidence-gathering loop.
