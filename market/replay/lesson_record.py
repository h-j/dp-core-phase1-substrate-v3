from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class LessonStatus(str, Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    RETIRED = "retired"


@dataclass
class LessonRecord:
    lesson_id: UUID
    target_regime: Dict[str, str] = field(default_factory=dict)
    activation_conditions: List[str] = field(default_factory=list)
    failure_conditions: List[str] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    validation_count: int = 0
    falsification_count: int = 0
    confidence: float = 0.0
    status: LessonStatus = LessonStatus.CANDIDATE
    lesson_text: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
    source_experience_ids: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            k: (
                str(v)
                if isinstance(v, UUID)
                else (
                    v.value
                    if isinstance(v, Enum)
                    else v.isoformat() if isinstance(v, datetime) else v
                )
            )
            for k, v in self.__dict__.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        data["lesson_id"] = UUID(data["lesson_id"])
        data["status"] = LessonStatus(data["status"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["last_updated_at"] = datetime.fromisoformat(data["last_updated_at"])
        data["source_experience_ids"] = [
            str(uid) for uid in data["source_experience_ids"]
        ]
        
        # Upgrade path from older unstructured format
        if "target_regime" not in data:
            metadata = data.get("metadata", {}) or {}
            target_regime = {}
            if "regime_subtype" in metadata:
                target_regime["regime_subtype"] = metadata["regime_subtype"]
            for k, v in metadata.items():
                if k != "regime_subtype":
                    target_regime[k.lower()] = str(v).lower()
            data["target_regime"] = target_regime
            
        if "activation_conditions" not in data:
            data["activation_conditions"] = []
        if "failure_conditions" not in data:
            data["failure_conditions"] = []
        if "affected_components" not in data:
            data["affected_components"] = []
            
        if "validation_count" not in data:
            data["validation_count"] = data.pop("support_count", 0)
        else:
            data.pop("support_count", None)
            
        if "falsification_count" not in data:
            data["falsification_count"] = data.pop("contradiction_count", 0)
        else:
            data.pop("contradiction_count", None)
            
        data.pop("metadata", None)
        return cls(**data)

