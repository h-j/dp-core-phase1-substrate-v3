# EDGE TEST — FORWARD PAPER-TRADING AUTOMATION & OPERATING GUIDE

**Status**: OPERATIONAL GUIDE  
**Target Document**: `experiments/edge_test/README.md`  

---

## 1. DAILY OPERATING PROCEDURE (5-LINE GUIDE)

1. **Ingest New Market Day**: Run `poetry run python -m experiments.edge_test.forward_runner --data data/nifty_daily_3y.csv` at EOD after market close.
2. **Verify Signal Registration**: Ensure `forward_ledger.jsonl` contains the `SIGNAL_GENERATED` record for day $t+1$ BEFORE day $t+1$ prices exist.
3. **Verify Settlement**: Confirm previous open signal settled against today's Open price fill with sequence invariant ($S_{\text{seq}} < O_{\text{seq}}$).
4. **Generate Status Report**: Run `poetry run python -m experiments.edge_test.forward_report` to update `forward_report.md`.
5. **Check Gating Banner**: Read banner output (`INSUFFICIENT SAMPLE — no conclusion permitted` vs `CLAIM ELIGIBLE`).

---

## 2. EXACT CONDITIONS FOR PRINTING "CLAIM ELIGIBLE"

The forward report generator (`forward_report.py`) will print **`CLAIM ELIGIBLE`** ONLY when ALL seven of the following pre-registered conditions hold simultaneously:

1. **Minimum Evaluation Duration**: Total evaluation days $\ge 250$ trading days.
2. **Minimum Exposure**: Active position days $\ge 60$ position-days (days not flat).
3. **Net Annualized Sharpe Ratio**: $\text{Sharpe}_{\text{net}} \ge 1.00$ (after all-in $20.5$ bps cost model).
4. **Probabilistic Sharpe Ratio**: $\text{PSR}(0) \ge 0.9500$ (Bailey & López de Prado 2012).
5. **Stationary Bootstrap Significance**: $p < 0.0500$ ($10,000$ resamples, block length $10$).
6. **Placebo Controls**: 5-day lagged Sharpe $\le 0.20$ AND direction-shuffled return $> 95\text{th}$ percentile ($1,000$ perms).
7. **Kill Criteria Un-triggered**: Peak-to-trough drawdown $< 15.0\%$ AND no $125$ trading days elapsed with $\text{PSR} < 0.50$.

---

## 3. AUTOMATION & SCHEDULING NOTE

### GitHub Actions Daily Workflow Example (`.github/workflows/forward_paper_trading.yml`)

```yaml
name: Forward Paper Trading Execution

on:
  schedule:
    - cron: '30 11 * * 1-5'  # Run daily at 17:00 IST (11:30 UTC) Mon-Fri
  workflow_dispatch:

jobs:
  paper_trade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - name: Install Poetry & Dependencies
        run: |
          pip install poetry
          poetry install
      - name: Execute Daily Forward Step
        run: |
          poetry run python -m experiments.edge_test.forward_runner --data data/nifty_daily_3y.csv
          poetry run python -m experiments.edge_test.forward_report
      - name: Commit & Push Forward Ledger
        run: |
          git config user.name "Forward Paper Trading Bot"
          git config user.email "bot@drishtipragya.org"
          git add experiments/edge_test/results/
          git commit -m "chore(edge_test): daily paper trading step [skip ci]" || exit 0
          git push
```

---

## 4. MISSED DAY & NO-BACKFILL POLICY

- **Missed Day Behavior**: If a day or weekend gap is missed, the runner logs `[SKIPPED NO SIGNAL]` and sets the position to **FLAT ($0$)**.
- **Strict Prohibition**: Retroactive backfilling of signals for days whose market outcomes already exist is strictly prohibited and guarded at runtime.
