from cognition.schemas.base import CognitionBase


class ReflectiveMemoryState(CognitionBase):

    recurring_themes: list[str] = []
    strengthening_patterns: list[str] = []
    weakening_patterns: list[str] = []
    persistent_uncertainties: list[str] = []
    contradiction_hotspots: list[str] = []
    cognition_trajectory_summary: str
