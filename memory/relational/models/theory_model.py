from sqlalchemy import Column, DateTime, String, Text, Float, Integer, JSON
from sqlalchemy.sql import func

from memory.relational.base import Base


class TheoryModel(Base):

    __tablename__ = "theories"

    id = Column(String, primary_key=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lineage_id = Column(String)

    thesis = Column(String)

    summary = Column(String)
    # Preserve structured JSON when available (stored as JSON string)
    summary_structured = Column(Text)

    confidence_state_id = Column(String)  # Assuming this exists

    # --- ADD THESE NEW COLUMN DEFINITIONS ---
    llm_evaluation = Column(JSON)  # Use JSON for JSONB in SQLAlchemy
    survival_days = Column(Float, default=0.0)
    falsified_at_index = Column(Integer)
    falsification_precision = Column(Float)
    # ----------------------------------------
