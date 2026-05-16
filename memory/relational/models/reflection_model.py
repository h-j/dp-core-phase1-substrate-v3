from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class ReflectionModel(Base):

    __tablename__ = "reflections"

    id = Column(String, primary_key=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    related_theory_id = Column(String)

    reflection_summary = Column(String)

    confidence_impact = Column(String)