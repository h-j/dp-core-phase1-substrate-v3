from cognition.schemas.base import CognitionBase


class ConfidenceState(CognitionBase):

    empirical_confidence: float = 0.5
    regime_confidence: float = 0.5
    reflection_confidence: float = 0.5
    theoretical_coherence: float = 0.5
    contradiction_pressure: float = 0.0
