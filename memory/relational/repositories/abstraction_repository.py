from memory.relational.models.abstraction_model import AbstractionModel
from memory.relational.postgres_client import SessionLocal


class AbstractionRepository:

    def save(self, abstraction):

        with SessionLocal() as session:
            model = AbstractionModel(
                id=abstraction.id,
                created_at=abstraction.created_at,
                source_observation_id=abstraction.source_observation_id,
                abstraction_summary=abstraction.abstraction_summary
            )

            session.merge(model)
            session.commit()

        return {
            "status": "stored",
            "abstraction_id": abstraction.id
        }
