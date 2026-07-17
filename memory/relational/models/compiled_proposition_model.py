from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from memory.relational.base import Base


class CompiledPropositionModel(Base):
    __tablename__ = "compiled_propositions"

    id = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    theory_id = Column(String, nullable=False)
    lineage_id = Column(String, nullable=False)
    replay_step = Column(Integer, nullable=False)
    compilation_status = Column(String, nullable=False)
    failure_reason = Column(Text, nullable=True)
    trigger_definition = Column(JSON, nullable=True)
    target_definition = Column(JSON, nullable=True)
    scope_definition = Column(JSON, nullable=True)
    compiler_trace = Column(JSON, nullable=False)
