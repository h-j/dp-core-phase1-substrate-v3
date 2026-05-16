from cognition.schemas.base import CognitionBase
from cognition.schemas.confidence.confidence_state import ConfidenceState


class Theory(CognitionBase):

    lineage_id: str
    thesis: str
    summary: str
    assumptions: list[str] = []
    confidence_state: ConfidenceState
