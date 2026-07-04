from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from cognition.schemas.base import CognitionBase


class ReconciliationReport(CognitionBase):
    """
    Structured report generated during each Knowledge Reconciliation cycle.
    Tracks structural shifts, knowledge growth, and changes in Knowledge Debt.
    """

    step: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    merged_count: int
    generalized_count: int
    retired_count: int
    restricted_count: int
    knowledge_debt_before: float
    knowledge_debt_after: float
    coverage_before: float
    coverage_after: float
    compression_ratio_before: str
    compression_ratio_after: str
    summary_text: str

    # Distillation metrics
    principle_compression_ratio: float = Field(default=0.0)
    distillation_efficiency: float = Field(default=0.0)
    knowledge_density: float = Field(default=0.0)
    canonical_growth_rate: float = Field(default=0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "step": self.step,
            "merged_count": self.merged_count,
            "generalized_count": self.generalized_count,
            "retired_count": self.retired_count,
            "restricted_count": self.restricted_count,
            "knowledge_debt_before": self.knowledge_debt_before,
            "knowledge_debt_after": self.knowledge_debt_after,
            "coverage_before": self.coverage_before,
            "coverage_after": self.coverage_after,
            "compression_ratio_before": self.compression_ratio_before,
            "compression_ratio_after": self.compression_ratio_after,
            "summary_text": self.summary_text,
            "principle_compression_ratio": self.principle_compression_ratio,
            "distillation_efficiency": self.distillation_efficiency,
            "knowledge_density": self.knowledge_density,
            "canonical_growth_rate": self.canonical_growth_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReconciliationReport":
        ca = data.get("created_at")
        if isinstance(ca, str):
            ca = datetime.fromisoformat(ca)
        inst = cls(
            step=data["step"],
            merged_count=data["merged_count"],
            generalized_count=data["generalized_count"],
            retired_count=data["retired_count"],
            restricted_count=data["restricted_count"],
            knowledge_debt_before=data["knowledge_debt_before"],
            knowledge_debt_after=data["knowledge_debt_after"],
            coverage_before=data["coverage_before"],
            coverage_after=data["coverage_after"],
            compression_ratio_before=data["compression_ratio_before"],
            compression_ratio_after=data["compression_ratio_after"],
            summary_text=data["summary_text"],
            principle_compression_ratio=data.get("principle_compression_ratio", 0.0),
            distillation_efficiency=data.get("distillation_efficiency", 0.0),
            knowledge_density=data.get("knowledge_density", 0.0),
            canonical_growth_rate=data.get("canonical_growth_rate", 0.0),
        )
        inst.id = data["id"]
        if ca:
            inst.created_at = ca
        return inst
