import logging
import math
from typing import Any, Dict, List, Optional

from uuid import uuid4

import pandas as pd

from cognition.schemas.proposition.market_proposition import \
    CompiledProposition
from cognition.schemas.proposition.validation_record import ValidationRecord
from cognition.schemas.validation.belief_state import (BeliefState,
                                                       BeliefTransitionEvent)
from memory.relational.repositories.belief_state_repository import \
    BeliefStateRepository

logger = logging.getLogger(__name__)


class BeliefDynamicsEngine:
    """Computes deterministic, uncertainty-modulated belief updates and manages lineage lifecycles."""

    def __init__(
        self,
        learning_rate: float = 0.15,
        uncertainty_rate: float = 0.10,
        decay_rate: float = 0.01,
        eta_max: float = 0.40,
        kappa: float = 0.20,
        beta: float = 10.0,
        belief_repo: Optional[BeliefStateRepository] = None,
    ):
        self.learning_rate = learning_rate
        self.uncertainty_rate = uncertainty_rate
        self.decay_rate = decay_rate
        self.eta_max = eta_max
        self.kappa = kappa
        self.beta = beta
        self.belief_repo = belief_repo or BeliefStateRepository()

    def process_validation(
        self,
        val_record: ValidationRecord,
        compiled_prop: CompiledProposition,
        history_df: pd.DataFrame,
        current_step: int,
        prediction_probe: Optional[Any] = None,
        contradiction_score: float = 0.0,
    ) -> BeliefTransitionEvent:
        """Processes a single validation record, updates parent lineage state, and logs transition event."""
        lineage_id = val_record.lineage_id
        theory_id = val_record.theory_id
        val_state = val_record.validation_state

        # Fetch or initialize BeliefState
        state = self.belief_repo.get_belief_state_by_lineage(lineage_id)
        if not state:
            state = BeliefState(
                lineage_id=lineage_id,
                active_theory_id=theory_id,
                confidence=0.50,
                uncertainty=0.50,
                status="ACTIVE",
            )

        C_t = state.confidence
        U_t = state.uncertainty
        status_before = state.status

        # 1. Compute Evidence Weight w_V
        # A. Prediction Conviction (C_pred)
        C_pred = 0.50
        if prediction_probe:
            C_pred = getattr(prediction_probe, "confidence", 0.50)

        # B. Outcome Magnitude (M_V)
        r_actual = 0.0
        if current_step > 0 and "close" in history_df.columns:
            close_curr = history_df["close"].iloc[current_step]
            close_prev = history_df["close"].iloc[current_step - 1]
            if close_prev != 0:
                r_actual = (close_curr - close_prev) / close_prev
        M_V = 1.0 + min(2.0, self.beta * abs(r_actual))

        # C. Statistical Rarity (R_V)
        R_V = 1.0
        trigger_def = getattr(compiled_prop, "trigger_definition", None)
        if (
            trigger_def
            and "field" in trigger_def
            and trigger_def["field"] in history_df.columns
        ):
            field = trigger_def["field"]
            trigger_val = history_df[field].iloc[current_step]
            hist_values = history_df[field].iloc[: current_step + 1]
            if len(hist_values) > 1:
                less_count = (hist_values < trigger_val).sum()
                percentile = less_count / len(hist_values)
                if percentile < 0.10 or percentile > 0.90:
                    R_V = 1.5

        # D. Combined Weight
        w_V = float(C_pred * M_V * R_V)
        eta_effective = float(min(self.eta_max, self.learning_rate * w_V))

        # 2. Update Confidence and Uncertainty
        transition_reason = f"Validation state: {val_state}"
        calc_trace = {
            "r_actual": float(r_actual),
            "C_pred": float(C_pred),
            "M_V": float(M_V),
            "R_V": float(R_V),
            "w_V": float(w_V),
            "eta_effective": float(eta_effective),
        }

        if val_state == "SUPPORTED":
            C_new = C_t + eta_effective * (1.0 - C_t) * (1.0 - U_t)
            U_new = U_t - self.uncertainty_rate * U_t * w_V
        elif val_state == "CONTRADICTED":
            C_new = C_t - eta_effective * C_t * (1.0 - U_t)
            U_new = U_t + self.uncertainty_rate * (1.0 - U_t) * w_V
        elif val_state == "UNTRIGGERED":
            C_new = C_t - self.decay_rate * (C_t - 0.50)
            U_new = U_t + self.decay_rate * (1.0 - U_t)
            transition_reason = "Decay due to untriggered step"
        else:
            # For GROUNDED, TRIGGERED (undecided), or errors: no mathematical update
            C_new = C_t
            U_new = U_t
            transition_reason = f"No change: state is {val_state}"

        # Clip values to [0.0, 1.0]
        C_new = float(max(0.0, min(1.0, C_new)))
        U_new = float(max(0.0, min(1.0, U_new)))

        # 3. Apply Contradiction Uncertainty Shocks
        if contradiction_score >= 0.50:
            U_shock = float(self.kappa * contradiction_score)
            U_new = float(min(1.0, U_new + U_shock))
            calc_trace["contradiction_shock"] = U_shock
            transition_reason += (
                f" | Contradiction shock applied (score={contradiction_score:.2f})"
            )

        # 4. Lifecycle Status Transitions
        status_after = "ACTIVE"
        if C_new < 0.30:
            status_after = "RETIRED"
        elif C_new < 0.40 and U_new > 0.70:
            status_after = "WEAKENED"
        else:
            # If it was WEAKENED or RETIRED, it can be revived back to ACTIVE if confidence gets back up
            if status_before in ["WEAKENED", "RETIRED"]:
                if C_new >= 0.50:
                    status_after = "ACTIVE"
                    transition_reason += " | Lineage revived to ACTIVE"
                else:
                    status_after = status_before

        # Update and save state
        state.active_theory_id = theory_id
        state.confidence = C_new
        state.uncertainty = U_new
        state.status = status_after
        state.last_validation_id = val_record.id
        self.belief_repo.save_belief_state(state)

        # Create and save transition event
        event = BeliefTransitionEvent(
            id=str(uuid4()),
            lineage_id=lineage_id,
            validation_record_id=val_record.id,
            confidence_before=C_t,
            confidence_after=C_new,
            uncertainty_before=U_t,
            uncertainty_after=U_new,
            status_before=status_before,
            status_after=status_after,
            evidence_weight=w_V,
            contradiction_score=contradiction_score,
            transition_reason=transition_reason,
            deterministic_calculation_trace=calc_trace,
        )
        self.belief_repo.save_transition_event(event)

        return event

    def apply_decay_to_other_lineages(
        self, active_lineage_ids: List[str], current_step: int
    ) -> List[BeliefTransitionEvent]:
        """Applies decay to any lineage that did not resolve a validation record on this step."""
        all_states = self.belief_repo.list_all_belief_states()
        events = []
        for state in all_states:
            if state.lineage_id in active_lineage_ids:
                # Already processed on this step
                continue

            # Skip already retired lineages
            if state.status == "RETIRED":
                continue

            C_t = state.confidence
            U_t = state.uncertainty
            status_before = state.status

            # Decay formula (Ornstein-Uhlenbeck mean reversion)
            C_new = C_t - self.decay_rate * (C_t - 0.50)
            U_new = U_t + self.decay_rate * (1.0 - U_t)

            C_new = max(0.0, min(1.0, C_new))
            U_new = max(0.0, min(1.0, U_new))

            # Status transition check
            status_after = status_before
            if C_new < 0.30:
                status_after = "RETIRED"
            elif C_new < 0.40 and U_new > 0.70:
                status_after = "WEAKENED"

            state.confidence = C_new
            state.uncertainty = U_new
            state.status = status_after
            self.belief_repo.save_belief_state(state)

            event = BeliefTransitionEvent(
                id=str(uuid4()),
                lineage_id=state.lineage_id,
                validation_record_id=None,
                confidence_before=C_t,
                confidence_after=C_new,
                uncertainty_before=U_t,
                uncertainty_after=U_new,
                status_before=status_before,
                status_after=status_after,
                evidence_weight=0.0,
                contradiction_score=0.0,
                transition_reason="Decay (no active validations evaluated)",
                deterministic_calculation_trace={"decay_rate": self.decay_rate},
            )
            self.belief_repo.save_transition_event(event)
            events.append(event)

        return events
