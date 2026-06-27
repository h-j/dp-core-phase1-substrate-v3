import json

from market.schemas.strategic_memory_state import StrategicMemoryState
from memory.relational.models.strategic_memory_model import \
    StrategicMemoryModel
from memory.relational.postgres_client import SessionLocal


class StrategicMemoryRepository:
    """Repository for persisting strategic memory snapshots."""

    def save(self, strategic_memory: StrategicMemoryState):
        """Save a strategic memory snapshot to PostgreSQL."""

        contradictions_json = json.dumps(strategic_memory.major_contradictions)
        assumptions_json = json.dumps(strategic_memory.weakening_assumptions)
        patterns_json = json.dumps(strategic_memory.strengthening_patterns)
        frequency_json = json.dumps(strategic_memory.contradiction_frequency)

        with SessionLocal() as session:
            model = StrategicMemoryModel(
                id=strategic_memory.id,
                created_at=strategic_memory.created_at,
                strategic_summary=strategic_memory.strategic_summary,
                cognition_posture=strategic_memory.cognition_posture,
                major_contradictions=contradictions_json,
                weakening_assumptions=assumptions_json,
                strengthening_patterns=patterns_json,
                regime_interpretation=strategic_memory.regime_interpretation,
                uncertainty_summary=strategic_memory.uncertainty_summary,
                coherence_trajectory=strategic_memory.coherence_trajectory,
                contradiction_frequency=frequency_json,
            )

            session.merge(model)
            session.commit()

        return {"status": "stored", "strategic_memory_id": strategic_memory.id}

    def list_recent(self, limit: int = 20):
        """Retrieve recent strategic memory snapshots."""

        with SessionLocal() as session:
            models = (
                session.query(StrategicMemoryModel)
                .order_by(StrategicMemoryModel.created_at.desc())
                .limit(limit)
                .all()
            )

            memories = []
            for model in models:
                contradictions = json.loads(model.major_contradictions or "[]")
                assumptions = json.loads(model.weakening_assumptions or "[]")
                patterns = json.loads(model.strengthening_patterns or "[]")
                frequency = json.loads(model.contradiction_frequency or "{}")

                memory = StrategicMemoryState(
                    id=model.id,
                    created_at=model.created_at,
                    strategic_summary=model.strategic_summary,
                    cognition_posture=model.cognition_posture,
                    major_contradictions=contradictions,
                    weakening_assumptions=assumptions,
                    strengthening_patterns=patterns,
                    regime_interpretation=model.regime_interpretation,
                    uncertainty_summary=model.uncertainty_summary,
                    coherence_trajectory=model.coherence_trajectory,
                    contradiction_frequency=frequency,
                )
                memories.append(memory)

            return memories
