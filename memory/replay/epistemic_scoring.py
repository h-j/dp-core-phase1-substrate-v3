"""Longitudinal epistemic scoring for theory usefulness.

The score is not market-prediction accuracy. It estimates whether cognition has
remained coherent, inspectable, appropriately contradicted, and reusable.
"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Dict, Iterable


class EpistemicScoringEngine:
    """Deterministic usefulness scoring over lineage records."""

    def score_theory(self, record: object) -> Dict[str, object]:
        survival = min(1.0, float(getattr(record, "survival_steps", 0)) / 10)
        contradiction_count = float(getattr(record, "contradiction_count", 0))
        contradiction_pressure = min(1.0, contradiction_count / 5)
        revival_count = float(getattr(record, "revival_count", 0))
        revival_usefulness = min(1.0, revival_count / 2)
        confidence_state = getattr(record, "confidence_state", {}) or {}
        confidence_values = [
            float(value)
            for key, value in confidence_state.items()
            if key != "contradiction_pressure"
        ]
        avg_confidence = mean(confidence_values) if confidence_values else 0.5
        confidence_stability = (
            max(0.0, 1.0 - pstdev(confidence_values) * 4)
            if len(confidence_values) > 1
            else 0.8
        )

        score = (
            0.34 * survival
            + 0.22 * confidence_stability
            + 0.18 * avg_confidence
            + 0.14 * revival_usefulness
            + 0.12 * (1.0 - contradiction_pressure)
        )
        score = round(max(0.0, min(1.0, score)), 3)
        return {"score": score, "label": self._label(score, contradiction_pressure)}

    def aggregate(self, records: Iterable[object]) -> Dict[str, float]:
        scores = [self.score_theory(record)["score"] for record in records]
        return {"avg_theory_usefulness": mean(scores) if scores else 0.0}

    def _label(self, score: float, contradiction_pressure: float) -> str:
        if score >= 0.68 and contradiction_pressure <= 0.45:
            return "helpful"
        if score >= 0.52:
            return "coherent"
        if contradiction_pressure >= 0.7 or score < 0.35:
            return "failed"
        return "fragile"
