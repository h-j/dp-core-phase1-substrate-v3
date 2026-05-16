from cognition.schemas.base import CognitionBase


class ReflectionEvent(CognitionBase):

    related_theory_id: str
    reflection_summary: str
    confidence_impact: str
