"""
World Model Metric Calculator (Layer 5)
Computes Causal Graph Coherence Index (G_coherence) and Anti-Correlational Counterfactual Accuracy (A_anti).
"""

from typing import Any, Dict, List


class WorldModelCalculator:
    """
    Evaluates Layer 5 World Model metrics for EEF v1.0 / MVF v1.0.
    """

    @staticmethod
    def calculate(
        contradictions_history: List[Dict[str, Any]] = None,
        counterfactuals_history: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        # Graph coherence index baseline
        g_coherence = 0.75
        if contradictions_history:
            unresolved = sum(1 for c in contradictions_history if not c.get("resolved", False))
            g_coherence = max(1.0 - (unresolved * 0.05), 0.40)

        # Anti-correlational counterfactual accuracy baseline
        a_anti = 0.48
        if counterfactuals_history:
            accs = [cf.get("counterfactual_accuracy", 0.48) for cf in counterfactuals_history]
            a_anti = float(sum(accs) / max(len(accs), 1))

        return {
            "graph_coherence_index": round(g_coherence, 4),
            "anti_correlational_counterfactual_acc": round(a_anti, 4),
        }
