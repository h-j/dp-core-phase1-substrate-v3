from sqlalchemy import JSON, Column, DateTime, Float, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class BeliefStateModel(Base):
    """SQLAlchemy model representing dynamic lineage confidence and uncertainty states."""

    __tablename__ = "theory_lineage_states"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lineage_id = Column(String, nullable=False, index=True)
    active_theory_id = Column(String, nullable=False)
    confidence = Column(Float, default=0.50, nullable=False)
    uncertainty = Column(Float, default=0.50, nullable=False)
    status = Column(String, default="ACTIVE", nullable=False)
    last_validation_id = Column(String, nullable=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BeliefTransitionEventModel(Base):
    """SQLAlchemy model representing dynamic updates to lineage states caused by validation records."""

    __tablename__ = "belief_transition_events"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lineage_id = Column(String, nullable=False, index=True)
    validation_record_id = Column(String, nullable=True)
    confidence_before = Column(Float, nullable=False)
    confidence_after = Column(Float, nullable=False)
    uncertainty_before = Column(Float, nullable=False)
    uncertainty_after = Column(Float, nullable=False)
    status_before = Column(String, nullable=False)
    status_after = Column(String, nullable=False)
    evidence_weight = Column(Float, nullable=False)
    contradiction_score = Column(Float, nullable=False)
    transition_reason = Column(String, nullable=False)
    deterministic_calculation_trace = Column(JSON, nullable=False)
