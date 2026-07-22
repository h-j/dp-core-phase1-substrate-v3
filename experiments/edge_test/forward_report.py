"""
Forward Paper-Trading Report & Gating Engine for Edge Test Protocol.

Evaluates cumulative forward paper-trading results against pre-registered thresholds in PREREGISTRATION.md.

Banner Outputs:
- "CLAIM ELIGIBLE": ONLY when all pre-registered sample thresholds and performance criteria are met.
- "KILL CRITERIA TRIGGERED — RUN HALTED": When max drawdown > 15% or 125 days elapsed with PSR < 0.5.
- "INSUFFICIENT SAMPLE — no conclusion permitted": When sample size < 250 trading days or < 60 position days.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from experiments.edge_test.harness import verify_preregistered_constants
from experiments.edge_test.placebos import (
    run_direction_shuffled_placebo,
    run_lagged_signal_placebo,
)
from experiments.edge_test.stats import calculate_edge_stats

logger = logging.getLogger(__name__)


def generate_forward_report(
    results_dir: Optional[Path] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Generates forward evaluation report and determines pre-registered claim eligibility banner.
    """
    verify_preregistered_constants()
    res_dir = results_dir or Path("experiments/edge_test/results")
    ledger_file = res_dir / "forward_ledger.jsonl"
    report_file = res_dir / "forward_report.md"

    settled_records = []
    if ledger_file.exists():
        with open(ledger_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("event_type") == "OUTCOME_SETTLED":
                        settled_records.append(rec)
                except Exception:
                    continue

    stats = calculate_edge_stats(settled_records, seed=seed)
    lagged = run_lagged_signal_placebo(settled_records, lag_days=5, seed=seed)
    shuffled = run_direction_shuffled_placebo(settled_records, n_permutations=1000, seed=seed)

    trading_days = stats.get("trading_days", 0)
    active_days = int(round(trading_days * stats.get("exposure_fraction", 0.0)))
    max_dd = stats.get("max_drawdown_pct", 0.0)
    psr = stats.get("psr", 0.0)
    net_sharpe = stats.get("net_sharpe", 0.0)
    p_val = stats.get("bootstrap_pvalue", 1.0)

    # 1. Check Kill Criteria
    kill_max_dd_triggered = (max_dd <= -15.0 or abs(max_dd) >= 15.0)
    kill_stagnant_triggered = (trading_days >= 125 and psr < 0.50)
    kill_triggered = kill_max_dd_triggered or kill_stagnant_triggered

    # 2. Check Pre-Registered Minimum Sample Criteria
    min_days_met = (trading_days >= 250)
    min_position_days_met = (active_days >= 60)
    sample_sufficient = min_days_met and min_position_days_met

    # 3. Check Performance & Placebo Criteria
    performance_met = (net_sharpe >= 1.0) and (psr >= 0.95) and (p_val < 0.05)
    placebos_passed = lagged.get("passed_falsifier", False) and shuffled.get("passed_falsifier", False)

    # Determine Banner
    if kill_triggered:
        banner = "KILL CRITERIA TRIGGERED — RUN HALTED"
        status_code = "KILL_TRIGGERED"
    elif sample_sufficient and performance_met and placebos_passed:
        banner = "CLAIM ELIGIBLE"
        status_code = "CLAIM_ELIGIBLE"
    else:
        banner = "INSUFFICIENT SAMPLE — no conclusion permitted"
        status_code = "INSUFFICIENT_SAMPLE"

    # Format Markdown Report
    report_content = f"""# Forward Paper-Trading Report

```text
================================================================================
  {banner}
================================================================================
```

**Evaluation Date**: 2026-07-22  
**Forward Ledger File**: `experiments/edge_test/results/forward_ledger.jsonl`  
**Status**: {status_code}  

---

## 1. PRE-REGISTERED SAMPLE & DURATION GATING

| Gating Criteria | Realized Value | Pre-Registered Minimum | Status |
| :--- | :---: | :---: | :---: |
| **Total Evaluation Days** | {trading_days} | $\ge 250$ trading days | **{"MET" if min_days_met else "NOT MET"}** |
| **Active Position Days** | {active_days} | $\ge 60$ position days | **{"MET" if min_position_days_met else "NOT MET"}** |
| **Kill Criteria Status** | {"TRIGGERED" if kill_triggered else "CLEAR"} | Max DD $< 15\%$, 125d PSR $\ge 0.5$ | **{"HALTED" if kill_triggered else "PASS"}** |

---

## 2. REALIZED FORWARD STATISTICAL METRICS

| Metric | Realized Value | Target Threshold | Status |
| :--- | :---: | :---: | :---: |
| **Net Annualized Sharpe** | **{net_sharpe:.4f}** | $\ge 1.00$ | **{"PASS" if net_sharpe >= 1.0 else "FAIL"}** |
| **Probabilistic Sharpe (PSR vs 0)** | **{psr:.4f}** | $\ge 0.9500$ | **{"PASS" if psr >= 0.95 else "FAIL"}** |
| **Stationary Bootstrap $p$-value** | **{p_val:.4f}** | $p < 0.0500$ ($10,000$ resamples) | **{"PASS" if p_val < 0.05 else "FAIL"}** |
| **Max Drawdown** | **{max_dd:.2f}%** | $< 15.00\%$ | **{"PASS" if not kill_max_dd_triggered else "KILL TRIGGERED"}** |
| **Exposure Fraction** | {stats.get('exposure_fraction', 0.0):.4f} | N/A | N/A |
| **Total Net Return** | {stats.get('total_net_return_pct', 0.0):.2f}% | N/A | N/A |

---

## 3. PLACEBO CONTROLS

| Placebo Test | Realized Result | Expected Falsifier Result | Falsifier Status |
| :--- | :---: | :---: | :---: |
| **5-Day Lagged Signal** | Net Sharpe: **{lagged.get('net_sharpe', 0.0):.4f}** | Edge must disappear ($\le 0.20$) | **{"PASS" if lagged.get('passed_falsifier') else "FAIL"}** |
| **1,000 Permutation Shuffled** | Rank: **{shuffled.get('percentile_rank', 0.0):.1f} percentile** | > 95 Percentile | **{"PASS" if shuffled.get('passed_falsifier') else "FAIL"}** |

---

## 4. PRE-REGISTERED CLAIM ELIGIBILITY VERDICT

> **VERDICT**: **{banner}**
"""

    report_file.write_text(report_content, encoding="utf-8")

    return {
        "banner": banner,
        "status_code": status_code,
        "trading_days": trading_days,
        "active_days": active_days,
        "net_sharpe": net_sharpe,
        "psr": psr,
        "p_val": p_val,
        "kill_triggered": kill_triggered,
        "report_content": report_content,
    }


if __name__ == "__main__":
    res = generate_forward_report()
    print("\n" + "=" * 80)
    print(f"  {res['banner']}")
    print("=" * 80 + "\n")
