"""
Step module for paper trading outcome evaluation, decision record construction,
conviction logging, accuracy history tracking, and final regime signature persistence in cognitive replay.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("replay_engine.step_decision")


@dataclass
class DailyDecisionResult:
    decision_record: Any
    action: str
    allocation_pct: float
    conviction_score: float
    recent_acc: float
    regime_acc: float
    lifetime_acc: float


def process_daily_decision(
    executor: Any,
    day_idx: int,
    date_str: str,
    obs_data: Dict[str, Any],
    market_obs: Any,
    theory: Any,
    prediction_probe: Any,
    transition_pressure: Any,
    contradiction_result: Dict[str, Any],
    confidence_state: Any,
    principles_accepted: List[Any],
    regime_subtype: str,
    regime_matches: List[Any],
    horizon_view: Any,
    decisions: Dict[str, Any],
    audit_created: bool,
    audit_mutated: bool,
    audit_merged: bool,
    audit_revived: bool,
    audit_retired: bool,
    prior_prediction_result: Optional[Any],
) -> DailyDecisionResult:
    """Processes paper trade outcome evaluation, decision record construction, conviction logging & accuracy tracking."""
    derived = obs_data.get("derived")
    actual_ret = derived["daily_return_pct"] if derived else 0.0

    if executor._prior_prediction and derived:
        executor.capital_simulator.record_day_result(
            date=date_str,
            prediction_direction=executor._prior_prediction.direction.value,
            prediction_confidence=executor._prior_prediction.confidence,
            actual_daily_return_pct=actual_ret,
            market_daily_return_pct=actual_ret,
            decisions=decisions,
        )
    elif derived:
        executor.capital_simulator.record_day_result(
            date_str, "uncertain", 0.0, actual_ret, actual_ret
        )

    if hasattr(executor, "paper_trader") and executor.paper_trader and derived:
        ohlcv = obs_data.get("ohlcv", {})
        open_p = ohlcv.get("open", 0.0)
        close_p = ohlcv.get("close", 0.0)
        prior_record = getattr(executor, "_prior_decision_record", None)
        if prior_record:
            executor.paper_trader.evaluate_decision_outcome(
                record=prior_record,
                open_price=open_p,
                close_price=close_p,
                actual_daily_return_pct=actual_ret,
                evaluation_date=date_str,
            )
            if hasattr(executor, "decision_journal") and executor.decision_journal:
                executor.decision_journal.save(prior_record)
        else:
            from cognition.schemas.decision.decision import Decision
            from cognition.schemas.decision.decision_record import DecisionRecord

            initial_decision = Decision(
                date=date_str,
                prediction_direction="uncertain",
                action="hold",
                allocation_pct=0.0,
                conviction_score=0.0,
                reason="Initialization day - no active prediction",
            )
            initial_record = DecisionRecord(
                prediction_date=date_str,
                asset=executor.engine.market_name or "RELIANCE",
                prediction="uncertain",
                decision=initial_decision,
                allocation=0.0,
                conviction_score=0.0,
                decision_reason="Initialization day - no active prediction",
            )
            executor.paper_trader.evaluate_decision_outcome(
                record=initial_record,
                open_price=open_p,
                close_price=close_p,
                actual_daily_return_pct=actual_ret,
                evaluation_date=date_str,
            )
            if hasattr(executor, "decision_journal") and executor.decision_journal:
                executor.decision_journal.save(initial_record)

    recent_acc = 0.5
    regime_acc = 0.5
    lifetime_acc = 0.5

    if prior_prediction_result:
        score = getattr(prior_prediction_result, "direction_score", 0.5)
        if score is None:
            score = 0.5

        if not hasattr(executor, "_lifetime_predictions_count"):
            executor._lifetime_predictions_count = 0
            executor._lifetime_correct_predictions_count = 0.0
        executor._lifetime_predictions_count += 1
        executor._lifetime_correct_predictions_count += score

        if not hasattr(executor, "_prediction_accuracy_history"):
            executor._prediction_accuracy_history = []
        executor._prediction_accuracy_history.append(score)

        if not hasattr(executor, "_regime_prediction_accuracy_history"):
            executor._regime_prediction_accuracy_history = {}
        prior_subtype = (
            getattr(executor, "_prior_dialectical_subtype", None)
            or regime_subtype
        )
        if prior_subtype not in executor._regime_prediction_accuracy_history:
            executor._regime_prediction_accuracy_history[prior_subtype] = []
        executor._regime_prediction_accuracy_history[prior_subtype].append(score)

    if hasattr(executor, "_prediction_accuracy_history") and executor._prediction_accuracy_history:
        recent_scores = executor._prediction_accuracy_history[-15:]
        recent_acc = sum(recent_scores) / len(recent_scores)

    if (
        hasattr(executor, "_regime_prediction_accuracy_history")
        and regime_subtype in executor._regime_prediction_accuracy_history
        and executor._regime_prediction_accuracy_history[regime_subtype]
    ):
        regime_scores = executor._regime_prediction_accuracy_history[regime_subtype][-15:]
        regime_acc = sum(regime_scores) / len(regime_scores)

    if hasattr(executor, "_lifetime_predictions_count") and executor._lifetime_predictions_count > 0:
        lifetime_acc = (
            executor._lifetime_correct_predictions_count
            / executor._lifetime_predictions_count
        )

    try:
        executor._confidence_history.append(confidence_state.empirical_confidence)
    except Exception as _exc:
        logger.debug("[ReplayExecutor] day=%d _confidence_history append failed: %s", day_idx, _exc)

    calibrated_confidence = prediction_probe.confidence
    contradiction_pressure = float(contradiction_result.get("score", 0.0))
    empirical_confidence = confidence_state.empirical_confidence
    principle_support = 1 if len(principles_accepted) > 0 else 0
    trans_pressure_val = transition_pressure.pressure_score
    pred_direction = prediction_probe.direction.value

    conv_res = executor.conviction_sizer.compute_sizer(
        calibrated_confidence=calibrated_confidence,
        contradiction_pressure=contradiction_pressure,
        empirical_confidence=empirical_confidence,
        principle_support=principle_support,
        transition_pressure=trans_pressure_val,
        prediction_direction=pred_direction,
    )
    allocation_pct = conv_res.allocation
    conviction_score = conv_res.final_score

    if allocation_pct > 0.0:
        action = "long" if pred_direction == "higher" else "short"
    else:
        action = "hold"

    regime_stability = 1.0 - trans_pressure_val
    executor._log(
        f"• [CONVICTION] Score: {conviction_score:.2f} | Allocation: {allocation_pct * 100:.1f}% | "
        f"Confidence: {calibrated_confidence:.2f} | Pressure: {contradiction_pressure:.2f} | "
        f"Empirical: {empirical_confidence:.2f} | Principles: {principle_support} | "
        f"Regime: {regime_stability:.2f}"
    )

    executor._prior_conviction = conviction_score
    executor._prior_allocation = allocation_pct
    executor._prior_components = {
        "calibrated_confidence": calibrated_confidence,
        "contradiction_pressure": contradiction_pressure,
        "empirical_confidence": empirical_confidence,
        "principle_support": principle_support,
        "transition_pressure": trans_pressure_val,
    }

    from cognition.schemas.decision.decision import Decision
    from cognition.schemas.decision.decision_record import DecisionRecord

    decision_obj = Decision(
        date=date_str,
        prediction_direction=pred_direction,
        action=action,
        allocation_pct=allocation_pct,
        conviction_score=conviction_score,
        reason=prediction_probe.tension or "Standard cognitive trade sizing",
    )

    supporting_lineages = (
        [theory.lineage_id]
        if (theory and getattr(theory, "lineage_id", None))
        else []
    )
    supporting_principles = [str(pid) for pid in principles_accepted]
    retrieved_memories = (
        [
            f"Regime Analog {getattr(m, 'regime_subtype', 'unknown')}"
            for m in regime_matches
        ]
        if regime_matches
        else []
    )

    knowledge_changes = []
    if audit_created:
        knowledge_changes.append("theory_created")
    if audit_mutated:
        knowledge_changes.append("theory_mutated")
    if audit_merged:
        knowledge_changes.append("theory_merged")
    if audit_revived:
        knowledge_changes.append("theory_revived")
    if audit_retired:
        knowledge_changes.append("theory_retired")

    decision_record = DecisionRecord(
        prediction_date=date_str,
        asset=executor.engine.market_name or "RELIANCE",
        prediction=pred_direction,
        decision=decision_obj,
        allocation=allocation_pct,
        conviction_score=conviction_score,
        decision_reason=prediction_probe.tension or "Standard cognitive trade sizing",
        supporting_lineages=supporting_lineages,
        supporting_principles=supporting_principles,
        retrieved_memories=retrieved_memories,
        novelty_score=1.0 if (audit_created or audit_mutated) else 0.0,
        contradiction_pressure=contradiction_pressure,
        transition_pressure=trans_pressure_val,
        calibrated_confidence=calibrated_confidence,
        empirical_confidence=empirical_confidence,
        reflection_confidence=confidence_state.reflection_confidence,
        regime_confidence=confidence_state.regime_confidence,
        expected_scenarios=[prediction_probe.tension] if prediction_probe.tension else [],
        knowledge_changes=knowledge_changes,
        conviction_breakdown=conv_res.component_breakdown,
    )
    executor._prior_decision_record = decision_record

    executor._prior_transition_context = {
        "pressure": transition_pressure.pressure_score,
        "breakout": transition_pressure.breakout_risk,
        "bias": transition_pressure.direction_bias,
        "confidence": theory.confidence_state.empirical_confidence,
        "usefulness": 0.0,
        "contradiction": float(contradiction_result.get("score", 0.0)),
        "horizon": horizon_view,
        "theory_summary": theory.summary,
    }

    final_regime_signature = executor.regime_memory.build_signature(
        date=date_str,
        observation=market_obs,
        confidence_values=executor._confidence_history[-10:],
        contradiction_severity=float(contradiction_result.get("score", 0.0)),
        active_theory_count=(
            executor.theory_lineage.active_count()
            if executor.theory_lineage
            else 0
        ),
    )
    active_lineage_records = (
        executor.theory_lineage.active_theories() if executor.theory_lineage else []
    )
    executor.regime_memory.persist(
        step=day_idx,
        signature=final_regime_signature,
        active_theories=active_lineage_records,
        contradictions=contradiction_result.get("indicators", []),
        confidence=getattr(confidence_state, "empirical_confidence", 0.5),
    )

    return DailyDecisionResult(
        decision_record=decision_record,
        action=action,
        allocation_pct=allocation_pct,
        conviction_score=conviction_score,
        recent_acc=recent_acc,
        regime_acc=regime_acc,
        lifetime_acc=lifetime_acc,
    )
