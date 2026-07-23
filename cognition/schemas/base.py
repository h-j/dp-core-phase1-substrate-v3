from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CognitionBase(BaseModel):

    id: str = Field(default_factory=lambda: str(uuid4()))
    structural_id: Optional[str] = None
    content_hash: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

