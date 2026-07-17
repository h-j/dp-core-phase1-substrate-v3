from datetime import timezone
from typing import List

from cognition.schemas.proposition.canonical_semantic_proposition import \
    CanonicalSemanticProposition
from memory.relational.models.canonical_semantic_proposition_model import \
    CanonicalSemanticPropositionModel
from memory.relational.postgres_client import SessionLocal
from telemetry.structured_cognition_tracer import get_tracer


class CanonicalSemanticPropositionRepository:

    def save(self, prop: CanonicalSemanticProposition) -> dict:
        tracer = get_tracer()
        with SessionLocal() as session:
            model = CanonicalSemanticPropositionModel(
                id=prop.id,
                created_at=prop.created_at,
                theory_id=prop.theory_id,
                lineage_id=prop.lineage_id,
                trigger_concept=prop.trigger_concept,
                target_concept=prop.target_concept,
                scope_concept=prop.scope_concept,
                causal_direction=prop.causal_direction,
                compiler_provenance=prop.compiler_provenance,
            )
            session.merge(model)
            session.commit()
            tracer.trace_persisted(prop.id, model)

        return {
            "status": "stored",
            "canonical_proposition_id": prop.id,
            "theory_id": prop.theory_id,
        }

    def list_by_theory(self, theory_id: str) -> List[CanonicalSemanticProposition]:
        tracer = get_tracer()
        with SessionLocal() as session:
            models = (
                session.query(CanonicalSemanticPropositionModel)
                .filter(CanonicalSemanticPropositionModel.theory_id == theory_id)
                .all()
            )
            props = []
            for model in models:
                prop = CanonicalSemanticProposition(
                    id=model.id,
                    created_at=(
                        model.created_at.replace(tzinfo=timezone.utc)
                        if model.created_at.tzinfo is None
                        else model.created_at
                    ),
                    theory_id=model.theory_id,
                    lineage_id=model.lineage_id,
                    trigger_concept=model.trigger_concept,
                    target_concept=model.target_concept,
                    scope_concept=model.scope_concept,
                    causal_direction=model.causal_direction,
                    compiler_provenance=model.compiler_provenance,
                )
                props.append(prop)
                tracer.trace_retrieved(prop.id, prop)
            return props
