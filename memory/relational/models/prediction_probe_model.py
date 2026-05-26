from sqlalchemy import Column, Integer, String, Float, DateTime, func
from memory.relational.models.base import Base

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
    
    # v1.4 Adjustment: Use logical references instead of integer FKs
    theory_ref = Column(String, nullable=True)
    reflection_ref = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=func.now())