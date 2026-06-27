"""Longitudinal epistemic scoring for theory usefulness.

The score is not market-prediction accuracy. It estimates whether cognition has
remained coherent, inspectable, appropriately contradicted, and reusable.
"""

from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List


class EpistemicScoringEngine:
    """Deterministic usefulness scoring over lineage records."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def score_theory(
        self,
        lineage_record: Any,
        regime_matches: List[Any],
        prior_prediction_result: Dict[str, Any],
        contradiction_score: float,
        reflection_summary: str,
    ) -> Dict[str, Any]:
        """
        Calculates a theory usefulness score.
        """

        # ---------------------------------------------------
        # contribution caps
        # ---------------------------------------------------
        MAX_SIMILARITY_CONTRIBUTION = 0.25
        MAX_PREDICTION_CONTRIBUTION = 0.30
        MAX_REFLECTION_CONTRIBUTION = 0.10
        MAX_RECURRENCE_CONTRIBUTION = 0.35
        MAX_CONTRADICTION_PENALTY = 0.22

        # ---------------------------------------------------
        # 1. regime similarity
        # ---------------------------------------------------
        avg_similarity = 0.0

        if regime_matches:
            try:
                similarities = [
                    (
                        m.get("similarity")
                        if isinstance(m, dict)
                        else getattr(m, "similarity", 0.0)
                    )
                    for m in regime_matches
                ]
                avg_similarity = mean(similarities) if similarities else 0.0
            except Exception:
                avg_similarity = 0.0

        current_similarity_contribution = avg_similarity * MAX_SIMILARITY_CONTRIBUTION

        # mild cushion for familiar regimes
        epistemic_cushion = 0.85 if avg_similarity > 0.70 else 1.0

        # ---------------------------------------------------
        # 2. lineage metrics
        # ---------------------------------------------------
        survival_steps = 0
        revival_count = 0

        if lineage_record:
            survival_steps = getattr(
                lineage_record,
                "survival_steps",
                None,
            )

            if survival_steps is None:
                survival_steps = getattr(
                    lineage_record,
                    "active_days",
                    0,
                )

            revival_count = getattr(
                lineage_record,
                "revival_count",
                0,
            )

        # ---------------------------------------------------
        # 3. prediction contribution
        # ---------------------------------------------------
        current_prediction_contribution = 0.0

        if (
            prior_prediction_result
            and prior_prediction_result.get("direction_score") is not None
        ):
            pred_score = prior_prediction_result["direction_score"]

            # established theories survive one miss
            if pred_score == 0.0 and survival_steps > 3:
                current_prediction_contribution = 0.08
            else:
                current_prediction_contribution = (
                    pred_score * MAX_PREDICTION_CONTRIBUTION
                )

        # ---------------------------------------------------
        # 4. reflection contribution
        # ---------------------------------------------------
        current_reflection_contribution = 0.0

        if reflection_summary:
            text = reflection_summary.lower()

            if any(
                k in text
                for k in (
                    "confirmed",
                    "validated",
                    "strengthened",
                )
            ):
                current_reflection_contribution += 0.08

            if any(
                k in text
                for k in (
                    "uncertain",
                    "weakened",
                    "challenged",
                )
            ):
                current_reflection_contribution -= 0.03

        # ---------------------------------------------------
        # 5. recurrence / persistence
        # ---------------------------------------------------
        current_recurrence_contribution = 0.0

        if survival_steps > 0 or revival_count > 0:
            survival_factor = min(
                1.0,
                survival_steps / 12.0,
            )

            recurrence_factor = min(
                1.0,
                revival_count / 3.0,
            )

            combined_factor = survival_factor * 0.70 + recurrence_factor * 0.30

            current_recurrence_contribution = (
                combined_factor * MAX_RECURRENCE_CONTRIBUTION
            )

        # ---------------------------------------------------
        # 6. contradiction
        # ---------------------------------------------------
        current_contradiction_penalty = (
            contradiction_score * MAX_CONTRADICTION_PENALTY * epistemic_cushion
        )

        # ---------------------------------------------------
        # 7. score
        # ---------------------------------------------------
        raw_score = (
            current_similarity_contribution
            + current_prediction_contribution
            + current_reflection_contribution
            + current_recurrence_contribution
            - current_contradiction_penalty
        )

        # preserve weak-but-viable theories
        if 0 < raw_score < 0.10:
            score = 0.10
        else:
            score = max(
                0.0,
                min(1.0, raw_score),
            )

        # ---------------------------------------------------
        # debug output
        # ---------------------------------------------------
        if getattr(self, "verbose", False):
            print(
                {
                    "id": getattr(
                        lineage_record,
                        "id",
                        None,
                    ),
                    "created_at_step": getattr(
                        lineage_record,
                        "created_at_step",
                        None,
                    ),
                    "survival_steps": survival_steps,
                    "revival_count": revival_count,
                    "raw_score": round(raw_score, 4),
                    "sim": round(
                        current_similarity_contribution,
                        4,
                    ),
                    "pred": round(
                        current_prediction_contribution,
                        4,
                    ),
                    "reflection": round(
                        current_reflection_contribution,
                        4,
                    ),
                    "recurrence": round(
                        current_recurrence_contribution,
                        4,
                    ),
                    "penalty": round(
                        current_contradiction_penalty,
                        4,
                    ),
                }
            )

        # ---------------------------------------------------
        # labels
        # ---------------------------------------------------
        label = "failed"

        if score >= 0.65:
            label = "strong"
        elif score >= 0.40:
            label = "useful"
        elif score >= 0.15:
            label = "weak"

        return {
            "score": float(score),
            "label": label,
        }
