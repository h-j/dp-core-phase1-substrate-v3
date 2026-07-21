"""
Contradiction Resolver — Epistemic conflict resolution engine for competing theories.

Evaluates active graph contradictions using multi-signal evidence without immediate deletion.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from cognition.contradiction.contradiction_graph import (
    ContradictionEdge,
    ContradictionGraph,
    ContradictionStatus,
)

logger = logging.getLogger(__name__)


class ContradictionResolver:
    """
    Evaluates competing hypotheses using prediction performance, validation history,
    accumulated evidence, memory reuse, reflection quality, and historical confidence.
    """

    def __init__(self, resolution_threshold: float = 0.15):
        self.resolution_threshold = resolution_threshold

    def resolve_conflicts(
        self,
        graph: ContradictionGraph,
        theory_context: Optional[Dict[str, Any]] = None,
        current_step: int = 0,
    ) -> List[ContradictionEdge]:
        """
        Evaluates active contradiction edges and updates their statuses.

        Args:
            graph: The ContradictionGraph containing active contradiction edges.
            theory_context: Dictionary mapping theory_id to context dict/object containing
                            confidence, prediction_score, validation_count, reuse_score, reflection_score.
            current_step: Current replay step.

        Returns:
            List of resolved or updated ContradictionEdge objects.
        """
        theory_context = theory_context or {}
        active_edges = graph.get_active_contradictions()
        resolved_edges: List[ContradictionEdge] = []

        for edge in active_edges:
            src_id = edge.source_theory_id
            tgt_id = edge.target_theory_id

            src_ctx = theory_context.get(src_id, {})
            tgt_ctx = theory_context.get(tgt_id, {})

            src_score = self._compute_epistemic_strength(src_ctx)
            tgt_score = self._compute_epistemic_strength(tgt_ctx)

            score_diff = abs(src_score - tgt_score)

            if score_diff >= self.resolution_threshold:
                if src_score > tgt_score:
                    winning_id = src_id
                    losing_id = tgt_id
                else:
                    winning_id = tgt_id
                    losing_id = src_id

                edge.status = ContradictionStatus.RESOLVED
                edge.winning_theory_id = winning_id
                edge.resolution_notes = (
                    f"Resolved at step {current_step}: Theory '{winning_id}' outperformed '{losing_id}' "
                    f"(strength: {max(src_score, tgt_score):.3f} vs {min(src_score, tgt_score):.3f}, "
                    f"diff: {score_diff:.3f} >= {self.resolution_threshold:.3f})."
                )
                logger.info("[ContradictionResolver] %s", edge.resolution_notes)
                resolved_edges.append(edge)

            elif current_step - edge.step > 5:
                # Long standing unresolved contradiction transitions to PENDING_INVESTIGATION
                edge.status = ContradictionStatus.PENDING_INVESTIGATION
                edge.resolution_notes = f"Pending investigation at step {current_step}: unresolved after 5 steps."
                resolved_edges.append(edge)

        return resolved_edges

    def _compute_epistemic_strength(self, ctx: Dict[str, Any]) -> float:
        """
        Computes multi-signal composite epistemic strength score for a theory.
        """
        confidence = float(ctx.get("confidence", 0.50))
        prediction_score = float(ctx.get("prediction_score", 0.50))
        validation_score = float(ctx.get("validation_score", 0.50))
        reuse_score = float(ctx.get("reuse_score", 0.0))
        reflection_score = float(ctx.get("reflection_score", 0.50))

        # Composite score formula
        strength = (
            0.30 * confidence
            + 0.25 * prediction_score
            + 0.25 * validation_score
            + 0.10 * reuse_score
            + 0.10 * reflection_score
        )
        return max(0.0, min(1.0, strength))
