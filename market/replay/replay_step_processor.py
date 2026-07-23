from cognition.evaluation.epistemic_quality import evaluate_epistemic_quality
from cognition.schemas.confidence.confidence_state import ConfidenceState
from market.replay.cognition_result import CognitionResult


class ReplayStepProcessor:
    """Owns per-day execution orchestration."""

    def __init__(
        self,
        pipeline,
        persistence,
        simulator,
        engines,
        theory_lineage,
        contradiction_registry,
        regime_memory,
        regime_continuity_memory,
    ):
        self.pipeline = pipeline
        self.persistence = persistence
        self.simulator = simulator
        self.engines = (
            engines  # Dict of prediction, pressure, decision, horizon, epistemic
        )
        self.theory_lineage = theory_lineage
        self.contradiction_registry = contradiction_registry
        self.regime_memory = regime_memory
        self.regime_continuity_memory = regime_continuity_memory

    def process_day(self, ctx: dict) -> CognitionResult:
        """Coordinates the full cognition flow for a single market day."""
        day_idx = ctx["day_idx"]
        date_str = ctx["date_str"]
        market_obs = ctx["market_obs"]
        obs_data = ctx["obs_data"]

        # 1. Pre-Cognition Retrieval
        horizon_view = self.engines["horizon"].compute(
            ctx["run_market_observations"] + [market_obs]
        )
        horizon_context = f"Horizon Context: {horizon_view.summary()}"

        # Regime Retrieval
        active_theory_count = (
            self.theory_lineage.active_count() if self.theory_lineage else 0
        )
        preliminary_sig = self.regime_memory.build_signature(
            date=date_str,
            observation=market_obs,
            confidence_values=(
                ctx["confidence_history"][-10:] if ctx["confidence_history"] else [0.5]
            ),
            contradiction_severity=ctx["marker_severity"],
            active_theory_count=active_theory_count,
        )
        regime_matches = self.regime_memory.retrieve(
            preliminary_sig, getattr(market_obs, "contradiction_markers", [])
        )

        # 2. Cognition Pipeline
        regime_subtype = getattr(market_obs, "regime_subtype", "neutral")
        cog_payload = self.pipeline.run_cognition(
            day_idx=day_idx,
            market_obs=market_obs,
            recent_theories=list(reversed(ctx["run_theories"][-5:])),
            recent_validations=list(reversed(ctx["run_validations"][-5:])),
            recent_reflections=list(reversed(ctx["run_reflections"][-5:])),
            horizon_context=horizon_context,
            regime_matches=regime_matches,
            prior_dialectical_synthesis=ctx["prior_synthesis"],
            prior_dialectical_subtype=ctx["prior_subtype"],
            regime_history_prompt=self.regime_continuity_memory.summary(regime_subtype),
            regime_subtype=regime_subtype,
            falsifiability_conditions=getattr(
                market_obs, "falsifiability_conditions", []
            ),
            debug=ctx["debug"],
        )

        theory = cog_payload["theory"]
        contradiction = cog_payload["contradiction"]
        reflection = cog_payload["reflection"]

        # 3. Evolution & Scoring
        lineage_record = self._evolve_lineage(
            day_idx, cog_payload["abstraction"], theory
        )
        self._register_contradictions(day_idx, lineage_record, contradiction)

        # Retire/Revive
        self.theory_lineage.retire_stale_theories(
            day_idx,
            float(contradiction.get("score", 0.0)),
            lineage_record.id if lineage_record else None,
        )
        self.theory_lineage.revive_matching_theories(
            getattr(
                cog_payload["abstraction"],
                "abstraction_summary",
                str(cog_payload["abstraction"]),
            ),
            day_idx,
        )

        # Epistemic Scoring
        theory_usefulness = {"score": 0.0, "label": "unknown"}
        if self.engines["epistemic"] and lineage_record:
            theory_usefulness = self.engines["epistemic"].score_theory(
                lineage_record=lineage_record,
                regime_matches=regime_matches,
                prior_prediction_result=ctx["prior_prediction_result"],
                contradiction_score=float(contradiction.get("score", 0.0)),
                reflection_summary=reflection.reflection_summary,
            )

        # 4. Inferences
        pressure = self.engines["pressure"].infer(
            observation=market_obs,
            horizons=horizon_view,
            regime_matches=regime_matches,
            confidence_state=theory.confidence_state,
            contradiction_result=contradiction,
            reflection=reflection,
            theory_usefulness=theory_usefulness,
            prior_observations=ctx["run_market_observations"][-10:],
            volume_state=obs_data["derived"].get("volume_state", "normal"),
            atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200),
            volume_ratio_5d=float(obs_data["derived"].get("volume_ratio_5d", 1.0)),
            range_pct=float(obs_data["derived"].get("range_pct", 0.0)),
        )

        prediction = self.engines["prediction"].generate_prediction(
            observation=market_obs,
            horizons=horizon_view,
            regime_matches=regime_matches,
            theory=theory,
            contradictions=contradiction,
            reflection=reflection,
            transition_examples=[],  # Placeholder
            volume_state=obs_data["derived"].get("volume_state", "normal"),
            momentum_regime=ctx["mom_regime"],
            volatility_regime=ctx["vol_regime"],
            volume_ratio_5d=float(obs_data["derived"].get("volume_ratio_5d", 1.0)),
            return_3d=float(obs_data["derived"].get("return_3d", 0.0)),
            return_5d=float(obs_data["derived"].get("return_5d", 0.0)),
            close_position_pct=getattr(market_obs, "close_position_pct", 0.5),
            participation_confirmation=getattr(
                market_obs, "participation_confirmation", "normal"
            ),
            theory_usefulness=theory_usefulness,
        )

        decisions = self.engines["decision"].evaluate(
            prediction_probe=prediction,
            transition_pressure=pressure,
            contradiction_score=float(contradiction.get("score", 0.0)),
            theory_usefulness=theory_usefulness.get("score", 0.0),
            confidence_state=None,
            date=date_str,
            volume_state=obs_data["derived"].get("volume_state", "normal"),
            participation_confirmation=getattr(
                market_obs, "participation_confirmation", "normal"
            ),
        )

        # 5. Simulation & Confidence Evolution
        self.simulator.record_day_result(
            date=date_str,
            prediction_direction=(
                ctx["prior_prediction"].direction.value
                if ctx["prior_prediction"]
                else "uncertain"
            ),
            prediction_confidence=(
                ctx["prior_prediction"].confidence if ctx["prior_prediction"] else 0.0
            ),
            actual_daily_return_pct=(
                obs_data["derived"]["daily_return_pct"]
                if obs_data.get("derived")
                else 0.0
            ),
            market_daily_return_pct=(
                obs_data["derived"]["daily_return_pct"]
                if obs_data.get("derived")
                else 0.0
            ),
            decisions=decisions,
        )

        conf_engine = self.engines.get("confidence_evolution") or self.engines.get("confidence_engine")
        conf_state = conf_engine.evolve(
            confidence_state=theory.confidence_state,
            validation=cog_payload["validation"],
            reflection=reflection,
            contradiction_result=contradiction,
            market_observation=market_obs,
            recent_validations=ctx["run_validations"][-5:],
            outcome_validation_result=ctx["prior_prediction_result"],
            lineage_event={},  # Optional
            theory_usefulness=theory_usefulness,
            regime_matches=regime_matches,
            day_idx=day_idx,
        )


        # 6. Memory Persist
        final_sig = self.regime_memory.build_signature(
            date=date_str,
            observation=market_obs,
            confidence_values=ctx["confidence_history"][-10:],
            contradiction_severity=float(contradiction.get("score", 0.0)),
            active_theory_count=(
                self.theory_lineage.active_count()
                if self.theory_lineage
                else active_theory_count
            ),
        )
        self.regime_memory.persist(
            step=day_idx,
            signature=final_sig,
            active_theories=self.theory_lineage.active_theories(),
            contradictions=contradiction.get("indicators", []),
            confidence=conf_state.empirical_confidence,
        )

        # Result Assembly
        result = CognitionResult(
            day_index=day_idx,
            date=date_str,
            observation=market_obs,
            abstraction=cog_payload["abstraction"],
            theory=theory,
            contradiction=contradiction,
            reflection=reflection,
            confidence_state=conf_state,
            validation=cog_payload["validation"],
            theory_usefulness=theory_usefulness,
            transition_pressure=pressure,
            prediction=prediction,
            prior_prediction_result=ctx["prior_prediction_result"],
            regime_matches=regime_matches,
            horizon_view=horizon_view,
            regime_signature=final_sig,
            regime_history=self.regime_continuity_memory.summary(regime_subtype),
            decisions=decisions,
            branch_stats=cog_payload["branch_stats"],
            lesson=ctx.get("lesson", ""),
            epistemic_quality={
                "theory": evaluate_epistemic_quality(
                    theory.summary_structured.claim
                    if theory.summary_structured
                    else theory.summary
                )
            },
        )

        return result

    def _evolve_lineage(self, day_idx, abstraction, theory):
        if not self.theory_lineage:
            return None
        abs_text = getattr(abstraction, "abstraction_summary", str(abstraction))
        res = self.theory_lineage.evolve_theory(
            abstraction=abs_text,
            step=day_idx,
            confidence_state={
                "empirical_confidence": theory.confidence_state.empirical_confidence,
                "theoretical_coherence": theory.confidence_state.theoretical_coherence,
                "contradiction_pressure": theory.confidence_state.contradiction_pressure,
            },
        )
        return res["record"]

    def _register_contradictions(self, day_idx, record, contradiction):
        if not self.contradiction_registry or not record:
            return
        indicators = contradiction.get("indicators", [])
        self.contradiction_registry.register_contradictions(
            theory_id=record.id,
            descriptions=indicators,
            severity=float(contradiction.get("score", 0.0)),
            step=day_idx,
        )
        if indicators:
            self.theory_lineage.record_contradictions(
                tid=record.id, descriptions=indicators, step=day_idx
            )
