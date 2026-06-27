# Regime Pattern Layer v1 Validation Report

**Execution Date:** 2026-06-21 23:07:54
**Objective:** Comparative evaluation of Baseline (A) vs Theory Retrieval (B) vs Theory + Pattern Retrieval (C).

---

## 1. Executive Comparative Summary

- **Success Criteria Status:** ★ PASSED
  - Pattern retrieval successfully improves usefulness and validation while keeping contradiction pressure low.

| Metric | Baseline (A) | Theory Retrieval (B) | Theory + Pattern (C) | Comparison (C vs B) |
|---|---|---|---|---|
| **Average Usefulness** | 0.2780 | 0.5207 | 0.6707 | ✓ Improved |
| **Average Contradiction Pressure** | 0.0000 | 0.1316 | 0.1048 | ✓ Stable/Reduced |
| **Average Validation Rate** | 0.4271 | 0.4412 | 0.5304 | ✓ Improved |
| **Mutation Rate** | 100.00% | 76.67% | 90.00% | (REUSED: 3, MOD: 16, REJ: 11) |

---

## 2. Comparative Step-by-Step Logs (C - Theory + Pattern)

### Day 1: 2026-05-08
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_3` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by exhaustion; price remains range-bound despite volume contraction.. If liquidity decreases below average: favor breakout lower. Else volatility increases above average: favor range persistence. Unless participation evaporates entirely. Falsified if: decisive close above the prior resistance floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, yet volume expands on up days relative to down days.. If liquidity remains above average: favor range persistence. Else volatility increases: favor breakout higher. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Range-bound regime is driven by absorption; price remains range-bound despite volume expansion.. If liquidity increases above average: favor range persistence. Else volatility decreases below average: favor breakout higher. Unless participation evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.57
- **Theory-Only Metrics (B):** Usefulness=0.50, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.65, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **REJECTED**

### Day 2: 2026-05-11
**Current Regime:** Trend=`closed_lower`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_23` (Similarity: 0.848)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *NIFTY 50 closes lower with weak short-term momentum and compressed volatility, suggesting a regime driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Regime is driven by closed_lower mechanism; price closes below support level, indicating a lack of upward momentum.. If close < support_level: favor short-term sell. Else close >= support_level: favor long-term buy. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by closed_lower mechanism; price closes below support level, indicating a lack of upward momentum.. If close < support_level: adjust logic branches or assumptions to preemptively handle volume_divergence. Else true: continue with current logic. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.49, Contradiction=0.46, Validation=0.57
- **Theory+Pattern Metrics (C):** Usefulness=0.64, Contradiction=0.41, Validation=0.54
- **Reuse Decision:** **REUSED**

### Day 3: 2026-05-12
**Current Regime:** Trend=`extended_lower`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_22` (Similarity: 0.848)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *Extended Lower regime is driven by passive exhaustion; price remains lower-bound despite volume contraction.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Extended_lower regime is driven by passive exhaustion; price remains lower-bound despite volume contraction.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by extended_lower mechanism; price maintains lower highs and higher lows despite weak short-term momentum.. If close below support level: falsify claim. Else price closes above support level: continue observation. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.49, Contradiction=0.26, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.64, Contradiction=0.71, Validation=0.39
- **Reuse Decision:** **REJECTED**

### Day 4: 2026-05-13
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_1` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Regime is driven by Absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, with reduced volatility and decreasing short-term momentum.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a deviation from this theory.. If close above support level: falsify. Else close below support level: accept. Unless no contrary evidence emerges. Falsified if: close below support level.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.52, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.67, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 5: 2026-05-14
**Current Regime:** Trend=`extended_higher`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_59` (Similarity: 0.848)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *Extended Higher regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Extended Higher regime is driven by extended_higher mechanism; price maintains sequence of higher highs and higher lows, with volume expanding on up days relative to down days.. If NIFTY 50 closes above the prior high: continue holding long positions. Else NIFTY 50 closes below the prior low: rebalance portfolio to favor risk-off strategies. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by extended_higher mechanism; price maintains sequence of higher highs and higher lows.. If close above support level: continue to favor extended_higher. Else close below support level: falsify claim. Unless no contrary evidence emerges. Falsified if: close below support level.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.49, Contradiction=0.08, Validation=0.51
- **Theory+Pattern Metrics (C):** Usefulness=0.64, Contradiction=0.03, Validation=0.56
- **Reuse Decision:** **REUSED**

### Day 6: 2026-05-15
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_44` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *NIFTY 50 trading in a neutral state with low volatility and increasing short-term momentum is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a deviation from this theory.. If close above support level: falsify. Else close below support level: accept. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.52, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.67, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 7: 2026-05-18
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *NIFTY 50 trading within a narrow range with compressed volatility and strengthened breadth is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent market behavior suggests a deviation from this theory.. If close above support level: falsify. Else close below support level: accept. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 8: 2026-05-19
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *NIFTY 50 trades within a compressed trading range, exhibiting normal upper participation, with strengthened breadth; regime is driven by passive absorption.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, with strengthened breadth.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent compression and strengthened breadth suggest a more complex underlying driver.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **MODIFIED**

