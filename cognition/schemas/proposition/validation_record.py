from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import Field

from cognition.schemas.base import CognitionBase


class ValidationRecord(CognitionBase):
    proposition_id: str
    canonical_proposition_id: str
    theory_id: str
    lineage_id: str
    mechanism_ids: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    replay_step: int
    validation_state: str  # GROUNDED, UNTRIGGERED, TRIGGERED, PARTIALLY_SUPPORTED, SUPPORTED, PARTIALLY_CONTRADICTED, CONTRADICTED, DORMANT, RETIRED
    supporting_evidence: Optional[Dict[str, Any]] = None
    contradicting_evidence: Optional[Dict[str, Any]] = None
    confidence_before: float
    confidence_after: float
    confidence_delta: float
    uncertainty_before: Optional[float] = None
    uncertainty_after: Optional[float] = None
    uncertainty_delta: Optional[float] = None
    market_context: Optional[Dict[str, Any]] = None
    regime: str
    grounding_version: str
    compiler_version: str
    validation_engine_version: str
    validation_trace: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
