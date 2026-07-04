from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from cognition.schemas.base import CognitionBase
from cognition.schemas.confidence.confidence_state import ConfidenceState


class Branch(CognitionBase):
    condition: str
    action: str


class MechanismComponent(CognitionBase):
    component_id: str
    description: str
    observable: str
    expected_behavior: str
    dependency: Optional[str] = None
    concept_tags: List[str] = Field(
        default_factory=list, description="Ontology concept tags (core/candidate)"
    )
    relation_type: Optional[str] = Field(
        default=None, description="Relation type (AMPLIFIES/DAMPENS/etc.)"
    )
    mechanism_id: Optional[str] = Field(
        default=None, description="Stable mechanism identifier (e.g. MECH_001)"
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "component_id": self.component_id,
            "description": self.description,
            "observable": self.observable,
            "expected_behavior": self.expected_behavior,
            "dependency": self.dependency,
            "concept_tags": self.concept_tags,
            "relation_type": self.relation_type,
            "mechanism_id": self.mechanism_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MechanismComponent":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            component_id=data["component_id"],
            description=data["description"],
            observable=data["observable"],
            expected_behavior=data["expected_behavior"],
            dependency=data.get("dependency"),
            concept_tags=data.get("concept_tags", []),
            relation_type=data.get("relation_type"),
            mechanism_id=data.get("mechanism_id"),
        )
        inst.id = data.get("id", inst.id)
        if ca:
            inst.created_at = ca
        return inst


class TheoryStructured(CognitionBase):
    mechanism: str = ""
    claim: str
    if_branch: Branch
    else_branch: Branch
    unless: str = ""
    falsified_if: str
    forbidden_state: str = ""
    mechanism_components: List[MechanismComponent] = Field(default_factory=list)
    falsification_conditions: List[str] = Field(default_factory=list)
    reuse_decision: Optional[str] = None


class Theory(CognitionBase):
    lineage_id: str
    thesis: str
    summary: str
    summary_structured: Optional[TheoryStructured] = None
    assumptions: List[str] = Field(default_factory=list)
    confidence_state: ConfidenceState
    regime_subtype: str = "neutral"
    falsifiability_conditions: List[str] = Field(default_factory=list)
    regime_continuity_score: float = 0.0
    analog_divergence_claim: str = ""
    regime_description: str = ""
