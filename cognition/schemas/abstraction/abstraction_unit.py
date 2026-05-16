from cognition.schemas.base import CognitionBase


class AbstractionUnit(CognitionBase):

    source_observation_id: str
    abstraction_summary: str
    concepts: list[str] = []
