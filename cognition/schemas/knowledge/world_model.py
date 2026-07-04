from datetime import datetime
from typing import Any, Dict, List

from pydantic import Field

from cognition.schemas.base import CognitionBase


class WorldModel(CognitionBase):
    step: int
    narrative_summary: str = Field(
        description="Narrative text synthesis of current active forces"
    )
    active_principle_ids: List[str] = Field(
        default_factory=list, description="IDs of active/stable principles"
    )
    regime_constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Deterministic constraints mapping regime to overrides",
    )

    # Matured World Model fields
    dominant_mechanisms: List[Dict[str, Any]] = Field(
        default_factory=list, description="Mechanisms backed by principles"
    )
    active_constraints: List[Dict[str, Any]] = Field(
        default_factory=list, description="Overriding constraints with references"
    )
    supporting_canonical_principles: List[str] = Field(
        default_factory=list, description="List of canonical principle IDs"
    )
    confidence: float = Field(default=0.5)
    stability: str = Field(default="Emerging")
    evidence_count: int = Field(default=0)
    applicable_regimes: List[str] = Field(default_factory=list)
    explanatory_constraints: List[str] = Field(
        default_factory=list, description="Descriptive constraint tokens"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "step": self.step,
            "narrative_summary": self.narrative_summary,
            "active_principle_ids": self.active_principle_ids,
            "regime_constraints": self.regime_constraints,
            "dominant_mechanisms": self.dominant_mechanisms,
            "active_constraints": self.active_constraints,
            "supporting_canonical_principles": self.supporting_canonical_principles,
            "confidence": self.confidence,
            "stability": self.stability,
            "evidence_count": self.evidence_count,
            "applicable_regimes": self.applicable_regimes,
            "explanatory_constraints": self.explanatory_constraints,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldModel":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            step=data["step"],
            narrative_summary=data["narrative_summary"],
            active_principle_ids=data.get("active_principle_ids", []),
            regime_constraints=data.get("regime_constraints", {}),
            dominant_mechanisms=data.get("dominant_mechanisms", []),
            active_constraints=data.get("active_constraints", []),
            supporting_canonical_principles=data.get(
                "supporting_canonical_principles", []
            ),
            confidence=data.get("confidence", 0.5),
            stability=data.get("stability", "Emerging"),
            evidence_count=data.get("evidence_count", 0),
            applicable_regimes=data.get("applicable_regimes", []),
            explanatory_constraints=data.get("explanatory_constraints", []),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst
