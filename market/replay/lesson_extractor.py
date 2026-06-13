from __future__ import annotations
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from market.replay.lesson_record import LessonRecord, LessonStatus
from market.replay.lesson_repository import LessonRepository
if TYPE_CHECKING:
    from experience.experience_types import Experience
from experience.experience_repository import ExperienceRepository

class LessonExtractor: #
    def __init__(self, lesson_repo: LessonRepository, experience_repo: ExperienceRepository):
        self.lesson_repo = lesson_repo
        self.experience_repo = experience_repo
        self.debug = True # For logging during development
        self.MAX_GROUP_SIZE = 5 # Max experiences to group for pattern detection

    def extract_lessons_from_closed_experience(self, closed_experience: Experience) -> Optional[LessonRecord]:
        if self.debug: print(f"[LessonExtractor] Processing closed experience: {closed_experience.experience_id}")

        # 1. Group Similar Experiences
        similar_experiences = self._get_similar_closed_experiences(closed_experience)
        if self.debug: print(f"[LessonExtractor] Found {len(similar_experiences)} similar experiences for pattern detection.")
 
        # 2. Pattern Detection & Candidate Lesson Generation
        candidate_lesson_data = self._detect_patterns_and_generate_lesson(similar_experiences, closed_experience) #
        if not candidate_lesson_data:
            if self.debug: print("[LessonExtractor] No clear pattern detected for lesson generation. Skipping.")
            return None
        if self.debug: print(f"[LessonExtractor] Candidate Lesson: '{candidate_lesson_data['lesson_text']}'")
 
        # 4. Calculate Lesson Confidence
        confidence = self._calculate_lesson_confidence(
            candidate_lesson_data['support_count'],
            candidate_lesson_data['contradiction_count']
        )
        if self.debug: print(f"[LessonExtractor] Confidence: {confidence:.2f}")
 
        # 5. Create/Update LessonRecord
        existing_lesson = self._find_existing_lesson(
            candidate_lesson_data['lesson_text']
        )
        if existing_lesson:
            updated_lesson = self._update_lesson_record(
                existing_lesson,
                similar_experiences,
                confidence,
                candidate_lesson_data['support_count'],
                candidate_lesson_data['contradiction_count']
            )
            self.lesson_repo.save(updated_lesson)
            if self.debug: print(f"[LessonExtractor] Updated existing lesson: {updated_lesson.lesson_id} to status {updated_lesson.status.value}")
            return updated_lesson
        else:
            new_lesson = self._create_new_lesson_record(
                candidate_lesson_data['lesson_text'],
                similar_experiences,
                confidence,
                candidate_lesson_data['support_count'],
                candidate_lesson_data['contradiction_count']
            )
            self.lesson_repo.save(new_lesson)
            if self.debug: print(f"[LessonExtractor] Created new lesson: {new_lesson.lesson_id} with status {new_lesson.status.value}")
            return new_lesson

    def _get_similar_closed_experiences(self, primary_experience: Experience) -> List[Experience]:
        # Retrieve other closed experiences that share similar regime context and theory family
        # Assuming ExperienceRepository.list_experiences can filter by status
        all_closed_experiences = self.experience_repo.list_experiences(status="closed")
        
        similar_experiences = [primary_experience] # Always include the primary experience
        
        for exp in all_closed_experiences:
            if exp.experience_id == primary_experience.experience_id:
                continue # Skip self

            # V1 Pattern Detection: Simple matching criteria
            # 1. Same theory family (lineage)
            # 2. Similar regime context (at least one common element)
            # 3. Similar outcome (e.g., both validated or both falsified)
            # 4. Overlapping contradiction signals (at least one common element)

            # Check 1: Same theory family
            if exp.theory_family_id != primary_experience.theory_family_id:
                continue

            # Check 2: Overlapping regime context
            common_regimes = set(exp.regime_context) & set(primary_experience.regime_context)
            if not common_regimes:
                continue

            # Check 3: Similar outcome (simplified: both validated or both falsified)
            primary_outcome_validated = primary_experience.outcome.outcome_confidence >= 0.7
            exp_outcome_validated = exp.outcome.outcome_confidence >= 0.7
            if primary_outcome_validated != exp_outcome_validated:
                continue

            # Check 4: Overlapping contradiction signals (if any)
            common_contradictions = set(exp.contradictions) & set(primary_experience.contradictions)
            if primary_experience.contradictions and exp.contradictions and not common_contradictions:
                continue

            similar_experiences.append(exp)

            if len(similar_experiences) >= self.MAX_GROUP_SIZE:
                break # Limit group size

        return similar_experiences

    def _detect_patterns_and_generate_lesson(self, experiences: List[Experience], primary_experience: Experience) -> Optional[Dict[str, Any]]:
        if not experiences:
            return None

        # Aggregate data from similar experiences
        support_count = sum(1 for exp in experiences if exp.outcome.outcome_confidence >= 0.7) # High validation
        contradiction_count = sum(1 for exp in experiences if exp.outcome.outcome_confidence < 0.3) # Low validation/falsified

        # Determine common condition
        # For V1, let's simplify: common regime context and theory family
        common_regimes = set.intersection(*[set(exp.regime_context) for exp in experiences])
        condition_part = f"Under regime context: {', '.join(sorted(list(common_regimes)))}" if common_regimes else "Under various regime contexts"
        condition_part += f" and theory family: {primary_experience.theory_family_id}"
 
        # Determine common implication
        # If mostly supported, implication is positive. If mostly contradicted, implication is negative.
        if support_count > contradiction_count * 2:
            implication_part = "theories of this family tend to be validated."
        elif contradiction_count > support_count * 2:
            implication_part = "theories of this family tend to be falsified."
        else:
            implication_part = "theories of this family show mixed results."
 
        # Add more detail based on common contradiction signals if present
        all_contradictions = [c for exp in experiences for c in exp.contradictions]
        if all_contradictions:
            common_contradiction_signals = max(set(all_contradictions), key=all_contradictions.count)
            if all_contradictions.count(common_contradiction_signals) > len(experiences) / 2:
                implication_part += f" Often contradicted by: '{common_contradiction_signals}'."
 
        lesson_text = f"{condition_part}, {implication_part}"
 
        return {
            "lesson_text": lesson_text,
            "support_count": support_count,
            "contradiction_count": contradiction_count
        }

    def _calculate_lesson_confidence(self, support_count: int, contradiction_count: int) -> float:
        total_count = support_count + contradiction_count
        if total_count == 0:
            return 0.0
        return support_count / total_count #

    def _find_existing_lesson(self, lesson_text: str) -> Optional[LessonRecord]:
        # Simple matching: look for lessons with identical lesson_text
        # In V1, lesson_text is the primary identifier for a unique lesson.
        # This assumes lesson_text generation is deterministic for recurring patterns.
        all_lessons = self.lesson_repo.list_lessons(limit=1000) # Retrieve a reasonable number
        
        for lesson in all_lessons:
            if lesson.lesson_text == lesson_text:
                return lesson
        return None

    def _update_lesson_record(
        self,
        existing_lesson: LessonRecord,
        experiences: List[Experience],
        new_confidence: float,
        new_support_count: int,
        new_contradiction_count: int
    ) -> LessonRecord:
        # Update counts and recalculate cumulative confidence
        existing_lesson.support_count += new_support_count
        existing_lesson.contradiction_count += new_contradiction_count
        total = existing_lesson.support_count + existing_lesson.contradiction_count
        existing_lesson.confidence = existing_lesson.support_count / total if total > 0 else 0.0
        
        # Update source experience IDs
        new_exp_ids = [exp.experience_id for exp in experiences]
        existing_lesson.source_experience_ids = list(set(existing_lesson.source_experience_ids + new_exp_ids))

        # Update status based on confidence and counts
        # Reduced lifecycle states to candidate, active, retired
        if existing_lesson.confidence >= 0.5 and existing_lesson.support_count > existing_lesson.contradiction_count:
            existing_lesson.status = LessonStatus.ACTIVE
        elif existing_lesson.confidence < 0.2:
            existing_lesson.status = LessonStatus.RETIRED
        else:
            # If not active or retired, it remains a candidate or becomes one
            existing_lesson.status = LessonStatus.CANDIDATE

        existing_lesson.last_updated_at = datetime.utcnow()
        return existing_lesson

    def _create_new_lesson_record(
        self,
        lesson_text: str,
        experiences: List[Experience],
        confidence: float,
        support_count: int,
        contradiction_count: int
    ) -> LessonRecord:
        lesson_id = uuid4()
        status = LessonStatus.CANDIDATE
        if confidence >= 0.5 and support_count > contradiction_count:
            status = LessonStatus.ACTIVE
 
        return LessonRecord(
            lesson_id=lesson_id,
            lesson_text=lesson_text,
            confidence=confidence,
            support_count=support_count,
            contradiction_count=contradiction_count,
            source_experience_ids=[exp.experience_id for exp in experiences],
            status=status,
        )