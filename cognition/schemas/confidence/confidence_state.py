from cognition.schemas.base import CognitionBase


class ConfidenceState(CognitionBase):

    alpha: float = 1.0
    beta: float = 1.0
    empirical_confidence: float = 0.5
    regime_confidence: float = 0.5
    reflection_confidence: float = 0.5
    theoretical_coherence: float = 0.5
    contradiction_pressure: float = 0.0

    @property
    def confidence(self) -> float:
        total = self.alpha + self.beta
        if total <= 0:
            return 0.5
        return self.alpha / total

    @property
    def uncertainty(self) -> float:
        total = self.alpha + self.beta
        if total <= 0:
            return 0.0
        return (self.alpha * self.beta) / ((total ** 2) * (total + 1.0))

    @property
    def evidence_count(self) -> float:
        return self.alpha + self.beta

