from typing import List

from cognition.schemas.base import CognitionBase


class AbstractionUnit(CognitionBase):

    source_observation_id: str
    abstraction_summary: str
    concepts: List[str] = []
