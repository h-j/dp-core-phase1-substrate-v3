from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class ValidationRecordModel(Base):
    """SQLAlchemy model representing a proposition's empirical validation history."""

    __tablename__ = "validation_records"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    proposition_id = Column(String, nullable=False)
    canonical_proposition_id = Column(String, nullable=False)
    theory_id = Column(String, nullable=False)
    lineage_id = Column(String, nullable=False)
    mechanism_ids = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    replay_step = Column(Integer, nullable=False)
    validation_state = Column(String, nullable=False)
    supporting_evidence = Column(JSON, nullable=True)
    contradicting_evidence = Column(JSON, nullable=True)
    confidence_before = Column(Float, nullable=False)
    confidence_after = Column(Float, nullable=False)
    confidence_delta = Column(Float, nullable=False)
    uncertainty_before = Column(Float, nullable=True)
    uncertainty_after = Column(Float, nullable=True)
    uncertainty_delta = Column(Float, nullable=True)
    market_context = Column(JSON, nullable=True)
    regime = Column(String, nullable=False)
    grounding_version = Column(String, nullable=False)
    compiler_version = Column(String, nullable=False)
    validation_engine_version = Column(String, nullable=False)
    validation_trace = Column(JSON, nullable=False)
    notes = Column(String, nullable=True)