### Day 9: 2026-05-20
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound market is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **REJECTED**

### Day 10: 2026-05-21
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_13` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound market is driven by passive absorption; price remains range-bound despite weak bear participation.. If bear participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price remains range-bound despite weak bear participation.. If bear participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **REJECTED**

### Day 11: 2026-05-22
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a deviation from this theory.. If close above support level: falsify. Else close below support level: reject. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 12: 2026-05-25
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by increased short-term momentum, indicating a strong bull market participation.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, with increased short-term momentum indicating a strong bull market participation.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a shift towards increased short-term momentum and strong bull market participation.. If short-term momentum increases: favor continuation higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **MODIFIED**

### Day 13: 2026-05-26
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *NIFTY 50 trading within a narrow range, driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, with volume expanding on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a hidden causal mechanism of passive absorption and exhaustion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **MODIFIED**

### Day 14: 2026-05-27
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **REJECTED**

### Day 15: 2026-05-29
**Current Regime:** Trend=`extended_lower`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_53` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *Extended Lower regime is driven by passive exhaustion; price remains lower-bound despite volume contraction.. If breadth strengthens below average: favor continuation lower. Else volatility expands above average: favor breakout lower. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*
- **Theory-Only Generated Theory (B):** *Extended_lower regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by extended_lower mechanism; price maintains lower highs and higher lows despite compressed volatility.. If close below support level: falsify claim. Else price closes above support level: continue claim. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.49
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.26, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.70, Validation=0.39
- **Reuse Decision:** **REJECTED**

### Day 16: 2026-06-01
**Current Regime:** Trend=`closed_lower`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_76` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *NIFTY 50 closes lower with weak short-term momentum and compressed volatility, driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Regime is driven by closed_lower mechanism; price closes below support level, indicating a lack of upward momentum and compressed volatility.. If close < support_level: favor short-term sell. Else close >= support_level: favor long-term buy. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by closed_lower mechanism; price closes below support level, indicating a lack of upward momentum.. If close < support_level: adjust logic branches or assumptions to preemptively handle volume_divergence. Else true: continue with current logic. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.50, Contradiction=0.46, Validation=0.57
- **Theory+Pattern Metrics (C):** Usefulness=0.65, Contradiction=0.34, Validation=0.54
- **Reuse Decision:** **REJECTED**

### Day 17: 2026-06-02
**Current Regime:** Trend=`closed_higher`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_18` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *NIFTY 50 shows signs of a potential reversal, driven by passive absorption; price remains range-bound despite weak short-term momentum and compressed volatility.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Closed-higher regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, but weak short-term momentum and compressed volatility hint at potential reversal.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by closed_higher mechanism; however, current signs of potential reversal suggest a deviation from this theory.. If weak short-term momentum: favor reversal. Else strong bull participation: favor continuation. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.38
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.39, Validation=0.38
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.33, Validation=0.56
- **Reuse Decision:** **MODIFIED**

