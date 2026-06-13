from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID

class LessonStatus(str, Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RETIRED = "retired"

@dataclass
class LessonRecord:
    lesson_id: UUID
    lesson_text: str
    support_count: int = 0
    contradiction_count: int = 0
    confidence: float = 0.0
    status: LessonStatus = LessonStatus.CANDIDATE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
    source_experience_ids: List[str] = field(default_factory=list)

    def to_dict(self):
        return {k: str(v) if isinstance(v, UUID) else v.value if isinstance(v, Enum) else v.isoformat() if isinstance(v, datetime) else v for k, v in self.__dict__.items()}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        data['lesson_id'] = UUID(data['lesson_id'])
        data['status'] = LessonStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated_at'] = datetime.fromisoformat(data['last_updated_at'])
        data['source_experience_ids'] = [str(uid) for uid in data['source_experience_ids']]
        return cls(**data)