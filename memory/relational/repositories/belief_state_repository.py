from datetime import timezone
from typing import List, Optional

from cognition.schemas.validation.belief_state import (BeliefState,
                                                       BeliefTransitionEvent)
from memory.relational.models.belief_state_model import (
    BeliefStateModel, BeliefTransitionEventModel)
from memory.relational.postgres_client import SessionLocal
from telemetry.structured_cognition_tracer import get_tracer


class BeliefStateRepository:

    def save_belief_state(self, state: BeliefState) -> dict:
        tracer = get_tracer()
        with SessionLocal() as session:
            existing = (
                session.query(BeliefStateModel)
                .filter(BeliefStateModel.lineage_id == state.lineage_id)
                .first()
            )
            if existing:
                # Update existing lineage state
                existing.active_theory_id = state.active_theory_id
                existing.confidence = state.confidence
                existing.uncertainty = state.uncertainty
                existing.status = state.status
                existing.last_validation_id = state.last_validation_id
                existing.updated_at = state.updated_at
                model = existing
                status = "updated"
            else:
                # Create new lineage state
                model = BeliefStateModel(
                    id=state.id,
                    created_at=state.created_at,
                    lineage_id=state.lineage_id,
                    active_theory_id=state.active_theory_id,
                    confidence=state.confidence,
                    uncertainty=state.uncertainty,
                    status=state.status,
                    last_validation_id=state.last_validation_id,
                    updated_at=state.updated_at,
                )
                session.add(model)
                status = "created"

            session.commit()
            tracer.trace_persisted(state.id, model)

        return {
            "status": status,
            "belief_state_id": state.id,
            "lineage_id": state.lineage_id,
        }

    def save_transition_event(self, event: BeliefTransitionEvent) -> dict:
        tracer = get_tracer()
        with SessionLocal() as session:
            existing = (
                session.query(BeliefTransitionEventModel)
                .filter(BeliefTransitionEventModel.id == event.id)
                .first()
            )
            if existing:
                raise ValueError(
                    f"Immutability Contract Violation: BeliefTransitionEvent {event.id} already exists."
                )

            model = BeliefTransitionEventModel(
                id=event.id,
                created_at=event.created_at,
                lineage_id=event.lineage_id,
                validation_record_id=event.validation_record_id,
                confidence_before=event.confidence_before,
                confidence_after=event.confidence_after,
                uncertainty_before=event.uncertainty_before,
                uncertainty_after=event.uncertainty_after,
                status_before=event.status_before,
                status_after=event.status_after,
                evidence_weight=event.evidence_weight,
                contradiction_score=event.contradiction_score,
                transition_reason=event.transition_reason,
                deterministic_calculation_trace=event.deterministic_calculation_trace,
            )
            session.add(model)
            session.commit()
            tracer.trace_persisted(event.id, model)

        return {
            "status": "stored",
            "event_id": event.id,
            "lineage_id": event.lineage_id,
        }

    def get_belief_state_by_lineage(self, lineage_id: str) -> Optional[BeliefState]:
        with SessionLocal() as session:
            model = (
                session.query(BeliefStateModel)
                .filter(BeliefStateModel.lineage_id == lineage_id)
                .first()
            )
            if not model:
                return None
            return self._to_state_schema(model)

    def list_transition_events_by_lineage(
        self, lineage_id: str
    ) -> List[BeliefTransitionEvent]:
        with SessionLocal() as session:
            models = (
                session.query(BeliefTransitionEventModel)
                .filter(BeliefTransitionEventModel.lineage_id == lineage_id)
                .order_by(BeliefTransitionEventModel.created_at.asc())
                .all()
            )
            return [self._to_event_schema(m) for m in models]

    def list_all_belief_states(self) -> List[BeliefState]:
        with SessionLocal() as session:
            models = session.query(BeliefStateModel).all()
            return [self._to_state_schema(m) for m in models]

    def _to_state_schema(self, model: BeliefStateModel) -> BeliefState:
        # Normalize timezone to UTC
        ca = model.created_at.replace(tzinfo=timezone.utc)
        ua = model.updated_at.replace(tzinfo=timezone.utc)
        state = BeliefState(
            lineage_id=model.lineage_id,
            active_theory_id=model.active_theory_id,
            confidence=model.confidence,
            uncertainty=model.uncertainty,
            status=model.status,
            last_validation_id=model.last_validation_id,
        )
        state.id = model.id
        state.created_at = ca
        state.updated_at = ua
        return state

    def _to_event_schema(
        self, model: BeliefTransitionEventModel
    ) -> BeliefTransitionEvent:
        ca = model.created_at.replace(tzinfo=timezone.utc)
        event = BeliefTransitionEvent(
            lineage_id=model.lineage_id,
            validation_record_id=model.validation_record_id,
            confidence_before=model.confidence_before,
            confidence_after=model.confidence_after,
            uncertainty_before=model.uncertainty_before,
            uncertainty_after=model.uncertainty_after,
            status_before=model.status_before,
            status_after=model.status_after,
            evidence_weight=model.evidence_weight,
            contradiction_score=model.contradiction_score,
            transition_reason=model.transition_reason,
            deterministic_calculation_trace=model.deterministic_calculation_trace,
        )
        event.id = model.id
        event.created_at = ca
        return event
