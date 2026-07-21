"""
Contradiction package for DP-Core.
"""
from cognition.contradiction.contradiction_detector import ContradictionDetector
from cognition.contradiction.contradiction_graph import (
    ContradictionEdge,
    ContradictionGraph,
    ContradictionStatus,
)
from cognition.contradiction.contradiction_resolver import ContradictionResolver

__all__ = [
    "ContradictionDetector",
    "ContradictionGraph",
    "ContradictionEdge",
    "ContradictionStatus",
    "ContradictionResolver",
]
