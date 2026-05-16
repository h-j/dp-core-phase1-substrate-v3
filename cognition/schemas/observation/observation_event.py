from cognition.schemas.base import CognitionBase


class ObservationEvent(CognitionBase):

    source_type: str
    raw_content: str
    source_reliability: float = 0.5
