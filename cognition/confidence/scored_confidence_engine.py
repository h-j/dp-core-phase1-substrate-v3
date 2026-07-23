"""
Scored Confidence Engine — Beta Posterior Epistemic Confidence Substrate.

REPLACES the legacy keyword-based ConfidenceEvolutionEngine.
NO generated text (reflection summaries, validation summaries, observation narratives)
may influence any confidence value anywhere in the live path.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from cognition.schemas.confidence.confidence_state import ConfidenceState
from config.settings import cognition_tuning


class EvidenceLedgerRecord(BaseModel):
    """
    Byte-stable transition record of confidence parameter evolution.
    No wall-clock fields (no timestamps) to guarantee deterministic hashing across runs.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    day: int
    trigger_event: str
    event_type: str  # SUPPORTED | CONTRADICTED | DECAY | CONTRADICTION
    evidence_state: str
    alpha_before: float
    alpha_after: float
    beta_before: float
    beta_after: float


class LineageEvidenceLedger:
    """
    Immutable transition ledger storing byte-stable evidence transition records per theory/lineage.
    """
    def __init__(self):
        self.records: List[EvidenceLedgerRecord] = []

    def append_record(self, record: EvidenceLedgerRecord) -> None:
        self.records.append(record)

    def to_list(self) -> List[Dict[str, Any]]:
        return [r.model_dump() for r in self.records]


