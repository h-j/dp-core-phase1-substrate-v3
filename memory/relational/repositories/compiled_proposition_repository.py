import json
from datetime import datetime, timezone
from typing import List, Optional

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from memory.relational.models.compiled_proposition_model import \
    CompiledPropositionModel
from memory.relational.postgres_client import SessionLocal
from telemetry.structured_cognition_tracer import get_tracer


class CompiledPropositionRepository:

    def save(self, prop: CompiledProposition) -> dict:
        tracer = get_tracer()
        with SessionLocal() as session:
            model = CompiledPropositionModel(
                id=prop.id,
                created_at=prop.created_at,
                theory_id=prop.theory_id,
                lineage_id=prop.lineage_id,
                replay_step=prop.replay_step,
                compilation_status=prop.compilation_status,
                failure_reason=prop.failure_reason,
                trigger_definition=prop.trigger_definition,
                target_definition=prop.target_definition,
                scope_definition=prop.scope_definition,
                compiler_trace=prop.compiler_trace,
            )
            session.merge(model)
            session.commit()
            tracer.trace_persisted(prop.id, model)

        return {
            "status": "stored",
            "proposition_id": prop.id,
            "theory_id": prop.theory_id,
        }

    def list_by_theory(self, theory_id: str) -> List[CompiledProposition]:
        tracer = get_tracer()
        with SessionLocal() as session:
            models = (
                session.query(CompiledPropositionModel)
                .filter(CompiledPropositionModel.theory_id == theory_id)
                .all()
            )
            props = []
            for model in models:
                prop = CompiledProposition(
                    id=model.id,
                    created_at=(
                        model.created_at.replace(tzinfo=timezone.utc)
                        if model.created_at.tzinfo is None
                        else model.created_at
                    ),
                    theory_id=model.theory_id,
                    lineage_id=model.lineage_id,
                    replay_step=model.replay_step,
                    compilation_status=model.compilation_status,
                    failure_reason=model.failure_reason,
                    trigger_definition=model.trigger_definition,
                    target_definition=model.target_definition,
                    scope_definition=model.scope_definition,
                    compiler_trace=model.compiler_trace,
                )
                props.append(prop)
                tracer.trace_retrieved(prop.id, prop)
            return props

    def query_by_lineage(self, lineage_id: str) -> List[CompiledProposition]:
        tracer = get_tracer()
        with SessionLocal() as session:
            models = (
                session.query(CompiledPropositionModel)
                .filter(CompiledPropositionModel.lineage_id == lineage_id)
                .all()
            )
            props = []
            for model in models:
                prop = CompiledProposition(
                    id=model.id,
                    created_at=(
                        model.created_at.replace(tzinfo=timezone.utc)
                        if model.created_at.tzinfo is None
                        else model.created_at
                    ),
                    theory_id=model.theory_id,
                    lineage_id=model.lineage_id,
                    replay_step=model.replay_step,
                    compilation_status=model.compilation_status,
                    failure_reason=model.failure_reason,
                    trigger_definition=model.trigger_definition,
                    target_definition=model.target_definition,
                    scope_definition=model.scope_definition,
                    compiler_trace=model.compiler_trace,
                )
                props.append(prop)
                tracer.trace_retrieved(prop.id, prop)
            return props

    def query_by_replay_step(self, replay_step: int) -> List[CompiledProposition]:
        tracer = get_tracer()
        with SessionLocal() as session:
            models = (
                session.query(CompiledPropositionModel)
                .filter(CompiledPropositionModel.replay_step == replay_step)
                .all()
            )
            props = []
            for model in models:
                prop = CompiledProposition(
                    id=model.id,
                    created_at=(
                        model.created_at.replace(tzinfo=timezone.utc)
                        if model.created_at.tzinfo is None
                        else model.created_at
                    ),
                    theory_id=model.theory_id,
                    lineage_id=model.lineage_id,
                    replay_step=model.replay_step,
                    compilation_status=model.compilation_status,
                    failure_reason=model.failure_reason,
                    trigger_definition=model.trigger_definition,
                    target_definition=model.target_definition,
                    scope_definition=model.scope_definition,
                    compiler_trace=model.compiler_trace,
                )
                props.append(prop)
                tracer.trace_retrieved(prop.id, prop)
            return props
