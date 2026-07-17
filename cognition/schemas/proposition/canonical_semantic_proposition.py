from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import Field

from cognition.schemas.base import CognitionBase


class CanonicalSemanticProposition(CognitionBase):
    theory_id: str
    lineage_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trigger_concept: Dict[str, Any] = Field(default_factory=dict)
    target_concept: Dict[str, Any] = Field(default_factory=dict)
    scope_concept: List[Dict[str, Any]] = Field(default_factory=list)
    causal_direction: str  # "positive", "negative", "neutral"
    compiler_provenance: Dict[str, Any] = Field(default_factory=dict)
