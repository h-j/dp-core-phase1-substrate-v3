"""
Contradiction Graph — Explicit graph representation of competing theories and epistemic conflicts.
"""
import enum
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ContradictionStatus(str, enum.Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"
    PENDING_INVESTIGATION = "pending_investigation"


class ContradictionEdge(BaseModel):
    """Represents a directed contradiction relation between two theories."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: f"CONTR_{uuid.uuid4().hex[:8]}")
    source_theory_id: str
    target_theory_id: str
    contradiction_type: str = "STRUCTURAL"  # e.g., DIRECTIONAL, STRUCTURAL, EMPIRICAL
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.50
    timestamp: float = Field(default_factory=time.time)
    step: int = 0
    status: ContradictionStatus = ContradictionStatus.ACTIVE
    resolution_notes: Optional[str] = None
    winning_theory_id: Optional[str] = None


class ContradictionGraph:
    """
    Epistemic Contradiction Graph storing theories as nodes and contradictions as explicit edges.
    """

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: Dict[str, ContradictionEdge] = {}

    def add_theory_node(self, theory_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a theory node in the graph."""
        if theory_id not in self._nodes:
            self._nodes[theory_id] = metadata or {"id": theory_id}
            logger.debug("[ContradictionGraph] Added theory node '%s'.", theory_id)

    def add_contradiction(
        self,
        source_theory_id: str,
        target_theory_id: str,
        contradiction_type: str = "STRUCTURAL",
        supporting_evidence: Optional[List[str]] = None,
        confidence: float = 0.50,
        step: int = 0,
    ) -> ContradictionEdge:
        """
        Creates an explicit contradiction edge between two competing theories.
        """
        self.add_theory_node(source_theory_id)
        self.add_theory_node(target_theory_id)

        # Check for existing active edge to avoid duplicates
        for edge in self._edges.values():
            if (
                edge.status == ContradictionStatus.ACTIVE
                and edge.source_theory_id == source_theory_id
                and edge.target_theory_id == target_theory_id
                and edge.contradiction_type == contradiction_type
            ):
                return edge

        edge = ContradictionEdge(
            source_theory_id=source_theory_id,
            target_theory_id=target_theory_id,
            contradiction_type=contradiction_type,
            supporting_evidence=supporting_evidence or [],
            confidence=confidence,
            step=step,
            status=ContradictionStatus.ACTIVE,
        )
        self._edges[edge.id] = edge
        logger.info(
            "[ContradictionGraph] Created contradiction edge '%s' (%s -> %s) [%s]",
            edge.id,
            source_theory_id,
            target_theory_id,
            contradiction_type,
        )
        return edge

    def get_active_contradictions(self) -> List[ContradictionEdge]:
        """Return all active contradiction edges."""
        return [e for e in self._edges.values() if e.status == ContradictionStatus.ACTIVE]

    def get_conflicts_for_theory(self, theory_id: str) -> List[ContradictionEdge]:
        """Return all active contradiction edges involving the given theory."""
        return [
            e
            for e in self._edges.values()
            if (e.source_theory_id == theory_id or e.target_theory_id == theory_id)
            and e.status == ContradictionStatus.ACTIVE
        ]

    def get_competing_hypotheses(self, theory_id: str) -> List[str]:
        """Return IDs of all theories currently competing with the given theory."""
        competing: Set[str] = set()
        for edge in self.get_conflicts_for_theory(theory_id):
            if edge.source_theory_id == theory_id:
                competing.add(edge.target_theory_id)
            else:
                competing.add(edge.source_theory_id)
        return list(competing)

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Return graph diagnostics and summary statistics."""
        edges = list(self._edges.values())
        total = len(edges)
        active = sum(1 for e in edges if e.status == ContradictionStatus.ACTIVE)
        resolved = sum(1 for e in edges if e.status == ContradictionStatus.RESOLVED)
        superseded = sum(1 for e in edges if e.status == ContradictionStatus.SUPERSEDED)
        pending = sum(1 for e in edges if e.status == ContradictionStatus.PENDING_INVESTIGATION)

        return {
            "total_contradictions": total,
            "active_conflicts": active,
            "resolved_conflicts": resolved,
            "superseded_conflicts": superseded,
            "pending_investigation_conflicts": pending,
            "node_count": len(self._nodes),
            "edge_count": total,
        }
