from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class ObservationModel(Base):

    __tablename__ = "observations"

    id = Column(String, primary_key=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    source_type = Column(String)

    raw_content = Column(String)

    source_reliability = Column(Float)