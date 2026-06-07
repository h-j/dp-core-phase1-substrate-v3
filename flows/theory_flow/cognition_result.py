from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class CognitionResult:
    """Encapsulates the full cognitive state of a single trading day."""
    day_index: int
    date: str
    observation: Any
    abstraction: Any
    theory: Any
    contradiction: Dict[str, Any]
    reflection: Any
    confidence: Any
    theory_usefulness: Dict[str, Any]
    
    # Inference & Assessment
    transition_pressure: Any
    prediction: Any
    prior_prediction_result: Optional[Any]
    decisions: Dict[str, Any]
    
    # Context & Memory
    regime_matches: List[Any]
    regime_history: Dict[str, Any]
    horizon_view: Any
    final_regime_signature: Any
    epistemic_quality: Dict[str, Any]
    dialectical_data: Optional[Dict[str, Any]] = None