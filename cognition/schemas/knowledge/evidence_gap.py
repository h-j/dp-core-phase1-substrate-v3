from datetime import datetime, UTC
from typing import Dict, Any
from pydantic import Field

from cognition.schemas.base import CognitionBase

class EvidenceGap(CognitionBase):
    """
    EvidenceGap tracks unresolved Open Questions where missing evidence prevents learning.
    Future data acquisition is epistemically guided by these gaps.
    """
    open_question_id: str
    missing_evidence: str
    candidate_data_source: str
    expected_explanatory_value: str
    priority: str = "MEDIUM"  # "HIGH", "MEDIUM", "LOW"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "open_question_id": self.open_question_id,
            "missing_evidence": self.missing_evidence,
            "candidate_data_source": self.candidate_data_source,
            "expected_explanatory_value": self.expected_explanatory_value,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceGap":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            open_question_id=data["open_question_id"],
            missing_evidence=data["missing_evidence"],
            candidate_data_source=data["candidate_data_source"],
            expected_explanatory_value=data["expected_explanatory_value"],
            priority=data.get("priority", "MEDIUM"),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst
