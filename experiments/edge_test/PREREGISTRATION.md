# PRE-REGISTRATION PROTOCOL: THEORY RELIABILITY EDGE TEST

**Status**: PRE-REGISTERED (FROZEN UPON COMMIT)  
**Protocol Version**: 1.0.0  
**Commit Target**: `experiments/edge_test/PREREGISTRATION.md`  

---

## a) HYPOTHESIS

> **Exact Wording**:  
> *"A mechanical daily trading rule derived solely from DP theory reliability bands produces net-of-cost returns distinguishable from zero at the pre-registered significance level, on out-of-sample data the substrate has never processed."*

- **Null Hypothesis ($H_0$)**: Net returns are indistinguishable from zero ($E[R_{\text{net}}] \le 0$).
- **Alternative Hypothesis ($H_1$)**: Net returns are strictly positive and statistically distinguishable from zero ($E[R_{\text{net}}] > 0$) at $p < 0.05$.

---

## b) MECHANICAL RULE

The trading rule is completely deterministic with zero discretionary intervention.

### 1. Universe Selection
- **Instruments**: `<OWNER DECIDES: e.g., NIFTY index futures proxy + 4 liquid NSE large-caps (RELIANCE, TCS, INFYS, HDFCBANK)>`.
- **Constraint**: The mechanical rule must be executed identically across all universe instruments without asset-specific tuning.

### 2. Signal Generation (End-of-Day $t$)
For each instrument at the end of trading day $t$:
1. **Theory Collection**: Collect all active theories in the **established** reliability band ($\text{reliability} > 0.75$).
2. **Scope Evaluation**: Filter theories whose scope predicate evaluates `True` for day $t$.
3. **Activation Check**: Filter theories whose structured activation predicate fires for day $t$.
4. **Directional Commitment**: Each qualifying theory provides a directional commitment $d_i \in \{-1, +1\}$ derived strictly from its fallback payload.
5. **Combined Signal & Target Position ($P_{t+1}$)**:
   $$\text{Weighted Sum}_t = \sum_{i \in \text{Established}} \text{reliability}_i \cdot d_i$$
   $$P_{t+1} = \begin{cases} \text{sign}(\text{Weighted Sum}_t) & \text{if } |\text{Weighted Sum}_t| \ge 0.25 \\ 0 \text{ (Flat)} & \text{if } |\text{Weighted Sum}_t| < 0.25 \text{ or no established theory fires} \end{cases}$$
   *(Note: Signal threshold defaults to $0.25$. Owner decision parameter: `<OWNER DECIDES: Signal threshold threshold_default = 0.25>`)*

### 3. Position Sizing & Execution
- **Position Size**: Fixed fraction `<default: 100% notional, single unit - no compounding, no sizing cleverness>`.
- **Execution Assumption**: Execution occurs at the **Next-Day Open fill** (day $t+1$ Open price). No intraday logic or mid-day rebalancing.
- **Strict Data Access Isolation**: The rule reads ONLY theory reliability score, scope predicate, activation predicate, and directional commitment. It **MUST NOT** read raw asset prices or market indicators to make trading decisions beyond predicate inputs.

---

## c) COST MODEL (India Market, Conservative Specification)

All trading cost parameters are explicitly declared and parameterized for the Indian equity/derivatives market.

| Fee / Cost Component | Default Rate / Parameter | Instrument Match / Specification |
| :--- | :--- | :--- |
| **Brokerage** | `0.03%` (3.0 bps) per side | Standard institutional/retail equity futures brokerage |
| **STT (Securities Transaction Tax)** | `0.025%` (2.5 bps) on Sell side | Intraday / Futures proxy rate (`<OWNER DECIDES: Confirm instrument class & matching rate: Delivery 0.1% vs Futures 0.025%>`) |
| **Exchange Turnover Charges** | `0.003%` (0.3 bps) per side | Combined NSE / BSE transaction charges |
| **GST** | `18.0%` on Brokerage + Exch Charges | $18\% \times (3.0 + 0.3) = 0.594$ bps per side |
| **SEBI & Stamp Duty Charges** | `0.002%` (0.2 bps) on Buy side | Statutory SEBI turnover & state stamp duty |
| **Slippage** | `0.05%` (5.0 bps) per side | Conservatively modeled market impact vs. liquid NSE order book (`<OWNER DECIDES: Justify slippage assumption vs instrument liquidity>`) |

### All-In Round-Trip Cost Calculation

$$\text{Buy Side Cost} = 3.0 \text{ (Brokerage)} + 0.3 \text{ (Exch)} + 0.594 \text{ (GST)} + 0.2 \text{ (Stamp/SEBI)} + 5.0 \text{ (Slippage)} = 9.094 \text{ bps}$$
$$\text{Sell Side Cost} = 3.0 \text{ (Brokerage)} + 2.5 \text{ (STT)} + 0.3 \text{ (Exch)} + 0.594 \text{ (GST)} + 5.0 \text{ (Slippage)} = 11.394 \text{ bps}$$

