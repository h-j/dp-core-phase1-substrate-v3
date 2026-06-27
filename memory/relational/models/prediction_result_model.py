from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, func)

from memory.relational.base import Base


class PredictionResultModel(Base):
    """SQLAlchemy model for tracking realized prediction performance."""

    __tablename__ = "prediction_results"

    id = Column(Integer, primary_key=True)
    date = Column(String, index=True)
    day_index = Column(Integer)

    prediction_id = Column(Integer, ForeignKey("prediction_probes.id"))

    prior_direction = Column(String)
    actual_direction = Column(String)

    direction_score = Column(Float)
    partial_score = Column(Float, default=0.0)
    invalidation_triggered = Column(Boolean, default=False)

    created_at = Column(DateTime, default=func.now())
