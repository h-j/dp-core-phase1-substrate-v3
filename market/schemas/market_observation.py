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
    descriptors: list[str] = []
    body_pct: float = 0.0
    upper_wick_pct: float = 0.0
    lower_wick_pct: float = 0.0
    close_position_pct: float = 0.0
    open_position_pct: float = 0.0
    candle_type: str = "neutral"
    participation_strength: str = "normal"
    participation_confirmation: str = "normal"
