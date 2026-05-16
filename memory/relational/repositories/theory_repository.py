from memory.relational.models.confidence_model import ConfidenceModel
from memory.relational.models.theory_model import TheoryModel
from memory.relational.postgres_client import SessionLocal


class TheoryRepository:

    def save(self, theory):

        confidence = theory.confidence_state

        with SessionLocal() as session:
            theory_model = TheoryModel(
                id=theory.id,
                created_at=theory.created_at,
                lineage_id=theory.lineage_id,
                thesis=theory.thesis,
                summary=theory.summary
            )

            confidence_model = ConfidenceModel(
                id=confidence.id,
                created_at=confidence.created_at,
                empirical_confidence=confidence.empirical_confidence,
                regime_confidence=confidence.regime_confidence,
                reflection_confidence=confidence.reflection_confidence,
                theoretical_coherence=confidence.theoretical_coherence,
                contradiction_pressure=confidence.contradiction_pressure
            )

            session.merge(theory_model)
            session.merge(confidence_model)
            session.commit()

        return {
            "status": "stored",
            "theory_id": theory.id,
            "confidence_state_id": confidence.id
        }

    def list_recent(self, limit: int = 5):

        with SessionLocal() as session:
            return (
                session.query(TheoryModel)
                .order_by(TheoryModel.created_at.desc())
                .limit(limit)
                .all()
            )
