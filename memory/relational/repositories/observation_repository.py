from memory.relational.models.observation_model import ObservationModel
from memory.relational.postgres_client import SessionLocal


class ObservationRepository:

    def save(self, observation):

        with SessionLocal() as session:
            model = ObservationModel(
                id=observation.id,
                created_at=observation.created_at,
                source_type=observation.source_type,
                raw_content=observation.raw_content,
                source_reliability=observation.source_reliability
            )

            session.merge(model)
            session.commit()

        return {
            "status": "stored",
            "observation_id": observation.id
        }
