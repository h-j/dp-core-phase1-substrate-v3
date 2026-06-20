from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
import json
from pathlib import Path

from market.replay.lesson_record import LessonRecord, LessonStatus


class LessonRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.lessons: Dict[UUID, LessonRecord] = self._load_lessons()
        self.debug = True

    def save(self, lesson: LessonRecord):
        lesson.last_updated_at = datetime.utcnow()
        self.lessons[lesson.lesson_id] = lesson
        self._save_lessons()
        if self.debug:
            print(f"[LessonRepository] Saved lesson: {lesson.lesson_id}")

    def get_by_id(self, lesson_id: UUID) -> Optional[LessonRecord]:
        return self.lessons.get(lesson_id)

    def list_lessons(
        self, status: Optional[LessonStatus] = None, limit: int = 100
    ) -> List[LessonRecord]:
        filtered_lessons = list(self.lessons.values())
        if status:
            filtered_lessons = [
                lesson for lesson in filtered_lessons if lesson.status == status
            ]

        # Sort by last_updated_at descending
        filtered_lessons.sort(key=lambda x: x.last_updated_at, reverse=True)
        return filtered_lessons[:limit]

    def _load_lessons(self) -> Dict[UUID, LessonRecord]:
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                return {UUID(k): LessonRecord.from_dict(v) for k, v in data.items()}
        except json.JSONDecodeError:
            if self.debug:
                print(
                    f"[LessonRepository] Error decoding JSON from {self.file_path}. Starting with empty lessons."
                )
            return {}
        except Exception as e:
            if self.debug:
                print(
                    f"[LessonRepository] Unexpected error loading lessons: {e}. Starting with empty lessons."
                )
            return {}

    def _save_lessons(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w") as f:
            json.dump(
                {str(k): v.to_dict() for k, v in self.lessons.items()}, f, indent=4
            )

    def clear_lessons(self):
        """For testing/resetting purposes."""
        self.lessons = {}
        self._save_lessons()
        if self.debug:
            print(f"[LessonRepository] Cleared all lessons.")

    def get_lesson_stats(self) -> Dict[str, Any]:
        total_lessons = len(self.lessons)
        candidate_lessons = sum(
            1
            for lesson in self.lessons.values()
            if lesson.status == LessonStatus.CANDIDATE
        )
        active_lessons = sum(
            1
            for lesson in self.lessons.values()
            if lesson.status == LessonStatus.ACTIVE
        )
        retired_lessons = sum(
            1
            for lesson in self.lessons.values()
            if lesson.status == LessonStatus.RETIRED
        )

        confidences = [lesson.confidence for lesson in self.lessons.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return {
            "total_lessons": total_lessons,
            "candidate_lessons": candidate_lessons,
            "active_lessons": active_lessons,
            "retired_lessons": retired_lessons,
            "avg_confidence": avg_confidence,
        }
