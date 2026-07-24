# E2_v2 — 20-Seed Synthetic Benchmark Battery Results

Authoritative 20-seed synthetic battery evaluation against the external reference benchmark.

### Registered Gate A Branch Verdict: **[AMBIGUOUS]**

**Expected Calibration Error (ECE)**: `0.1630`

---

## Scenario S1 Results (20 Seeds)

| Learner | Brier Regret (mean ± std) | Precision (mean ± std) | Recall (mean ± std) | Decoy Claims (mean ± std) | Recovery Steps (mean ± std) | Collateral (mean ± std) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **FlatBayesian** | 0.0005 ± 0.0002 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **WindowedFrequency(w=200)** | 0.0030 ± 0.0004 | 0.8833 ± 0.1631 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **ContextualBayesian** | 0.0005 ± 0.0002 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **DP/EkamNet** | 0.0679 ± 0.0038 | 1.0000 ± 0.0000 | 0.4500 ± 0.2236 | 0.00 ± 0.00 | N/A | N/A |

## Scenario S2 Results (20 Seeds)

| Learner | Brier Regret (mean ± std) | Precision (mean ± std) | Recall (mean ± std) | Decoy Claims (mean ± std) | Recovery Steps (mean ± std) | Collateral (mean ± std) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **FlatBayesian** | 0.0178 ± 0.0014 | 0.6583 ± 0.0373 | 1.0000 ± 0.0000 | 1.05 ± 0.22 | N/A | N/A |
| **WindowedFrequency(w=200)** | 0.0076 ± 0.0009 | 0.9417 ± 0.1458 | 1.0000 ± 0.0000 | 0.20 ± 0.52 | N/A | N/A |
| **ContextualBayesian** | 0.0178 ± 0.0014 | 0.6583 ± 0.0373 | 1.0000 ± 0.0000 | 1.05 ± 0.22 | N/A | N/A |
| **DP/EkamNet** | 0.0702 ± 0.0049 | 1.0000 ± 0.0000 | 0.4750 ± 0.1118 | 0.00 ± 0.00 | N/A | N/A |

## Scenario S3 Results (20 Seeds)

| Learner | Brier Regret (mean ± std) | Precision (mean ± std) | Recall (mean ± std) | Decoy Claims (mean ± std) | Recovery Steps (mean ± std) | Collateral (mean ± std) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | 13.8 ± 55.9 | 0.0075 ± 0.0210 |
| **FlatBayesian** | 0.0313 ± 0.0011 | 0.6667 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | 1873.8 ± 175.4 | 0.0074 ± 0.0209 |
| **WindowedFrequency(w=200)** | 0.0038 ± 0.0003 | 0.9833 ± 0.0745 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | 123.8 ± 68.6 | 0.0079 ± 0.0205 |
| **ContextualBayesian** | 0.0313 ± 0.0011 | 0.6667 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | 1873.8 ± 175.4 | 0.0074 ± 0.0209 |
| **DP/EkamNet** | 0.0520 ± 0.0026 | 1.0000 ± 0.0000 | 0.4500 ± 0.2236 | 0.00 ± 0.00 | 292.5 ± 149.6 | 0.0093 ± 0.0458 |

## Scenario S4 Results (20 Seeds)

| Learner | Brier Regret (mean ± std) | Precision (mean ± std) | Recall (mean ± std) | Decoy Claims (mean ± std) | Recovery Steps (mean ± std) | Collateral (mean ± std) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | 0.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **FlatBayesian** | 0.0328 ± 0.0015 | 0.6667 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **WindowedFrequency(w=200)** | 0.0358 ± 0.0012 | 0.6667 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **ContextualBayesian** | 0.0005 ± 0.0002 | 0.6667 ± 0.0000 | 1.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |
| **DP/EkamNet** | 0.1163 ± 0.0028 | 0.0000 ± 0.0000 | 0.0000 ± 0.0000 | 0.00 ± 0.00 | N/A | N/A |

---

## Registered Winner Determination & IQR Analysis

### S1 20-Seed Interquartile Ranges (IQR: Q25 .. Q75)

| Learner | Brier Regret IQR | Precision IQR | Recall IQR |
| :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | [0.0000 .. 0.0000] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **FlatBayesian** | [0.0003 .. 0.0007] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **WindowedFrequency(w=200)** | [0.0027 .. 0.0034] | [0.6667 .. 1.0000] | [1.0000 .. 1.0000] |
| **ContextualBayesian** | [0.0003 .. 0.0007] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **DP/EkamNet** | [0.0653 .. 0.0709] | [1.0000 .. 1.0000] | [0.5000 .. 0.5000] |

### S2 20-Seed Interquartile Ranges (IQR: Q25 .. Q75)

| Learner | Brier Regret IQR | Precision IQR | Recall IQR |
| :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | [0.0000 .. 0.0000] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **FlatBayesian** | [0.0171 .. 0.0188] | [0.6667 .. 0.6667] | [1.0000 .. 1.0000] |
| **WindowedFrequency(w=200)** | [0.0070 .. 0.0081] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **ContextualBayesian** | [0.0171 .. 0.0188] | [0.6667 .. 0.6667] | [1.0000 .. 1.0000] |
| **DP/EkamNet** | [0.0676 .. 0.0748] | [1.0000 .. 1.0000] | [0.5000 .. 0.5000] |

### S3 20-Seed Interquartile Ranges (IQR: Q25 .. Q75)

| Learner | Brier Regret IQR | Precision IQR | Recall IQR |
| :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | [0.0000 .. 0.0000] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **FlatBayesian** | [0.0308 .. 0.0317] | [0.6667 .. 0.6667] | [1.0000 .. 1.0000] |
| **WindowedFrequency(w=200)** | [0.0036 .. 0.0040] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **ContextualBayesian** | [0.0308 .. 0.0317] | [0.6667 .. 0.6667] | [1.0000 .. 1.0000] |
| **DP/EkamNet** | [0.0506 .. 0.0539] | [1.0000 .. 1.0000] | [0.5000 .. 0.5000] |

### S4 20-Seed Interquartile Ranges (IQR: Q25 .. Q75)

| Learner | Brier Regret IQR | Precision IQR | Recall IQR |
| :--- | :--- | :--- | :--- |
| **TrueModel (oracle floor)** | [0.0000 .. 0.0000] | [1.0000 .. 1.0000] | [1.0000 .. 1.0000] |
| **FlatBayesian** | [0.0320 .. 0.0341] | [0.6667 .. 0.6667] | [1.0000 .. 1.0000] |
| **WindowedFrequency(w=200)** | [0.0349 .. 0.0367] | [0.6667 .. 0.6667] | [1.0000 .. 1.0000] |
| **ContextualBayesian** | [0.0004 .. 0.0006] | [0.6667 .. 0.6667] | [1.0000 .. 1.0000] |
| **DP/EkamNet** | [0.1148 .. 0.1183] | [nan .. nan] | [0.0000 .. 0.0000] |