### Day 18: 2026-06-03
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_13` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *NIFTY 50 trading in a range-bound manner with low volume and compressed volatility is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a deviation from this theory.. If close below support level: falsify. Else no close below support level: continue. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 19: 2026-06-04
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_13` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, current market conditions suggest a deviation from this theory.. If close below support level: falsify claim. Else close above resistance level: favor modified mechanism. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 20: 2026-06-05
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_13` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a hidden causal mechanism of Absorption leading to price structure and volume confirmation.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **MODIFIED**

### Day 21: 2026-06-08
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *NIFTY 50 trading in a range-bound manner with compressed volatility and strengthening breadth is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent market behavior suggests a deviation from this theory.. If close above support level: falsify. Else close below support level: accept. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 22: 2026-06-09
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_58` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=price_structure, cause=resistance_rejection, comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *NIFTY 50 trading in a range-bound manner with compressed volatility and weak short-term momentum is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a deviation from this theory.. If close above support level: falsify. Else close below support level: accept. Unless no contrary evidence emerges. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.52, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.67, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 23: 2026-06-10
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_13` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Regime is driven by Absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, with volume expanding on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a deviation from this theory.. If close below support level: falsify. Else no close below support level: continue. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 24: 2026-06-11
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_13` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *NIFTY 50 trading in a narrow range with low volatility is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, with volume expanding on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by range_bound mechanism; however, recent observations suggest a deviation from this theory.. If close above support level: falsify. Else close below support level: accept. Unless no contrary evidence emerges. Falsified if: close below support level.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 25: 2026-06-12
**Current Regime:** Trend=`extended_higher`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_59` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *Extended higher regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Extended Higher Regime is driven by selective momentum absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by extended_higher mechanism; price maintains sequence of higher highs and higher lows, with compressed volatility and strengthened breadth.. If close above support level: continue to favor range persistence. Else close below support level: falsify claim and adjust logic branches or assumptions. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.52, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.67, Contradiction=0.03, Validation=0.56
- **Reuse Decision:** **REUSED**

### Day 26: 2026-06-15
**Current Regime:** Trend=`closed_lower`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_38` (Similarity: 0.848)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence`
- **Baseline Generated Theory (A):** *Closed Lower regime is driven by weak bear participation; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Closed_lower regime is driven by closed_lower mechanism; price remains range-bound despite weak bear participation.. If weak bear participation: favor range persistence. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by closed_lower mechanism; however, current market conditions suggest a deviation from this theory.. If close below support level: falsify claim. Else compressed volatility and weak bear participation: modify claim to reflect adjusted logic branches or assumptions. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.49, Contradiction=0.08, Validation=0.57
- **Theory+Pattern Metrics (C):** Usefulness=0.64, Contradiction=0.03, Validation=0.62
- **Reuse Decision:** **MODIFIED**

### Day 27: 2026-06-16
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `theory_warmup_6` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by passive absorption; price remains within a narrow trading range despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.03, Validation=0.47
- **Reuse Decision:** **REJECTED**

### Day 28: 2026-06-17
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `None` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by exhaustion; price maintains sequence of higher highs and higher lows despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, with volume expanding on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Range-bound regime is driven by exhaustion; price structure maintains sequence of higher highs and higher lows despite volume divergence.. If price action daily structure shows higher high, higher low: favor range persistence. Else volume confirmation shows volume_divergence under contradictions [closed_higher, closed_lower, compressed, extended_higher, extended_lower]: favor breakout higher. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.00, Validation=0.38
- **Reuse Decision:** **REJECTED**

### Day 29: 2026-06-18
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `None` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by passive absorption; price remains compressed despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Regime is driven by Absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.42
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.08, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.00, Validation=0.47
- **Reuse Decision:** **REJECTED**

### Day 30: 2026-06-19
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
- **Retrieved ID:** `None` (Similarity: 0.988)
- **Retrieved Patterns:** `comp=volume_confirmation, cause=volume_divergence, comp=price_structure, cause=resistance_rejection`
- **Baseline Generated Theory (A):** *Range-bound regime is driven by passive absorption; price remains within a narrow trading range despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory-Only Generated Theory (B):** *Range-bound regime is driven by absorption; price maintains sequence of higher highs and higher lows, with volume expanding on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Theory+Pattern Generated Theory (C):** *Range-bound regime is driven by exhaustion; price structure maintains sequence of higher highs and higher lows despite volume divergence.. If price action daily structure shows higher high, higher low: favor range persistence. Else volume confirmation shows volume expansion on up days relative to down days: favor breakout higher. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*
- **Baseline Metrics (A):** Usefulness=0.28, Contradiction=0.00, Validation=0.33
- **Theory-Only Metrics (B):** Usefulness=0.53, Contradiction=0.09, Validation=0.42
- **Theory+Pattern Metrics (C):** Usefulness=0.68, Contradiction=0.00, Validation=0.38
- **Reuse Decision:** **REJECTED**
