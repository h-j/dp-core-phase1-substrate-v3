from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import Field

from cognition.schemas.base import CognitionBase


class BeliefState(CognitionBase):
    lineage_id: str
    active_theory_id: str
    confidence: float = 0.50
    uncertainty: float = 0.50
    status: str = "ACTIVE"  # "ACTIVE", "WEAKENED", "RETIRED", "DORMANT"
    last_validation_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "lineage_id": self.lineage_id,
            "active_theory_id": self.active_theory_id,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "status": self.status,
            "last_validation_id": self.last_validation_id,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeliefState":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        ua = data.get("updated_at")
        if isinstance(ua, str):
            ua = datetime.fromisoformat(ua)

        inst = cls(
            lineage_id=data["lineage_id"],
            active_theory_id=data["active_theory_id"],
            confidence=data.get("confidence", 0.50),
            uncertainty=data.get("uncertainty", 0.50),
            status=data.get("status", "ACTIVE"),
            last_validation_id=data.get("last_validation_id"),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        if ua:
            inst.updated_at = ua
        return inst


class BeliefTransitionEvent(CognitionBase):
    lineage_id: str
    validation_record_id: Optional[str] = None
    confidence_before: float
    confidence_after: float
    uncertainty_before: float
    uncertainty_after: float
    status_before: str
    status_after: str
    evidence_weight: float
    contradiction_score: float
    transition_reason: str
    deterministic_calculation_trace: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "lineage_id": self.lineage_id,
            "validation_record_id": self.validation_record_id,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "uncertainty_before": self.uncertainty_before,
            "uncertainty_after": self.uncertainty_after,
            "status_before": self.status_before,
            "status_after": self.status_after,
            "evidence_weight": self.evidence_weight,
            "contradiction_score": self.contradiction_score,
            "transition_reason": self.transition_reason,
            "deterministic_calculation_trace": self.deterministic_calculation_trace,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BeliefTransitionEvent":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)

        inst = cls(
            lineage_id=data["lineage_id"],
            validation_record_id=data.get("validation_record_id"),
            confidence_before=data["confidence_before"],
            confidence_after=data["confidence_after"],
            uncertainty_before=data["uncertainty_before"],
            uncertainty_after=data["uncertainty_after"],
            status_before=data["status_before"],
            status_after=data["status_after"],
            evidence_weight=data["evidence_weight"],
            contradiction_score=data["contradiction_score"],
            transition_reason=data["transition_reason"],
            deterministic_calculation_trace=data.get(
                "deterministic_calculation_trace", {}
            ),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst
