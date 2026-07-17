import logging
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4

import pandas as pd

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from cognition.schemas.proposition.validation_record import ValidationRecord
from cognition.schemas.validation.belief_state import BeliefState
from market.replay.lesson_record import LessonRecord, LessonStatus
from memory.relational.repositories.belief_state_repository import \
    BeliefStateRepository
from memory.relational.repositories.compiled_proposition_repository import \
    CompiledPropositionRepository
from memory.relational.repositories.validation_record_repository import \
    ValidationRecordRepository

logger = logging.getLogger(__name__)


class PatternConsolidationEngine:
    """Aggregates validations, clusters lineages by logic/behavior, and nominates Lesson candidates."""

    def __init__(
        self,
        min_validations: int = 5,
        min_temporal_span: int = 10,
        min_confidence: float = 0.70,
        max_uncertainty: float = 0.40,
        min_success_rate: float = 0.70,
        belief_repo: Optional[BeliefStateRepository] = None,
        val_record_repo: Optional[ValidationRecordRepository] = None,
        comp_prop_repo: Optional[CompiledPropositionRepository] = None,
    ):
        self.min_validations = min_validations
        self.min_temporal_span = min_temporal_span
        self.min_confidence = min_confidence
        self.max_uncertainty = max_uncertainty
        self.min_success_rate = min_success_rate
        self.belief_repo = belief_repo or BeliefStateRepository()
        self.val_record_repo = val_record_repo or ValidationRecordRepository()
        self.comp_prop_repo = comp_prop_repo or CompiledPropositionRepository()

    def consolidate_patterns(
        self, history_df: pd.DataFrame, current_step: int
    ) -> List[Dict[str, Any]]:
        """Scans all belief states, groups/clusters them, and evaluates them for lesson candidacy."""
        states = self.belief_repo.list_all_belief_states()
        active_states = [s for s in states if s.status != "RETIRED"]

        if not active_states:
            return []

        # 1. Fetch all validation records for each active lineage
        lineage_validations: Dict[str, List[ValidationRecord]] = {}
        lineage_propositions: Dict[str, List[CompiledProposition]] = {}

        for state in active_states:
            lid = state.lineage_id
            records = self.val_record_repo.query_by_lineage(lid)
            # Filter to records that have resolved (SUPPORTED or CONTRADICTED)
            resolved = [
                r
                for r in records
                if r.validation_state in ["SUPPORTED", "CONTRADICTED"]
            ]
            lineage_validations[lid] = resolved

            # Load compiled props for trigger/target context
            props = self.comp_prop_repo.query_by_lineage(lid)
            lineage_propositions[lid] = props

        # 2. Cluster lineages by logic signature (trigger/target fields overlap)
        clusters = self._cluster_lineages(active_states, lineage_propositions)

        nominations = []
        for cluster_id, lineage_ids in clusters.items():
            # Aggregate stats across the cluster
            agg_validations: List[ValidationRecord] = []
            for lid in lineage_ids:
                agg_validations.extend(lineage_validations.get(lid, []))

            if not agg_validations:
                continue

            # Sort by step to evaluate sequential metrics
            agg_validations.sort(key=lambda r: r.replay_step)

            # Evaluate promotion criteria
            criteria_check = self._evaluate_promotion_criteria(
                lineage_ids, agg_validations, history_df, current_step
            )

            if criteria_check["eligible"]:
                # Synthesize Lesson text description
                main_lid = lineage_ids[0]
                sample_prop = (
                    lineage_propositions[main_lid][0]
                    if lineage_propositions.get(main_lid)
                    else None
                )
                trigger_field = "unknown"
                target_field = "unknown"
                if sample_prop and sample_prop.trigger_definition:
                    trigger_field = sample_prop.trigger_definition.get(
                        "field", "unknown"
                    )
                if sample_prop and sample_prop.target_definition:
                    target_field = sample_prop.target_definition.get("field", "unknown")

                success_rate = criteria_check["success_rate"]
                mean_conf = criteria_check["mean_confidence"]

                lesson_text = (
                    f"Consolidated pattern across lineages {','.join(lineage_ids[:3])} "
                    f"verifies that trigger '{trigger_field}' predicts target '{target_field}' "
                    f"with a success rate of {success_rate:.2%}. Verified across multiple regime contexts."
                )

                nominations.append(
                    {
                        "cluster_id": cluster_id,
                        "lineage_ids": lineage_ids,
                        "lesson_text": lesson_text,
                        "success_rate": success_rate,
                        "confidence": mean_conf,
                        "evidence_count": len(agg_validations),
                        "regime_context": agg_validations[-1].regime,
                        "source_experience_ids": [r.id for r in agg_validations],
                        "criteria": criteria_check,
                    }
                )

        return nominations

    def _cluster_lineages(
        self,
        states: List[BeliefState],
        propositions: Dict[str, List[CompiledProposition]],
    ) -> Dict[str, List[str]]:
        """Groups lineages that share identical trigger and target fields."""
        clusters: Dict[str, List[str]] = {}
        for state in states:
            lid = state.lineage_id
            props = propositions.get(lid)
            if not props:
                continue
            sample_prop = props[0]
            trigger_field = "N/A"
            target_field = "N/A"
            if sample_prop.trigger_definition:
                trigger_field = sample_prop.trigger_definition.get("field", "N/A")
            if sample_prop.target_definition:
                target_field = sample_prop.target_definition.get("field", "N/A")

            # Unique logic signature key
            signature = f"trig:{trigger_field}_tgt:{target_field}"
            if signature not in clusters:
                clusters[signature] = []
            clusters[signature].append(lid)

        return clusters

    def _evaluate_promotion_criteria(
        self,
        lineage_ids: List[str],
        validations: List[ValidationRecord],
        history_df: pd.DataFrame,
        current_step: int,
    ) -> Dict[str, Any]:
        """Evaluates whether the validations meet Lesson promotion gates."""
        val_count = len(validations)
        if val_count == 0:
            return {
                "eligible": False,
                "reason": "No validation records",
                "success_rate": 0.0,
            }

        # success rate
        supported_count = sum(
            1 for r in validations if r.validation_state == "SUPPORTED"
        )
        success_rate = supported_count / val_count

        # temporal span
        steps = [r.replay_step for r in validations]
        min_step = min(steps)
        max_step = max(steps)
        temporal_span = max_step - min_step + 1

        # regime return direction diversity (at least one positive close day, one negative close day)
        pos_return_count = 0
        neg_return_count = 0
        for r in validations:
            step = r.replay_step
            if step > 0 and step < len(history_df) and "close" in history_df.columns:
                close_curr = history_df["close"].iloc[step]
                close_prev = history_df["close"].iloc[step - 1]
                if close_prev != 0:
                    ret = (close_curr - close_prev) / close_prev
                    if ret > 0:
                        pos_return_count += 1
                    else:
                        neg_return_count += 1

        regime_diversity_met = (pos_return_count > 0) and (neg_return_count > 0)

        # average confidence & uncertainty
        mean_conf = 0.0
        mean_unc = 0.0
        cluster_states = []
        for lid in lineage_ids:
            s = self.belief_repo.get_belief_state_by_lineage(lid)
            if s:
                cluster_states.append(s)

        if cluster_states:
            mean_conf = sum(s.confidence for s in cluster_states) / len(cluster_states)
            mean_unc = sum(s.uncertainty for s in cluster_states) / len(cluster_states)

        # contradiction contiguity gate (no sequence of 3 consecutive contradicted steps)
        consecutive_contradictions = 0
        max_consecutive_contradictions = 0
        for r in validations:
            if r.validation_state == "CONTRADICTED":
                consecutive_contradictions += 1
                max_consecutive_contradictions = max(
                    max_consecutive_contradictions, consecutive_contradictions
                )
            else:
                consecutive_contradictions = 0

        contradiction_gate_met = max_consecutive_contradictions < 3

        # Check all gates
        gates = {
            "validation_count_met": val_count >= self.min_validations,
            "temporal_span_met": temporal_span >= self.min_temporal_span,
            "regime_diversity_met": regime_diversity_met,
            "confidence_threshold_met": mean_conf >= self.min_confidence,
            "uncertainty_threshold_met": mean_unc <= self.max_uncertainty,
            "success_rate_met": success_rate >= self.min_success_rate,
            "contradiction_gate_met": contradiction_gate_met,
        }

        eligible = all(gates.values())
        reason = (
            "All gates passed"
            if eligible
            else "Failed gates: " + ", ".join(k for k, v in gates.items() if not v)
        )

        return {
            "eligible": eligible,
            "reason": reason,
            "validation_count": val_count,
            "temporal_span": temporal_span,
            "pos_return_count": pos_return_count,
            "neg_return_count": neg_return_count,
            "mean_confidence": mean_conf,
            "mean_uncertainty": mean_unc,
            "success_rate": success_rate,
            "max_consecutive_contradictions": max_consecutive_contradictions,
            "gates": gates,
        }
