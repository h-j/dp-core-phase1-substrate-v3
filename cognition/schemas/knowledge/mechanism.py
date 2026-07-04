from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import Field

from cognition.schemas.base import CognitionBase


class Mechanism(CognitionBase):
    mechanism_id: str = Field(
        default="", description="Persistent identifier e.g. MECH_001"
    )
    canonical_name: str = Field(
        default="", description="Grounded causal signature/name of the mechanism"
    )
    concept_tags: List[str] = Field(
        default_factory=list, description="Associated ontology concepts"
    )
    relation_type: Optional[str] = Field(default=None, description="Relation type")
    first_seen: int = Field(default=0, description="Step index when first seen")
    last_seen: int = Field(default=0, description="Step index when last seen")
    days_active: int = Field(
        default=0, description="Number of days this mechanism was active"
    )
    times_reused: int = Field(
        default=0, description="Number of times reused in other theories"
    )
    times_modified: int = Field(default=0, description="Number of times mutated")
    times_retired: int = Field(default=0, description="Number of times retired")
    support_count: int = Field(default=0, description="Number of validations/supports")
    contradiction_count: int = Field(default=0, description="Number of contradictions")
    prediction_helped: int = Field(
        default=0, description="Number of correct predictions contributed to"
    )
    prediction_harmed: int = Field(
        default=0, description="Number of incorrect predictions contributed to"
    )
    status: str = Field(
        default="candidate", description="candidate, active, stable, retired"
    )
    regimes_seen: List[str] = Field(
        default_factory=list, description="Market regimes/subtypes seen under"
    )

    # Keeping old fields for full backward compatibility
    name: str = Field(
        default="", description="Grounded causal signature/name of the mechanism"
    )
    description: str = Field(
        default="", description="Core structural claim of the mechanism"
    )
    concept_type: str = Field(
        default="candidate", description="Ontology class: core or candidate"
    )
    associated_theory_ids: List[str] = Field(
        default_factory=list, description="Theories mapped to this mechanism"
    )
    associated_lineages: List[str] = Field(
        default_factory=list, description="Lineages mapped to this mechanism"
    )
    created_at_step: int = Field(
        default=0,
        description="The replay step index when this mechanism was first extracted",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "mechanism_id": self.mechanism_id,
            "canonical_name": self.canonical_name,
            "concept_tags": self.concept_tags,
            "relation_type": self.relation_type,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "days_active": self.days_active,
            "times_reused": self.times_reused,
            "times_modified": self.times_modified,
            "times_retired": self.times_retired,
            "support_count": self.support_count,
            "contradiction_count": self.contradiction_count,
            "prediction_helped": self.prediction_helped,
            "prediction_harmed": self.prediction_harmed,
            "status": self.status,
            "regimes_seen": self.regimes_seen,
            # Backward compatibility
            "name": self.name or self.canonical_name,
            "description": self.description,
            "concept_type": self.concept_type,
            "associated_theory_ids": self.associated_theory_ids,
            "associated_lineages": self.associated_lineages,
            "created_at_step": self.created_at_step,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mechanism":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            mechanism_id=data.get("mechanism_id") or data.get("id") or "MECH_000",
            canonical_name=data.get("canonical_name") or data.get("name") or "",
            concept_tags=data.get("concept_tags") or [],
            relation_type=data.get("relation_type"),
            first_seen=data.get("first_seen") or data.get("created_at_step") or 0,
            last_seen=data.get("last_seen") or data.get("created_at_step") or 0,
            days_active=data.get("days_active", 0),
            times_reused=data.get("times_reused", 0),
            times_modified=data.get("times_modified", 0),
            times_retired=data.get("times_retired", 0),
            support_count=data.get("support_count", 0),
            contradiction_count=data.get("contradiction_count", 0),
            prediction_helped=data.get("prediction_helped", 0),
            prediction_harmed=data.get("prediction_harmed", 0),
            status=data.get("status") or "candidate",
            regimes_seen=data.get("regimes_seen") or [],
            # Backward compatibility
            name=data.get("name") or data.get("canonical_name") or "",
            description=data.get("description", ""),
            concept_type=data.get("concept_type", "candidate"),
            associated_theory_ids=data.get("associated_theory_ids", []),
            associated_lineages=data.get("associated_lineages", []),
            created_at_step=data.get("created_at_step") or data.get("first_seen") or 0,
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst
