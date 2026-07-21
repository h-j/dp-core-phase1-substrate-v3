"""
Generalization Metric Calculator (Layer 3)
Computes Cross-Regime Survival Rate (S_regime) and Active Principles Count.
"""

from typing import Any, Dict, List


class GeneralizationCalculator:
    """
    Evaluates Layer 3 Generalization metrics for EEF v1.0 / MVF v1.0.
    """

    @staticmethod
    def calculate(
        principles_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        active_principles = [
            p for p in principles_history
            if p.get("status", "").lower() in ["active", "stable", "trusted", "canonical"]
        ]

        s_regime = 0.0
        for p in active_principles:
            if p.get("uses_count", 0) > 0 and p.get("predictions_helped", 0) > p.get("predictions_harmed", 0):
                s_regime += 0.25

        s_regime = min(s_regime, 1.0)

        return {
            "cross_regime_survival_rate": round(s_regime, 4),
            "active_principles_count": len(active_principles),
            "total_principles_count": len(principles_history),
        }
