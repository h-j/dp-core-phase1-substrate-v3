from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CognitionResult:
    """Encapsulates the structured output of a day's cognition."""

    day_index: int
    date: str
    observation: Any
    abstraction: Any
    theory: Any
    contradiction: Dict
    reflection: Any
    confidence_state: Any
    validation: Any
    theory_usefulness: Dict
    transition_pressure: Any
    prediction: Any
    prior_prediction_result: Optional[Any]
    regime_matches: List[Any]
    horizon_view: Any
    regime_signature: Any
    regime_history: Any
    decisions: Dict
    branch_stats: Dict
    dialectical_data: Optional[Dict] = None
    lesson: str = ""
    epistemic_quality: Optional[Dict] = None
    snapshot_data: Optional[Dict] = None
