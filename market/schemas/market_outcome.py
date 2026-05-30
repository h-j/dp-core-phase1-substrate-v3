from typing import List

from cognition.schemas.base import CognitionBase


class MarketOutcome(CognitionBase):
    """
    Realized market behavior AFTER prior observations/theories.
    
    Captures what actually happened in the market, enabling 
    validation of theories against reality and confidence adaptation.
    """

    market_name: str
    related_observation_id: str
    
    outcome_summary: str
    realized_trend: str
    realized_volatility: str
    realized_breadth: str
    realized_liquidity: str

    outcome_contradictions: List[str] = []
    outcome_confidence: float = 0.5
