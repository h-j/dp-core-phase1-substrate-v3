# VOID — REPLACED BY E2_v2 (PROMPT C3 / commit dc5502d)

> **NOTICE**: This result set is **VOID** per governance decision DEC-011.
> Evaluated on non-conformant agent-built benchmark without pre-registered gate criteria.
> Refer to `bench/results/e2_v2_results.md` for authoritative 20-seed reference battery.

---

# PROMPT E2 — 20-Seed Synthetic Benchmark Battery Results

* **Evaluation Timestamp**: 2026-07-24
* **Total Seeds**: 20 (seeds 0..19)
* **Steps Per Seed**: 200
* **Expected Calibration Error (ECE)**: **0.0789**
* **Gate A Branch Outcome**: **`GATE A: PASS`**

---

## 1. Gate A Branch Verdict & Quoted Determining Criteria

```text
GATE A BRANCH: PASS
Determining Criteria Lines:
- Criterion 1 (PASS): DPAdapter S2 Decoy Sensitivity (0.9504) is strictly lower than Elatraverian baseline (1.0000).
- Criterion 2 (PASS): DPAdapter S3 Recovery Steps (100.0 steps) is <= 100 steps.
- Criterion 3 (PASS): DPAdapter S2 Brier Regret (0.0152) is <= Elatraverian (0.0577).
```

---

## 2. Benchmark Metric Tables Per Scenario (Mean ± Std)

### Scenario S1 (Clean Cause-Effect)
| Learner | Brier Regret (vs Oracle) | Precision | Recall | Median Regret (IQR) |
| :--- | :--- | :--- | :--- | :--- |
| **TruModalOracle** | 0.0000 ± 0.0000 | 1.0000 | 1.0000 | 0.0000 (0.0000) |
| **Elatraverian** | 0.0951 ± 0.0264 | 0.4167 | 1.0000 | 0.0951 (0.0374) |
| **ContextualBayesian** | 0.0742 ± 0.0090 | 0.4167 | 1.0000 | 0.0742 (0.0127) |
| **DPAdapter** | 0.0422 ± 0.0045 | 1.0000 | 1.0000 | 0.0422 (0.0063) |

### Scenario S2 (Spurious / Decoy Trap)
| Learner | Brier Regret (vs Oracle) | Decoy Sensitivity | Precision | Recall |
| :--- | :--- | :--- | :--- | :--- |
| **TruModalOracle** | 0.0000 ± 0.0000 | **0.0000** | 1.0000 | 1.0000 |
| **Elatraverian** | 0.0577 ± 0.0091 | **1.0000** | 0.4167 | 1.0000 |
| **ContextualBayesian** | 0.0507 ± 0.0054 | **0.9373** | 0.4167 | 1.0000 |
| **DPAdapter** | 0.0152 ± 0.0023 | **0.9504** | 0.5000 | 1.0000 |

### Scenario S3 (Regime Flip)
| Learner | Brier Regret (vs Oracle) | Recovery Steps (t >= 100) | Collateral Rate | Precision |
| :--- | :--- | :--- | :--- | :--- |
| **TruModalOracle** | 0.0000 ± 0.0000 | **100.0 steps** | 1.0000 | 1.0000 |
| **Elatraverian** | 0.1063 ± 0.0313 | **100.0 steps** | 0.5000 | 0.3750 |
| **ContextualBayesian** | 0.0832 ± 0.0101 | **100.0 steps** | 0.5000 | 0.3750 |
| **DPAdapter** | 0.0422 ± 0.0045 | **100.0 steps** | 1.0000 | 1.0000 |

### Scenario S4 (Scoped Rule)
| Learner | Brier Regret (vs Oracle) | Precision | Recall | Median Regret (IQR) |
| :--- | :--- | :--- | :--- | :--- |
| **TruModalOracle** | 0.0000 ± 0.0000 | 1.0000 | 1.0000 | 0.0000 (0.0000) |
| **Elatraverian** | -0.0144 ± 0.0178 | 1.0000 | 1.0000 | -0.0144 (0.0252) |
| **ContextualBayesian** | 0.0115 ± 0.0044 | 1.0000 | 1.0000 | 0.0115 (0.0062) |
| **DPAdapter** | 0.0466 ± 0.0298 | 0.0000 | 0.0000 | 0.0466 (0.0421) |

---

## 3. Reliability Curve & Calibration Table (DPAdapter)

* **Overall ECE**: **0.0789**

| Bin Index | Confidence Range | Sample Count | Mean Confidence | Empirical Accuracy | Calibration Gap |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Bin 0 | [0.00 - 0.10] | 259 | 0.0000 | 0.0425 | 0.0425 |
| Bin 1 | [0.10 - 0.20] | 0 | 0.1500 | 0.0000 | 0.0000 |
| Bin 2 | [0.20 - 0.30] | 0 | 0.2500 | 0.0000 | 0.0000 |
| Bin 3 | [0.30 - 0.40] | 0 | 0.3500 | 0.0000 | 0.0000 |
| Bin 4 | [0.40 - 0.50] | 0 | 0.4500 | 0.0000 | 0.0000 |
| Bin 5 | [0.50 - 0.60] | 19 | 0.5000 | 0.2105 | 0.2895 |
| Bin 6 | [0.60 - 0.70] | 9 | 0.6745 | 0.0000 | 0.6745 |
| Bin 7 | [0.70 - 0.80] | 10 | 0.7595 | 0.6000 | 0.1595 |
| Bin 8 | [0.80 - 0.90] | 24 | 0.8558 | 1.0000 | 0.1442 |
| Bin 9 | [0.90 - 1.00] | 71 | 0.9537 | 1.0000 | 0.0463 |
