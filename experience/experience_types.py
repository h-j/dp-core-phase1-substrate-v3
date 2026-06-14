from dataclasses import dataclass, field
from enum import Enum
from typing import List

class ExperienceStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    VALIDATED = "validated"
    FALSIFIED = "falsified"
    ABANDONED = "abandoned"

@dataclass
class ExperienceOutcome:
    outcome_confidence: float = 0.5

@dataclass
class Experience:
    experience_id: str
    lineage_id: str
    theory_family_id: str
    created_at: str
    status: ExperienceStatus = ExperienceStatus.ACTIVE
    theory_ids: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    outcome: ExperienceOutcome = field(default_factory=ExperienceOutcome)
    regime_context: List[str] = field(default_factory=list)
    theory_subtype: str = ""
    mutation_count: int = 0
    contradiction_count: int = 0
    validation_count: int = 0
    falsification_count: int = 0