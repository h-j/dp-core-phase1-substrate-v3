from cognition.schemas.base import CognitionBase


class MarketObservation(CognitionBase):

    market_name: str
    observation_text: str
    trend_state: str
    volatility_state: str
    liquidity_state: str
    breadth_state: str
    macro_sentiment: str
    contradiction_markers: list[str] = []
    observation_source: str
