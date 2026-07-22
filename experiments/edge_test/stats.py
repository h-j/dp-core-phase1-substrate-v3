"""
Statistical Analysis & Risk Engine for Edge Test Experiments.

Computes pre-registered metrics:
- Net & Gross Annualized Sharpe Ratio
- Probabilistic Sharpe Ratio (PSR vs Sharpe 0, Bailey & López de Prado 2012)
- Stationary Bootstrap P-value (Politis & Romano 1994, 10,000 resamples, block length 10)
- Max Drawdown, Hit Rate, Turnover, Cost Drag, and Exposure Fraction.
"""
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


def norm_cdf(z: float) -> float:
    """Standard normal cumulative distribution function (CDF)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def compute_sample_skew_kurtosis(arr: np.ndarray) -> Tuple[float, float]:
    """Computes sample skewness and Pearson kurtosis (normal = 3.0)."""
    n = len(arr)
    if n <= 2:
        return 0.0, 3.0
    mean_val = float(np.mean(arr))
    std_val = float(np.std(arr, ddof=0))
    if std_val < 1e-12:
        return 0.0, 3.0

    diff = arr - mean_val
    m3 = float(np.mean(diff ** 3))
    m4 = float(np.mean(diff ** 4))

    skew = m3 / (std_val ** 3)
    kurt = m4 / (std_val ** 4)  # Pearson kurtosis
    return skew, kurt


def compute_psr(daily_sharpe: float, n_obs: int, skewness: float, kurtosis: float, benchmark_sharpe: float = 0.0) -> float:
    """
    Computes Probabilistic Sharpe Ratio (PSR) per Bailey & López de Prado (2012).
    
    PSR(sr_star) = Z[ (sr - sr_star) * sqrt(n - 1) / sqrt(1 - skew * sr + (kurt - 1)/4 * sr^2) ]
    """
    if n_obs <= 1:
        return 0.0
    denom_sq = 1.0 - skewness * daily_sharpe + ((kurtosis - 1.0) / 4.0) * (daily_sharpe ** 2)
    if denom_sq <= 0:
        denom = 1.0
    else:
        denom = math.sqrt(denom_sq)
    
    z_stat = ((daily_sharpe - benchmark_sharpe) * math.sqrt(n_obs - 1)) / denom
    return float(norm_cdf(z_stat))


def stationary_bootstrap_pvalue(
    net_returns: np.ndarray,
    n_resamples: int = 10000,
    mean_block_length: float = 10.0,
    seed: int = 42,
) -> float:
    """
    Computes stationary bootstrap p-value for E[R_net] > 0 per Politis & Romano (1994).
    Uses a fixed random seed for 100% deterministic resample outputs.
    """
    n = len(net_returns)
    if n == 0:
        return 1.0

    rng = np.random.RandomState(seed)
    p_geom = 1.0 / mean_block_length

    block_lengths = rng.geometric(p_geom, size=n_resamples * max(10, n // int(mean_block_length) + 5))
    start_indices = rng.randint(0, n, size=len(block_lengths))

    boot_means = np.zeros(n_resamples)
    b_idx = 0

    for i in range(n_resamples):
        sample_indices = []
        while len(sample_indices) < n:
            b_len = block_lengths[b_idx]
            s_idx = start_indices[b_idx]
            b_idx += 1
            needed = n - len(sample_indices)
            take_len = min(b_len, needed)
            idx_range = (s_idx + np.arange(take_len)) % n
            sample_indices.extend(idx_range)
        boot_means[i] = np.mean(net_returns[sample_indices])

    p_val = float(np.mean(boot_means <= 0.0))
    return p_val


def calculate_edge_stats(
    trade_records: List[Dict[str, Any]],
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Calculates complete pre-registered statistical metrics from trade records.
    """
    if not trade_records:
        return {
            "trading_days": 0,
            "net_sharpe": 0.0,
            "gross_sharpe": 0.0,
            "psr": 0.0,
            "bootstrap_pvalue": 1.0,
            "max_drawdown_pct": 0.0,
            "hit_rate_pct": 0.0,
            "turnover_daily": 0.0,
            "cost_drag_bps_year": 0.0,
            "exposure_fraction": 0.0,
            "total_net_return_pct": 0.0,
            "seed": seed,
        }

    net_rets = np.array([r.get("net_return", 0.0) for r in trade_records], dtype=float)
    gross_rets = np.array([r.get("gross_return", 0.0) for r in trade_records], dtype=float)
    positions = np.array([r.get("target_position", 0) for r in trade_records], dtype=int)
    costs_bps = np.array([r.get("cost_bps", 0.0) for r in trade_records], dtype=float)

    n_obs = len(net_rets)

    # 1. Sharpe Ratios
    std_net = float(np.std(net_rets, ddof=1)) if n_obs > 1 else 0.0
    mean_net = float(np.mean(net_rets))
    daily_net_sharpe = mean_net / std_net if std_net > 1e-12 else 0.0
    net_sharpe_ann = daily_net_sharpe * math.sqrt(252)

    std_gross = float(np.std(gross_rets, ddof=1)) if n_obs > 1 else 0.0
    mean_gross = float(np.mean(gross_rets))
    daily_gross_sharpe = mean_gross / std_gross if std_gross > 1e-12 else 0.0
    gross_sharpe_ann = daily_gross_sharpe * math.sqrt(252)

    # 2. PSR vs Sharpe 0
    if n_obs > 3 and std_net > 1e-12:
        skew_val, kurt_val = compute_sample_skew_kurtosis(net_rets)
        psr_val = compute_psr(daily_net_sharpe, n_obs, skew_val, kurt_val, benchmark_sharpe=0.0)
    else:
        psr_val = 0.50

    # 3. Stationary Bootstrap P-value
    p_val = stationary_bootstrap_pvalue(net_rets, n_resamples=10000, mean_block_length=10.0, seed=seed)

    # 4. Max Drawdown
    cum_equity = np.cumprod(1.0 + net_rets)
    peak = np.maximum.accumulate(cum_equity)
    drawdowns = (cum_equity - peak) / peak
    max_dd = float(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0

    # 5. Hit Rate
    active_mask = (positions != 0)
    active_count = int(np.sum(active_mask))
    positive_count = int(np.sum((net_rets > 0) & active_mask))
    hit_rate = float(positive_count / active_count) if active_count > 0 else 0.0

    # 6. Turnover
    prev_pos = np.roll(positions, 1)
    prev_pos[0] = 0
    pos_changes = np.abs(positions - prev_pos)
    turnover = float(np.mean(pos_changes))

    # 7. Cost Drag in bps/year
    cost_drag_annual_bps = float(np.mean(costs_bps) * 252)

    # 8. Exposure Fraction
    exposure = float(active_count / n_obs)

    # 9. Total Net Return
    total_net_ret = float(cum_equity[-1] - 1.0) if len(cum_equity) > 0 else 0.0

    return {
        "trading_days": n_obs,
        "net_sharpe": round(net_sharpe_ann, 4),
        "gross_sharpe": round(gross_sharpe_ann, 4),
        "psr": round(psr_val, 4),
        "bootstrap_pvalue": round(p_val, 4),
        "max_drawdown_pct": round(max_dd * 100.0, 2),
        "hit_rate_pct": round(hit_rate * 100.0, 2),
        "turnover_daily": round(turnover, 4),
        "cost_drag_bps_year": round(cost_drag_annual_bps, 2),
        "exposure_fraction": round(exposure, 4),
        "total_net_return_pct": round(total_net_ret * 100.0, 2),
        "seed": seed,
    }
