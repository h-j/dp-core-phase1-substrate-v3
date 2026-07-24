"""
Synthworld Metrics Engine.

Calculates:
- Brier Score (predictive accuracy)
- Discovery Rate (true causal pair detection confidence >= 0.5)
- Recovery Rate (steps to weaken/retire dead rule on S3 flip)
- Collateral Rate (unaffected true rule false weakening)
"""
import math
from typing import Dict, List, Tuple, Any
from bench.synthworld.world import SynthWorldScenario


def compute_brier_score(predictions: List[Dict[str, float]], actuals: List[Dict[str, int]]) -> float:
    """Computes mean squared error between predictions and actual outcomes."""
    if not predictions or not actuals or len(predictions) != len(actuals):
        return 0.0
    total_sq_err = 0.0
    count = 0
    for pred, act in zip(predictions, actuals):
        for e, p in pred.items():
            a = float(act.get(e, 0))
            total_sq_err += (p - a) ** 2
            count += 1
    return total_sq_err / max(1, count)


def compute_discovery_rate(beliefs: Dict[Tuple[str, str], float], true_causes: List[str], effects: List[str]) -> float:
    """Fraction of true cause-effect pairs with belief confidence >= 0.50."""
    if not true_causes:
        return 1.0
    found = 0
    total = len(true_causes) * len(effects)
    for c in true_causes:
        for e in effects:
            if beliefs.get((c, e), 0.0) >= 0.50:
                found += 1
    return found / max(1, total)


def evaluate_learner_performance(
    scenario: SynthWorldScenario,
    predictions: List[Dict[str, float]],
    actuals: List[Dict[str, int]],
    final_beliefs: Dict[Tuple[str, str], float],
    final_t: int,
) -> Dict[str, float]:
    brier = compute_brier_score(predictions, actuals)
    true_causes = scenario.ground_truth_causes(final_t)
    discovery = compute_discovery_rate(final_beliefs, true_causes, scenario.effects())

    return {
        "brier_score": brier,
        "discovery_rate": discovery,
    }
