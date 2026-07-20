# EKAMNET EPOCH 009 GATE REDESIGN v0.5
**Status**: Refined Design Note Only — Implementation Pending Review & Approval
**Readiness**: This is the final design pass. The design is ready for implementation authorization, pending human sign-off.

---

## 1. Rule 6: `CLAIM_CONTRADICTED` for Adequately-Powered Wrong-Direction Results

We introduce an explicit **sixth rule** to differentiate between results that are simply underpowered or null vs. results that actively contradict the claim under adequate statistical power.

### Rule 6 Definition:
If the sample size is adequate ($N \ge N_{\text{required}}$) AND the computed confidence interval (CI) sits entirely on the opposite side of zero from what the claim type asserts, the gate returns:
$$\mathbf{CLAIM\_CONTRADICTED}$$

---

## 2. MLC v0.1 MME Inheritance Audit & Backtest

### Audit Finding:
The Milestone 5-9 lineage never inherited, imported, or referenced the provisional MME value of **5.0 percentage points (0.05 absolute)** defined in the MLC v0.1 pilot execution script ([bootstrap/run_mlc_v0_1_pilot.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/run_mlc_v0_1_pilot.py)). This constitutes a translation and wiring gap.

### A. PRIMARY BACKTEST TABLE (ACTUAL CURRENT BEHAVIOR)
This table shows the actual current gate output under the v0.5 design, reflecting that no MME is currently wired into the Milestone 5-9 lineage:

| Claim Under Review | Observed $N$ | Wired MME | CI Overlaps Zero | Gate v0.5 Output |
| --- | --- | --- | --- | --- |
| **Milestone 5**: Prospective Validation reduces false admissions | $50$ seeds | **None** (Undefined) | Yes (Both rates 0.0) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |
| **Milestone 6**: Accumulated contradiction retires beliefs | $5$ sequences | **None** (Undefined) | No (CI bounds `[1.0, 1.0]`) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |
| **Milestone 7 Family A**: Learning improves selection rate | $13$ events | **None** (Undefined) | Yes (CI overlaps 0) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |
| **Milestone 7 Family B**: Learning degrades rate under context shift | $13$ events | **None** (Undefined) | No (CI bounds separate) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |

---

### B. SECONDARY, HYPOTHETICAL BACKTEST TABLE (FOR ILLUSTRATION ONLY)
This table shows what the gate outputs WOULD be if the MLC v0.1 MME ($0.05$ absolute) were retroactively wired into the Milestone 5-9 lineage. Under this small effect target, all actual sample sizes ($N \le 50$) are severely underpowered:

| Claim Under Review | Observed $N$ | Hypothetical MME | CI Overlaps Zero | Gate v0.5 Output |
| --- | --- | --- | --- | --- |
| **Milestone 5**: Prospective Validation reduces false admissions | $50$ seeds | 0.05 | Yes (Both rates 0.0) | `INCONCLUSIVE` |
| **Milestone 6**: Accumulated contradiction retires beliefs | $5$ sequences | 0.05 | No (CI bounds `[1.0, 1.0]`) | `INSUFFICIENTLY_POWERED` |
| **Milestone 7 Family A**: Learning improves selection rate | $13$ events | 0.05 | Yes (CI overlaps 0) | `INCONCLUSIVE` |
| **Milestone 7 Family B**: Learning degrades rate under context shift | $13$ events | 0.05 | No (CI bounds separate) | `INSUFFICIENTLY_POWERED` |

---

## 3. Structural Enforcement of Closure Artifacts

To prevent bypasses, we implement strict enforcement on both the write-side and consumption-side of the validation pipeline.

### A. Write-Side Enforcement
We restrict all file write operations for `epistemic_effect_validation_results.json` and `scientific_closures_manifest.json` to a single manager:
* **Class**: `ValidationStorageManager` in `flows/minimal_learning_cycle/artifacts.py`.
* **Gate Enforcement**: This class only accepts an instantiated `EpistemicValidationManifest` Pydantic model. Because the manifest's constructor executes gate checks on initialization, serialization is structurally blocked for any dataset containing contradicted or underpowered claims.

### B. Consumption-Side Enforcement (Safeguard)
Import discipline alone does not prevent a developer from writing bypass code. To close this loophole, we implement read-time validation on the consumption side:

* **Class**: `EpistemicValidationManifestReader`
* **Gate Enforcement**:
  * Any code path or script that reads validation results to inform a milestone closure report or canonical state update must load the data through the `load_manifest()` method.
  * The reader parses the JSON file directly into the `EpistemicValidationManifest` Pydantic schema, executing all validation rules at read time.
  * If the on-disk file has been manually tampered with or contains any claims with unresolved/failed statuses (e.g. `CLAIM_CONTRADICTED`, `INSUFFICIENTLY_POWERED`, or `INDETERMINATE_NO_POWER_TARGET_DEFINED`), the reader raises a `ValueError`, halting downstream execution.

```python
class EpistemicValidationManifestReader:
    @staticmethod
    def load_manifest(filepath: str) -> EpistemicValidationManifest:
        with open(filepath, "r") as f:
            data = json.load(f)
        
        # 1. Triggers Pydantic schema parsing and gate checks at read time
        manifest = EpistemicValidationManifest.model_validate(data)
        
        # 2. Block consumption of unresolved or failed claims
        for claim in manifest.claims:
            if claim.status in (ClaimStatus.CLAIM_CONTRADICTED, ClaimStatus.INSUFFICIENTLY_POWERED, ClaimStatus.INDETERMINATE):
                raise ValueError(
                    f"Consumption Blocked: JSON contains unresolved or failed status: "
                    f"[{claim.claim_id}] -> {claim.status}"
                )
        return manifest
```

### Read-Side Wiring (Wired to Canonical Manifests):
* **Verification Runner**: In [bootstrap/verify_scientific_closures.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py), loading `epistemic_effect_validation_results.json` must be wired through `EpistemicValidationManifestReader.load_manifest()`. If a developer attempts to write a manual bypass or bypasses the gate during compilation, this reader crashes immediately upon execution.
* **Test Suite Verification**: The automated test suite (`poetry run pytest`) contains a regression test that runs `load_manifest()` on all current closure artifacts on disk. Any manual bypass or state file tampering will cause the test suite to fail, blocking the CI/CD pipeline.
* **State Generation Integration**: Any future automated tool that updates [EKAMNET_PROGRAM_STATE.md](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/EKAMNET_PROGRAM_STATE.md) from validation results is wired exclusively to this reader, preventing direct file readings.
