from memory.relational.models.validation_model import ValidationModel
from memory.relational.postgres_client import SessionLocal


class ValidationRepository:

    def save(self, validation):

        with SessionLocal() as session:
            model = ValidationModel(
                id=validation.id,
                created_at=validation.created_at,
                theory_id=validation.theory_id,
                validation_summary=validation.validation_summary,
                observed_behavior=validation.observed_behavior,
                expected_behavior=validation.expected_behavior,
            )

            session.merge(model)
            session.commit()

        return {"status": "stored", "validation_id": validation.id}

    def list_recent(self, limit: int = 5):

        with SessionLocal() as session:
            return (
                session.query(ValidationModel)
                .order_by(ValidationModel.created_at.desc())
                .limit(limit)
                .all()
            )
