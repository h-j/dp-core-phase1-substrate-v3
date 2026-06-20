from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func

from memory.relational.base import Base


class StrategicMemoryModel(Base):
    """SQLAlchemy model for strategic memory snapshots."""

    __tablename__ = "strategic_memory"

    id = Column(String, primary_key=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    strategic_summary = Column(Text)

    cognition_posture = Column(String)

    major_contradictions = Column(String, default="")

    weakening_assumptions = Column(String, default="")

    strengthening_patterns = Column(String, default="")

    regime_interpretation = Column(Text)

    uncertainty_summary = Column(Text)

    coherence_trajectory = Column(Text)

    contradiction_frequency = Column(String, default="{}")
