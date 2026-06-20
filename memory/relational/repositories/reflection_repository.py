from memory.relational.models.reflection_model import ReflectionModel
from memory.relational.postgres_client import SessionLocal


class ReflectionRepository:

    def save(self, reflection):

        with SessionLocal() as session:
            model = ReflectionModel(
                id=reflection.id,
                created_at=reflection.created_at,
                related_theory_id=reflection.related_theory_id,
                reflection_summary=reflection.reflection_summary,
                confidence_impact=reflection.confidence_impact,
            )

            session.merge(model)
            session.commit()

        return {"status": "stored", "reflection_id": reflection.id}

    def list_recent(self, limit: int = 5):

        with SessionLocal() as session:
            return (
                session.query(ReflectionModel)
                .order_by(ReflectionModel.created_at.desc())
                .limit(limit)
                .all()
            )
