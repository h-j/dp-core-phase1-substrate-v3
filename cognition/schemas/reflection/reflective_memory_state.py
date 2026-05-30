from typing import List

from cognition.schemas.base import CognitionBase


class ReflectiveMemoryState(CognitionBase):

    recurring_themes: List[str] = []
    strengthening_patterns: List[str] = []
    weakening_patterns: List[str] = []
    persistent_uncertainties: List[str] = []
    contradiction_hotspots: List[str] = []
    cognition_trajectory_summary: str
