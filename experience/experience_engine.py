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

    def _get_or_load_experience(self, lineage_id: str) -> Optional[Experience]:
        """Ensures the experience is in the active cache, loading from repo if needed."""
        if lineage_id in self.active_experiences:
            return self.active_experiences[lineage_id]
        
        # Try to recover from repository to maintain lineage persistence
        exp = self.repository.load_by_lineage(lineage_id)
        if exp:
            self.active_experiences[lineage_id] = exp
            return exp
        return None

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
        exp = self._get_or_load_experience(lineage_id)
        if exp and theory_id not in exp.theory_ids:
            exp.theory_ids.append(theory_id)
            exp.mutation_count += 1
            if exp.status in [ExperienceStatus.OPEN, ExperienceStatus.ABANDONED]:
                exp.status = ExperienceStatus.ACTIVE
            exp.updated_at = datetime.now().isoformat()
            self.repository.save(exp)

    def record_contradiction(self, lineage_id: str):
        """Increments the contradiction count for an experience."""
        exp = self._get_or_load_experience(lineage_id)
        if exp:
            exp.contradiction_count += 1
            exp.updated_at = datetime.now().isoformat()
            self.repository.save(exp)

    def record_validation(self, lineage_id: str):
        """Explicitly records a successful outcome validation."""
        exp = self._get_or_load_experience(lineage_id)
        if exp:
            exp.validation_count += 1
            exp.status = ExperienceStatus.VALIDATED
            exp.updated_at = datetime.now().isoformat()
            self.repository.save(exp)

    def record_falsification(self, lineage_id: str):
        """Explicitly records a prediction failure or invalidation."""
        exp = self._get_or_load_experience(lineage_id)
        if exp:
            exp.falsification_count += 1
            exp.status = ExperienceStatus.FALSIFIED
            exp.updated_at = datetime.now().isoformat()
            self.repository.save(exp)

    def close_experience(self, lineage_id: str, date_str: str, summary: str):
        """Finalizes an experience when a theory lineage is retired."""
        exp = self._get_or_load_experience(lineage_id)
        if exp:
            self.active_experiences.pop(lineage_id, None)
            exp.end_date = date_str
            exp.summary = summary
            exp.updated_at = datetime.now().isoformat()
            
            if exp.status in [ExperienceStatus.OPEN, ExperienceStatus.ACTIVE]:
                exp.status = ExperienceStatus.ABANDONED
            self.repository.save(exp)

    def get_active_experience_for_lineage(self, lineage_id: str) -> Optional[Experience]:
        """Retrieves current experience context for cognitive logging."""
        return self._get_or_load_experience(lineage_id)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Provides aggregate metrics for the final Replay Journal."""
        all_exps = self.repository.get_all()
        if not all_exps:
            return {"created": 0}
        
        abandoned = sum(1 for e in all_exps if e.status == ExperienceStatus.ABANDONED)
        
        most_active_exp = max(all_exps, key=lambda e: e.mutation_count + e.contradiction_count + len(e.theory_ids))

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

    def audit(self) -> Dict[str, Any]:
        """Performs a deep integrity audit of all persisted experiences."""
        all_exps = self.repository.load()
        if not all_exps:
            return {"total_experiences": 0}

        count = len(all_exps)
        stats = {
            "total_experiences": count,
            "open": sum(1 for e in all_exps if e.status == ExperienceStatus.OPEN),
            "active": sum(1 for e in all_exps if e.status == ExperienceStatus.ACTIVE),
            "validated": sum(1 for e in all_exps if e.status == ExperienceStatus.VALIDATED),
            "falsified": sum(1 for e in all_exps if e.status == ExperienceStatus.FALSIFIED),
            "abandoned": sum(1 for e in all_exps if e.status == ExperienceStatus.ABANDONED),
            
            "avg_theories_per_experience": sum(len(e.theory_ids) for e in all_exps) / count,
            "avg_mutations_per_experience": sum(e.mutation_count for e in all_exps) / count,
            "avg_contradictions_per_experience": sum(e.contradiction_count for e in all_exps) / count,
        }

        # Identify the largest experience by total cognitive accumulation
        largest = max(
            all_exps, 
            key=lambda e: (e.mutation_count + e.contradiction_count + len(e.theory_ids))
        )
        stats["largest_experience"] = {
            "lineage": largest.lineage_id,
            "theories": len(largest.theory_ids),
            "mutations": largest.mutation_count,
            "contradictions": largest.contradiction_count,
            "status": largest.status.value
        }
        
        return stats