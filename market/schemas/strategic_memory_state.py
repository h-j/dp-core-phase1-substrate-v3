from typing import List

from cognition.schemas.base import CognitionBase


class StrategicMemoryState(CognitionBase):
    """
    Strategic cognition snapshot capturing reflective market understanding.
    
    Preserves longitudinal interpretation of:
    - Theory evolution trajectories
    - Coherence/instability patterns
    - Contradiction accumulation
    - Regime-sensitive postures
    - Uncertainty evolution
    """

    strategic_summary: str
    cognition_posture: str
    major_contradictions: List[str] = []
    weakening_assumptions: List[str] = []
    strengthening_patterns: List[str] = []
    regime_interpretation: str
    uncertainty_summary: str
    coherence_trajectory: str
    contradiction_frequency: dict = {}
