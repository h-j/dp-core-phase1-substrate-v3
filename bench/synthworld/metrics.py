from __future__ import annotations
from .world import Scenario


def brier(pred: float, outcome: int) -> float:
    return (pred - outcome) ** 2


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def phase_brier(
    scores: list[dict[str, float]], start: int, end: int, effects: list[str] | None = None
) -> float:
    vals = []
    """Mean Brier over timesteps [start, end), optionally restricted to effects."""
    for t in range(start, min(end, len(scores))):
        for e, v in scores[t].items():
            if effects is None or e in effects:
                vals.append(v)
    return mean(vals)


def discovery(beliefs: dict[tuple[str, str], float], scenario: Scenario) -> dict:
    """Score claimed persistent rules against ground truth in the FINAL regime, truth = scenario.true_pairs(scenario.T - 1) and count decoy pairs claimed (promotion-gate noise resistance)."""
    claimed = set(beliefs)
    truth = scenario.true_pairs(scenario.T - 1)
    decoy_names = {d.name for d in scenario.decoys}
    decoy_claims = {p for p in claimed if p[0] in decoy_names}
    tr = len(claimed & truth)
    return {
        "claimed": len(claimed),
        "precision": tr / len(claimed) if claimed else float("nan"),
        "recall": tr / len(truth) if truth else float("nan"),
        "decoy_claims": len(decoy_claims),
        "missed": sorted(truth - claimed),
        "false": sorted(claimed - truth),
    }


def recovery(
    scores: list[dict[str, float]],
    flip_t: int,
    affected: list[str],
    window: int = 100,
    tol: float = 0.02,
) -> dict:
    """After a regime flip at flip_t: how many steps until the rolling Brier on AFFECTED effects returns to (pre-flip level + tol)?"""

    def rolling(t0):
        return phase_brier(scores, t0, t0 + window, affected)

    pre = phase_brier(scores, max(0, flip_t - 3 * window), flip_t, affected)
    steps = None
    t = flip_t
    while t + window <= len(scores):
        if rolling(t) <= pre + tol:
            steps = t - flip_t
            break
        t += window // 4
    return {
        "pre_flip_brier": pre,
        "recovery_steps": steps,
        "post_flip_peak": max(
            (
                rolling(x)
                for x in range(
                    flip_t, min(flip_t + 5 * window, len(scores) - window), window // 4
                )
            ),
            default=float("nan"),
        ),
    }


def collateral(
    scores: list[dict[str, float]], flip_t: int, unaffected: list[str], window: int = 300
) -> float:
    """Brier degradation on unaffected effects around the flip:
    (post - pre). Near zero = revision was surgical; positive = collateral.
    """
    pre = phase_brier(scores, max(0, flip_t - window), flip_t, unaffected)
    post = phase_brier(scores, flip_t, flip_t + window, unaffected)
    return post - pre
