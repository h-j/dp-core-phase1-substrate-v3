from cognition.schemas.base import CognitionBase


class ValidationEvent(CognitionBase):

    theory_id: str
    validation_summary: str
    observed_behavior: str
    expected_behavior: str
