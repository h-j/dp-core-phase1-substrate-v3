from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

class ExperienceStatus(Enum):
    OPEN = "open"
    ACTIVE = "active"
    VALIDATED = "validated"
    FALSIFIED = "falsified"
    ABANDONED = "abandoned"


@dataclass
class Experience:
    experience_id: str
    lineage_id: str
    originating_theory_id: str
    start_date: str
    end_date: Optional[str] = None
    status: ExperienceStatus = ExperienceStatus.ACTIVE
    theory_ids: List[str] = field(default_factory=list)
    contradiction_count: int = 0
    validation_count: int = 0
    falsification_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    mutation_count: int = 0
    summary: Optional[str] = None

class ExperienceEngine:
    def __init__(self, repository):
        self.repository = repository
        # Run-local cache of active experiences mapped by lineage_id
        self.active_experiences: Dict[str, Experience] = {}

    def create_experience(self, theory_id: str, lineage_id: str, date_str: str):
        """Starts a new experience tracking entry for a theory lineage."""
        experience_id = f"exp_{lineage_id}_{date_str}"
        now = datetime.now().isoformat()
        experience = Experience(
            experience_id=experience_id, 
            lineage_id=lineage_id, 
            originating_theory_id=theory_id,
            theory_ids=[theory_id],
            status=ExperienceStatus.OPEN,
            start_date=date_str,
            created_at=now,
            updated_at=now
        )
        self.active_experiences[lineage_id] = experience
        self.repository.save(experience)

    def attach_theory(self, lineage_id: str, theory_id: str):
        """Attaches a mutated or revived theory to an existing experience."""
        if lineage_id in self.active_experiences:
            exp = self.active_experiences[lineage_id]
            if theory_id not in exp.theory_ids:
                exp.theory_ids.append(theory_id)
                exp.mutation_count += 1
                if exp.status == ExperienceStatus.OPEN:
                    exp.status = ExperienceStatus.ACTIVE
                exp.updated_at = datetime.now().isoformat()
                self.repository.save(exp)

    def record_contradiction(self, lineage_id: str):
        """Increments the contradiction count for an experience."""
        if lineage_id in self.active_experiences:
            exp = self.active_experiences[lineage_id]
            exp.contradiction_count += 1
            exp.updated_at = datetime.now().isoformat()
            self.repository.save(exp)

    def record_validation(self, lineage_id: str):
        """Explicitly records a successful outcome validation."""
        if lineage_id in self.active_experiences:
            exp = self.active_experiences[lineage_id]
            exp.validation_count += 1
            exp.status = ExperienceStatus.VALIDATED
            exp.updated_at = datetime.now().isoformat()
            self.repository.save(exp)

    def record_falsification(self, lineage_id: str):
        """Explicitly records a prediction failure or invalidation."""
        if lineage_id in self.active_experiences:
            exp = self.active_experiences[lineage_id]
            exp.falsification_count += 1
            exp.status = ExperienceStatus.FALSIFIED
            exp.updated_at = datetime.now().isoformat()
            self.repository.save(exp)

    def close_experience(self, lineage_id: str, date_str: str, summary: str):
        """Finalizes an experience when a theory lineage is retired."""
        if lineage_id in self.active_experiences:
            exp = self.active_experiences.pop(lineage_id)
            exp.end_date = date_str
            exp.summary = summary
            exp.updated_at = datetime.now().isoformat()
            
            if exp.status in [ExperienceStatus.OPEN, ExperienceStatus.ACTIVE]:
                exp.status = ExperienceStatus.ABANDONED
            self.repository.save(exp)

    def get_active_experience_for_lineage(self, lineage_id: str) -> Optional[Experience]:
        """Retrieves current experience context for cognitive logging."""
        return self.active_experiences.get(lineage_id)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Provides aggregate metrics for the final Replay Journal."""
        all_exps = self.repository.get_all()
        
        abandoned = sum(1 for e in all_exps if e.status == ExperienceStatus.ABANDONED)
        
        most_active_exp = None
        if all_exps:
            most_active_exp = max(all_exps, key=lambda e: e.mutation_count + e.contradiction_count)

        stats = {
            "created": len(all_exps),
            "active": sum(1 for e in all_exps if e.status == ExperienceStatus.ACTIVE),
            "validated": sum(1 for e in all_exps if e.status == ExperienceStatus.VALIDATED),
            "falsified": sum(1 for e in all_exps if e.status == ExperienceStatus.FALSIFIED),
            "abandoned": abandoned,
        }
        
        if most_active_exp:
            stats["most_active"] = {
                "lineage": most_active_exp.lineage_id,
                "theories": len(most_active_exp.theory_ids),
                "contradictions": most_active_exp.contradiction_count,
                "mutations": most_active_exp.mutation_count
            }
            
        return stats