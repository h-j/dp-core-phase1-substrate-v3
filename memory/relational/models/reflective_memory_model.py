from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class ReflectiveMemoryModel(Base):

    __tablename__ = "reflective_memory_states"

    id = Column(String, primary_key=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    recurring_themes = Column(String)

    strengthening_patterns = Column(String)

    weakening_patterns = Column(String)

    persistent_uncertainties = Column(String)

    contradiction_hotspots = Column(String)

    cognition_trajectory_summary = Column(String)
