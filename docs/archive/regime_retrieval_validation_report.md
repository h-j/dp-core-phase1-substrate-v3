# Regime Retrieval Validation Report

**Execution Date:** 2026-06-21 21:50:12
**Objective:** Shadow mode validation comparing independently generated theories with retrieved historical theories.

---

## 1. Executive Summary

- **Success Criteria Status:** ★ PASSED
- **Target Metric:** $\ge 70\%$ of retrieved theories classified as RELEVANT (non-degrading)
- **Actual Metric:** **93.33%**
- **Total Retrieved Theories:** 90
  - **RELEVANT:** 84 (93.3%)
  - **PARTIALLY_RELEVANT:** 3 (3.3%)
  - **IRRELEVANT:** 3 (3.3%)

---

## 2. Step-by-Step Validation Logs

### Day 1: 2026-05-08
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by exhaustion; price maintains sequence of higher highs and higher lows despite volume expansion.. If liquidity decreases: favor range persistence. Else volatility remains compressed: favor breakout lower. Unless participation evaporates entirely. Falsified if: decisive close above the prior resistance floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-11 | 0.988 | `theory_warmup_3` | 0.28 | 0.50 | 0.16 | **RELEVANT** |
| 2025-12-09 | 0.848 | `theory_warmup_1` | 0.28 | 0.50 | 0.16 | **RELEVANT** |
| 2025-12-10 | 0.848 | `theory_warmup_2` | 0.28 | 0.50 | 0.16 | **RELEVANT** |


### Day 2: 2026-05-11
**Current Regime:** Trend=`closed_lower`, Volatility=`compressed`
**Independently Generated Theory:** *Closed_lower regime is driven by exhaustion; price closes lower despite weak short-term momentum and compressed volatility.. If short-term momentum strengthens: expect reversal. Else volatility remains compressed: expect range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-01-09 | 0.848 | `theory_warmup_23` | 0.28 | 0.49 | 0.16 | **RELEVANT** |
| 2026-01-23 | 0.848 | `theory_warmup_32` | 0.28 | 0.49 | 0.16 | **RELEVANT** |
| 2026-04-01 | 0.848 | `theory_warmup_76` | 0.28 | 0.49 | 0.16 | **RELEVANT** |


### Day 3: 2026-05-12
**Current Regime:** Trend=`extended_lower`, Volatility=`compressed`
**Independently Generated Theory:** *Extended Lower regime is driven by passive exhaustion; price weakens despite volume expansion.. If participation widens above average: favor breakout lower. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-01-08 | 0.848 | `theory_warmup_22` | 0.28 | 0.49 | 0.16 | **RELEVANT** |
| 2026-01-20 | 0.848 | `theory_warmup_29` | 0.28 | 0.49 | 0.16 | **RELEVANT** |
| 2026-02-24 | 0.848 | `theory_warmup_53` | 0.28 | 0.49 | 0.16 | **RELEVANT** |


### Day 4: 2026-05-13
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound NIFTY 50 trading is driven by passive absorption; price remains within a narrow range despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-09 | 0.988 | `theory_warmup_1` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2025-12-10 | 0.988 | `theory_warmup_2` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2025-12-11 | 0.848 | `theory_warmup_3` | 0.28 | 0.52 | 0.09 | **RELEVANT** |


### Day 5: 2026-05-14
**Current Regime:** Trend=`extended_higher`, Volatility=`compressed`
**Independently Generated Theory:** *Extended Higher regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-03-05 | 0.848 | `theory_warmup_59` | 0.28 | 0.49 | 0.09 | **RELEVANT** |
| 2026-03-16 | 0.848 | `theory_warmup_66` | 0.28 | 0.49 | 0.09 | **RELEVANT** |
| 2026-03-25 | 0.848 | `theory_warmup_73` | 0.28 | 0.49 | 0.09 | **RELEVANT** |


