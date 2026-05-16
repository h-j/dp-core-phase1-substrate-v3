from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class AbstractionModel(Base):

    __tablename__ = "abstractions"

    id = Column(String, primary_key=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    source_observation_id = Column(String)

    abstraction_summary = Column(String)