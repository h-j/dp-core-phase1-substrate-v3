"""
Reflective Metric Calculator (Layer 4)
Computes Mechanism Refinement Ratio (M_ref) and Lessons Extraction Stats.
"""

from typing import Any, Dict, List


class ReflectiveCalculator:
    """
    Evaluates Layer 4 Reflective metrics for EEF v1.0 / MVF v1.0.
    """

    @staticmethod
    def calculate(
        mechanisms_history: List[Dict[str, Any]],
        lessons_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        refinement_payoff = 0.0
        for m in mechanisms_history:
            if m.get("times_modified", 0) > 0 and m.get("prediction_helped", 0) > 0:
                refinement_payoff += m.get("prediction_helped", 0) / float(m.get("times_modified", 1))

        m_ref = min(refinement_payoff, 1.0)

        return {
            "mechanism_refinement_ratio": round(m_ref, 4),
            "lessons_count": len(lessons_history),
            "lessons_active_count": sum(1 for l in lessons_history if l.get("status") == "active"),
        }