$$\mathbf{\text{All-In Round-Trip Cost}} = 9.094 + 11.394 = \mathbf{20.488 \text{ bps}} \approx \mathbf{20.5 \text{ bps}}$$

---

## d) WALK-FORWARD SCHEME

### 1. Historical Walk-Forward (Diagnostic Only)
- **Anchored Walk-Forward Protocol**: The substrate accumulates beliefs on window $[t_{\text{start}}, t_{\text{eval}}]$. Trades are scored on $[t_{\text{eval}}, t_{\text{eval}} + 63 \text{ trading days}]$.
- **Freezing Rule**: ALL learning constants and trading rule logic are frozen. Confidence updates and belief accumulation continue (learning continues; the RULE and CONSTANTS are what remain frozen).
- **Roll Step**: Roll $t_{\text{eval}}$ forward by $63$ trading days.
- **Minimum Out-of-Sample Size**: Minimum total $500$ out-of-sample trading days across the universe.

### 2. Forward Walk-Forward (The Primary Registration Test)
- **Protocol**: Daily paper-trading starting on the first trading day after this document's commit date: `<OWNER DECIDES: Start Date e.g., 2026-07-23>`.
- **Minimum Evaluation Window**: Minimum duration before ANY claim can be evaluated or published: `<default: 250 trading days AND >= 60 position-days (days not flat)>`.
- **No Early Stopping**: Interim stopping or cherry-picking on favorable early results is strictly prohibited.

---

## e) SUCCESS CRITERIA

All four criteria must hold simultaneously on the FORWARD run to claim edge:

1. **Net Annualized Sharpe Ratio**:  
   $$\text{Sharpe}_{\text{net}} \ge 1.0$$  
   Computed on daily net returns after deducting the all-in $20.5$ bps round-trip cost model.  
   *(Owner decision parameter: `<OWNER DECIDES: Target Net Sharpe threshold_default = 1.0>`)*

2. **Probabilistic Sharpe Ratio (PSR)**:  
   $$\text{PSR}(0) \ge 0.95$$  
   Computed against a benchmark Sharpe of $0.0$ using Bailey & López de Prado (2012) formulation with realized return skewness and kurtosis.

3. **Stationary Bootstrap Significance**:  
   Stationary-bootstrap $p$-value for mean net daily return $> 0$:  
   $$p < 0.05$$  
   Evaluated using $10,000$ resamples with a mean block length of $10$ trading days (Politis & Romano, 1994).

4. **Buy-and-Hold Reporting Benchmark**:  
   Net total return comparison against a buy-and-hold benchmark of the same universe over the identical period. (Beating B&H is NOT a required pass/fail criterion, but MUST be explicitly reported).

---

## f) PLACEBO CONTROLS (Pre-Registered Falsifiers)

Two placebo control experiments must be executed on the identical evaluation dataset:

1. **Lagged Signal Control (5-Day Lag)**:  
   - Shift the generated signal $P_t$ by $+5$ trading days.  
   - **Falsification Expectation**: The trading edge must disappear ($\text{Sharpe}_{\text{lagged}} \le 0.2$).

2. **Direction-Shuffled Control (1,000 Permutations)**:  
   - Permute the directional commitments $d_i$ randomly across the test period ($1,000$ iterations).  
   - **Falsification Expectation**: Realized net return of the unpermuted rule must sit strictly above the **95th percentile** of the shuffled return distribution ($p_{\text{perm}} < 0.05$).

> **CRITICAL RULE**: If either placebo control "passes" (shows positive edge comparable to the true signal), the experimental result is **VOID**, regardless of the realized Sharpe ratio.

---

## g) KILL CRITERIA

The forward paper-trading run must immediately halt and record a definitive **FAILURE** if either condition triggers:

1. **Maximum Drawdown Threshold**: Peak-to-trough paper equity drawdown exceeds `<default: 15%>` (`<OWNER DECIDES: Max Drawdown Kill Limit default = 15%>`).
2. **Stagnant Performance Threshold**: $125$ trading days elapsed with $\text{PSR} < 0.50$.

---

## h) AMENDMENT LOG

| Date | Amendment / Change Description | Reason & Justification | Impact on Forward Clock |
| :--- | :--- | :--- | :--- |
| **2026-07-22** | Initial pre-registration document commit. | Baseline specification of edge test protocol. | Clock initialized. |

*(Note: Any modification to thresholds, rules, or universes after initial commit MUST be appended to this log and automatically RESTARTS the forward evaluation clock).*
