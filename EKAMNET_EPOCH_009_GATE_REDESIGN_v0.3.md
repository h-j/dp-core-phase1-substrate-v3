# EKAMNET EPOCH 009 GATE REDESIGN v0.3
**Status**: Refined Design Note Only — Implementation Pending Review & Approval

---

## 1. Uniform Power/Sample-Adequacy Check Across All Claim Types

We extend the MME-based power and sample-adequacy verification uniformly to **all** claim types in the Claim validator engine. 

Under this design, even if the computed confidence interval (CI) indicates statistical significance (e.g., does not overlap zero in the expected direction), the gate will not validate the claim unless the sample size $N$ is statistically adequate to detect the pre-registered Minimum Meaningful Effect (MME) at the target power level ($\beta = 0.80$).

### Refined Logic Rules:
1. **MME Undefined**: If `minimum_meaningful_effect` is `None` (undefined) for the claim, the gate immediately halts and returns:
   $$\mathbf{INDETERMINATE\_NO\_POWER\_TARGET\_DEFINED}$$
2. **Underpowered Sample ($N < N_{\text{required}}$)**: If the sample size $N$ is smaller than the required sample size ($N_{\text{required}}$) calculated to detect the MME:
   * Returns **`INCONCLUSIVE`** if the CI overlaps zero.
   * Returns **`INSUFFICIENTLY_POWERED`** (claim blocked) if the CI does *not* overlap zero.
3. **Powered Sample ($N \ge N_{\text{required}}$)**:
   * **`POSITIVE_IMPROVEMENT`**: Returns `CLAIM_SUPPORTED` if the CI lower bound > 0.
   * **`HARM_DEGRADATION`**: Returns `CLAIM_SUPPORTED` if the CI upper bound < 0.
   * **`NO_DIFFERENCE`**: Returns `NO_DIFFERENCE` if the CI overlaps zero.

### Refined Pydantic Schema Design:
```python
class ClaimType(str, Enum):
    POSITIVE_IMPROVEMENT = "positive_improvement"
    HARM_DEGRADATION = "harm_degradation"
    NO_DIFFERENCE = "no_difference"
    INCONCLUSIVE = "inconclusive"
    INSUFFICIENTLY_POWERED = "insufficiently_powered"


class ClaimSpecification(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    minimum_meaningful_effect: float | None = None
    confidence_level: float = 0.95
    target_power: float = 0.80
```

---

## 2. Historical Backtest

We backtest the v0.3 gate design on paper against every claim in our historical and current evidence records.

### Backtest Table:

| Claim Under Review | Observed $N$ | Pre-registered MME | CI Overlaps Zero | Gate v0.3 Output |
| --- | --- | --- | --- | --- |
| **Milestone 5**: Prospective Validation reduces false admissions | $50$ seeds ($N \approx 10-23$ competition events) | **None** (Undefined) | Yes (Both rates 0.0) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |
| **Milestone 6**: Accumulated contradiction retires beliefs | $5$ sequences | **None** (Undefined) | No (Deterministic transition) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |
| **Milestone 7 Family A**: Learning improves selection rate | $13$ events | **None** (Undefined) | Yes (CI overlap) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |
| **Milestone 7 Family B**: Learning degrades rate under context shift | $13$ events | **None** (Undefined) | No (CI bounds separate) | `INDETERMINATE_NO_POWER_TARGET_DEFINED` |

### Program-Process Finding:
* Every single claim across Milestone 5, 6, and 7 lacks a numerically defined Minimum Meaningful Effect (MME) in their pre-registration protocols.
* Consequently, **all historical claims are classified as `INDETERMINATE_NO_POWER_TARGET_DEFINED`** under the v0.3 design.
* **Remediation**: Any future pre-registration protocols (beginning with Milestone 8) **must** declare a numerical MME value (e.g., $+15\%$ lift or $-20\%$ degradation) to render statistical power calculations executable.

---

## 3. Structural Enforcement Design

To prevent bypassing gate verification, gate checks must be integrated directly into the serialization pathway of the experiment runner:

### 1. Specific Integration Point:
* The integration point is in [flows/minimal_learning_cycle/experiment.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/experiment.py) inside the `MLCExperimentRunner` class.
* We hook into the method where experimental suites are compiled and results are exported. A natural hook is at the completion of a batch run, immediately before writing output files.

### 2. Enforcement Mechanism:
* Define a serialized model class `EpistemicValidationManifest` in `flows/minimal_learning_cycle/schemas.py`.
* This class accepts raw experimental results and a list of `ClaimSpecification` objects.
* A root validator (`@model_validator(mode="after")`) is defined on the class:
  ```python
  @model_validator(mode="after")
  def run_gate_checks(self) -> "EpistemicValidationManifest":
      for claim in self.claims:
          gate = ClaimEvidenceConsistencyGate.evaluate_claim_consistency(self.results, claim)
          if gate.status in (ClaimStatus.CLAIM_CONTRADICTED, ClaimStatus.INSUFFICIENTLY_POWERED):
              raise ValueError(f"Structural Gate Validation Failure: {claim.claim_text} has status {gate.status}")
      return self
  ```
* When `MLCExperimentRunner` attempts to write validation results to `data/epistemic_effect_validation_results.json`, it must instantiate this Pydantic class.
* If a gate fails or is underpowered, the instantiation raises a `ValueError`, **failing close-closed** and preventing the results file or manifest from being written to disk.
