from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String,
                        func)

from memory.relational.base import Base


class PredictionProbeModel(Base):
    """SQLAlchemy model for longitudinal prediction tracking."""

    __tablename__ = "prediction_probes"

    id = Column(Integer, primary_key=True)
    date = Column(String, index=True)
    day_index = Column(Integer)

    direction = Column(String)
    confidence = Column(Float)

    tension = Column(String, nullable=True)
    invalidation = Column(String, nullable=True)

    theory_id = Column(String, ForeignKey("theories.id"), nullable=True)
    reflection_id = Column(String, ForeignKey("reflections.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
