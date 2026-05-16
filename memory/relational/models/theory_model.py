from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class TheoryModel(Base):

    __tablename__ = "theories"

    id = Column(String, primary_key=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    lineage_id = Column(String)

    thesis = Column(String)

    summary = Column(String)