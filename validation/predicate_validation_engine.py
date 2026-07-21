"""
Predicate Validation Framework — Explicit condition evaluation for falsifiable cognition.

Forms, stores, and evaluates mechanism predicates against replay data to yield explicit
outcomes (CONFIRMED, PARTIALLY_CONFIRMED, REJECTED, INSUFFICIENT_EVIDENCE) and diagnostic reports.
"""
import enum
import logging
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class PredicateOutcome(str, enum.Enum):
    CONFIRMED = "confirmed"
    PARTIALLY_CONFIRMED = "partially_confirmed"
    REJECTED = "rejected"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class PredicateStatus(str, enum.Enum):
    PENDING = "pending"
    EVALUATED = "evaluated"
    EXPIRED = "expired"


class Predicate(BaseModel):
    """Structured representation of a falsifiable mechanism predicate."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: f"PRED_VAL_{uuid.uuid4().hex[:8]}")
    theory_id: str
    mechanism_id: Optional[str] = None
    description: str
    condition: Dict[str, Any]  # e.g., {"metric": "daily_return_pct", "operator": ">", "threshold": 0.0}
    supporting_evidence: List[str] = Field(default_factory=list)
    created_at_step: int
    evaluation_window: int = 1  # Steps to wait before evaluation
    expected_outcome: str = "CONFIRMED"
    status: PredicateStatus = PredicateStatus.PENDING


class PredicateEvaluationResult(BaseModel):
    """Structured evaluation result produced when a predicate matures."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    predicate_id: str
    theory_id: str
    outcome: PredicateOutcome
    evaluated_at_step: int
    observed_value: Any
    justification: str
    confidence_impact: float


