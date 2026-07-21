"""
Diagnostics package for DP-Core.
"""
from diagnostics.collectors import EpistemicEventCollector
from diagnostics.report_generator import ResearchReportGenerator

__all__ = [
    "EpistemicEventCollector",
    "ResearchReportGenerator",
]
