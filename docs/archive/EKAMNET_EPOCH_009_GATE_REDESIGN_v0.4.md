# EKAMNET EPOCH 009 GATE REDESIGN v0.4
**Status**: Refined Design Note Only — Implementation Pending Review & Approval

---

## 1. Rule 6: `CLAIM_CONTRADICTED` for Adequately-Powered Wrong-Direction Results

We introduce an explicit **sixth rule** to differentiate between results that are simply underpowered or null vs. results that actively contradict the claim under adequate statistical power.

### Rule 6 Definition:
If the sample size is adequate ($N \ge N_{\text{required}}$) AND the computed confidence interval (CI) sits entirely on the opposite side of zero from what the claim type asserts, the gate returns:
$$\mathbf{CLAIM\_CONTRADICTED}$$

### Expected CI Bounds for Rule 6:
* **`POSITIVE_IMPROVEMENT`**: The pre-registered MME is positive (e.g., $+0.15$). If $N \ge N_{\text{required}}$ and the computed CI upper bound is $< 0$ (observed difference is significantly negative), returns `CLAIM_CONTRADICTED`.
* **`HARM_DEGRADATION`**: The pre-registered MME is negative (e.g., $-0.20$). If $N \ge N_{\text{required}}$ and the computed CI lower bound is $> 0$ (observed difference is significantly positive), returns `CLAIM_CONTRADICTED`.

### Logic Verification:
No other logic path in the v0.3 design outputs `CLAIM_CONTRADICTED`. In v0.3, a wrong-direction significant result would have failed the `CI bounds in expected direction` check and fallen through to `CLAIM_NOT_DEMONSTRATED`. Adding this rule ensures active contradictions are explicitly flagged, preserving scientific integrity.

---

## 2. MLC v0.1 MME Inheritance Audit & Updated Backtest

### Audit Findings:
1. **Pilot Configuration**: The MLC v0.1 pilot execution script ([bootstrap/run_mlc_v0_1_pilot.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/run_mlc_v0_1_pilot.py)) did define a provisional MME:
   * `minimum_meaningful_effect_percentage_points = 5.0`
   * `minimum_meaningful_effect_absolute = 0.05`
2. **Inheritance Status**: **NO**. The Milestone 5-9 lineage never imported, referenced, or inherited this value in its code, protocols, or reports. It remained isolated in the MLC v0.1 pilot configurations.
3. **Wiring/Config Finding**: This is a **translation and wiring gap** rather than an absolute absence of a defined MME in the repository history.

### Updated Backtest Table (Assuming MME = 0.05 is inherited):
Under a 5 percentage point MME ($\delta = 0.05$, $\alpha = 0.05$, $\beta = 0.80$), the required sample size ($N_{\text{required}}$) to compare two proportions is on the order of **several hundred to a thousand events** (since $\delta$ is very small). 

With our historical sample sizes ($N \le 50$), all runs are severely underpowered to verify such a small effect:

| Claim Under Review | Observed $N$ | Assumed MME | CI Overlaps Zero | Gate v0.4 Output |
| --- | --- | --- | --- | --- |
| **Milestone 5**: Prospective Validation reduces false admissions | $50$ seeds ($N \approx 10-23$ events) | 0.05 | Yes (Both rates 0.0) | `INCONCLUSIVE` |
| **Milestone 6**: Accumulated contradiction retires beliefs | $5$ sequences | 0.05 | No (CI bounds `[1.0, 1.0]`) | `INSUFFICIENTLY_POWERED` |
| **Milestone 7 Family A**: Learning improves selection rate | $13$ events | 0.05 | Yes (CI overlaps 0) | `INCONCLUSIVE` |
| **Milestone 7 Family B**: Learning degrades rate under context shift | $13$ events | 0.05 | No (CI bounds separate) | `INSUFFICIENTLY_POWERED` |

*Note*: If MME is treated as undefined (due to the wiring gap), the output for all rows remains `INDETERMINATE_NO_POWER_TARGET_DEFINED`.

---

## 3. Structural Enforcement of Closure Artifacts

To prevent bypasses like the one implemented in `verify_scientific_closures.py`, we must eliminate loose direct-write paths.

### 1. The Bypass Gap:
Currently, the files `epistemic_effect_validation_results.json` and `scientific_closures_manifest.json` are written using raw Python `json.dump()` calls scattered in `bootstrap/` files. Any script can overwrite them without executing gate logic.

### 2. Single Write Path Remediation (Design):
We propose centralizing all file write interface calls into a dedicated helper module:

* **File Location**: `flows/minimal_learning_cycle/artifacts.py`
* **Class**: `ValidationStorageManager`
* **Gate Enforcement**:
  * The `save_validation_results` method accepts only a valid, fully initialized Pydantic `EpistemicValidationManifest` instance.
  * Direct string-path writes to the validation directory are blocked by standard imports interface design.
  
```python
class ValidationStorageManager:
    @staticmethod
    def save_manifest(manifest: EpistemicValidationManifest, filepath: str):
        # 1. Manifest initialization already executed the root validator gate checks.
        # 2. Directly serializes the validated model object and writes to filepath.
```

### 3. Downstream Integrity Check:
* Implement an automated regression test in `bootstrap/executable_gates_test.py` that loads the live files on disk and validates them against the `EpistemicValidationManifest` model schema.
* If any manual script directly edited or wrote an invalid manifest, this test raises an exception, failing the test suite build.
