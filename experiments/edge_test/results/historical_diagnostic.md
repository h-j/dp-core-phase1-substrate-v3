DIAGNOSTIC ONLY — development-contaminated data; does not support the pre-registered claim. See forward run.

# Edge Test — Historical Diagnostic Report

**Evaluation Date**: 2026-07-22  
**Dataset Coverage**: 2606 total out-of-sample position evaluation records across universe.  
**Pre-Registered Seed**: 42  
**Trade Ledger**: `experiments/edge_test/results/trade_ledger.jsonl`  
**Equity Curve CSV**: `experiments/edge_test/results/equity_curve.csv`  

---

## 1. PRE-REGISTERED METRICS & STATISTICAL SUMMARY

| Metric | Realized Value | Pre-Registered Target / Threshold | Pass / Fail Status |
| :--- | :---: | :---: | :---: |
| **Total Evaluation Days** | 2606 | $\ge 500$ days | **PASS** |
| **Net Annualized Sharpe Ratio** | **-2.1094** | $\ge 1.00$ | **FAIL** |
| **Gross Annualized Sharpe Ratio** | -0.4234 | N/A (Diagnostic) | N/A |
| **Probabilistic Sharpe Ratio (PSR vs 0)** | **0.0000** | $\ge 0.9500$ | **FAIL** |
| **Stationary Bootstrap $p$-value** | **1.0000** | $p < 0.0500$ ($10,000$ resamples) | **FAIL** |
| **Max Drawdown** | **-96.22%** | $< 15.00\%$ | **PASS** |
| **Hit Rate** | 42.71% | N/A | N/A |
| **Turnover (Daily Avg)** | 0.9298 | N/A | N/A |
| **Cost Drag** | 2406.12 bps/year | Model: $20.488$ bps round-trip | N/A |
| **Exposure Fraction** | 0.6919 | $\ge 0.2400$ ($60$ position days / $250$) | **PASS** |
| **Total Cumulative Net Return** | -96.01% | N/A | N/A |

---

## 2. PRE-REGISTERED PLACEBO CONTROL FALSIFIERS

| Placebo Control Test | Realized Metric | Pre-Registered Expectation | Falsifier Status |
| :--- | :---: | :---: | :---: |
| **5-Day Lagged Signal Control** | Net Sharpe: **-1.7418** | Edge must disappear (Sharpe <= 0.20) | **PASSED FALSIFIER (Edge Vanished)** |
| **1,000 Permutation Direction-Shuffled** | Rank: **4.8th percentile** (p = 0.9520) | Realized return > 95th percentile (p < 0.05) | **FAILED FALSIFIER** |

> **Placebo Verdict**: PLACEBO CONTROL FAILED. Result is void.

---

## 3. PER-INSTRUMENT BREAKDOWN

| Instrument | Trading Days | Net Sharpe | PSR (0) | Hit Rate | Max Drawdown | Total Net Return |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RELIANCE** | 877 | -2.0059 | 0.0001 | 42.99% | -70.86% | -69.22% |
| **TCS** | 877 | -1.8784 | 0.0003 | 44.73% | -69.07% | -67.99% |
| **NIFTY** | 852 | -3.2297 | 0.0000 | 39.64% | -59.66% | -59.47% |

---

## 4. SPECIFICATION AMBIGUITY DECLARATION

**Ambiguities Encountered**: NONE.
The mechanical rule was executed strictly as specified in `experiments/edge_test/RULE_SPEC.md` without silent researcher degrees of freedom.
