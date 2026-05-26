from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, func
from memory.relational.models.base import Base

class TransitionPressureModel(Base):
    """SQLAlchemy model for tracking regime transition pressure metrics."""
    __tablename__ = "transition_pressure_events"

    id = Column(Integer, primary_key=True)
    date = Column(String, index=True)
    day_index = Column(Integer)
    
    direction_bias = Column(String)
    pressure_score = Column(Float)
    stability_score = Column(Float)
    breakout_risk = Column(Boolean)
    
    # v1.4 Adjustment: Use Text for portability
    drivers_json = Column(Text)
    created_at = Column(DateTime, default=func.now())