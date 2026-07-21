"""
Step Observation Module for Replay Engine.

Handles market observation synthesis, trend persistence classification,
transition example recording, multi-horizon computation, regime matching,
and abstraction creation.
"""

from dataclasses import dataclass
from statistics import mean
from typing import Any, List

from cognition.schemas.observation.observation_event import ObservationEvent
from market.replay.transition_memory import TransitionExample


@dataclass
class DailyObservationResult:
    market_obs: Any
    obs_event: Any
    abstraction: Any
    horizon_view: Any
    horizon_context: str
    regime_matches: List[Any]
    regime_context: List[str]
    vol_regime: str
    mom_regime: str
    persistence_3d: float
    persistence_5d: float
    persistence_10d: float
    reg_5d: str


def classify_persistence(val: float) -> str:
    if val > 0.6:
        return "Persistent Higher"
    if val < -0.6:
        return "Persistent Lower"
    return "Mixed"


def process_daily_observation(
    executor: Any,
    day_idx: int,
    date_str: str,
    obs_data: dict,
    synthesizer: Any,
) -> DailyObservationResult:
    """
    Synthesizes daily market observation, calculates persistence metrics,
    records transition examples, builds multi-horizon view, retrieves regime matches,
    and runs abstraction processing.
    """
    # Synthesize observation
    market_obs = synthesizer.synthesize(day_idx)

    # Track directional persistence
    actual_dir_str = market_obs.trend_state.lower()
    dir_val = (
        1 if "higher" in actual_dir_str else -1 if "lower" in actual_dir_str else 0
    )
    executor._actual_directions_val_history.append(dir_val)

    persistence_3d = (
        mean(executor._actual_directions_val_history[-3:])
        if len(executor._actual_directions_val_history) >= 3
        else 0.0
    )
    persistence_5d = (
        mean(executor._actual_directions_val_history[-5:])
        if len(executor._actual_directions_val_history) >= 5
        else 0.0
    )
    persistence_10d = (
        mean(executor._actual_directions_val_history[-10:])
        if len(executor._actual_directions_val_history) >= 10
        else 0.0
    )

    reg_5d = classify_persistence(persistence_5d)
    market_obs.observation_text += (
        f"\nTrend Persistence: 3D: {classify_persistence(persistence_3d)}, "
        f"5D: {reg_5d}, 10D: {classify_persistence(persistence_10d)}. "
        f"Overall Regime: {reg_5d}."
    )

    # Transition Detection and Recording
    if day_idx > 0 and getattr(executor, "_prior_transition_context", None):
        prev_obs = executor._run_market_observations[-1]
        ctx = executor._prior_transition_context

        if prev_obs.trend_state != market_obs.trend_state:
            example = TransitionExample(
                date=prev_obs.observation_source.replace(
                    "replay_engine_", ""
                ),
                day_index=day_idx - 1,
                from_regime=prev_obs.trend_state,
                to_regime=market_obs.trend_state,
                confidence=ctx["confidence"],
                theory_usefulness=ctx["usefulness"],
                contradiction_score=ctx["contradiction"],
                pressure_score=ctx["pressure"],
                breakout_risk=ctx["breakout"],
                direction_bias=ctx["bias"],
                horizon_daily=ctx["horizon"].daily,
                horizon_weekly=ctx["horizon"].weekly,
                horizon_monthly=ctx["horizon"].monthly,
                theory_summary=ctx["theory_summary"],
            )

            meaningful = (
                (
                    example.from_regime == "range_bound"
                    and example.to_regime
                    in [
                        "closed_higher",
                        "extended_higher",
                        "closed_lower",
                        "extended_lower",
                    ]
                )
                or (
                    example.from_regime.startswith("closed_higher")
                    and "lower" in example.to_regime
                )
                or (
                    example.from_regime.startswith("closed_lower")
                    and "higher" in example.to_regime
                )
            )

            if meaningful:
                executor.transition_memory.record_transition(example)

    # Compute horizons
    horizon_view = executor.horizon_engine.compute(
        [*executor._run_market_observations, market_obs]
    )
    horizon_context = f"Horizon Context: {horizon_view.summary()}"

    prior_confidence_values = (
        list(executor._confidence_history[-10:])
        if executor._confidence_history
        else [0.5]
    )
    marker_severity = min(
        1.0, len(getattr(market_obs, "contradiction_markers", [])) * 0.2
    )

    # Regime calculation for memory and analysis
    vol_30d = float(obs_data["derived"].get("volatility_30d", 0.0))
    vol_regime = (
        "compressed"
        if vol_30d < 0.8
        else "expanded" if vol_30d > 1.5 else "normal"
    )
    ret_3d = float(obs_data["derived"].get("return_3d", 0.0))
    mom_regime = (
        "strengthening"
        if ret_3d > 0.5
        else "weakening" if ret_3d < -0.5 else "flat"
    )

    active_theory_count = (
        executor.theory_lineage.active_count() if executor.theory_lineage else 0
    )
    preliminary_regime_signature = executor.regime_memory.build_signature(
        date=date_str,
        observation=market_obs,
        confidence_values=prior_confidence_values,
        contradiction_severity=marker_severity,
        active_theory_count=active_theory_count,
    )
    regime_matches = executor.regime_memory.retrieve(
        preliminary_regime_signature,
        getattr(market_obs, "contradiction_markers", []),
    )
    executor._regime_matches_by_step.append(regime_matches)
    regime_context = executor._format_regime_context(regime_matches)

    # Analog divergence update
    if regime_matches and regime_matches[0].similarity > 0.8:
        analog = regime_matches[0]
        analog_sig = (
            analog.to_dict().get("signature", {})
            if hasattr(analog, "to_dict")
            else {}
        )
        diffs = []

        if getattr(
            market_obs, "participation_strength", "normal"
        ) != analog_sig.get("participation_strength", "normal"):
            diffs.append(
                f"participation is {market_obs.participation_strength} (prior was {analog_sig.get('participation_strength', 'normal')})"
            )

        if getattr(
            market_obs, "liquidity_state", "normal"
        ) != analog_sig.get("liquidity_state", "normal"):
            diffs.append(
                f"liquidity is {market_obs.liquidity_state} (prior was {analog_sig.get('liquidity_state', 'normal')})"
            )

        if getattr(
            market_obs, "volatility_state", "normal"
        ) != analog_sig.get("volatility_state", "normal"):
            diffs.append(
                f"volatility is {market_obs.volatility_state} (prior was {analog_sig.get('volatility_state', 'normal')})"
            )

        market_obs.analog_divergence_claim = (
            f"Analog to {analog.date}: " + ", ".join(diffs)
            if diffs
            else "Analog continuity"
        )

    # Observe and abstract
    obs_event = ObservationEvent(
        source_type="replay",
        raw_content=(f"{market_obs.observation_text}\n{horizon_context}"),
    )
    abstraction = executor.abstraction_flow.process(obs_event)

    try:
        from core.event_bus import get_event_bus
        from core.events import ObservationCreated

        get_event_bus().publish(
            ObservationCreated(
                date=date_str,
                symbol=getattr(executor, "market_name", "RELIANCE"),
                ohlcv=obs_data.get("ohlcv", {}),
                derived=obs_data.get("derived", {}),
            ),
            publisher="step_observation",
        )
    except Exception as _evt_exc:
        pass

    return DailyObservationResult(
        market_obs=market_obs,
        obs_event=obs_event,
        abstraction=abstraction,
        horizon_view=horizon_view,
        horizon_context=horizon_context,
        regime_matches=regime_matches,
        regime_context=regime_context,
        vol_regime=vol_regime,
        mom_regime=mom_regime,
        persistence_3d=persistence_3d,
        persistence_5d=persistence_5d,
        persistence_10d=persistence_10d,
        reg_5d=reg_5d,
    )