### Day 6: 2026-05-15
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *NIFTY 50 trading in a neutral state with low volatility and increasing short-term momentum is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-02-11 | 0.988 | `theory_warmup_44` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2026-04-29 | 0.988 | `theory_warmup_94` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2025-12-12 | 0.848 | `theory_warmup_4` | 0.28 | 0.52 | 0.09 | **RELEVANT** |


### Day 7: 2026-05-18
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound NIFTY 50 trading is driven by passive absorption; price remains within a narrow range despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 8: 2026-05-19
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 9: 2026-05-20
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound market is driven by passive exhaustion; price maintains sequence of higher highs and higher lows despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 10: 2026-05-21
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound market is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-26 | 0.988 | `theory_warmup_13` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-05 | 0.988 | `theory_warmup_19` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-14 | 0.988 | `theory_warmup_26` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 11: 2026-05-22
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by exhaustion; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 12: 2026-05-25
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by increased short-term momentum, indicating a strong bull market participation.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.08 | **RELEVANT** |


### Day 13: 2026-05-26
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound NIFTY 50 trading is driven by passive absorption; price remains within a narrow range despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 14: 2026-05-27
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 15: 2026-05-29
**Current Regime:** Trend=`extended_lower`, Volatility=`compressed`
**Independently Generated Theory:** *Extended Lower regime is driven by passive exhaustion; price weakens as volume confirms trend.. If breadth strengthens above average: favor continuation lower. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-02-24 | 0.988 | `theory_warmup_53` | 0.28 | 0.53 | 0.32 | **PARTIALLY_RELEVANT** |
| 2026-03-19 | 0.988 | `theory_warmup_69` | 0.28 | 0.53 | 0.32 | **PARTIALLY_RELEVANT** |
| 2026-03-23 | 0.988 | `theory_warmup_71` | 0.28 | 0.53 | 0.32 | **PARTIALLY_RELEVANT** |


### Day 16: 2026-06-01
**Current Regime:** Trend=`closed_lower`, Volatility=`compressed`
**Independently Generated Theory:** *Closed_lower regime is driven by passive exhaustion; price closes lower with weak short-term momentum and compressed volatility.. If short-term momentum weakens: favor range persistence. Else volatility remains compressed: favor breakout lower. Unless liquidity evaporates entirely. Falsified if: decisive close above the prior resistance floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-04-01 | 0.988 | `theory_warmup_76` | 0.28 | 0.50 | 0.16 | **RELEVANT** |
| 2026-01-09 | 0.848 | `theory_warmup_23` | 0.28 | 0.50 | 0.16 | **RELEVANT** |
| 2026-01-23 | 0.848 | `theory_warmup_32` | 0.28 | 0.50 | 0.16 | **RELEVANT** |


### Day 17: 2026-06-02
**Current Regime:** Trend=`closed_higher`, Volatility=`compressed`
**Independently Generated Theory:** *NIFTY 50 is driven by passive absorption; price maintains sequence of higher highs and higher lows despite weak short-term momentum and compressed volatility, but still maintains strong bull participation.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-01-02 | 0.988 | `theory_warmup_18` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-02-16 | 0.988 | `theory_warmup_47` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-04-27 | 0.988 | `theory_warmup_92` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 18: 2026-06-03
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound NIFTY 50 trading is driven by passive absorption; price remains within established bounds despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-26 | 0.988 | `theory_warmup_13` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-05 | 0.988 | `theory_warmup_19` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-14 | 0.988 | `theory_warmup_26` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 19: 2026-06-04
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Regime is driven by passive absorption; price remains range-bound despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-26 | 0.988 | `theory_warmup_13` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2026-01-05 | 0.988 | `theory_warmup_19` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2026-01-14 | 0.988 | `theory_warmup_26` | 0.28 | 0.53 | 0.08 | **RELEVANT** |


### Day 20: 2026-06-05
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by passive exhaustion; price maintains sequence of higher highs and higher lows despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-26 | 0.988 | `theory_warmup_13` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2026-01-05 | 0.988 | `theory_warmup_19` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2026-01-14 | 0.988 | `theory_warmup_26` | 0.28 | 0.53 | 0.08 | **RELEVANT** |


