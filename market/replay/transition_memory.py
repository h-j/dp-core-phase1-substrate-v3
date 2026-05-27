from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class TransitionExample:
    date: str
    day_index: int
    from_regime: str
    to_regime: str
    confidence: float
    theory_usefulness: float
    contradiction_score: float
    pressure_score: float
    breakout_risk: bool
    direction_bias: str
    horizon_daily: str
    horizon_weekly: str
    horizon_monthly: str
    theory_summary: str

class TransitionMemoryStore:
    """Deterministic store for persisting and retrieving transition events."""
    
    def __init__(self):
        self.examples: List[TransitionExample] = []

    def record_transition(self, example: TransitionExample):
        self.examples.append(example)

    def retrieve_similar(
        self, 
        from_regime: str, 
        direction_bias: str, 
        pressure_score: float, 
        horizon_daily: str = "",
        limit: int = 3
    ) -> List[TransitionExample]:
        """Retrieve similar transitions using deterministic ranking."""
        # 1. Primary Filter: Regime and Bias
        candidates = [
            ex for ex in self.examples 
            if ex.from_regime == from_regime and ex.direction_bias == direction_bias
        ]
        
        if not candidates:
            return []

        # 2. Score Similarity (Pressure)
        def calculate_similarity(ex: TransitionExample):
            # Similarity is inverse of pressure distance
            pressure_dist = abs(ex.pressure_score - pressure_score)
            
            # Bonus for horizon alignment
            horizon_bonus = 0.2 if ex.horizon_daily == horizon_daily else 0.0
            
            # Higher is better
            return -(pressure_dist - horizon_bonus)

        # 3. Deterministic Sort
        sorted_candidates = sorted(
            candidates, key=lambda x: (calculate_similarity(x), x.day_index), reverse=True
        )
        
        return sorted_candidates[:limit]