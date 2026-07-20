"""
Step Prediction Module for Replay Engine.

Handles transition pressure inference, active principles applicability evaluation,
prediction probe generation, deterministic World Model constraint overrides,
and conviction position sizing.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from cognition.schemas.prediction.prediction import PredictionDirection

logger = logging.getLogger("replay_engine.step_prediction")


@dataclass
class DailyPredictionResult:
    prediction_probe: Any
    transition_pressure: Any
    similar_transitions: List[Any]
    principles_consulted: List[str]
    principles_accepted: List[str]
    principles_rejected: List[str]
    confidence_delta: float
    world_model_applied: bool
    prediction_override_applied: bool
    decisions: Dict[str, Any]
    conviction_score: float
    allocation_pct: float
    conviction_components: Dict[str, float]


def process_daily_prediction(
    executor: Any,
    day_idx: int,
    date_str: str,
    obs_data: dict,
    market_obs: Any,
    horizon_view: Any,
    regime_matches: List[Any],
    theory: Any,
    contradiction_result: dict,
    reflection: Any,
    theory_usefulness: dict,
    intelligence_metadata: dict,
    regime_subtype: str,
    vol_regime: str,
    mom_regime: str,
    confidence_state: Any,
) -> DailyPredictionResult:
    """
    Evaluates transition pressure, active principles applicability, generates prediction probe,
    applies deterministic World Model overrides, evaluates decisions, and computes conviction sizing.
    """
    # Infer transition pressure
    transition_pressure = executor.transition_pressure_engine.infer(
        observation=market_obs,
        horizons=horizon_view,
        regime_matches=regime_matches,
        confidence_state=theory.confidence_state,
        contradiction_result=contradiction_result,
        reflection=reflection,
        theory_usefulness=theory_usefulness,
        prior_observations=executor._run_market_observations[-10:],
        volume_state=obs_data["derived"].get("volume_state", "normal"),
        atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200),
        volume_ratio_5d=float(obs_data["derived"].get("volume_ratio_5d", 1.0)),
        range_pct=float(obs_data["derived"].get("range_pct", 0.0)),
    )

    # Retrieve transitions
    similar_transitions = executor.transition_memory.retrieve_similar(
        from_regime=market_obs.trend_state,
        direction_bias=transition_pressure.direction_bias,
        pressure_score=transition_pressure.pressure_score,
        horizon_daily=horizon_view.daily,
    )

    active_principles = (
        executor.knowledge_repository.list_principles(status="active")
        + executor.knowledge_repository.list_principles(status="stable")
        + executor.knowledge_repository.list_principles(status="emerging")
        + executor.knowledge_repository.list_principles(status="trusted")
        + executor.knowledge_repository.list_principles(status="canonical")
    )
    latest_wm = executor.knowledge_repository.get_latest_world_model()

    # Prediction probe generation
    prediction_probe = executor.prediction_generator.generate_prediction(
        observation=market_obs,
        horizons=horizon_view,
        regime_matches=regime_matches,
        theory=theory,
        contradictions=contradiction_result,
        reflection=reflection,
        transition_examples=similar_transitions,
        volume_state=obs_data["derived"].get("volume_state", "normal"),
        momentum_regime=mom_regime,
        volatility_regime=vol_regime,
        volume_ratio_5d=float(obs_data["derived"].get("volume_ratio_5d", 1.0)),
        return_3d=float(obs_data["derived"].get("return_3d", 0.0)),
        return_5d=float(obs_data["derived"].get("return_5d", 0.0)),
        close_position_pct=getattr(market_obs, "close_position_pct", 0.5),
        participation_confirmation=getattr(
            market_obs, "participation_confirmation", "normal"
        ),
        theory_usefulness=theory_usefulness,
        intelligence_data=intelligence_metadata,
        world_model=latest_wm,
        active_principles=active_principles,
    )

    # Evaluate Active Principles influence
    principles_consulted = []
    principles_accepted = []
    principles_rejected = []
    confidence_delta = 0.0

    for p in active_principles:
        is_applicable = False
        for fp in p.falsifiable_predictions:
            filter_matches = True
            for k, v in fp.applicability_filter.items():
                val = None
                if k == "regime_subtype":
                    val = regime_subtype
                elif k == "volatility_regime":
                    val = vol_regime
                elif k == "momentum_regime":
                    val = mom_regime

                if isinstance(v, (list, tuple, set)):
                    if val not in v:
                        filter_matches = False
                else:
                    if val != v:
                        filter_matches = False
            if filter_matches:
                is_applicable = True
                break
        if is_applicable:
            principles_consulted.append(p.id)
            if fp.expected_status == "failed":
                confidence_delta -= 0.15
                principles_accepted.append(p.id)
            else:
                principles_accepted.append(p.id)

    if confidence_delta != 0.0:
        new_conf = max(
            0.1, min(1.0, prediction_probe.confidence + confidence_delta)
        )
        from dataclasses import replace

        prediction_probe = replace(
            prediction_probe,
            confidence=new_conf,
            tension=prediction_probe.tension
            + f" [Principle adjustment: {confidence_delta:+.2f}]",
        )

        for pid in principles_accepted:
            p_obj = executor.knowledge_repository.get_principle(pid)
            if p_obj:
                p_obj.confidence_adjustments_triggered += 1
                executor.knowledge_repository.save_principle(p_obj)

    for pid in principles_accepted:
        p_obj = executor.knowledge_repository.get_principle(pid)
        if p_obj:
            p_obj.uses_count += 1
            executor.knowledge_repository.save_principle(p_obj)

    principles_rejected = [
        pid for pid in principles_consulted if pid not in principles_accepted
    ]

    executor._prior_prediction_accepted_principles = principles_accepted
    executor._prior_prediction_active_mechanisms = (
        [
            comp.mechanism_id
            for comp in theory.summary_structured.mechanism_components
            if comp.mechanism_id
        ]
        if (
            theory
            and theory.summary_structured
            and theory.summary_structured.mechanism_components
        )
        else []
    )

    # Apply deterministic World Model overrides/constraints
    latest_wm = executor.knowledge_repository.get_latest_world_model()
    world_model_applied = False
    prediction_override_applied = False
    if latest_wm and latest_wm.regime_constraints:
        constraints = latest_wm.regime_constraints.get(regime_subtype)
        if constraints:
            blocked_bias = constraints.get("blocked_bias")
            max_confidence = constraints.get("max_confidence")

            new_dir = prediction_probe.direction
            new_conf = prediction_probe.confidence

            if (
                blocked_bias == "bullish"
                and prediction_probe.direction == PredictionDirection.higher
            ):
                new_dir = PredictionDirection.uncertain
            elif (
                blocked_bias == "bearish"
                and prediction_probe.direction == PredictionDirection.lower
            ):
                new_dir = PredictionDirection.uncertain
            elif (
                blocked_bias == "neutral"
                and prediction_probe.direction
                in [
                    PredictionDirection.range_bound,
                    PredictionDirection.uncertain,
                ]
            ):
                new_dir = PredictionDirection.higher

            if max_confidence is not None and new_conf > float(max_confidence):
                new_conf = float(max_confidence)

            if (
                new_dir != prediction_probe.direction
                or new_conf != prediction_probe.confidence
            ):
                world_model_applied = True
                if new_dir != prediction_probe.direction:
                    prediction_override_applied = True

                from dataclasses import replace

                prediction_probe = replace(
                    prediction_probe,
                    direction=new_dir,
                    confidence=new_conf,
                    tension=prediction_probe.tension
                    + " [Deterministic override applied]",
                )
                for pid in latest_wm.active_principle_ids:
                    p_obj = executor.knowledge_repository.get_principle(pid)
                    if p_obj:
                        p_obj.world_model_influence_count += 1
                        executor.knowledge_repository.save_principle(p_obj)

    # Decision Policy Layer
    decisions = executor.decision_engine.evaluate(
        prediction_probe=prediction_probe,
        transition_pressure=transition_pressure,
        contradiction_score=float(contradiction_result.get("score", 0.0)),
        theory_usefulness=(
            theory_usefulness.get("score", 0.0) if theory_usefulness else 0.0
        ),
        confidence_state=confidence_state,
        date=date_str,
        volume_state=obs_data["derived"].get("volume_state", "normal"),
        atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200),
        participation_confirmation=getattr(
            market_obs, "participation_confirmation", "normal"
        ),
    )

    # Conviction position sizer calculation
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

    return DailyPredictionResult(
        prediction_probe=prediction_probe,
        transition_pressure=transition_pressure,
        similar_transitions=similar_transitions,
        principles_consulted=principles_consulted,
        principles_accepted=principles_accepted,
        principles_rejected=principles_rejected,
        confidence_delta=confidence_delta,
        world_model_applied=world_model_applied,
        prediction_override_applied=prediction_override_applied,
        decisions=decisions,
        conviction_score=conv_res.final_score,
        allocation_pct=conv_res.allocation,
        conviction_components=conv_res.component_breakdown,
    )