### Day 21: 2026-06-08
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound NIFTY 50 trading is driven by passive absorption; price remains within established bounds despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 22: 2026-06-09
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound NIFTY 50 trading is driven by passive absorption; price remains within established bounds despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-03-04 | 0.988 | `theory_warmup_58` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2026-04-02 | 0.988 | `theory_warmup_77` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2026-01-21 | 0.928 | `theory_warmup_30` | 0.28 | 0.52 | 0.09 | **RELEVANT** |


### Day 23: 2026-06-10
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by exhaustion; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-26 | 0.988 | `theory_warmup_13` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-05 | 0.988 | `theory_warmup_19` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-14 | 0.988 | `theory_warmup_26` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 24: 2026-06-11
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound NIFTY 50 trading is driven by passive absorption; price remains within established bounds despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-26 | 0.988 | `theory_warmup_13` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-05 | 0.988 | `theory_warmup_19` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-01-14 | 0.988 | `theory_warmup_26` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 25: 2026-06-12
**Current Regime:** Trend=`extended_higher`, Volatility=`compressed`
**Independently Generated Theory:** *Extended higher regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-03-05 | 0.988 | `theory_warmup_59` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2026-03-25 | 0.988 | `theory_warmup_73` | 0.28 | 0.52 | 0.09 | **RELEVANT** |
| 2026-03-16 | 0.848 | `theory_warmup_66` | 0.28 | 0.52 | 0.09 | **RELEVANT** |


### Day 26: 2026-06-15
**Current Regime:** Trend=`closed_lower`, Volatility=`compressed`
**Independently Generated Theory:** *Closed_lower regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-02-03 | 0.848 | `theory_warmup_38` | 0.28 | 0.49 | 0.96 | **IRRELEVANT** |
| 2026-04-01 | 0.848 | `theory_warmup_76` | 0.28 | 0.49 | 0.96 | **IRRELEVANT** |
| 2026-04-09 | 0.848 | `theory_warmup_81` | 0.28 | 0.49 | 0.96 | **IRRELEVANT** |


### Day 27: 2026-06-16
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2025-12-16 | 0.988 | `theory_warmup_6` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-17 | 0.988 | `theory_warmup_7` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2025-12-18 | 0.988 | `theory_warmup_8` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 28: 2026-06-17
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by exhaustion; price maintains sequence of higher highs and higher lows despite volume expansion.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-01-30 | 0.988 | `theory_warmup_36` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2026-02-04 | 0.988 | `theory_warmup_39` | 0.28 | 0.53 | 0.08 | **RELEVANT** |
| 2026-02-23 | 0.988 | `theory_warmup_52` | 0.28 | 0.53 | 0.08 | **RELEVANT** |


### Day 29: 2026-06-18
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-01-30 | 0.988 | `theory_warmup_36` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-02-04 | 0.988 | `theory_warmup_39` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-02-23 | 0.988 | `theory_warmup_52` | 0.28 | 0.53 | 0.09 | **RELEVANT** |


### Day 30: 2026-06-19
**Current Regime:** Trend=`range_bound`, Volatility=`compressed`
**Independently Generated Theory:** *Range-bound regime is driven by passive absorption; price maintains sequence of higher highs and higher lows, while volume expands on up days relative to down days.. If participation widens above average: favor breakout higher. Else volatility remains compressed: favor range persistence. Unless liquidity evaporates entirely. Falsified if: decisive close below the prior support floor.*

| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |
|---|---|---|---|---|---|---|
| 2026-01-30 | 0.988 | `theory_warmup_36` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-02-04 | 0.988 | `theory_warmup_39` | 0.28 | 0.53 | 0.09 | **RELEVANT** |
| 2026-02-23 | 0.988 | `theory_warmup_52` | 0.28 | 0.53 | 0.09 | **RELEVANT** |

