from typing import List

from pydantic import Field

from cognition.schemas.base import CognitionBase


class Pattern(CognitionBase):
    pattern_id: str
    failed_component: str
    root_cause: str
    contradiction_signatures: List[str] = Field(default_factory=list)
    regime_context: List[str] = Field(default_factory=list)
    source_experience_ids: List[str] = Field(default_factory=list)
    support_count: int = 0
    contradiction_count: int = 0
    confidence: float = 1.0
    lesson_text: str = ""
