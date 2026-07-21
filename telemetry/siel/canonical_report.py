from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ReportMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    days: int
    date_range: str
    execution_hash: str
    git_commit: str
    llm_version: str
    replay_version: str


class NarrativeSummary(BaseModel):
    model_config = ConfigDict(frozen=True)
    story_text: str
    theories_generated: int
    propositions_compiled: int
    lessons_extracted: int
    principles_active: int
    evidence_gaps_count: int


class CanonicalReplayReport(BaseModel):
    """
    Single Immutable Source of Truth for DP/EkamNet Replay Reports.
    Enforces frozen dictionary structure and schema validation.
    """
    model_config = ConfigDict(frozen=True)

    metadata: ReportMetadata
    narrative: NarrativeSummary
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    metrics_kpi: Dict[str, float] = Field(default_factory=dict)
    knowledge_health: Dict[str, float] = Field(default_factory=dict)
    knowledge_lifecycle: Dict[str, int] = Field(default_factory=dict)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    theory_evolution: List[Dict[str, Any]] = Field(default_factory=list)
    compilation_metrics: Dict[str, Any] = Field(default_factory=dict)
    eef_dashboard: Dict[str, Any] = Field(default_factory=dict)
    certification: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.model_dump()
