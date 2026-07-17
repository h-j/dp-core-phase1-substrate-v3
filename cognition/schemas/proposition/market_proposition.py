from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import Field

from cognition.schemas.base import CognitionBase


class CompiledProposition(CognitionBase):
    theory_id: str
    lineage_id: str
    replay_step: int
    compilation_status: str  # "SUCCESS", "PARTIAL", "FAILED"
    failure_reason: Optional[str] = None
    trigger_definition: Optional[Dict[str, Any]] = None
    target_definition: Optional[Dict[str, Any]] = None
    scope_definition: Optional[List[Dict[str, Any]]] = None
    compiler_trace: Dict[str, Any] = Field(default_factory=dict)
