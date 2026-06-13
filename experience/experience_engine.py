from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID
from experience.experience_repository import ExperienceRepository
from experience.experience_types import Experience, ExperienceStatus, ExperienceOutcome

if TYPE_CHECKING:
    from market.replay.lesson_extractor import LessonExtractor
from market.replay.lesson_record import LessonRecord

class ExperienceEngine:
    def __init__(self, experience_repo: ExperienceRepository):
        self.experience_repo = experience_repo
        self.lesson_extractor: Optional[LessonExtractor] = None
        self._last_extracted_lesson: Optional[LessonRecord] = None

    def create_experience(self, theory_id: str, lineage_id: str, date: str):
        exp_id = f"exp_{lineage_id}_{date}"
        experience = Experience(
            experience_id=exp_id,
            lineage_id=lineage_id,
            theory_family_id=lineage_id, # Simplified for V1
            created_at=date,
            theory_ids=[theory_id]
        )
        self.experience_repo.save(experience)

    def attach_theory(self, lineage_id: str, theory_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.theory_ids.append(theory_id)
            exp.mutation_count += 1
            self.experience_repo.save(exp)

    def record_contradiction(self, lineage_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.contradiction_count += 1
            self.experience_repo.save(exp)

    def close_experience(self, lineage_id: str, date: str, message: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.status = ExperienceStatus.CLOSED
            self.experience_repo.save(exp)
            if self.lesson_extractor:
                self._last_extracted_lesson = self.lesson_extractor.extract_lessons_from_closed_experience(exp)

    def record_validation(self, lineage_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.outcome.outcome_confidence = min(1.0, exp.outcome.outcome_confidence + 0.1)
            self.experience_repo.save(exp)

    def record_falsification(self, lineage_id: str):
        exp = self.get_active_experience_for_lineage(lineage_id)
        if exp:
            exp.outcome.outcome_confidence = max(0.0, exp.outcome.outcome_confidence - 0.2)
            self.experience_repo.save(exp)

    def get_active_experience_for_lineage(self, lineage_id: str) -> Optional[Experience]:
        return self.experience_repo.load_by_lineage(lineage_id)

    def set_lesson_extractor(self, lesson_extractor: "LessonExtractor"):
        """Sets the lesson extractor for the experience engine."""
        from market.replay.lesson_extractor import LessonExtractor
        self.lesson_extractor = lesson_extractor

    def get_last_extracted_lesson(self) -> Optional[LessonRecord]:
        """Returns the last lesson extracted by the lesson extractor."""
        return self._last_extracted_lesson

    def get_summary_stats(self) -> Dict[str, Any]: return {} # Placeholder
    def audit(self) -> Dict[str, Any]: return {} # Placeholder
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
        if exps:
            most_active = max(exps, key=lambda e: e.mutation_count + e.contradiction_count)
            stats["most_active"] = {
                "lineage": most_active.lineage_id,
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