"""
Step Validation Module for Replay Engine.

Handles prior prediction scoring, causal attribution, experience outcome grounding,
lesson hypothesis validation, proposition compilation, statistical parameter grounding,
and validation record creation.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import pandas as pd

from cognition.schemas.knowledge.evidence_gap import EvidenceGap
from cognition.schemas.knowledge.open_question import OpenQuestion, QuestionStatus
from market.replay.lesson_record import LessonStatus

logger = logging.getLogger("replay_engine.step_validation")


@dataclass
class DailyValidationResult:
    prior_prediction_result: Any
    prior_attribution: Any
    newly_retired_count: int


def process_daily_validation(
    executor: Any,
    day_idx: int,
    date_str: str,
    obs_data: dict,
    market_obs: Any,
    theory: Any,
    regime_subtype: str,
    vol_regime: str,
    persistence_3d: float,
    persistence_5d: float,
    persistence_10d: float,
    reg_5d: str,
) -> DailyValidationResult:
    """
    Evaluates Day N-1 prediction against Day N market observation, computes causal attribution,
    grounds experience outcome counters, compiles executable propositions, and evaluates validation records.
    """
    prior_prediction_result = None
    attribution = None
    newly_retired_count = 0

    if executor._prior_prediction is not None:
        prior_prediction_result = executor.prediction_generator.score_actual(
            executor._prior_prediction, market_obs
        )

        # Causal Attribution Step
        if executor._prior_lineage_id and executor._run_theories:
            theory_to_attr = executor._run_theories[-1]

            try:
                market_snapshot = {
                    "regime": (
                        market_obs.get("regime_descriptor", "")
                        if hasattr(market_obs, "get")
                        else getattr(market_obs, "regime_descriptor", "")
                    ),
                    "abstractions": (
                        market_obs.get("abstractions", [])
                        if hasattr(market_obs, "get")
                        else getattr(market_obs, "abstractions", [])
                    ),
                    "trend_persistence": {
                        "3d": persistence_3d,
                        "5d": persistence_5d,
                        "10d": persistence_10d,
                        "regime": reg_5d,
                    },
                }

                attribution = executor.attribution_engine.attribute(
                    theory=theory_to_attr,
                    prediction=(
                        str(executor._prior_prediction.direction.value)
                        if executor._prior_prediction
                        else ""
                    ),
                    observation=market_obs,
                    market_context=market_snapshot,
                )
                executor._prior_attribution = attribution
                if not hasattr(executor, "_accumulated_attributions"):
                    executor._accumulated_attributions = []
                executor._accumulated_attributions.append(attribution)

                if attribution.components_failed:
                    logger.info(
                        f"[ATTRIBUTION] Theory {getattr(theory_to_attr, 'id', 'unknown')}: "
                        f"Failed components: {attribution.components_failed}"
                    )
                    if attribution.root_cause_component:
                        logger.info(
                            f"[ATTRIBUTION] Root cause: {attribution.root_cause_component}"
                        )
                    if attribution.attribution_reasoning:
                        logger.info(
                            f"[ATTRIBUTION] Causal analysis: {attribution.attribution_reasoning[:200]}"
                        )

                    # Contradiction Resolution & Open Question Generation
                    active_principles = (
                        executor.knowledge_repository.list_principles(status="active")
                        + executor.knowledge_repository.list_principles(status="stable")
                        + executor.knowledge_repository.list_principles(status="emerging")
                        + executor.knowledge_repository.list_principles(status="trusted")
                        + executor.knowledge_repository.list_principles(status="canonical")
                    )
                    regime_context = {
                        "regime_subtype": regime_subtype,
                        "volatility_regime": vol_regime,
                        "volume_state": obs_data["derived"].get("volume_state", "normal"),
                    }

                    updated_principles = executor.knowledge_compression_engine.resolve_contradictions(
                        active_principles=active_principles,
                        latest_attribution=attribution,
                        current_regime_context=regime_context,
                        step=day_idx,
                    )
                    for p in updated_principles:
                        executor.knowledge_repository.save_principle(p)

                    # Open Question Generation for unexplained failures
                    for comp_failed in attribution.components_failed:
                        is_explained = False
                        for p in active_principles:
                            for fp in p.falsifiable_predictions:
                                if fp.target_component == comp_failed:
                                    context_match = True
                                    for k, v in fp.applicability_filter.items():
                                        val = regime_context.get(k)
                                        if isinstance(v, (list, tuple, set)):
                                            if val not in v:
                                                context_match = False
                                                break
                                        else:
                                            if val != v:
                                                context_match = False
                                                break
                                    if context_match:
                                        is_explained = True
                                        break
                            if is_explained:
                                break

                        if not is_explained:
                            new_oq = OpenQuestion(
                                created_at_step=day_idx,
                                question_text=f"Why did component '{comp_failed}' fail under {regime_subtype} regime?",
                                source_contradiction_ids=[attribution.theory_id],
                                hypothesized_factors=[
                                    str(vol_regime),
                                    (
                                        str(obs_data["derived"].get("volume_state", "normal"))
                                        if not pd.isna(obs_data["derived"].get("volume_state"))
                                        else "normal"
                                    ),
                                ],
                                status=QuestionStatus.ACTIVE,
                            )
                            executor.knowledge_repository.save_open_question(new_oq)

                            # Evidence Gap Generation
                            if "volume" in comp_failed:
                                descriptors = getattr(market_obs, "descriptors", [])
                                is_deliv_unknown = (
                                    "delivery:unknown" in descriptors
                                    or not any(d.startswith("delivery:") for d in descriptors)
                                )
                                is_sec_unknown = (
                                    "sector:unknown" in descriptors
                                    or not any(d.startswith("sector:") for d in descriptors)
                                )
                                if not is_deliv_unknown and not is_sec_unknown:
                                    logger.info(
                                        f"[ATTRIBUTION] Evidence gap for '{comp_failed}' is resolved, skipping saving."
                                    )
                                    continue

                            missing_evidence = f"Order book imbalance and detailed participation dynamics for '{comp_failed}'"
                            candidate_source = "FII/DII Flows & Order Book Depth"
                            if "volume" in comp_failed:
                                missing_evidence = f"Detailed delivery volume % and sector relative strength for volume confirmation validation"
                                candidate_source = "Delivery % & Sector Relative Strength"

                            gap = EvidenceGap(
                                id=str(uuid4()),
                                open_question_id=new_oq.id,
                                missing_evidence=missing_evidence,
                                candidate_data_source=candidate_source,
                                expected_explanatory_value=f"To resolve structural failure of component '{comp_failed}' under {regime_subtype} regime",
                                priority=(
                                    "HIGH"
                                    if comp_failed == attribution.root_cause_component
                                    else "MEDIUM"
                                ),
                            )
                            executor.knowledge_repository.save_evidence_gap(gap)
                else:
                    logger.info(
                        f"[ATTRIBUTION] Theory {getattr(theory_to_attr, 'id', 'unknown')}: All components passed"
                    )

            except Exception as e:
                logger.warning(f"[ATTRIBUTION] Attribution failed: {e}")
                attribution = None

        # Experience Lifecycle: Outcome Grounding & Hypothesis Validation
        if prior_prediction_result and executor._prior_lineage_id:
            target_exp = executor.experience_repo.load_by_lineage(
                executor._prior_lineage_id
            )
            if target_exp:
                attributed = False
                score = getattr(prior_prediction_result, "direction_score", 0.0)
                is_invalidated = getattr(prior_prediction_result, "invalidation_triggered", False)

                if score == 1.0 and not is_invalidated:
                    target_exp.validation_count += 1
                    attributed = True
                elif is_invalidated or score == 0.0:
                    target_exp.falsification_count += 1
                    attributed = True
                else:
                    if hasattr(target_exp, "undecidable_count"):
                        target_exp.undecidable_count += 1
                    attributed = True

                if attributed:
                    executor.experience_engine.process_cycle(
                        lineage_id=executor._prior_lineage_id,
                        experience=target_exp,
                        status=getattr(
                            target_exp.status,
                            "value",
                            target_exp.status,
                        ),
                        attribution=attribution,
                    )
                    executor.experience_repo.save(target_exp)

                # Structured Lesson Hypothesis Validation
                if getattr(executor, "_prior_lessons", None) and executor.lesson_repo:
                    score_val = getattr(prior_prediction_result, "direction_score", 0.5)
                    is_invalidated = getattr(
                        prior_prediction_result, "invalidation_triggered", False
                    )

                    for l_text in executor._prior_lessons:
                        matching_lesson = None
                        for l in executor.lesson_repo.list_lessons():
                            if l.lesson_text == l_text:
                                matching_lesson = l
                                break
                        if matching_lesson:
                            if score_val == 1.0 and not is_invalidated:
                                matching_lesson.validation_count += 1
                            elif is_invalidated or score_val == 0.0:
                                matching_lesson.falsification_count += 1

                            total = (
                                matching_lesson.validation_count
                                + matching_lesson.falsification_count
                            )
                            matching_lesson.confidence = (
                                matching_lesson.validation_count / total
                                if total > 0
                                else 0.0
                            )

                            was_retired = (
                                matching_lesson.status == LessonStatus.RETIRED
                                or getattr(matching_lesson, "status", None) == "retired"
                            )
                            if matching_lesson.confidence >= 0.75:
                                matching_lesson.status = LessonStatus.ACTIVE
                            elif matching_lesson.confidence < 0.2:
                                matching_lesson.status = LessonStatus.RETIRED
                                if not was_retired:
                                    newly_retired_count += 1
                            else:
                                matching_lesson.status = LessonStatus.CANDIDATE

                            executor.lesson_repo.save(matching_lesson)

    # Proposition Compilation & Validation Execution
    executor.compilation_metrics["theories_generated"] += 1
    try:
        if (
            executor.proposition_compiler
            and executor.compiled_proposition_repo
            and executor.canonical_semantic_proposition_repo
        ):
            history_df = getattr(executor.engine, "data", None)
            history_slice = (
                history_df.iloc[: day_idx + 1]
                if (history_df is not None and hasattr(history_df, "iloc"))
                else None
            )

            canonical_prop, compiled_prop = executor.proposition_compiler.compile_theory(
                theory, day_idx, history_slice
            )

            executor.canonical_semantic_proposition_repo.save(canonical_prop)
            executor.compiled_proposition_repo.save(compiled_prop)

            # Local file snapshot persistence
            run_canon_path = (
                executor.run_dir / "canonical_propositions" / f"prop_{theory.id}.json"
            )
            with open(run_canon_path, "w") as f:
                json.dump(canonical_prop.model_dump(), f, indent=2, default=str)

            out_canon_path = (
                executor.base_output_dir / "canonical_propositions" / f"prop_{theory.id}.json"
            )
            with open(out_canon_path, "w") as f:
                json.dump(canonical_prop.model_dump(), f, indent=2, default=str)

            run_snap_path = (
                executor.run_dir / "propositions" / f"prop_{theory.id}.json"
            )
            with open(run_snap_path, "w") as f:
                json.dump(compiled_prop.model_dump(), f, indent=2, default=str)

            out_snap_path = (
                executor.base_output_dir / "propositions" / f"prop_{theory.id}.json"
            )
            with open(out_snap_path, "w") as f:
                json.dump(compiled_prop.model_dump(), f, indent=2, default=str)

            # Metrics tracking
            c_status = canonical_prop.compiler_provenance.get("status", "FAILED")
            if c_status in ["SUCCESS", "PARTIAL"]:
                executor.compilation_metrics["semantic_propositions_created"] += 1
            else:
                executor.compilation_metrics["semantic_failures"] += 1

            from flows.proposition_flow.parameter_grounder import CONCEPT_TO_FIELD as _C2F
            trig_c = canonical_prop.trigger_concept.get("concept")
            tar_c = canonical_prop.target_concept.get("concept")
            if (trig_c and trig_c not in _C2F) or (tar_c and tar_c not in _C2F):
                executor.compilation_metrics["ontology_mapping_failures"] += 1

            g_status = compiled_prop.compilation_status
            if g_status == "SUCCESS":
                executor.compilation_metrics["propositions_grounded"] += 1
            else:
                executor.compilation_metrics["grounding_failures"] += 1

            ground_provenance = compiled_prop.compiler_trace.get("grounding_provenance", {})
            executor.compilation_metrics["percentile_grounding"] += ground_provenance.get("percentile_groundings_applied", 0)
            executor.compilation_metrics["relative_references_resolved"] += ground_provenance.get("relative_references_resolved", 0)

            executor.compilation_metrics["propositions_compiled"] += 1
            if g_status == "SUCCESS":
                executor.compilation_metrics["compilation_success_count"] += 1
            elif g_status == "PARTIAL":
                executor.compilation_metrics["compilation_partial_count"] += 1
            else:
                executor.compilation_metrics["compilation_failed_count"] += 1

            reason = compiled_prop.failure_reason or "Unknown Reason"
            if g_status != "SUCCESS":
                executor.compilation_metrics["failure_reasons"][reason] = (
                    executor.compilation_metrics["failure_reasons"].get(reason, 0) + 1
                )

            tot = executor.compilation_metrics["theories_generated"]
            executor.compilation_metrics["compilation_success_rate"] = (
                executor.compilation_metrics["compilation_success_count"] / tot
                if tot > 0
                else 0.0
            )

            # Validation Engine execution
            if compiled_prop and compiled_prop.compilation_status == "SUCCESS":
                try:
                    full_df = executor.engine.data
                    regime_str = getattr(market_obs, "regime_subtype", "neutral")
                    conf_val = (
                        getattr(theory.confidence_state, "empirical_confidence", 0.5)
                        if theory
                        else 0.5
                    )
                    unc_val = (
                        getattr(theory.confidence_state, "epistemic_uncertainty", 0.5)
                        if theory
                        else 0.5
                    )

                    val_rec = executor.validation_engine.validate(
                        compiled_prop=compiled_prop,
                        history_df=full_df,
                        current_step=day_idx,
                        confidence_before=conf_val,
                        confidence_after=conf_val,
                        uncertainty_before=unc_val,
                        uncertainty_after=unc_val,
                        regime=regime_str,
                        market_context={"trend": getattr(market_obs, "trend_state", "neutral")},
                    )

                    executor.validation_record_repo.save(val_rec)

                    run_val_path = executor.run_dir / "validation_records" / f"val_{val_rec.id}.json"
                    with open(run_val_path, "w") as f:
                        json.dump(val_rec.model_dump(), f, indent=2, default=str)

                    out_val_path = executor.base_output_dir / "validation_records" / f"val_{val_rec.id}.json"
                    with open(out_val_path, "w") as f:
                        json.dump(val_rec.model_dump(), f, indent=2, default=str)

                    executor.compilation_metrics["propositions_evaluated"] += 1
                    executor.compilation_metrics["validation_records_created"] += 1
                    if val_rec.validation_state == "SUPPORTED":
                        executor.compilation_metrics["supported_records"] += 1
                    elif val_rec.validation_state == "CONTRADICTED":
                        executor.compilation_metrics["contradicted_records"] += 1
                    elif val_rec.validation_state == "PARTIALLY_SUPPORTED":
                        executor.compilation_metrics["partially_supported_records"] += 1
                    elif val_rec.validation_state in ["GROUNDED", "UNTRIGGERED", "TRIGGERED"]:
                        executor.compilation_metrics["undecidable_records"] += 1

                except Exception as val_err:
                    executor._log(f"WARNING: Validation Engine execution failed: {val_err}")

    except Exception as comp_err:
        err_msg = f"Unexpected compiler error: {str(comp_err)}"
        executor.compilation_metrics["compilation_failed_count"] += 1
        executor.compilation_metrics["grounding_failures"] += 1
        executor.compilation_metrics["failure_reasons"][err_msg] = (
            executor.compilation_metrics["failure_reasons"].get(err_msg, 0) + 1
        )

    return DailyValidationResult(
        prior_prediction_result=prior_prediction_result,
        prior_attribution=attribution,
        newly_retired_count=newly_retired_count,
    )
