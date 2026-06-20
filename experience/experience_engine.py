from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import UUID

from experience.experience_repository import ExperienceRepository
from experience.experience_types import (Experience, ExperienceOutcome,
                                         ExperienceStatus)

if TYPE_CHECKING:
    from market.replay.lesson_extractor import LessonExtractor

from dp.models.attribution import AttributionResult
from market.replay.lesson_record import LessonRecord


class ExperienceEngine:
    def __init__(self, experience_repo: ExperienceRepository):
        self.experience_repo = experience_repo
        self.lesson_extractor: Optional[LessonExtractor] = None
        self._last_extracted_lesson_info: Tuple[Optional[LessonRecord], str, int] = (
            None,
            "not_processed",
            0,
        )

    def create_experience(
        self,
        theory_id: str,
        lineage_id: str,
        date: str,
        regime_context: List[str] = None,
        theory_subtype: str = "",
    ):
        exp_id = f"exp_{lineage_id}_{date}"
        experience = Experience(
            experience_id=exp_id,
            lineage_id=lineage_id,
            theory_family_id=lineage_id,  # Simplified for V1
            created_at=date,
            theory_ids=[theory_id],
            regime_context=regime_context or [],
            theory_subtype=theory_subtype,
        )
        self.experience_repo.save(experience)

    def attach_theory(
        self, lineage_id: str, theory_id: str, synthesis_meta: Dict = None
    ):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.theory_ids.append(theory_id)
            exp.mutation_count += 1
            if synthesis_meta:
                # Store the logic of the synthesis as a mutation record
                exp.mutations.append(
                    f"Dialectical Synthesis: {synthesis_meta.get('conflict')}"
                )
            self.experience_repo.save(exp)

    def update_experience_with_attribution(
        self, lineage_id: str, attribution: "AttributionResult"
    ):
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

            if (
                not hasattr(exp, "component_failure_counts")
                or exp.component_failure_counts is None
            ):
                exp.component_failure_counts = {}

            for comp_id in attribution.components_failed:
                exp.component_failure_counts[comp_id] = (
                    exp.component_failure_counts.get(comp_id, 0) + 1
                )

            self.experience_repo.save(exp)

            # v3.8: Continuous Learning - Extract lessons even from active experiences
            if (
                self.lesson_extractor
                and (exp.validation_count + exp.falsification_count) >= 3
            ):
                self._last_extracted_lesson_info = (
                    self.lesson_extractor.extract_lessons_from_active_experience(exp)
                )

    def process_cycle(
        self,
        lineage_id: str,
        experience: Any,
        status: str,
        attribution: Optional[AttributionResult] = None,
    ):
        """Processes causal attribution for a validation cycle."""
        # Store causal attribution data if available
        if attribution is not None:
            # Initialize causal_events list if not present
            if isinstance(experience, dict):
                if "causal_events" not in experience:
                    experience["causal_events"] = []

                # Record this validation as a causal event
                event = {
                    "event_type": "validation",
                    "timestamp": attribution.timestamp,
                    "outcome": attribution.outcome,
                    "theory_claim": attribution.theory_claim[:200],
                    "components_passed": attribution.components_passed,
                    "components_failed": attribution.components_failed,
                    "root_cause": attribution.root_cause_component,
                    "falsification_triggered": attribution.falsification_triggered,
                    "divergence_point": attribution.divergence_point,
                    "attribution_confidence": attribution.attribution_confidence,
                    "attribution_reasoning": (
                        attribution.attribution_reasoning[:300]
                        if attribution.attribution_reasoning
                        else ""
                    ),
                }
                experience["causal_events"].append(event)

                # Update component failure counts for pattern detection
                if "component_failure_counts" not in experience:
                    experience["component_failure_counts"] = {}
                for comp_id in attribution.components_failed:
                    experience["component_failure_counts"][comp_id] = (
                        experience["component_failure_counts"].get(comp_id, 0) + 1
                    )
            else:
                # experience is an object (dataclass)
                if (
                    not hasattr(experience, "causal_events")
                    or experience.causal_events is None
                ):
                    experience.causal_events = []

                event = {
                    "event_type": "validation",
                    "timestamp": attribution.timestamp,
                    "outcome": attribution.outcome,
                    "theory_claim": attribution.theory_claim[:200],
                    "components_passed": attribution.components_passed,
                    "components_failed": attribution.components_failed,
                    "root_cause": attribution.root_cause_component,
                    "falsification_triggered": attribution.falsification_triggered,
                    "divergence_point": attribution.divergence_point,
                    "attribution_confidence": attribution.attribution_confidence,
                    "attribution_reasoning": (
                        attribution.attribution_reasoning[:300]
                        if attribution.attribution_reasoning
                        else ""
                    ),
                }
                experience.causal_events.append(event)

                if (
                    not hasattr(experience, "component_failure_counts")
                    or experience.component_failure_counts is None
                ):
                    experience.component_failure_counts = {}
                for comp_id in attribution.components_failed:
                    experience.component_failure_counts[comp_id] = (
                        experience.component_failure_counts.get(comp_id, 0) + 1
                    )

        # Automatically transition experience status based on confidence
        if isinstance(experience, dict):
            val_count = experience.get("validation_count", 0)
            fals_count = experience.get("falsification_count", 0)
            total = val_count + fals_count
            if total > 0:
                if "outcome" not in experience:
                    experience["outcome"] = {"outcome_confidence": 0.5}
                elif isinstance(experience["outcome"], dict):
                    experience["outcome"]["outcome_confidence"] = val_count / total
                else:
                    experience["outcome"].outcome_confidence = val_count / total

            conf = (
                experience["outcome"]["outcome_confidence"]
                if isinstance(experience["outcome"], dict)
                else experience["outcome"].outcome_confidence
            )

            if status in ["closed", "closed"]:
                experience["status"] = ExperienceStatus.CLOSED
            elif status in ["abandoned"]:
                experience["status"] = ExperienceStatus.ABANDONED
            else:
                if attribution is not None and getattr(attribution, "outcome", None) is not None:
                    attr_outcome = attribution.outcome
                    if attr_outcome == "validated":
                        experience["status"] = ExperienceStatus.VALIDATED
                    elif attr_outcome == "falsified":
                        experience["status"] = ExperienceStatus.FALSIFIED
                    else:
                        experience["status"] = ExperienceStatus.ACTIVE
                else:
                    if conf >= 0.7:
                        experience["status"] = ExperienceStatus.VALIDATED
                    elif conf < 0.3:
                        experience["status"] = ExperienceStatus.FALSIFIED
                    else:
                        experience["status"] = ExperienceStatus.ACTIVE
        else:
            total = experience.validation_count + experience.falsification_count
            if total > 0:
                experience.outcome.outcome_confidence = (
                    experience.validation_count / total
                )

            if status in [
                "closed",
                ExperienceStatus.CLOSED,
                ExperienceStatus.CLOSED.value,
            ]:
                experience.status = ExperienceStatus.CLOSED
            elif status in [
                "abandoned",
                ExperienceStatus.ABANDONED,
                ExperienceStatus.ABANDONED.value,
            ]:
                experience.status = ExperienceStatus.ABANDONED
            else:
                if attribution is not None and getattr(attribution, "outcome", None) is not None:
                    attr_outcome = attribution.outcome
                    if attr_outcome == "validated":
                        experience.status = ExperienceStatus.VALIDATED
                    elif attr_outcome == "falsified":
                        experience.status = ExperienceStatus.FALSIFIED
                    else:
                        experience.status = ExperienceStatus.ACTIVE
                else:
                    if experience.outcome.outcome_confidence >= 0.7:
                        experience.status = ExperienceStatus.VALIDATED
                    elif experience.outcome.outcome_confidence < 0.3:
                        experience.status = ExperienceStatus.FALSIFIED
                    else:
                        experience.status = ExperienceStatus.ACTIVE

            # Save the updated experience to repository
            self.experience_repo.save(experience)

            # Trigger lesson extraction from process_cycle
            if self.lesson_extractor:
                if experience.status == ExperienceStatus.CLOSED:
                    self._last_extracted_lesson_info = (
                        self.lesson_extractor.extract_lessons_from_closed_experience(
                            experience
                        )
                    )
                else:
                    self._last_extracted_lesson_info = (
                        self.lesson_extractor.extract_lessons_from_active_experience(
                            experience
                        )
                    )

        # For printing compatibility, retrieve experience_id and create a getter wrapper if needed
        original_experience = experience
        if not hasattr(experience, "get"):

            class ExperienceWrapper:
                def __init__(self, obj):
                    self.obj = obj

                def get(self, key, default=None):
                    val = getattr(self.obj, key, None)
                    return default if val is None else val

            experience = ExperienceWrapper(original_experience)
            experience_id = getattr(original_experience, "experience_id", "")
        else:
            experience_id = experience.get("experience_id", "")

        # Get actual transitioned status
        if isinstance(original_experience, dict):
            current_status = original_experience.get("status", "active")
            if hasattr(current_status, "value"):
                current_status = current_status.value
        else:
            current_status = original_experience.status.value

        # Print statement exactly as requested
        if attribution is not None and attribution.components_failed:
            print(
                f"  [ATTRIBUTION] lineage={lineage_id} exp={experience_id} "
                f"status={current_status} failed={attribution.components_failed} "
                f"root_cause={attribution.root_cause_component}"
            )
        elif attribution is not None:
            print(
                f"  [ATTRIBUTION] lineage={lineage_id} exp={experience_id} "
                f"status={current_status} all_components_passed "
                f"confidence={attribution.attribution_confidence:.2f}"
            )
        else:
            print(
                f"  [ATTRIBUTION] lineage={lineage_id} exp={experience_id} "
                f"status={current_status} validation_count={experience.get('validation_count', 0)} "
                f"falsification_count={experience.get('falsification_count', 0)}"
            )

    def record_mutation_event(
        self,
        lineage_id: str,
        parent_theory_id: str,
        mutated_theory_id: str,
        attribution: "AttributionResult",
    ):
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
                        print(
                            f"[ExperienceEngine] Contradiction Signature Added: {sig}"
                        )
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
            if self.lesson_extractor:  # CHANGE 7: Capture lesson info
                self._last_extracted_lesson_info = (
                    self.lesson_extractor.extract_lessons_from_closed_experience(exp)
                )

    def _update_lifecycle_status(self, exp: Experience):
        total = exp.validation_count + exp.falsification_count
        if total > 0:
            exp.outcome.outcome_confidence = exp.validation_count / total

        if exp.status not in [ExperienceStatus.CLOSED, ExperienceStatus.ABANDONED]:
            if exp.outcome.outcome_confidence >= 0.7:
                exp.status = ExperienceStatus.VALIDATED
            elif exp.outcome.outcome_confidence < 0.3:
                exp.status = ExperienceStatus.FALSIFIED
            else:
                exp.status = ExperienceStatus.ACTIVE

    def record_validation(self, lineage_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.validation_count += 1
            self._update_lifecycle_status(exp)
            self.experience_repo.save(exp)

            # Trigger lesson check on successful validation
            if self.lesson_extractor and exp.validation_count >= 2:
                self._last_extracted_lesson_info = (
                    self.lesson_extractor.extract_lessons_from_active_experience(exp)
                )

    def record_falsification(self, lineage_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.falsification_count += 1
            self._update_lifecycle_status(exp)
            self.experience_repo.save(exp)

    def get_active_experience_for_lineage(
        self, lineage_id: str
    ) -> Optional[Experience]:
        for status in [
            ExperienceStatus.ACTIVE,
            ExperienceStatus.VALIDATED,
            ExperienceStatus.FALSIFIED,
        ]:
            exp = self.experience_repo.load_by_lineage(lineage_id, status=status)
            if exp:
                return exp
        return None

    def set_lesson_extractor(self, lesson_extractor: "LessonExtractor"):
        """Sets the lesson extractor for the experience engine."""
        from market.replay.lesson_extractor import LessonExtractor

        self.lesson_extractor = lesson_extractor

    def get_last_extracted_lesson_with_reason(
        self,
    ) -> Tuple[Optional[LessonRecord], str, int]:
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
            most_active = max(
                closed_exps, key=lambda e: e.mutation_count + e.contradiction_count
            )
            avg_conf = sum(e.outcome.outcome_confidence for e in closed_exps) / len(
                closed_exps
            )
            stats["most_active"] = {
                "lineage": most_active.lineage_id,
                "avg_confidence": round(avg_conf, 2),
                "theories": len(most_active.theory_ids),
                "contradictions": most_active.contradiction_count,
                "mutations": most_active.mutation_count,
            }
        return stats

    def audit(self) -> Dict[str, Any]:
        """Provides a deeper health check on experience data."""
        exps = self.experience_repo.get_all()
        if not exps:
            return {}
        return {
            "avg_theories_per_experience": sum(len(e.theory_ids) for e in exps)
            / len(exps),
            "avg_mutations_per_experience": sum(e.mutation_count for e in exps)
            / len(exps),
            "avg_contradictions_per_experience": sum(
                e.contradiction_count for e in exps
            )
            / len(exps),
            "largest_experience": max(
                [
                    {
                        "lineage": e.lineage_id,
                        "theories": len(e.theory_ids),
                        "mutations": e.mutation_count,
                        "contradictions": e.contradiction_count,
                    }
                    for e in exps
                ],
                key=lambda x: x["theories"],
            ),
        }
