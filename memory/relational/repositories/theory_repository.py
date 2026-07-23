import json
from typing import Any, Dict, List, Optional


from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.theory.theory import (  # Import Theory Pydantic model
    Branch, Theory, TheoryStructured)
from memory.relational.models.confidence_model import ConfidenceModel
from memory.relational.models.theory_model import TheoryModel
from memory.relational.postgres_client import SessionLocal
from telemetry.structured_cognition_tracer import get_tracer


def _is_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except Exception:
        return False


class TheoryRepository:

    def save(self, theory):

        confidence = theory.confidence_state
        tracer = get_tracer()

        with SessionLocal() as session:
            # v4.1: Schema patching removed from save() - delegated to SchemaValidator.validate_startup()
            theory_model = TheoryModel(
                id=theory.id,
                created_at=theory.created_at,
                lineage_id=theory.lineage_id,
                thesis=theory.thesis,
                summary=theory.summary,  # Keep text for legacy/search
                # v4.0 Canonical Semantic Storage: Store TheoryStructured as JSON string
                summary_structured=(
                    theory.summary_structured.model_dump_json()
                    if theory.summary_structured
                    else None
                ),
                confidence_state_id=theory.confidence_state.id,  # Populate this field
                # Phase 1: Store LLM-based semantic assessment
                llm_evaluation=getattr(theory, "llm_evaluation", None),
                survival_days=getattr(theory, "survival_days", 0),
                falsified_at_index=getattr(theory, "falsified_at_index", None),
                falsification_precision=getattr(
                    theory, "falsification_precision", None
                ),
            )

            confidence_model = ConfidenceModel(
                id=confidence.id,
                created_at=confidence.created_at,
                empirical_confidence=confidence.empirical_confidence,
                regime_confidence=confidence.regime_confidence,
                reflection_confidence=confidence.reflection_confidence,
                theoretical_coherence=confidence.theoretical_coherence,
                contradiction_pressure=confidence.contradiction_pressure,
            )

            session.merge(theory_model)
            session.merge(confidence_model)

            session.commit()

            # Trace persistence event
            tracer.trace_persisted(theory.id, theory_model)

        return {
            "status": "stored",
            "theory_id": theory.id,
            "confidence_state_id": confidence.id,
        }

    def list_recent(self, limit: int = 5) -> List[Theory]:

        tracer = get_tracer()
        with SessionLocal() as session:
            theory_models = (
                session.query(TheoryModel)
                .order_by(TheoryModel.created_at.desc())
                .limit(limit)
                .all()
            )

            theories = []
            for model in theory_models:
                # Reconstruct TheoryStructured from JSON string
                structured_data = None
                if model.summary_structured:
                    try:
                        structured_data = TheoryStructured(
                            **json.loads(model.summary_structured)
                        )
                    except Exception:
                        # Fallback if structured data is malformed
                        structured_data = TheoryStructured(
                            claim="Malformed structured theory.",
                            if_branch=Branch(condition="unknown", action="unknown"),
                            else_branch=Branch(condition="unknown", action="unknown"),
                            falsified_if="unknown",
                            forbidden_state="unknown",
                        )

                # Reconstruct ConfidenceState from relational database
                confidence_state = None
                if model.confidence_state_id:
                    conf_model = (
                        session.query(ConfidenceModel)
                        .filter(ConfidenceModel.id == model.confidence_state_id)
                        .first()
                    )
                    if conf_model:
                        confidence_state = ConfidenceState(
                            id=conf_model.id,
                            created_at=conf_model.created_at,
                            empirical_confidence=conf_model.empirical_confidence,
                            regime_confidence=conf_model.regime_confidence,
                            reflection_confidence=conf_model.reflection_confidence,
                            theoretical_coherence=conf_model.theoretical_coherence,
                            contradiction_pressure=conf_model.contradiction_pressure,
                        )
                if not confidence_state:
                    confidence_state = ConfidenceState()

                theory = Theory(
                    id=model.id,
                    created_at=model.created_at,
                    lineage_id=model.lineage_id,
                    thesis=model.thesis,
                    summary=model.summary,
                    summary_structured=structured_data,
                    confidence_state=confidence_state,
                    llm_evaluation=model.llm_evaluation,
                    survival_days=model.survival_days,
                    falsified_at_index=model.falsified_at_index,
                    falsification_precision=model.falsification_precision,
                )
                theories.append(theory)
                tracer.trace_retrieved(theory.id, theory)

            return theories
