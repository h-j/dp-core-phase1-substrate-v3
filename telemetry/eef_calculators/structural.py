"""
Structural Cognition Metric Calculator (Layer 1)
Computes Mechanism Reuse Rate (R_exec), Mechanism Count, and Compression Ratio.
"""

from typing import Any, Dict, List


class StructuralCalculator:
    """
    Evaluates Layer 1 Structural metrics for EEF v1.0 / MVF v1.0.
    """

    @staticmethod
    def calculate(
        total_steps: int,
        mechanisms_history: List[Dict[str, Any]],
        principles_count: int = 0,
    ) -> Dict[str, Any]:
        steps = max(total_steps, 1)
        num_mechanisms = max(len(mechanisms_history), 1)
        reused_count = sum(m.get("times_reused", 0) for m in mechanisms_history)
        modified_count = sum(m.get("times_modified", 0) for m in mechanisms_history)

        # R_exec: Mechanism reuse rate normalized over steps
        r_exec = min(reused_count / (steps * 1.5), 1.0) if steps > 0 else 0.0

        # Compression ratio: Observations / (Principles + Mechanisms)
        c_ratio = steps / float(principles_count + num_mechanisms)

        return {
            "mechanism_creation_count": len(mechanisms_history),
            "mechanism_reuse_count": reused_count,
            "mechanism_modified_count": modified_count,
            "mechanism_reuse_rate": round(r_exec, 4),
            "compression_ratio": round(c_ratio, 4),
        }
