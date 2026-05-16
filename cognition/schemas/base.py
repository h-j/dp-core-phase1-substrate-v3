from datetime import datetime, UTC
from uuid import uuid4

from pydantic import BaseModel, Field


class CognitionBase(BaseModel):

    id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