class PredicateValidationEngine:
    """
    Manages formation, storage, maturation evaluation, and diagnostics of mechanism predicates.
    """

    def __init__(self):
        self._predicates: Dict[str, Predicate] = {}
        self._evaluations: List[PredicateEvaluationResult] = []

    def form_predicate(
        self,
        theory: Any,
        mechanism_id: Optional[str] = None,
        step: int = 0,
        evaluation_window: int = 1,
        condition_override: Optional[Dict[str, Any]] = None,
    ) -> Predicate:
        """
        Forms a falsifiable predicate from a theory after theory creation.
        """
        theory_id = getattr(theory, "id", None) or (
            theory.get("id") if isinstance(theory, dict) else "TH_UNKNOWN"
        )
        claim_text = getattr(theory, "summary", None) or (
            theory.get("summary", "Market regime condition") if isinstance(theory, dict) else "Market condition"
        )

        if condition_override:
            condition = condition_override
        else:
            # Extract condition from text heuristic
            claim_lower = claim_text.lower()
            if "higher" in claim_lower or "bull" in claim_lower or "expansion" in claim_lower:
                condition = {"metric": "daily_return_pct", "operator": ">=", "threshold": 0.0}
            elif "lower" in claim_lower or "bear" in claim_lower or "compression" in claim_lower:
                condition = {"metric": "daily_return_pct", "operator": "<=", "threshold": 0.0}
            else:
                condition = {"metric": "volume_ratio_5d", "operator": ">=", "threshold": 0.8}

        predicate = Predicate(
            theory_id=theory_id,
            mechanism_id=mechanism_id,
            description=f"Predicate for theory {theory_id[:8]}: {claim_text[:60]}",
            condition=condition,
            supporting_evidence=[f"Created at step {step}"],
            created_at_step=step,
            evaluation_window=evaluation_window,
            expected_outcome="CONFIRMED",
            status=PredicateStatus.PENDING,
        )

        self.store_predicate(predicate)
        return predicate

    def store_predicate(self, predicate: Predicate) -> None:
        """Store a new predicate in the pending queue."""
        self._predicates[predicate.id] = predicate
        logger.debug("[PredicateValidationEngine] Stored predicate '%s' for theory '%s'.", predicate.id, predicate.theory_id)

    def evaluate_pending_predicates(
        self, current_step: int, obs_data: Dict[str, Any]
    ) -> List[PredicateEvaluationResult]:
        """
        Evaluates predicates whose evaluation window has matured against observed market data.
        """
        results: List[PredicateEvaluationResult] = []
        derived = obs_data.get("derived", {})

        for pred in list(self._predicates.values()):
            if pred.status != PredicateStatus.PENDING:
                continue

            target_step = pred.created_at_step + pred.evaluation_window
            if current_step < target_step:
                continue  # Not matured yet

            # Evaluate condition
            cond = pred.condition
            metric_name = cond.get("metric", "daily_return_pct")
            operator = cond.get("operator", ">=")
            threshold = cond.get("threshold", 0.0)

            if metric_name not in derived and metric_name not in obs_data:
                outcome = PredicateOutcome.INSUFFICIENT_EVIDENCE
                observed_val = None
                justification = f"Metric '{metric_name}' not available in observation data at step {current_step}."
                conf_impact = 0.0
            else:
                observed_val = derived.get(metric_name, obs_data.get(metric_name))
                matched = self._eval_condition(observed_val, operator, threshold)

                if matched:
                    outcome = PredicateOutcome.CONFIRMED
                    justification = f"Condition matched: {metric_name} ({observed_val}) {operator} {threshold}."
                    conf_impact = +0.06
                else:
                    # Check partial match (within 20% margin)
                    if isinstance(observed_val, (int, float)) and isinstance(threshold, (int, float)) and abs(observed_val - threshold) <= 0.5:
                        outcome = PredicateOutcome.PARTIALLY_CONFIRMED
                        justification = f"Condition partially matched: {metric_name} ({observed_val}) near threshold {threshold}."
                        conf_impact = +0.02
                    else:
                        outcome = PredicateOutcome.REJECTED
                        justification = f"Condition rejected: {metric_name} ({observed_val}) failed {operator} {threshold}."
                        conf_impact = -0.08

            pred.status = PredicateStatus.EVALUATED
            res = PredicateEvaluationResult(
                predicate_id=pred.id,
                theory_id=pred.theory_id,
                outcome=outcome,
                evaluated_at_step=current_step,
                observed_value=observed_val,
                justification=justification,
                confidence_impact=conf_impact,
            )
            self._evaluations.append(res)
            results.append(res)
            logger.info("[PredicateValidationEngine] Evaluated '%s' -> %s | %s", pred.id, outcome.value, justification)

        return results

    def _eval_condition(self, val: Any, op: str, threshold: Any) -> bool:
        try:
            if op == ">=":
                return float(val) >= float(threshold)
            elif op == ">":
                return float(val) > float(threshold)
            elif op == "<=":
                return float(val) <= float(threshold)
            elif op == "<":
                return float(val) < float(threshold)
            elif op == "==":
                return str(val).lower() == str(threshold).lower()
            elif op == "!=":
                return str(val).lower() != str(threshold).lower()
        except Exception:
            return False
        return False

    def get_diagnostics_summary(self) -> Dict[str, Any]:
        """
        Produces validation summary statistics for replay report diagnostics.
        """
        evaluated = self._evaluations
        total_eval = len(evaluated)
        confirmed = sum(1 for e in evaluated if e.outcome == PredicateOutcome.CONFIRMED)
        partial = sum(1 for e in evaluated if e.outcome == PredicateOutcome.PARTIALLY_CONFIRMED)
        rejected = sum(1 for e in evaluated if e.outcome == PredicateOutcome.REJECTED)
        insufficient = sum(1 for e in evaluated if e.outcome == PredicateOutcome.INSUFFICIENT_EVIDENCE)
        unresolved = sum(1 for p in self._predicates.values() if p.status == PredicateStatus.PENDING)

        success_rate = float((confirmed + 0.5 * partial) / total_eval) if total_eval > 0 else 0.0

        failures = [
            {
                "predicate_id": e.predicate_id,
                "theory_id": e.theory_id,
                "justification": e.justification,
                "evaluated_at_step": e.evaluated_at_step,
            }
            for e in evaluated
            if e.outcome == PredicateOutcome.REJECTED
        ]

        return {
            "predicates_evaluated": total_eval,
            "success_rate": round(success_rate, 4),
            "confirmed_count": confirmed,
            "partially_confirmed_count": partial,
            "rejected_count": rejected,
            "insufficient_evidence_count": insufficient,
            "unresolved_count": unresolved,
            "failures": failures,
        }
