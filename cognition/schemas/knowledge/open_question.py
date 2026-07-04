from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from cognition.schemas.base import CognitionBase


class QuestionStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    RETIRED = "retired"


class OpenQuestion(CognitionBase):
    created_at_step: int
    question_text: str = Field(description="Structured question statement")
    source_contradiction_ids: List[str] = Field(
        default_factory=list,
        description="Surprise/contradiction IDs that prompted the question",
    )
    hypothesized_factors: List[str] = Field(
        default_factory=list,
        description="Hypothesized indicators/missing factors to test",
    )
    status: QuestionStatus = Field(default=QuestionStatus.ACTIVE)
    resolution_principle_id: Optional[str] = Field(
        default=None, description="Principle ID that resolved the question"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "created_at_step": self.created_at_step,
            "question_text": self.question_text,
            "source_contradiction_ids": self.source_contradiction_ids,
            "hypothesized_factors": self.hypothesized_factors,
            "status": self.status.value,
            "resolution_principle_id": self.resolution_principle_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OpenQuestion":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        status_val = data.get("status", "active")
        if isinstance(status_val, str):
            status_val = QuestionStatus(status_val)
        inst = cls(
            created_at_step=data["created_at_step"],
            question_text=data["question_text"],
            source_contradiction_ids=data.get("source_contradiction_ids", []),
            hypothesized_factors=data.get("hypothesized_factors", []),
            status=status_val,
            resolution_principle_id=data.get("resolution_principle_id"),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst
