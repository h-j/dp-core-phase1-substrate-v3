from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from memory.relational.base import Base


class MarketObservationModel(Base):

    __tablename__ = "market_observations"

    id = Column(String, primary_key=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    market_name = Column(String)

    observation_text = Column(String)

    trend_state = Column(String)

    volatility_state = Column(String)

    liquidity_state = Column(String)

    breadth_state = Column(String)

    macro_sentiment = Column(String)

    contradiction_markers = Column(String)

    observation_source = Column(String)
