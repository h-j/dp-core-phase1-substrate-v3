from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from cognition.schemas.base import CognitionBase


class PrincipleStatus(str, Enum):
    CANDIDATE = "candidate"
    EMERGING = "emerging"
    TRUSTED = "trusted"
    CANONICAL = "canonical"
    RETIRED = "retired"

    # Keep active/stable/challenged/revised for backward compatibility
    ACTIVE = "active"
    STABLE = "stable"
    CHALLENGED = "challenged"
    REVISED = "revised"


class FalsifiablePrediction(CognitionBase):
    target_component: str = Field(description="MechanismComponent being tested")
    expected_status: str = Field(description="Expected outcome: passed or failed")
    applicability_filter: Dict[str, Any] = Field(
        default_factory=dict, description="Context conditions"
    )
    empirical_support_count: int = Field(default=0)
    empirical_failure_count: int = Field(default=0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "target_component": self.target_component,
            "expected_status": self.expected_status,
            "applicability_filter": self.applicability_filter,
            "empirical_support_count": self.empirical_support_count,
            "empirical_failure_count": self.empirical_failure_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FalsifiablePrediction":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            target_component=data["target_component"],
            expected_status=data["expected_status"],
            applicability_filter=data.get("applicability_filter", {}),
            empirical_support_count=data.get("empirical_support_count", 0),
            empirical_failure_count=data.get("empirical_failure_count", 0),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst


class PrincipleRevision(CognitionBase):
    revision_step: int
    previous_statement: str
    updated_statement: str
    change_reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "revision_step": self.revision_step,
            "previous_statement": self.previous_statement,
            "updated_statement": self.updated_statement,
            "change_reason": self.change_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrincipleRevision":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            revision_step=data["revision_step"],
            previous_statement=data["previous_statement"],
            updated_statement=data["updated_statement"],
            change_reason=data["change_reason"],
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst


class MaturationEntry(CognitionBase):
    step: int
    status_before: str
    status_after: str
    support_count: int
    contradiction_count: int
    trust_score: float
    accuracy: float
    promotion_criteria: Dict[str, bool] = Field(default_factory=dict)
    promotion_requirements_remaining: List[str] = Field(default_factory=list)
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "step": self.step,
            "status_before": self.status_before,
            "status_after": self.status_after,
            "support_count": self.support_count,
            "contradiction_count": self.contradiction_count,
            "trust_score": self.trust_score,
            "accuracy": self.accuracy,
            "promotion_criteria": self.promotion_criteria,
            "promotion_requirements_remaining": self.promotion_requirements_remaining,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaturationEntry":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            step=data["step"],
            status_before=data["status_before"],
            status_after=data["status_after"],
            support_count=data.get("support_count", 0),
            contradiction_count=data.get("contradiction_count", 0),
            trust_score=data.get("trust_score", 0.0),
            accuracy=data.get("accuracy", 0.0),
            promotion_criteria=data.get("promotion_criteria", {}),
            promotion_requirements_remaining=data.get(
                "promotion_requirements_remaining", []
            ),
            reason=data.get("reason", ""),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst


class Principle(CognitionBase):
    status: PrincipleStatus = Field(default=PrincipleStatus.CANDIDATE)
    statement: str
    associated_lineage_ids: List[str] = Field(default_factory=list)
    supporting_theory_ids: List[str] = Field(default_factory=list)
    contradicting_theory_ids: List[str] = Field(default_factory=list)
    supporting_experience_ids: List[str] = Field(default_factory=list)
    falsifiable_predictions: List[FalsifiablePrediction] = Field(default_factory=list)
    confidence: float = Field(default=0.5)
    support_count: int = Field(default=0)
    contradiction_count: int = Field(default=0)
    created_at_step: int
    revision_history: List[PrincipleRevision] = Field(default_factory=list)
    uses_count: int = Field(default=0)
    predictions_helped: int = Field(default=0)
    predictions_harmed: int = Field(default=0)
    confidence_adjustments_triggered: int = Field(default=0)
    world_model_influence_count: int = Field(default=0)

    # Grounded ontology mappings
    grounded_mechanism_ids: List[str] = Field(default_factory=list)
    valid_under: Dict[str, Any] = Field(default_factory=dict)
    fails_under: Dict[str, Any] = Field(default_factory=dict)
    competing_principle_ids: List[str] = Field(default_factory=list)
    maturation_history: List[MaturationEntry] = Field(default_factory=list)
    grounded_concepts: List[str] = Field(default_factory=list)
    grounded_relations: Dict[str, str] = Field(default_factory=dict)
    supported_concepts: List[str] = Field(default_factory=list)
    supported_relations: List[str] = Field(default_factory=list)
    ontology_version: str = Field(default="1.0.0")
    validation_taxonomy_version: str = Field(default="1.0.0")

    # Trust parameters
    empirical_support: int = Field(default=0)
    cross_asset_support: int = Field(default=0)
    usefulness_trend: float = Field(default=0.0)
    stability_age: int = Field(default=0)
    confidence_interval: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    last_successful_reuse: Optional[str] = Field(default=None)
    last_contradiction: Optional[str] = Field(default=None)

    @property
    def usefulness_score(self) -> float:
        total_uses = self.uses_count
        if total_uses == 0:
            return 0.0
        net_helped = self.predictions_helped - self.predictions_harmed
        return float(net_helped / total_uses + 0.05 * total_uses)

    @property
    def trust_score(self) -> float:
        # Trust Score = Evidence + Reuse + Prediction Helpfulness + Cross Asset Validation - Contradictions - Age Decay
        evidence_term = min(15.0, self.support_count * 1.0)
        reuse_term = self.uses_count * 2.0
        helpfulness_term = self.predictions_helped * 3.0 - self.predictions_harmed * 5.0
        cross_asset_term = self.cross_asset_support * 5.0

        # Evidence-weighted penalty: penalty per contradiction drops as support accumulates
        penalty_per_contradiction = 4.0 * (1.0 / (1.0 + self.support_count * 0.1))
        contradiction_term = self.contradiction_count * penalty_per_contradiction

        age_decay_term = self.stability_age * 0.05

        score = (
            evidence_term
            + reuse_term
            + helpfulness_term
            + cross_asset_term
            - contradiction_term
            - age_decay_term
        )
        return float(round(score, 3))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "statement": self.statement,
            "associated_lineage_ids": self.associated_lineage_ids,
            "supporting_theory_ids": self.supporting_theory_ids,
            "contradicting_theory_ids": self.contradicting_theory_ids,
            "supporting_experience_ids": self.supporting_experience_ids,
            "falsifiable_predictions": [
                p.to_dict() for p in self.falsifiable_predictions
            ],
            "confidence": self.confidence,
            "support_count": self.support_count,
            "contradiction_count": self.contradiction_count,
            "created_at_step": self.created_at_step,
            "revision_history": [r.to_dict() for r in self.revision_history],
            "uses_count": self.uses_count,
            "predictions_helped": self.predictions_helped,
            "predictions_harmed": self.predictions_harmed,
            "confidence_adjustments_triggered": self.confidence_adjustments_triggered,
            "world_model_influence_count": self.world_model_influence_count,
            # Grounded ontology mappings
            "grounded_mechanism_ids": self.grounded_mechanism_ids,
            "valid_under": self.valid_under,
            "fails_under": self.fails_under,
            "competing_principle_ids": self.competing_principle_ids,
            "maturation_history": [m.to_dict() for m in self.maturation_history],
            "grounded_concepts": self.grounded_concepts,
            "grounded_relations": self.grounded_relations,
            "supported_concepts": self.supported_concepts,
            "supported_relations": self.supported_relations,
            "ontology_version": self.ontology_version,
            "validation_taxonomy_version": self.validation_taxonomy_version,
            # Trust parameters
            "empirical_support": self.empirical_support,
            "cross_asset_support": self.cross_asset_support,
            "usefulness_trend": self.usefulness_trend,
            "stability_age": self.stability_age,
            "confidence_interval": self.confidence_interval,
            "last_successful_reuse": self.last_successful_reuse,
            "last_contradiction": self.last_contradiction,
            "trust_score": self.trust_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Principle":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)

        status_val = data.get("status", "candidate")
        if isinstance(status_val, str):
            status_val = PrincipleStatus(status_val)

        inst = cls(
            status=status_val,
            statement=data["statement"],
            associated_lineage_ids=data.get("associated_lineage_ids", []),
            supporting_theory_ids=data.get("supporting_theory_ids", []),
            contradicting_theory_ids=data.get("contradicting_theory_ids", []),
            supporting_experience_ids=data.get("supporting_experience_ids", []),
            falsifiable_predictions=[
                FalsifiablePrediction.from_dict(p)
                for p in data.get("falsifiable_predictions", [])
            ],
            confidence=data.get("confidence", 0.5),
            support_count=data.get("support_count", 0),
            contradiction_count=data.get("contradiction_count", 0),
            created_at_step=data["created_at_step"],
            revision_history=[
                PrincipleRevision.from_dict(r) for r in data.get("revision_history", [])
            ],
            uses_count=data.get("uses_count", 0),
            predictions_helped=data.get("predictions_helped", 0),
            predictions_harmed=data.get("predictions_harmed", 0),
            confidence_adjustments_triggered=data.get(
                "confidence_adjustments_triggered", 0
            ),
            world_model_influence_count=data.get("world_model_influence_count", 0),
            # Grounded ontology mappings
            grounded_mechanism_ids=data.get("grounded_mechanism_ids", []),
            valid_under=data.get("valid_under", {}),
            fails_under=data.get("fails_under", {}),
            competing_principle_ids=data.get("competing_principle_ids", []),
            maturation_history=[
                MaturationEntry.from_dict(m) for m in data.get("maturation_history", [])
            ],
            grounded_concepts=data.get("grounded_concepts", []),
            grounded_relations=data.get("grounded_relations", {}),
            supported_concepts=data.get("supported_concepts", []),
            supported_relations=data.get("supported_relations", []),
            ontology_version=data.get("ontology_version", "1.0.0"),
            validation_taxonomy_version=data.get(
                "validation_taxonomy_version", "1.0.0"
            ),
            # Trust parameters
            empirical_support=data.get("empirical_support", 0),
            cross_asset_support=data.get("cross_asset_support", 0),
            usefulness_trend=data.get("usefulness_trend", 0.0),
            stability_age=data.get("stability_age", 0),
            confidence_interval=data.get("confidence_interval", [0.0, 0.0]),
            last_successful_reuse=data.get("last_successful_reuse"),
            last_contradiction=data.get("last_contradiction"),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst
