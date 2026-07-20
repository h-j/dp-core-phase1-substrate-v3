# EKAMNET EPOCH 009 GATE REDESIGN v0.2
**Status**: Refined Design Note Only — Implementation Pending Review & Approval

---

## 1. Threshold-Justification Hierarchy Analysis

We evaluate the proposed default settings of $\text{min\_sample\_size} = 30$ and $\text{confidence\_level} = 0.95$ against the program's established five-tier threshold justification hierarchy:

1. **Replay Evidence Anchor**: Empirical values derived from past replay simulations.
2. **Architectural Plausibility**: Thresholds dictated by structural limits (e.g., vocabulary sizes, memory capacities).
3. **Established Statistical Convention**: Standards accepted in scientific research (e.g., $N=30$, $\alpha=0.05$).
4. **Power Analysis**: Formally calculated sample requirements based on expected effect size and variance.
5. **Explicit Exploratory Grid**: Parameters tuned via grid search to optimize selection rates.

### Default Justification Ratings:
* **`min_sample_size = 30`**: **Established Statistical Convention (Tier 3)**. This default is based entirely on the introductory statistical heuristic that sample distributions become approximately normal under the Central Limit Theorem (CLT) at $N \ge 30$. It is **not** anchored in replay evidence, power analysis, or exploratory grids.
* **`confidence_level = 0.95`**: **Established Statistical Convention (Tier 3)**. The standard $\alpha = 0.05$ threshold is a default scientific convention. It does not reflect a formal risk-utility trade-off of false belief admissions in the EkamNet cognition loop.

---

## 2. Historical Sample Size Calibration

We check the utility of the static $\text{min\_sample\_size} = 30$ default against the actual triggered event counts from historical and current experiments:

* **Milestone 5 (Selection Risk)**: Staged primary seeds 51-100 (50 seeds), yielding $N \approx 10-23$ triggered competition events.
* **Milestone 7 (Epoch 8 Baseline)**: Primary seeds 101-150 (50 seeds), yielding **$N = 2$** triggered pruning events.
* **Milestone 7 (Epoch 9 Continuation)**: Primary seeds 151-350 (200 seeds), yielding **$N = 13$** triggered pruning events.

### Calibration Finding:
A static default threshold of $\text{min\_sample\_size} = 30$ is **severely miscalibrated** against the actual event densities produced by our experiments. 
* If enforced, it would have classified the entire Epoch 9 primary evidence record ($N=13$) — which required a 200-seed run — as **insufficiently powered**, blocking closure.
* Meeting a threshold of 30 under current prevalence rates ($6.5\%$) would require running a minimum of **462 seeds**, significantly increasing local computational cost.
* Enforcing $N \ge 30$ statically is therefore impractical. The gate redesign must support **dynamic power requirements** based on the specific claim's Minimum Meaningful Effect (MME), rather than a hardcoded default.

---

## 3. Split Neutrality: `NO_DIFFERENCE` vs. `INCONCLUSIVE`

To align the gate's classification logic with the existing program verdicts, the general `NEUTRAL_NO_EFFECT` classification is split into two distinct, non-collapsed outputs:

### 1. `NO_DIFFERENCE`
* **Definition**: The observed difference is statistically indistinguishable from zero, and the sample size is large enough to confirm the absence of a meaningful effect.
* **Gate Logic**: 
  * The computed confidence interval (CI) for the difference overlaps zero.
  * The sample size $N$ meets or exceeds the required sample size ($N_{\text{req}}$) calculated to achieve $\ge 80\%$ statistical power to detect the pre-registered Minimum Meaningful Effect (MME) at the specified alpha.

### 2. `INCONCLUSIVE`
* **Definition**: The observed difference is statistically indistinguishable from zero, but the sample size is too small to rule out a meaningful effect.
* **Gate Logic**:
  * The computed CI overlaps zero.
  * The sample size $N$ is *less* than the required sample size ($N_{\text{req}}$) needed to detect the pre-registered MME.

### Handling Undefined Power Targets:
If a pre-registered MME is not defined in the claim specification, the gate cannot calculate $N_{\text{req}}$ and cannot distinguish between a true null effect and an underpowered sample. Under this condition, the gate must return:
$$\mathbf{INDETERMINATE\_NO\_POWER\_TARGET\_DEFINED}$$
rather than guessing.

---

## 4. Refined Claim Validation Interface Schema
This design note proposes the following Pydantic schemas to govern claim validation:

```python
from enum import Enum
from pydantic import BaseModel, Field

class ClaimType(str, Enum):
    POSITIVE_IMPROVEMENT = "positive_improvement"
    HARM_DEGRADATION = "harm_degradation"
    NO_DIFFERENCE = "no_difference"
    INCONCLUSIVE = "inconclusive"


class ClaimSpecification(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    minimum_meaningful_effect: float | None = Field(
        default=None, 
        description="The smallest change (e.g. +0.15) considered scientifically meaningful."
    )
    confidence_level: float = Field(
        default=0.95, 
        description="Significance level (1 - alpha) for CI calculation."
    )
```

### Validator Method Interface:
```python
class ClaimEvidenceConsistencyGate(BaseModel):
    # ... attributes ...

    @staticmethod
    def evaluate_claim_consistency(
        results: dict, spec: ClaimSpecification
    ) -> "ClaimEvidenceConsistencyGate":
        """
        Refined Validator:
        1. Reads sample size N, observed diff, and computes the exact binomial CI bounds.
        2. If spec.claim_type == ClaimType.NO_DIFFERENCE or spec.claim_type == ClaimType.INCONCLUSIVE:
            - If MME is None, returns INDETERMINATE_NO_POWER_TARGET_DEFINED.
            - Else, calculates the power-justified required N.
            - If CI overlaps zero and N >= N_required -> status = ClaimStatus.NO_DIFFERENCE.
            - If CI overlaps zero and N < N_required -> status = ClaimStatus.INCONCLUSIVE.
        3. For POSITIVE_IMPROVEMENT / HARM_DEGRADATION, checks CI bounds against zero in the expected direction.
        """
        pass
```