class ScoredConfidenceEngine:
    """
    Beta(alpha, beta) posterior confidence evolution engine over falsifiable theory commitments.

    Evidence Source: ONLY resolved terminal states from predicate validation engine (SUPPORTED -> alpha+1,
    CONTRADICTED -> beta+k_falsify). No text scanning permitted.
    Staleness Decay: alpha, beta <- (1 - lambda) on days with no resolved evidence.
    Contradiction Pressure: fed ONLY by contradiction registry count metrics.
    """

    def __init__(
        self,
        k_falsify: Optional[float] = None,
        decay_lambda: Optional[float] = None,
    ):
        tuning_cfg = cognition_tuning.get("scored_confidence", {})
        self.k_falsify: float = (
            k_falsify if k_falsify is not None else float(tuning_cfg.get("k_falsify", 3.0))
        )
        self.decay_lambda: float = (
            decay_lambda if decay_lambda is not None else float(tuning_cfg.get("lambda", 0.01))
        )
        self._ledger = LineageEvidenceLedger()
        # SD-002: Retrospective evaluation buffer for day t-1 resolutions during day t processing
        self._retrospective_buffer: List[Dict[str, Any]] = []

    @property
    def ledger(self) -> LineageEvidenceLedger:
        return self._ledger

    def buffer_retrospective_resolutions(self, resolutions: List[Dict[str, Any]]) -> None:
        """Buffers day t-1 resolved predicate outcomes for consumption during day t processing."""
        if resolutions:
            self._retrospective_buffer.extend(resolutions)

    def evolve(
        self,
        confidence_state: ConfidenceState,
        predicate_results: Optional[List[Any]] = None,
        contradiction_result: Optional[Dict[str, Any]] = None,
        day_idx: int = 0,
        lineage_id: Optional[str] = None,
        validation: Any = None,
        reflection: Any = None,
        market_observation: Any = None,
        recent_validations: Any = None,
        outcome_validation_result: Any = None,
        lineage_event: Any = None,
        theory_usefulness: Any = None,
        regime_matches: Any = None,
        rolling_accuracy: float = 0.5,
        regime_accuracy: float = 0.5,
        lifetime_accuracy: float = 0.5,
        **kwargs,
    ) -> ConfidenceState:
        """
        Evolves confidence state using ONLY predicate validation engine resolved terminal states
        and numerical contradiction registry counts.

        TEXT PARAMETERS (validation, reflection, market_observation) ARE STRICTLY UNUSED FOR CONFIDENCE CALCULATION.
        """

        alpha_before = float(getattr(confidence_state, "alpha", 1.0))
        beta_before = float(getattr(confidence_state, "beta", 1.0))

        alpha_cur = alpha_before
        beta_cur = beta_before

        resolved_count = 0

        # Collect evidence items from predicate_results or retrospective buffer
        evidence_items = []
        if predicate_results:
            evidence_items.extend(predicate_results)

        # Check retrospective buffer for pending day t-1 resolutions
        if self._retrospective_buffer:
            evidence_items.extend(self._retrospective_buffer)
            self._retrospective_buffer.clear()

        # Also inspect outcome_validation_result if passed as a structured object/dict with predicate outcome
        if outcome_validation_result and isinstance(outcome_validation_result, dict):
            if "outcome" in outcome_validation_result or "predicate_id" in outcome_validation_result:
                evidence_items.append(outcome_validation_result)

        for item in evidence_items:
            outcome_val = ""
            if hasattr(item, "outcome"):
                outcome_val = item.outcome.value if hasattr(item.outcome, "value") else str(item.outcome)
            elif isinstance(item, dict):
                outcome_val = item.get("outcome", "")
            else:
                outcome_val = str(item)

            if isinstance(outcome_val, str):
                outcome_val = outcome_val.strip()

            if outcome_val in ["confirmed", "partially_confirmed", "supported", "CONFIRMED", "PARTIALLY_CONFIRMED", "SUPPORTED"]:
                alpha_cur += 1.0
                resolved_count += 1
                rec = EvidenceLedgerRecord(
                    day=day_idx,
                    trigger_event="predicate_supported",
                    event_type="SUPPORTED",
                    evidence_state=f"Outcome matched: {outcome_val}",
                    alpha_before=round(alpha_before, 6),
                    alpha_after=round(alpha_cur, 6),
                    beta_before=round(beta_before, 6),
                    beta_after=round(beta_cur, 6),
                )
                self._ledger.append_record(rec)
            elif outcome_val in ["rejected", "contradicted", "failed", "REJECTED", "CONTRADICTED", "FAILED"]:
                beta_cur += self.k_falsify
                resolved_count += 1
                rec = EvidenceLedgerRecord(
                    day=day_idx,
                    trigger_event="predicate_contradicted",
                    event_type="CONTRADICTED",
                    evidence_state=f"Outcome failed: {outcome_val} (penalty k_falsify={self.k_falsify})",
                    alpha_before=round(alpha_before, 6),
                    alpha_after=round(alpha_cur, 6),
                    beta_before=round(beta_before, 6),
                    beta_after=round(beta_cur, 6),
                )
                self._ledger.append_record(rec)


        # Staleness decay: if no resolved terminal evidence received this day for this lineage
        if resolved_count == 0:
            alpha_cur = alpha_cur * (1.0 - self.decay_lambda)
            beta_cur = beta_cur * (1.0 - self.decay_lambda)
            rec = EvidenceLedgerRecord(
                day=day_idx,
                trigger_event="staleness_decay",
                event_type="DECAY",
                evidence_state=f"No resolved evidence received (lambda={self.decay_lambda})",
                alpha_before=round(alpha_before, 6),
                alpha_after=round(alpha_cur, 6),
                beta_before=round(beta_before, 6),
                beta_after=round(beta_cur, 6),
            )
            self._ledger.append_record(rec)

        # Contradiction Pressure: fed ONLY by numeric registry counts (new/active/resolved)
        if contradiction_result and isinstance(contradiction_result, dict):
            new_cnt = int(contradiction_result.get("new_contradictions", 0))
            active_cnt = int(contradiction_result.get("active_contradictions", 0))
            resolved_cnt = int(contradiction_result.get("resolved_contradictions", 0))

            if new_cnt > 0 or active_cnt > 0 or resolved_cnt > 0:
                p_delta = (new_cnt * 0.14) + (active_cnt * 0.09) - (resolved_cnt * 0.07)
                old_p = confidence_state.contradiction_pressure
                confidence_state.contradiction_pressure = max(0.0, min(1.0, old_p + p_delta))
                rec = EvidenceLedgerRecord(
                    day=day_idx,
                    trigger_event="contradiction_registry_count",
                    event_type="CONTRADICTION",
                    evidence_state=f"Counts new={new_cnt}, active={active_cnt}, resolved={resolved_cnt}",
                    alpha_before=round(alpha_cur, 6),
                    alpha_after=round(alpha_cur, 6),
                    beta_before=round(beta_cur, 6),
                    beta_after=round(beta_cur, 6),
                )
                self._ledger.append_record(rec)

        # Update confidence_state attributes
        confidence_state.alpha = round(alpha_cur, 6)
        confidence_state.beta = round(beta_cur, 6)

        calc_conf = confidence_state.confidence
        confidence_state.empirical_confidence = round(calc_conf, 6)
        confidence_state.regime_confidence = round(calc_conf, 6)
        confidence_state.reflection_confidence = round(calc_conf, 6)
        confidence_state.theoretical_coherence = max(
            0.0, min(1.0, round(calc_conf - confidence_state.contradiction_pressure * 0.04, 6))
        )

        if hasattr(confidence_state, "ledger"):
            confidence_state.ledger = self._ledger

        return confidence_state
