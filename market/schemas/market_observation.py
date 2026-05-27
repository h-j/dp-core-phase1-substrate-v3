from cognition.schemas.base import CognitionBase


class MarketObservation(CognitionBase):

    market_name: str
    observation_text: str
    trend_state: str
    volatility_state: str
    liquidity_state: str
    breadth_state: str
    macro_sentiment: str
    observation_source: str
    related_observation_id: str = ""
    outcome_summary: str = ""
    realized_trend: str = ""
    realized_volatility: str = ""
    realized_breadth: str = ""
    realized_liquidity: str = ""
    outcome_confidence: float = 0.5
    contradiction_markers: list[str] = []
    outcome_contradictions: list[str] = []
