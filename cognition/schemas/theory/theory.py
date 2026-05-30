from typing import List

from cognition.schemas.base import CognitionBase
from cognition.schemas.confidence.confidence_state import ConfidenceState


class Theory(CognitionBase):

    lineage_id: str
    thesis: str
    summary: str
    assumptions: List[str] = []
    confidence_state: ConfidenceState
    # v3.0 Regime-based theory continuity
    regime_subtype: str = "neutral"
    falsifiability_conditions: List[str] = []
    regime_continuity_score: float = 0.0
    analog_divergence_claim: str = ""
    regime_description: str = ""
