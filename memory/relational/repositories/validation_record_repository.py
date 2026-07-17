from datetime import timezone
from typing import List, Optional

from cognition.schemas.proposition.validation_record import ValidationRecord
from memory.relational.models.validation_record_model import \
    ValidationRecordModel
from memory.relational.postgres_client import SessionLocal
from telemetry.structured_cognition_tracer import get_tracer


class ValidationRecordRepository:

    def save(self, record: ValidationRecord) -> dict:
        tracer = get_tracer()
        with SessionLocal() as session:
            # Enforce the strict immutability contract: reject updates
            existing = (
                session.query(ValidationRecordModel)
                .filter(ValidationRecordModel.id == record.id)
                .first()
            )
            if existing:
                raise ValueError(
                    f"Immutability Contract Violation: ValidationRecord {record.id} already exists and cannot be modified."
                )

            model = ValidationRecordModel(
                id=record.id,
                created_at=record.created_at,
                proposition_id=record.proposition_id,
                canonical_proposition_id=record.canonical_proposition_id,
                theory_id=record.theory_id,
                lineage_id=record.lineage_id,
                mechanism_ids=record.mechanism_ids,
                timestamp=record.timestamp,
                replay_step=record.replay_step,
                validation_state=record.validation_state,
                supporting_evidence=record.supporting_evidence,
                contradicting_evidence=record.contradicting_evidence,
                confidence_before=record.confidence_before,
                confidence_after=record.confidence_after,
                confidence_delta=record.confidence_delta,
                uncertainty_before=record.uncertainty_before,
                uncertainty_after=record.uncertainty_after,
                uncertainty_delta=record.uncertainty_delta,
                market_context=record.market_context,
                regime=record.regime,
                grounding_version=record.grounding_version,
                compiler_version=record.compiler_version,
                validation_engine_version=record.validation_engine_version,
                validation_trace=record.validation_trace,
                notes=record.notes,
            )
            session.add(model)
            session.commit()
            tracer.trace_persisted(record.id, model)

        return {
            "status": "stored",
            "validation_id": record.id,
            "proposition_id": record.proposition_id,
        }

    def query_by_proposition(self, proposition_id: str) -> List[ValidationRecord]:
        with SessionLocal() as session:
            models = (
                session.query(ValidationRecordModel)
                .filter(ValidationRecordModel.proposition_id == proposition_id)
                .all()
            )
            return [self._to_schema(m) for m in models]

    def query_by_lineage(self, lineage_id: str) -> List[ValidationRecord]:
        with SessionLocal() as session:
            models = (
                session.query(ValidationRecordModel)
                .filter(ValidationRecordModel.lineage_id == lineage_id)
                .all()
            )
            return [self._to_schema(m) for m in models]

    def query_by_replay_step(self, step: int) -> List[ValidationRecord]:
        with SessionLocal() as session:
            models = (
                session.query(ValidationRecordModel)
                .filter(ValidationRecordModel.replay_step == step)
                .all()
            )
            return [self._to_schema(m) for m in models]

    def query_by_validation_state(self, state: str) -> List[ValidationRecord]:
        with SessionLocal() as session:
            models = (
                session.query(ValidationRecordModel)
                .filter(ValidationRecordModel.validation_state == state)
                .all()
            )
            return [self._to_schema(m) for m in models]

    def _to_schema(self, model: ValidationRecordModel) -> ValidationRecord:
        record = ValidationRecord(
            id=model.id,
            created_at=(
                model.created_at.replace(tzinfo=timezone.utc)
                if model.created_at.tzinfo is None
                else model.created_at
            ),
            proposition_id=model.proposition_id,
            canonical_proposition_id=model.canonical_proposition_id,
            theory_id=model.theory_id,
            lineage_id=model.lineage_id,
            mechanism_ids=model.mechanism_ids,
            timestamp=(
                model.timestamp.replace(tzinfo=timezone.utc)
                if model.timestamp.tzinfo is None
                else model.timestamp
            ),
            replay_step=model.replay_step,
            validation_state=model.validation_state,
            supporting_evidence=model.supporting_evidence,
            contradicting_evidence=model.contradicting_evidence,
            confidence_before=model.confidence_before,
            confidence_after=model.confidence_after,
            confidence_delta=model.confidence_delta,
            uncertainty_before=model.uncertainty_before,
            uncertainty_after=model.uncertainty_after,
            uncertainty_delta=model.uncertainty_delta,
            market_context=model.market_context,
            regime=model.regime,
            grounding_version=model.grounding_version,
            compiler_version=model.compiler_version,
            validation_engine_version=model.validation_engine_version,
            validation_trace=model.validation_trace,
            notes=model.notes,
        )
        return record
