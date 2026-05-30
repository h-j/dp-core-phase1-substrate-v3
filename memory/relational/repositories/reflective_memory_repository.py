from typing import List, Union
from cognition.schemas.reflection.reflective_memory_state import (
    ReflectiveMemoryState
)
from memory.relational.models.reflective_memory_model import (
    ReflectiveMemoryModel
)
from memory.relational.postgres_client import SessionLocal


class ReflectiveMemoryRepository:

    def save(self, reflective_memory_state):

        with SessionLocal() as session:
            model = ReflectiveMemoryModel(
                id=reflective_memory_state.id,
                created_at=reflective_memory_state.created_at,
                recurring_themes=self._serialize(
                    reflective_memory_state.recurring_themes
                ),
                strengthening_patterns=self._serialize(
                    reflective_memory_state.strengthening_patterns
                ),
                weakening_patterns=self._serialize(
                    reflective_memory_state.weakening_patterns
                ),
                persistent_uncertainties=self._serialize(
                    reflective_memory_state.persistent_uncertainties
                ),
                contradiction_hotspots=self._serialize(
                    reflective_memory_state.contradiction_hotspots
                ),
                cognition_trajectory_summary=(
                    reflective_memory_state.cognition_trajectory_summary
                )
            )

            session.merge(model)
            session.commit()

        return {
            "status": "stored",
            "reflective_memory_state_id": reflective_memory_state.id
        }

    def list_recent(self, limit: int = 5):

        with SessionLocal() as session:
            models = (
                session.query(ReflectiveMemoryModel)
                .order_by(ReflectiveMemoryModel.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                self._to_schema(model)
                for model in models
            ]

    def _to_schema(self, model):

        return ReflectiveMemoryState(
            id=model.id,
            created_at=model.created_at,
            recurring_themes=self._deserialize(model.recurring_themes),
            strengthening_patterns=self._deserialize(
                model.strengthening_patterns
            ),
            weakening_patterns=self._deserialize(model.weakening_patterns),
            persistent_uncertainties=self._deserialize(
                model.persistent_uncertainties
            ),
            contradiction_hotspots=self._deserialize(
                model.contradiction_hotspots
            ),
            cognition_trajectory_summary=(
                model.cognition_trajectory_summary
            )
        )

    def _serialize(self, values: List[str]) -> str:

        return "\n".join(values)

    def _deserialize(self, value: Union[str, None]) -> List[str]:

        if not value:
            return []

        return [
            item
            for item in value.splitlines()
            if item
        ]
