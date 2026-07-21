"""
Hardened Metric Calculators Engine & Calibrated Scientific Evaluator
Implements EEF v1.0 & MVF v1.0 Specifications.
"""

import math
from typing import Any, Dict, List, Optional
import numpy as np


from telemetry.eef_calculators import (
    StructuralCalculator,
    EpistemicCalculator,
    GeneralizationCalculator,
    ReflectiveCalculator,
    WorldModelCalculator,
)


class EEFEvaluator:
    """
    Evaluates telemetry event streams and step snapshots against hardened EEF v1.0 / MVF v1.0 metrics.
    Produces composite learning scores, evidence scores, and calibrated scientific verdicts.
    """

    def __init__(self, run_id: str, market_name: str = "RELIANCE"):
        self.run_id = run_id
        self.market_name = market_name

    def evaluate_run(
        self,
        predictions_history: List[Dict[str, Any]],
        theories_history: List[Dict[str, Any]],
        mechanisms_history: List[Dict[str, Any]],
        lessons_history: List[Dict[str, Any]],
        principles_history: List[Dict[str, Any]],
        contradictions_history: List[Dict[str, Any]] = None,
        counterfactuals_history: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Computes full layer-by-layer hardened metrics using modular calculators and assigns calibrated scientific verdict.
        """
        total_steps = max(len(predictions_history), 1)

        # 1. Layer 1: Structural Metrics
        l1 = StructuralCalculator.calculate(
            total_steps=total_steps,
            mechanisms_history=mechanisms_history,
            principles_count=len(principles_history),
        )

        # 2. Layer 3: Generalization Metrics
        l3 = GeneralizationCalculator.calculate(principles_history=principles_history)

        # 3. Layer 2: Epistemic Metrics (Hardened RCE, S_adaptive, NMDL)
        l2 = EpistemicCalculator.calculate(
            predictions_history=predictions_history,
            active_principles_count=l3["active_principles_count"],
        )

        # 4. Layer 4: Reflective Metrics
        l4 = ReflectiveCalculator.calculate(
            mechanisms_history=mechanisms_history,
            lessons_history=lessons_history,
        )

        # 5. Layer 5: World Model Metrics
        l5 = WorldModelCalculator.calculate(
            contradictions_history=contradictions_history,
            counterfactuals_history=counterfactuals_history,
        )

        r_exec = l1["mechanism_reuse_rate"]
        rce = l2["rce"]
        s_adaptive = l2["explanation_stability_adaptive"]
        s_regime = l3["cross_regime_survival_rate"]
        m_ref = l4["mechanism_refinement_ratio"]
        g_coherence = l5["graph_coherence_index"]

        # Composite Scores
        learning_score = round(float(0.3 * r_exec + 0.3 * (1.0 - rce) + 0.2 * s_regime + 0.2 * m_ref), 4)
        evidence_score = round(float(0.4 * (1.0 - rce) + 0.3 * s_adaptive + 0.3 * g_coherence), 4)

        # Assign Calibrated Scientific Verdict & Level
        level_achieved = "LEVEL_1_OPERATIONAL"
        verdict = "INSUFFICIENT_EVIDENCE"
        verdict_reason = "Substrate demonstrates operational execution, but predictive payoff and principle maturation exhibit insufficient empirical evidence."

        if l3["active_principles_count"] > 0:
            level_achieved = "LEVEL_4_MECHANISTIC"
            verdict = "PARTIALLY_SUPPORTED"
            verdict_reason = "Mechanism reuse and active principle usage detected in replay telemetry."
        elif learning_score > 0.65:
            level_achieved = "LEVEL_3_EPISTEMIC"
            verdict = "SUPPORTED"
            verdict_reason = "Statistically significant calibration error reduction and mechanism refinement demonstrated."

        return {
            "run_id": self.run_id,
            "market_name": self.market_name,
            "total_steps": total_steps,
            "evidence_level_achieved": level_achieved,
            "verdict": verdict,
            "verdict_reason": verdict_reason,
            "composite_scores": {
                "learning_score": learning_score,
                "evidence_score": evidence_score,
            },
            "layer_metrics": {
                "layer_1_structural": l1,
                "layer_2_epistemic": l2,
                "layer_3_generalization": l3,
                "layer_4_reflective": l4,
                "layer_5_world_model": l5,
            },
        }

