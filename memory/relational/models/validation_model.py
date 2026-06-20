from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class ValidationModel(Base):

    __tablename__ = "validations"

    id = Column(String, primary_key=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    theory_id = Column(String)

    validation_summary = Column(String)

    observed_behavior = Column(String)

    expected_behavior = Column(String)
