from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class CanonicalSemanticPropositionModel(Base):
    __tablename__ = "canonical_semantic_propositions"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    theory_id = Column(String, nullable=False)
    lineage_id = Column(String, nullable=False)
    trigger_concept = Column(JSON, nullable=False)
    target_concept = Column(JSON, nullable=False)
    scope_concept = Column(JSON, nullable=False)
    causal_direction = Column(String, nullable=False)
    compiler_provenance = Column(JSON, nullable=False)
