from enum import Enum
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CertificationLevel(str, Enum):
    CERTIFIED_GOLD = "CERTIFIED_GOLD"
    CERTIFIED_VALID = "CERTIFIED_VALID"
    WARNING_PROVISIONAL = "WARNING_PROVISIONAL"
    INVALID_REJECTED = "INVALID_REJECTED"


class ReportCertification(BaseModel):
    """
    Immutable certification signature issued by SIEL v1.0 upon report validation.
    """
    certificate_id: str
    level: CertificationLevel
    integrity_score: float = Field(..., ge=0.0, le=100.0)
    passed_rules_count: int
    failed_rules_count: int
    critical_failures_count: int
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: List[Dict[str, Any]] = Field(default_factory=list)
    remediation_recommendations: List[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()
