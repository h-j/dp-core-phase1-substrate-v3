from memory.relational.models.confidence_model import ConfidenceModel
from memory.relational.postgres_client import SessionLocal


class ConfidenceRepository:

    def save(self, confidence_state):

        with SessionLocal() as session:
            model = ConfidenceModel(
                id=confidence_state.id,
                created_at=confidence_state.created_at,
                empirical_confidence=(
                    confidence_state.empirical_confidence
                ),
                regime_confidence=confidence_state.regime_confidence,
                reflection_confidence=(
                    confidence_state.reflection_confidence
                ),
                theoretical_coherence=(
                    confidence_state.theoretical_coherence
                ),
                contradiction_pressure=(
                    confidence_state.contradiction_pressure
                )
            )

            session.merge(model)
            session.commit()

        return {
            "status": "stored",
            "confidence_state_id": confidence_state.id
        }

    def list_recent(self, limit: int = 5):

        with SessionLocal() as session:
            return (
                session.query(ConfidenceModel)
                .order_by(ConfidenceModel.created_at.desc())
                .limit(limit)
                .all()
            )
