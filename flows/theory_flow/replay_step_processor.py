import hashlib

from market.replay.runtime.cognition_result import CognitionResult


class ReplayStepProcessor:
    """Orchestrates per-day execution logic for the ReplayExecutor."""

    def __init__(self, executor):
        self.ex = executor  # Reference to God Object for lifecycle access
        self.pipeline = executor.cognition_pipeline
        self.persistence = executor.persistence_coordinator

    def process_day(
        self, day_idx: int, date_str: str, obs_data: dict
    ) -> CognitionResult:
        from cognition.schemas.observation.observation_event import \
            ObservationEvent

        # 1. Synthesis & Grounding
        market_obs = self.ex.synthesizer.synthesize(day_idx)
        horizon_view = self.ex.horizon_engine.compute(
            [*self.ex._run_market_observations, market_obs]
        )

        # 2. Context Retrieval
        regime_matches = self._get_regime_matches(day_idx, date_str, market_obs)
        regime_context = self.ex._format_regime_context(regime_matches)

        # CHANGE: Retrieve Active Lessons relevant to current regime via multi-dimensional metadata matching
        regime_subtype = getattr(market_obs, "regime_subtype", "neutral")
        lesson_repo = self.persistence.repos.get("lesson")
        relevant_lessons = []
        if lesson_repo:
            all_active = [
                l
                for l in lesson_repo.list_lessons()
                if getattr(l, "status", None) == "active"
                or getattr(l, "status", None) == "LessonStatus.ACTIVE"
                or (
                    hasattr(getattr(l, "status", None), "value")
                    and getattr(l, "status").value == "active"
                )
            ]

            # Derive current metadata state
            vol_30d = (
                float(obs_data["derived"].get("volatility_30d", 0.0))
                if obs_data.get("derived")
                else 0.0
            )
            vol_regime = (
                "compressed"
                if vol_30d < 0.8
                else "expanded" if vol_30d > 1.5 else "normal"
            )
            ret_3d = (
                float(obs_data["derived"].get("return_3d", 0.0))
                if obs_data.get("derived")
                else 0.0
            )
            mom_regime = (
                "strengthening"
                if ret_3d > 0.5
                else "weakening" if ret_3d < -0.5 else "flat"
            )
            vol_state = (
                obs_data["derived"].get("volume_state", "normal")
                if obs_data.get("derived")
                else "normal"
            )

            query_state = {
                "regime_subtype": regime_subtype,
                "volatility": vol_regime,
                "momentum": mom_regime,
                "volume": vol_state,
            }

            scored_lessons = []
            for l in all_active:
                match_score = 0
                meta = getattr(l, "metadata", {}) or {}
                for k, v in query_state.items():
                    if k in meta and str(meta[k]).lower() == str(v).lower():
                        match_score += 1

                subtype_matches = (
                    "regime_subtype" in meta
                    and str(meta["regime_subtype"]).lower()
                    == str(regime_subtype).lower()
                )

                # Retrieve lessons that match subtype or have at least 2 other matching keys
                if subtype_matches or match_score >= 2:
                    scored_lessons.append((l, match_score))

            scored_lessons.sort(key=lambda x: x[1], reverse=True)
            relevant_lessons = [item[0].lesson_text for item in scored_lessons[:5]]
            self.ex._prior_lessons = relevant_lessons

        historical_context = self.ex._format_historical_context(
            list(reversed(self.ex._run_validations[-5:])),
            list(reversed(self.ex._run_reflections[-5:])),
        )

        # 3. Execute Cognition Pipeline
        obs_event = ObservationEvent(
            source_type="replay",
            raw_content=f"{market_obs.observation_text}\n{horizon_view.summary()}",
        )
        regime_subtype = getattr(market_obs, "regime_subtype", "neutral")

        abstraction, theory, contradiction, branch_stats = self.pipeline.process(
            obs_event,
            market_obs,
            historical_context,
            regime_context,
            horizon_view.summary(),
            regime_subtype,
            getattr(market_obs, "falsifiability_conditions", []),
            self.ex.regime_continuity_memory.summary(regime_subtype),
            self._get_active_synthesis(regime_subtype, regime_matches),
            list(reversed(self.ex._run_theories[-5:])),
            list(reversed(self.ex._run_validations[-5:])),
            list(reversed(self.ex._run_reflections[-5:])),
            self.ex._run_market_observations[-5:],
            relevant_lessons=relevant_lessons,
        )

        # 4. Lineage & Synthesis Lifecycle
        lineage_record, synthesis_data = self._handle_evolution(
            day_idx, abstraction, theory, contradiction, market_obs, relevant_lessons
        )

        # 5. Reflection
        reflection = self.ex.reflection_flow.process(
            theory,
            None,
            contradiction_result=contradiction,
            market_observation=market_obs,
            regime_subtype=regime_subtype,
            regime_history=self.ex.regime_continuity_memory.summary(regime_subtype),
            dialectical_synthesis=(
                self.ex.dialectical_synthesizer.format_for_reflection(synthesis_data)
                if synthesis_data
                else None
            ),
        )

        # 6. Assessment
        prior_prediction_result = self._score_prior(market_obs)

        # Calculate rolling 15-day prediction accuracy
        if prior_prediction_result:
            score = getattr(prior_prediction_result, "direction_score", 0.5)
            if score is None:
                score = 0.5
            if not hasattr(self.ex, "_prediction_accuracy_history"):
                self.ex._prediction_accuracy_history = []
            self.ex._prediction_accuracy_history.append(score)

            # Hypothesis Validation: reinforce/penalize lessons used for this prediction
            if getattr(self.ex, "_prior_lessons", None):
                lesson_repo = self.persistence.repos.get("lesson")
                if lesson_repo:
                    from market.replay.lesson_record import LessonStatus

                    for l_text in self.ex._prior_lessons:
                        matching_lesson = None
                        for l in lesson_repo.list_lessons():
                            if l.lesson_text == l_text:
                                matching_lesson = l
                                break
                        if matching_lesson:
                            if score == 1.0:
                                matching_lesson.support_count += 1
                            elif score == 0.0:
                                matching_lesson.contradiction_count += 1

                            total = (
                                matching_lesson.support_count
                                + matching_lesson.contradiction_count
                            )
                            matching_lesson.confidence = (
                                matching_lesson.support_count / total
                                if total > 0
                                else 0.0
                            )

                            if matching_lesson.confidence >= 0.75:
                                matching_lesson.status = LessonStatus.ACTIVE
                            elif matching_lesson.confidence < 0.2:
                                matching_lesson.status = LessonStatus.RETIRED
                            else:
                                matching_lesson.status = LessonStatus.CANDIDATE

                            lesson_repo.save(matching_lesson)

        rolling_accuracy = 0.5
        if (
            hasattr(self.ex, "_prediction_accuracy_history")
            and self.ex._prediction_accuracy_history
        ):
            recent_scores = self.ex._prediction_accuracy_history[-15:]
            rolling_accuracy = sum(recent_scores) / len(recent_scores)

        theory_usefulness = self.ex.epistemic_scoring.score_theory(
            lineage_record=lineage_record,
            regime_matches=regime_matches,
            prior_prediction_result=(
                prior_prediction_result.to_dict() if prior_prediction_result else {}
            ),
            contradiction_score=float(contradiction.get("score", 0.0)),
            reflection_summary=reflection.reflection_summary,
        )

        transition_pressure = self.ex.transition_pressure_engine.infer(
            observation=market_obs,
            horizons=horizon_view,
            regime_matches=regime_matches,
            confidence_state=theory.confidence_state,
            contradiction_result=contradiction,
            reflection=reflection,
            theory_usefulness=theory_usefulness,
            prior_observations=self.ex._run_market_observations[-10:],
            volume_state=obs_data["derived"].get("volume_state", "normal"),
        )

        prediction = self.ex.prediction_generator.generate_prediction(
            observation=market_obs,
            horizons=horizon_view,
            regime_matches=regime_matches,
            theory=theory,
            contradictions=contradiction,
            reflection=reflection,
            theory_usefulness=theory_usefulness,
            volume_state=obs_data["derived"].get("volume_state", "normal"),
        )

        decisions = self.ex.decision_engine.evaluate(
            prediction,
            transition_pressure,
            float(contradiction.get("score", 0.0)),
            theory_usefulness.get("score", 0.0),
            theory.confidence_state,
            date_str,
        )

        # 7. Confidence & Memory Evolution
        confidence_state = self.ex.confidence_engine.evolve(
            theory.confidence_state,
            None,
            reflection,
            contradiction,
            market_obs,
            outcome_validation_result=(
                prior_prediction_result.to_dict() if prior_prediction_result else {}
            ),
            theory_usefulness=theory_usefulness,
            regime_matches=regime_matches,
            rolling_accuracy=rolling_accuracy,
        )

        # Build Result
        result = CognitionResult(
            day_index=day_idx,
            date=date_str,
            observation=market_obs,
            abstraction=abstraction,
            theory=theory,
            contradiction=contradiction,
            reflection=reflection,
            confidence=confidence_state,
            theory_usefulness=theory_usefulness,
            transition_pressure=transition_pressure,
            prediction=prediction,
            prior_prediction_result=prior_prediction_result,
            decisions=decisions,
            regime_matches=regime_matches,
            regime_history=self.ex.regime_continuity_memory.summary(regime_subtype),
            horizon_view=horizon_view,
            final_regime_signature=None,
            epistemic_quality={"theory": evaluate_epistemic_quality(theory.summary)},
            dialectical_data=synthesis_data,
        )

        # 8. Persistence
        self.persistence.save_day(result, obs_event)

        return result

    def _get_regime_matches(self, day_idx, date_str, market_obs):
        prior_conf = (
            [0.5]
            if not self.ex._confidence_history
            else list(self.ex._confidence_history[-10:])
        )
        sig = self.ex.regime_memory.build_signature(
            date=date_str,
            observation=market_obs,
            confidence_values=prior_conf,
            contradiction_severity=0.0,
            active_theory_count=0,
        )
        return self.ex.regime_memory.retrieve(
            sig, getattr(market_obs, "contradiction_markers", [])
        )

    def _get_active_synthesis(self, subtype, matches):
        if not self.ex._prior_dialectical_synthesis:
            return None
        max_sim = max([getattr(m, "similarity", 0.0) for m in matches] + [0.0])
        if subtype == self.ex._prior_dialectical_subtype or max_sim > 0.8:
            return self.ex._prior_dialectical_synthesis
        return None

    def _handle_evolution(
        self,
        day_idx,
        abstraction,
        theory,
        contradiction,
        market_obs,
        relevant_lessons=None,
    ):
        lineage_record = None
        synthesis_data = None
        try:
            contra_score = float(contradiction.get("score", 0.0))

            # NEW: Cognitive Inertia - ignore low-level semantic jitter
            if contra_score < 0.15:
                # If score is very low, treat as 'continued' rather than mutation
                lineage_res = self.ex.theory_lineage.evolve_theory(
                    getattr(abstraction, "abstraction_summary", ""),
                    {},
                    day_idx,
                    force_continue=True,
                )
            else:
                lineage_res = self.ex.theory_lineage.evolve_theory(
                    getattr(abstraction, "abstraction_summary", ""), {}, day_idx
                )

            lineage_record = lineage_res["record"]

            active_lineage = self.ex.theory_lineage.active_theories()
            if len(active_lineage) >= 2 and contra_score >= 0.35:
                # Aggregate component failures for the current regime subtype
                component_failures = {}
                if hasattr(self.ex, "experience_repo") and self.ex.experience_repo:
                    try:
                        current_subtype = getattr(
                            market_obs, "regime_subtype", "neutral"
                        )
                        for exp in self.ex.experience_repo.get_all():
                            if getattr(exp, "theory_subtype", None) == current_subtype:
                                f_counts = (
                                    getattr(exp, "component_failure_counts", {}) or {}
                                )
                                for comp, count in f_counts.items():
                                    component_failures[comp] = (
                                        component_failures.get(comp, 0) + count
                                    )
                    except Exception:
                        pass

                synthesis_data = self.ex.dialectical_synthesizer.synthesize(
                    market_obs.observation_text,
                    active_lineage,
                    contradiction.get("indicators", []),
                    getattr(market_obs, "regime_subtype", "neutral"),
                    [],
                    relevant_lessons=relevant_lessons,
                    component_failures=component_failures,
                )

            # NEW: Only retire if the theory has had at least one chance to be validated
            # This prevents "infant mortality" from immediate contradictions
            is_new_lineage = (
                lineage_record.created_at_step == day_idx if lineage_record else False
            )
            if (
                not is_new_lineage or contra_score > 0.8
            ):  # Allow immediate death only for extreme conflicts
                self.ex.theory_lineage.retire_stale_theories(
                    day_idx, contra_score, lineage_record.id if lineage_record else None
                )

        except:
            pass
        return lineage_record, synthesis_data

    def _score_prior(self, market_obs):
        if self.ex._prior_prediction:
            return self.ex.prediction_generator.score_actual(
                self.ex._prior_prediction, market_obs
            )
        return None
