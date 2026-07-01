# Conviction Sizer Configuration Weights
WEIGHT_CALIBRATED_CONFIDENCE = 0.35
WEIGHT_INVERSE_CONTRADICTION = 0.20
WEIGHT_EMPIRICAL_CONFIDENCE = 0.20
WEIGHT_PRINCIPLE_SUPPORT = 0.15
WEIGHT_REGIME_STABILITY = 0.10

# Position Sizing Parameters
MIN_ALLOCATION = 0.02  # 2% minimum allocation
MAX_ALLOCATION = 0.15  # 15% maximum allocation

# Override Thresholds
THRESHOLD_CONTRADICTION_OVERRIDE = 0.70


from typing import Dict


class ConvictionResult:
    """
    Result containing allocation, final conviction score, and detailed component breakdown.
    Supports unpacking as a 2-tuple (allocation, final_score) for backward compatibility.
    """
    def __init__(self, allocation: float, final_score: float, component_breakdown: Dict[str, float]):
        self.allocation = allocation
        self.final_score = final_score
        self.component_breakdown = component_breakdown

    def __iter__(self):
        return iter((self.allocation, self.final_score))

    def __getitem__(self, item):
        # Allow indexing for backward compatibility
        return (self.allocation, self.final_score)[item]


class ConvictionSizer:
    """
    Computes conviction scores and sizes positions based on cognitive states.
    """

    def __init__(
        self,
        weight_calibrated: float = WEIGHT_CALIBRATED_CONFIDENCE,
        weight_contradiction: float = WEIGHT_INVERSE_CONTRADICTION,
        weight_empirical: float = WEIGHT_EMPIRICAL_CONFIDENCE,
        weight_principles: float = WEIGHT_PRINCIPLE_SUPPORT,
        weight_regime: float = WEIGHT_REGIME_STABILITY,
        min_alloc: float = MIN_ALLOCATION,
        max_alloc: float = MAX_ALLOCATION,
        contradiction_threshold: float = THRESHOLD_CONTRADICTION_OVERRIDE,
    ):
        self.weight_calibrated = weight_calibrated
        self.weight_contradiction = weight_contradiction
        self.weight_empirical = weight_empirical
        self.weight_principles = weight_principles
        self.weight_regime = weight_regime
        self.min_alloc = min_alloc
        self.max_alloc = max_alloc
        self.contradiction_threshold = contradiction_threshold

    def compute_sizer(
        self,
        calibrated_confidence: float,
        contradiction_pressure: float,
        empirical_confidence: float,
        principle_support: int,  # 0 or 1
        transition_pressure: float,
        prediction_direction: str,
    ) -> ConvictionResult:
        """
        Computes conviction score and allocation percentage based on cognitive state.

        Returns:
            ConvictionResult
        """
        # Calculate individual score components
        inverse_contradiction = 1.0 - contradiction_pressure
        regime_stability = 1.0 - transition_pressure

        # Conviction score: weighted sum
        conviction_score = (
            self.weight_calibrated * calibrated_confidence
            + self.weight_contradiction * inverse_contradiction
            + self.weight_empirical * empirical_confidence
            + self.weight_principles * principle_support
            + self.weight_regime * regime_stability
        )

        # Clamp conviction score to [0, 1] defensively
        conviction_score = max(0.0, min(1.0, conviction_score))

        # Linear mapping: allocation = min_alloc + conviction_score * (max_alloc - min_alloc)
        allocation = self.min_alloc + conviction_score * (
            self.max_alloc - self.min_alloc
        )

        # Hard overrides
        if (
            prediction_direction == "uncertain"
            or contradiction_pressure > self.contradiction_threshold
        ):
            allocation = 0.0

        # Round values for presentation
        allocation = float(round(allocation, 4))
        conviction_score = float(round(conviction_score, 4))

        # Build detailed components breakdown (Option B: showing base + penalties)
        component_breakdown = {
            "base": 0.30,
            "confidence": float(round(self.weight_calibrated * calibrated_confidence, 4)),
            "empirical": float(round(self.weight_empirical * empirical_confidence, 4)),
            "principle_support": float(round(self.weight_principles * principle_support, 4)),
            "contradictions": float(round(-self.weight_contradiction * contradiction_pressure, 4)),
            "transition_pressure": float(round(-self.weight_regime * transition_pressure, 4)),
        }

        return ConvictionResult(
            allocation=allocation,
            final_score=conviction_score,
            component_breakdown=component_breakdown,
        )
