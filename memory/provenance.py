"""
Memory Retrieval Quality & Provenance Models.

Provides explicit metrics, explanations, and reasoning lineage tracking for
retrieved memories and generated theories in DP-Core.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RetrievalDetail(BaseModel):
    """Detailed quality metrics and provenance for an individual retrieved memory."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_id: str
    date: str
    retrieval_score: float
    ranking: int
    similarity: float
    recency_contribution: float
    usefulness_estimate: float
    provenance_chain: List[str] = Field(default_factory=list)


class IgnoredCandidate(BaseModel):
    """Details of a candidate memory evaluated but excluded from retrieval results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    memory_id: str
    date: str
    similarity: float
    reason: str


class RetrievalExplanation(BaseModel):
    """Complete explainable summary produced for a memory retrieval query."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    retrieved_memories: List[RetrievalDetail] = Field(default_factory=list)
    ignored_candidates: List[IgnoredCandidate] = Field(default_factory=list)
    retrieval_success: bool = False
    query_signature: Optional[Dict[str, Any]] = None
    top_score: float = 0.0


class ReasoningProvenance(BaseModel):
    """Complete reasoning lineage attached to generated theories."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    observations_used: List[str] = Field(default_factory=list)
    mechanisms_used: List[str] = Field(default_factory=list)
    retrieved_memories: List[Dict[str, Any]] = Field(default_factory=list)
    reflections_consulted: List[str] = Field(default_factory=list)
    validation_results_incorporated: List[str] = Field(default_factory=list)
