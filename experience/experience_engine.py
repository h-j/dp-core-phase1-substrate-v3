from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple
from uuid import UUID
from experience.experience_repository import ExperienceRepository
from experience.experience_types import Experience, ExperienceStatus, ExperienceOutcome

if TYPE_CHECKING:
    from market.replay.lesson_extractor import LessonExtractor
from market.replay.lesson_record import LessonRecord

if TYPE_CHECKING: # For type hinting without circular imports
    from flows.theory_flow.attribution import AttributionResult

class ExperienceEngine:
    def __init__(self, experience_repo: ExperienceRepository):
        self.experience_repo = experience_repo
        self.lesson_extractor: Optional[LessonExtractor] = None
        self._last_extracted_lesson_info: Tuple[Optional[LessonRecord], str, int] = (None, "not_processed", 0)

    def create_experience(self, theory_id: str, lineage_id: str, date: str, regime_context: List[str] = None, theory_subtype: str = ""):
        exp_id = f"exp_{lineage_id}_{date}"
        experience = Experience(
            experience_id=exp_id,
            lineage_id=lineage_id,
            theory_family_id=lineage_id, # Simplified for V1
            created_at=date,
            theory_ids=[theory_id],
            regime_context=regime_context or [],
            theory_subtype=theory_subtype
        )
        self.experience_repo.save(experience)

    def attach_theory(self, lineage_id: str, theory_id: str, synthesis_meta: Dict = None):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.theory_ids.append(theory_id)
            exp.mutation_count += 1
            if synthesis_meta:
                # Store the logic of the synthesis as a mutation record
                exp.mutations.append(f"Dialectical Synthesis: {synthesis_meta.get('conflict')}")
            self.experience_repo.save(exp)

    def update_experience_with_attribution(self, lineage_id: str, attribution: "AttributionResult"):
        """Update an experience record with causal attribution data."""
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            if not hasattr(exp, "causal_events") or exp.causal_events is None:
                exp.causal_events = []
            
            event = {
                "event_type": "validation",
                "timestamp": attribution.timestamp,
                "outcome": attribution.outcome,
                "theory_claim": attribution.theory_claim,
                "components_passed": attribution.components_passed,
                "components_failed": attribution.components_failed,
                "root_cause": attribution.root_cause_component,
                "attribution_reasoning": attribution.attribution_reasoning[:500],
            }
            exp.causal_events.append(event)
            
            if not hasattr(exp, "component_failure_counts") or exp.component_failure_counts is None:
                exp.component_failure_counts = {}
            
            for comp_id in attribution.components_failed:
                exp.component_failure_counts[comp_id] = exp.component_failure_counts.get(comp_id, 0) + 1
            
            self.experience_repo.save(exp)

            # v3.8: Continuous Learning - Extract lessons even from active experiences
            if self.lesson_extractor and (exp.validation_count + exp.falsification_count) >= 3:
                self._last_extracted_lesson_info = self.lesson_extractor.extract_lessons_from_active_experience(exp)

    def record_mutation_event(self, lineage_id: str, parent_theory_id: str, mutated_theory_id: str, attribution: "AttributionResult"):
        """Record a theory mutation linked to attribution."""
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            if not hasattr(exp, "causal_events") or exp.causal_events is None:
                exp.causal_events = []
                
            event = {
                "event_type": "mutation",
                "timestamp": attribution.timestamp,
                "parent_theory_id": parent_theory_id,
                "mutated_theory_id": mutated_theory_id,
                "triggered_by_components_failed": attribution.components_failed,
                "mutation_guidance": attribution.get_mutation_guidance()[:500],
            }
            exp.causal_events.append(event)
            self.experience_repo.save(exp)
    def record_contradiction(self, lineage_id: str, signatures: List[str] = None):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.contradiction_count += 1
            if signatures:
                for sig in signatures:
                    if sig not in exp.contradictions:
                        exp.contradictions.append(sig)
                        print(f"[ExperienceEngine] Contradiction Signature Added: {sig}")
            self.experience_repo.save(exp)

    def close_experience(self, lineage_id: str, date: str, message: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.status = ExperienceStatus.CLOSED
            # Calculate final outcome based on counts before saving
            total_signals = exp.validation_count + exp.falsification_count
            if total_signals > 0:
                exp.outcome.outcome_confidence = exp.validation_count / total_signals
            self.experience_repo.save(exp)
            if self.lesson_extractor: # CHANGE 7: Capture lesson info
                self._last_extracted_lesson_info = self.lesson_extractor.extract_lessons_from_closed_experience(exp)

    def record_validation(self, lineage_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.validation_count += 1
            exp.outcome.outcome_confidence = min(1.0, exp.outcome.outcome_confidence + 0.1)
            self.experience_repo.save(exp)
            
            # Trigger lesson check on successful validation
            if self.lesson_extractor and exp.validation_count >= 2:
                self._last_extracted_lesson_info = self.lesson_extractor.extract_lessons_from_active_experience(exp)


    def record_falsification(self, lineage_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.falsification_count += 1
            exp.outcome.outcome_confidence = max(0.0, exp.outcome.outcome_confidence - 0.1) # Balanced penalty
            self.experience_repo.save(exp)

    def get_active_experience_for_lineage(self, lineage_id: str) -> Optional[Experience]:
        return self.experience_repo.load_by_lineage(lineage_id, status=ExperienceStatus.ACTIVE)

    def set_lesson_extractor(self, lesson_extractor: "LessonExtractor"):
        """Sets the lesson extractor for the experience engine."""
        from market.replay.lesson_extractor import LessonExtractor
        self.lesson_extractor = lesson_extractor

    def get_last_extracted_lesson_with_reason(self) -> Tuple[Optional[LessonRecord], str, int]:
        """CHANGE 7: Returns the last lesson extracted by the lesson extractor along with reason and similar experience count."""
        return self._last_extracted_lesson_info

    def get_summary_stats(self) -> Dict[str, Any]:
        """Aggregates status and activity stats for the final journal."""
        exps = self.experience_repo.get_all()
        stats = {
            "created": len(exps),
            "active": sum(1 for e in exps if e.status == ExperienceStatus.ACTIVE),
            "closed": sum(1 for e in exps if e.status == ExperienceStatus.CLOSED),
            "validated": sum(1 for e in exps if e.outcome.outcome_confidence >= 0.7),
            "falsified": sum(1 for e in exps if e.outcome.outcome_confidence < 0.3),
            "abandoned": sum(1 for e in exps if e.status == ExperienceStatus.ABANDONED),
        }
        
        closed_exps = [e for e in exps if e.status == ExperienceStatus.CLOSED]
        if closed_exps:
            most_active = max(closed_exps, key=lambda e: e.mutation_count + e.contradiction_count)
            avg_conf = sum(e.outcome.outcome_confidence for e in closed_exps) / len(closed_exps)
            stats["most_active"] = {
                "lineage": most_active.lineage_id,
                "avg_confidence": round(avg_conf, 2),
                "theories": len(most_active.theory_ids),
                "contradictions": most_active.contradiction_count,
                "mutations": most_active.mutation_count
            }
        return stats

    def audit(self) -> Dict[str, Any]:
        """Provides a deeper health check on experience data."""
        exps = self.experience_repo.get_all()
        if not exps: return {}
        return {
            "avg_theories_per_experience": sum(len(e.theory_ids) for e in exps) / len(exps),
            "avg_mutations_per_experience": sum(e.mutation_count for e in exps) / len(exps),
            "avg_contradictions_per_experience": sum(e.contradiction_count for e in exps) / len(exps),
            "largest_experience": max([{"lineage": e.lineage_id, "theories": len(e.theory_ids), "mutations": e.mutation_count, "contradictions": e.contradiction_count} for e in exps], key=lambda x: x["theories"])
        }
