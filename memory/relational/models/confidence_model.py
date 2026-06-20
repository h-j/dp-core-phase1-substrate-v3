from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class ConfidenceModel(Base):

    __tablename__ = "confidence_states"

    id = Column(String, primary_key=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empirical_confidence = Column(Float)

    regime_confidence = Column(Float)

    reflection_confidence = Column(Float)

    theoretical_coherence = Column(Float)

    contradiction_pressure = Column(Float)
