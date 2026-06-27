from typing import List, Optional

from cognition.schemas.base import CognitionBase
from cognition.schemas.confidence.confidence_state import ConfidenceState


class Branch(CognitionBase):
    condition: str
    action: str


class TheoryStructured(CognitionBase):
    mechanism: str = ""
    claim: str
    if_branch: Branch
    else_branch: Branch
    unless: str = ""
    falsified_if: str
    forbidden_state: str = ""
    mechanism_components: List[dict] = []
    falsification_conditions: List[str] = []
    reuse_decision: Optional[str] = None


class Theory(CognitionBase):

    lineage_id: str
    thesis: str
    summary: str
    summary_structured: Optional[TheoryStructured] = None
    assumptions: List[str] = []
    confidence_state: ConfidenceState
    # v3.0 Regime-based theory continuity
    regime_subtype: str = "neutral"
    falsifiability_conditions: List[str] = []
    regime_continuity_score: float = 0.0
    analog_divergence_claim: str = ""
    regime_description: str = ""
