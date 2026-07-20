# EKAMNET EPOCH 009 GATE COVERAGE AUDIT

## 1. VERSION CONTROL STATUS OF ALL GATE-RELEVANT FILES
A review of the active repository's git status reveals a critical version-control hygiene finding:
* **All gate evaluation and milestone closure files are currently UNTRACKED** in git.
* List of untracked gate-relevant files:
  * [flows/minimal_learning_cycle/completion_gates.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/flows/minimal_learning_cycle/completion_gates.py) — **`UNTRACKED`**
  * [bootstrap/verify_scientific_closures.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/verify_scientific_closures.py) — **`UNTRACKED`**
  * [bootstrap/executable_gates_test.py](file:///Users/hemantj/Proj/dp_core/dp-core-phase1-substrate-v3/bootstrap/executable_gates_test.py) — **`UNTRACKED`**
  * `data/scientific_closures_manifest.json` — **`UNTRACKED`**
  * `data/epistemic_effect_validation_results.json` — **`UNTRACKED`**

### Program-Process Finding:
Because the files executing the scientific gates and writing the verification manifest are untracked, their execution integrity cannot be independently audited using repository commit history. They exist only in IDE-local memory or transcript logs, violating the principle of inspectability and persistence integrity.

---

## 2. FULL CLAIM-BY-CLAIM GATE COVERAGE TABLE

| Claim | Milestone | Gate Mechanism Used | Was Claims List Evaluated | Evidence Cited |
| --- | --- | --- | --- | --- |
| **Epistemic Plurality Complete** | Milestone 3 | None found (Only unit tests) | **NO** | `milestone3_plurality_test.py` passes |
| **Prospective Validation reduced false admissions** | Milestone 5 | Hardcoded `GateStatus.PASS` | **NO** | Selection risk results on seeds 51-100 |
| **Longitudinal belief evolution rules validated** | Milestone 6 | Hardcoded `GateStatus.PASS` | **NO** | Sequence transition results on diagnostic runs |
| **Condition D improved causal selection rate (Family A)** | Milestone 7 | Standard validator (`evaluate_minimal_causal_learning()`) | **YES** | `results_a` selection rate difference (+0.538) |
| **Condition D degraded selection rate (Family B)** | Milestone 7 | Hand-set bypass (`ClaimEvidenceConsistencyGate()`) | **YES** | `results_b` selection rate difference (-0.769) |

---

## 3. VALIDATOR DESIGN GAP DESCRIPTION
The current implementation of `evaluate_minimal_causal_learning()` checks only the sign of the pre-computed difference:
```python
diff = results.get("epistemic_metric_diff", 0.0)
if diff > 0.0:
    status = ClaimStatus.CLAIM_SUPPORTED
elif diff < 0.0:
    status = ClaimStatus.CLAIM_CONTRADICTED
```

### Gap Identification:
1. **Positive-Only Claim Shape**: The gate hardcodes the assumption that any positive difference represents success. It automatically flags any negative difference (`diff < 0.0`) as `CLAIM_CONTRADICTED`. This makes it impossible to validate alternative hypotheses asserting harm/degradation as an expected/claimed direction (such as overgeneralization harm under context shift).
2. **Pre-Statistical Blindness**: The gate reads `epistemic_metric_diff` as a raw float. It does not check sample size, statistical significance, or confidence interval overlap, allowing underpowered claims (e.g. 1-of-2 vs 2-of-2) to be marked `CLAIM_SUPPORTED`.

---

## 4. MINIMAL REQUIRED INTERFACE CHANGE (DESIGN NOTE ONLY)
To resolve these gaps, the Claim validator interface should be restructured to accept a specification object detailing the claim's type and statistical requirements:

```python
class ClaimType(str, Enum):
    POSITIVE_IMPROVEMENT = "positive_improvement"  # Expects diff > 0 and CI lower bound > 0
    HARM_DEGRADATION = "harm_degradation"          # Expects diff < 0 and CI upper bound < 0
    NEUTRAL_NO_EFFECT = "neutral_no_effect"        # Expects diff == 0 or CI overlapping 0


class ClaimSpecification(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    min_sample_size: int = 30
    confidence_level: float = 0.95
```

### Signature Change:
The validator should accept the spec along with the results:
```python
@staticmethod
def evaluate_claim_consistency(
    results: Dict[str, Any], spec: ClaimSpecification
) -> "ClaimEvidenceConsistencyGate":
    # 1. Enforce min_sample_size against results["sample_size"]
    # 2. Check overlap of results["ci_lower"] and results["ci_upper"] with 0
    # 3. Match outcome against spec.claim_type and return status
```

---

## 5. RECOMMENDATION
**`YES`**. Milestone 5 and Milestone 6 canonical status should be flagged as **`GATE_UNVERIFIED`** in the capability map and decision logs.

### Reason:
* The active manifest validator script `verify_scientific_closures.py` bypassed the standard validators for Milestone 5 and Milestone 6.
* The standard validator functions `evaluate_false_admission_reduction` and `evaluate_order_sensitivity` were never run against any actual stored results during the manifest run.
* Without automated execution checks, the assertions of completeness in `EKAMNET_PROGRAM_STATE.md` remain human narrative claims unsupported by active gate execution records, increasing the risk of canonical state drift.
