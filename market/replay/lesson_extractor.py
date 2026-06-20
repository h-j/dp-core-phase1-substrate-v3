from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID, uuid4

from experience.experience_repository import ExperienceRepository
from experience.experience_types import Experience, ExperienceStatus
from market.replay.lesson_record import LessonRecord, LessonStatus
from market.replay.lesson_repository import LessonRepository


class LessonExtractor:  #
    def __init__(
        self, lesson_repo: LessonRepository, experience_repo: ExperienceRepository
    ):
        self.lesson_repo = lesson_repo
        self.experience_repo = experience_repo
        self.debug = True
        self.MAX_GROUP_SIZE = 5  # Max experiences to consider for a lesson
        self.MIN_EVIDENCE_THRESHOLD = (
            2  # Lower threshold to allow lessons to form in volatile regimes
        )
        self.processed_experience_ids: set[str] = set()

    def extract_lessons_from_active_experience(
        self, active_experience: Experience
    ) -> tuple[Optional[LessonRecord], str, int]:
        """v3.8: Support for continuous learning from ongoing lineages."""
        # We pass a flag to allow looking at other active experiences for quorum
        return self._run_extraction_logic(active_experience, allow_active=True)

    def extract_lessons_from_closed_experience(
        self, closed_experience: Experience
    ) -> tuple[Optional[LessonRecord], str, int]:
        return self._run_extraction_logic(closed_experience, allow_active=False)

    def _run_extraction_logic(
        self, experience: Experience, allow_active: bool = False
    ) -> tuple[Optional[LessonRecord], str, int]:
        # Prevent duplicate extraction for CLOSED experiences.
        # For ACTIVE experiences, we want to allow re-processing as their counts change,
        # so we do NOT add them to processed_experience_ids here.
        if (
            not allow_active
            and experience.experience_id in self.processed_experience_ids
        ):
            return None, "duplicate_extraction", 0
        if not allow_active:  # Only add closed experiences to the processed set
            self.processed_experience_ids.add(experience.experience_id)

        if self.debug:
            print(
                f"[LessonExtractor] Processing {'active' if allow_active else 'closed'} experience: {experience.experience_id}"
            )

        # 1. Group Similar Experiences
        similar_experiences = self._get_similar_experiences(
            experience, allow_active=allow_active
        )
        count = len(similar_experiences)

        # CHANGE 1: Minimum Evidence Threshold
        if count < self.MIN_EVIDENCE_THRESHOLD:
            if self.debug:
                print(
                    f"[LessonExtractor] Insufficient evidence: {count}/{self.MIN_EVIDENCE_THRESHOLD}"
                )
            return None, "insufficient_evidence", count

        # CHANGE 2: Internal Pattern Stage
        pattern = self._detect_patterns_and_generate_lesson(
            similar_experiences, experience
        )
        if not pattern:
            return None, "no_pattern", count

        # CHANGE 3: Remove Internal IDs From Lesson Text
        if self._contains_internal_id(pattern["lesson_text"]):
            if self.debug:
                print(
                    f"[LessonExtractor] Rejected lesson text containing internal IDs."
                )
            return None, "internal_id_rejected", count

        # 4. Calculate Lesson Confidence
        confidence = self._calculate_lesson_confidence(
            pattern["support_count"], pattern["contradiction_count"]
        )
        if self.debug:
            print(f"[LessonExtractor] Confidence: {confidence:.2f}")

        # REQUIREMENT 3: Prevent lessons with confidence=0.0 from being persisted
        if confidence == 0.0:
            if self.debug:
                print(
                    f"[LessonExtractor] Confidence is 0.0. Preventing lesson persistence."
                )
            return None, "zero_confidence_rejected", count
        existing_lesson = self._find_existing_lesson(pattern["lesson_text"])
        if existing_lesson:
            updated_lesson = self._update_lesson_record(
                existing_lesson,
                similar_experiences,
                confidence,
                pattern["support_count"],
                pattern["contradiction_count"],
            )
            self.lesson_repo.save(updated_lesson)
            return updated_lesson, "updated", count
        else:
            new_lesson = self._create_new_lesson_record(
                pattern["lesson_text"],
                similar_experiences,
                confidence,
                pattern["support_count"],
                pattern["contradiction_count"],
            )
            self.lesson_repo.save(new_lesson)
            return new_lesson, "created", count

    def _contains_internal_id(self, text: str) -> bool:
        """CHANGE 3: Checks if the lesson text contains internal identifiers."""
        uuid_pattern = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        hex_id_pattern = r"\b[0-9a-fA-F]{12,}\b"
        exp_id_pattern = r"exp_[a-zA-Z0-9_-]+"
        return any(
            re.search(p, text) for p in [uuid_pattern, hex_id_pattern, exp_id_pattern]
        )

    def _get_similar_experiences(
        self, primary_experience: Experience, allow_active: bool = False
    ) -> List[Experience]:
        # Retrieve other experiences that share similar regime context
        all_experiences = self.experience_repo.get_all()
        if not allow_active:
            all_experiences = [
                e for e in all_experiences if e.status == ExperienceStatus.CLOSED
            ]

        similar_experiences = [
            primary_experience
        ]  # Always include the primary experience

        for exp in all_experiences:
            if exp.experience_id == primary_experience.experience_id:
                continue  # Skip self

            # V1 Pattern Detection: Simple matching criteria
            # 1. Same theory family (lineage)
            # 2. Similar regime context (at least one common element)
            # 3. Similar outcome (e.g., both validated or both falsified)
            # 4. Overlapping contradiction signals (at least one common element)

            # CHANGE: Match on Theory Subtype to allow cross-lineage learning
            # This prevents knowledge from being siloed in specific lineage IDs
            if exp.theory_subtype != primary_experience.theory_subtype:
                continue  # Skip if subtypes don't match

            # Similarity based on grounded outcomes (validation/falsification counts)
            primary_outcome_validated = (
                primary_experience.validation_count
                >= primary_experience.falsification_count
            )
            exp_outcome_validated = exp.validation_count >= exp.falsification_count
            if primary_outcome_validated != exp_outcome_validated:
                continue

            # Check 4: Overlapping contradiction signals (if any)
            common_contradictions = set(exp.contradictions) & set(
                primary_experience.contradictions
            )
            if (
                primary_experience.contradictions
                and exp.contradictions
                and not common_contradictions
            ):
                continue

            similar_experiences.append(exp)

            if len(similar_experiences) >= self.MAX_GROUP_SIZE:
                break  # Limit group size

        return similar_experiences

    def _detect_patterns_and_generate_lesson(
        self, experiences: List[Experience], primary_experience: Experience
    ) -> Optional[Dict[str, Any]]:
        if not experiences:
            return None

        # Aggregate data from similar experiences
        # CHANGE: Use actual outcomes (validation_count), not outcome_confidence
        support_count = sum(
            1
            for exp in experiences
            if exp.validation_count > 0
            and exp.validation_count >= exp.falsification_count
        )
        contradiction_count = sum(
            1
            for exp in experiences
            if exp.falsification_count > 0
            and exp.falsification_count > exp.validation_count
        )

        # Determine common condition
        common_regimes = set.intersection(
            *[set(exp.regime_context) for exp in experiences]
        )

        condition_parts = []
        if common_regimes:
            condition_parts.append(
                f"Under regime context: {', '.join(sorted(list(common_regimes)))}"
            )

        if not condition_parts:
            condition_part = "Under various market conditions"
        else:
            condition_part = ", ".join(condition_parts)

        # Determine common implication
        if support_count > contradiction_count * 2:
            implication_part = "theories tend to be validated"
        elif contradiction_count > support_count * 2:
            implication_part = "theories tend to be falsified"
        else:
            implication_part = "theories show mixed results"

        if "compressed" in str(common_regimes).lower() and contradiction_count > 0:
            implication_part += " but degrade during volatility expansion"

        # Add more detail based on common contradiction signals if present
        all_contradictions = [c for exp in experiences for c in exp.contradictions]
        if all_contradictions:
            # Find most common contradiction signal
            from collections import Counter

            contradiction_counts = Counter(all_contradictions)
            most_common_contradiction, count = contradiction_counts.most_common(1)[0]

            # If it's common enough, add to implication
            if count >= 2 and count > len(experiences) / 2:
                implication_part += (
                    f" Often contradicted by: '{most_common_contradiction}'."
                )

        # REQUIREMENT 2: AttributionResult & component_failure_counts integration
        aggregated_failures = {}
        for exp in experiences:
            failure_counts = getattr(exp, "component_failure_counts", {}) or {}
            if isinstance(exp, dict):
                failure_counts = exp.get("component_failure_counts", {}) or {}
            for comp, cnt in failure_counts.items():
                aggregated_failures[comp] = aggregated_failures.get(comp, 0) + cnt

        root_causes = []
        for exp in experiences:
            events = getattr(exp, "causal_events", []) or []
            if isinstance(exp, dict):
                events = exp.get("causal_events", []) or []
            for event in events:
                if event.get("event_type") == "validation":
                    rc = event.get("root_cause")
                    if rc:
                        root_causes.append(rc)

        if aggregated_failures:
            sorted_failures = sorted(
                aggregated_failures.items(), key=lambda x: x[1], reverse=True
            )
            failure_str = ", ".join([f"{comp}:{cnt}" for comp, cnt in sorted_failures])
            implication_part += f" Component failure counts: [{failure_str}]."

        if root_causes:
            from collections import Counter

            rc_counts = Counter(root_causes)
            primary_rc, rc_cnt = rc_counts.most_common(1)[0]
            implication_part += f" Primary root cause: '{primary_rc}'."

        lesson_text = f"{condition_part}, {implication_part}"

        return {
            "lesson_text": lesson_text,
            "support_count": support_count,
            "contradiction_count": contradiction_count,
        }

    def _calculate_lesson_confidence(
        self, support_count: int, contradiction_count: int
    ) -> float:
        total_count = support_count + contradiction_count
        if total_count == 0:
            return 0.0
        return support_count / total_count

    def _find_existing_lesson(self, lesson_text: str) -> Optional[LessonRecord]:
        # Simple matching: look for lessons with identical lesson_text
        # In V1, lesson_text is the primary identifier for a unique lesson.
        # This assumes lesson_text generation is deterministic for recurring patterns.
        all_lessons = self.lesson_repo.list_lessons(
            limit=1000
        )  # Retrieve a reasonable number

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
        new_contradiction_count: int,
    ) -> LessonRecord:
        # Update counts and recalculate cumulative confidence
        existing_lesson.support_count += new_support_count
        existing_lesson.contradiction_count += new_contradiction_count
        total = existing_lesson.support_count + existing_lesson.contradiction_count
        existing_lesson.confidence = (
            existing_lesson.support_count / total if total > 0 else 0.0
        )

        # Update source experience IDs
        new_exp_ids = [exp.experience_id for exp in experiences]
        existing_lesson.source_experience_ids = list(
            set(existing_lesson.source_experience_ids + new_exp_ids)
        )

        # Update status based on confidence and counts
        # CHANGE 5: Simplified Lesson Lifecycle
        if existing_lesson.confidence >= 0.75:
            existing_lesson.status = LessonStatus.ACTIVE
        elif existing_lesson.confidence < 0.2:
            existing_lesson.status = LessonStatus.RETIRED
        else:
            existing_lesson.status = LessonStatus.CANDIDATE

        existing_lesson.last_updated_at = datetime.utcnow()
        return existing_lesson

    def _create_new_lesson_record(
        self,
        lesson_text: str,
        experiences: List[Experience],
        confidence: float,
        support_count: int,
        contradiction_count: int,
    ) -> LessonRecord:
        lesson_id = uuid4()
        status = LessonStatus.CANDIDATE
        if confidence >= 0.75:
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
