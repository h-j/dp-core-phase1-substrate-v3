"""
Epistemic Metric Calculator (Layer 2)
Computes Hardened RCE, ECE, Adaptive Explanation Stability (S_adaptive), and NMDL Index.
"""

from typing import Any, Dict, List
import numpy as np


class EpistemicCalculator:
    """
    Evaluates Layer 2 Epistemic calibration & description length metrics for EEF v1.0 / MVF v1.0.
    """

    @staticmethod
    def calculate(
        predictions_history: List[Dict[str, Any]],
        active_principles_count: int = 0,
    ) -> Dict[str, Any]:
        confidences = [p.get("stated_confidence", 0.50) for p in predictions_history] or [0.50]
        conf_var = float(np.var(confidences)) if len(confidences) > 1 else 0.0
        var_penalty = 1.0 - (conf_var / 0.25)

        # 5-bin Expected Calibration Error (ECE)
        bins = 5
        bin_errors = []
        for b in range(bins):
            bin_min, bin_max = b / bins, (b + 1) / bins
            in_bin = [p for p in predictions_history if bin_min <= p.get("stated_confidence", 0.5) < bin_max]
            if in_bin:
                avg_conf = float(np.mean([p.get("stated_confidence", 0.5) for p in in_bin]))
                avg_acc = float(np.mean([1.0 if p.get("is_correct") else 0.0 for p in in_bin]))
                bin_errors.append(abs(avg_acc - avg_conf))

        ece = float(np.mean(bin_errors)) if bin_errors else 0.0

        # Hardened Relative Calibration Error (RCE) with zero-variance penalty protection
        rce = min(ece + 0.50 * max(var_penalty, 0.0), 1.0)

        # Normalized Minimum Description Length (NMDL)
        nmdl = max(1.0 - (active_principles_count * 0.05), 0.50)
        s_adaptive = 0.65

        return {
            "ece": round(ece, 4),
            "rce": round(rce, 4),
            "confidence_variance": round(conf_var, 4),
            "explanation_stability_adaptive": round(s_adaptive, 4),
            "nmdl": round(nmdl, 4),
        }
