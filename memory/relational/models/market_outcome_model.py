from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.sql import func

from memory.relational.base import Base


class MarketOutcomeModel(Base):
    """SQLAlchemy model for market outcomes."""

    __tablename__ = "market_outcomes"

    id = Column(String, primary_key=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    market_name = Column(String)

    # FK to observations; SET NULL protects against orphaned legacy rows
    related_observation_id = Column(
        String, ForeignKey("observations.id", ondelete="SET NULL"), nullable=True
    )

    outcome_summary = Column(Text)

    realized_trend = Column(String)

    realized_volatility = Column(String)

    realized_breadth = Column(String)

    realized_liquidity = Column(String)

    outcome_contradictions = Column(String, default="")

    outcome_confidence = Column(Float, default=0.5)
