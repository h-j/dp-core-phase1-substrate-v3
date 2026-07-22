"""
Step module for theory generation, mutation, dialectical synthesis, reflection processing,
contradiction detection, and theory usefulness evaluation in cognitive replay.
"""

import copy
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from cognition.schemas.knowledge.ontology import OntologyRegistry
from cognition.schemas.theory.theory import Branch, MechanismComponent, TheoryStructured
from flows.knowledge_flow.mechanism_engine import match_and_register_in_registry

logger = logging.getLogger("replay_engine.step_theory")


def count_conditional_clauses(theory_structured) -> int:
    count = 0
    if theory_structured:
        if getattr(theory_structured, "if_branch", None) and getattr(
            theory_structured.if_branch, "condition", None
        ):
            count += 1
        if getattr(theory_structured, "else_branch", None) and getattr(
            theory_structured.else_branch, "condition", None
        ):
            count += 1
        if (
            getattr(theory_structured, "unless", None)
            and theory_structured.unless != "no contrary evidence emerges"
        ):
            count += 1
    return count


@dataclass
class DailyTheoryResult:
    theory: Any
    validation: Any
    reflection: Any
    contradiction_result: Dict[str, Any]
    theory_usefulness: Dict[str, Any]
    intelligence_metadata: Dict[str, Any]
    lineage_record: Any
    lineage_id_val: str
    audit_created: bool
    audit_mutated: bool
    audit_merged: bool
    audit_revived: bool
    audit_retired: bool
    dialectical_data: Optional[Dict[str, Any]]
    active_synthesis: Optional[str]


def process_daily_theory(
    executor: Any,
    day_idx: int,
    date_str: str,
    obs_data: Dict[str, Any],
    market_obs: Any,
    abstraction: Any,
    horizon_view: Any,
    horizon_context: str,
    regime_matches: List[Any],
    regime_context: str,
    regime_subtype: str,
    vol_regime: str,
    mom_regime: str,
    persistence_3d: float,
    persistence_5d: float,
    persistence_10d: float,
    reg_5d: str,
    historical_context: str,
    recent_theories: List[Any],
    recent_validations: List[Any],
    recent_reflections: List[Any],
    prior_theory: Optional[Any],
    prior_attribution: Optional[Any],
    world_model_narrative: str,
    active_principles: List[Any],
    active_open_questions: List[Any],
    relevant_lessons: List[Any],
    regime_history: str,
    active_synthesis: Optional[str],
    falsifiability_conditions: List[str],
    last_lineage_id: str,
    degraded_steps: List[Dict[str, Any]],
) -> DailyTheoryResult:
    """Processes daily theory lifecycle: novelty gating, mechanism mutation, generation, reflection & contradiction."""
    prior_pred_obj = executor._prior_prediction
    prior_pred_res_obj = getattr(executor, "_prior_prediction_result", None)

    decision = "GENERATE"
    novelty_score = 1.0
    novelty_rationale = ""

    if prior_theory:
        decision, novelty_score, novelty_rationale = (
            executor.novelty_gate.is_novel(
                observation=market_obs,
                regime_subtype=regime_subtype,
                prior_theory=prior_theory,
                prior_prediction=prior_pred_obj,
                prior_prediction_result=prior_pred_res_obj,
                prior_attribution=prior_attribution,
                active_principles=active_principles,
                active_lessons=relevant_lessons,
            )
        )
    executor.novelty_decision_history.append(decision)

    daily_theory_word_count = 0
    daily_mechanism_count = 0
    daily_conditional_clauses_count = 0
    daily_exceptions_added = 0
    daily_mechanisms_retired = 0
    daily_mechanisms_added = 0
    daily_mechanisms_modified = 0
    daily_mechanism_stability = 1.0
    daily_words_before_mutation = 0
    daily_words_after_mutation = 0
    daily_mechanisms_before_mutation = 0
    daily_mechanisms_after_mutation = 0

    branch_stats = {"generated": 0}

    if decision == "REINFORCE":
        executor._log(
            f"[NOVELTY GATE] Decision: REINFORCE | Score: {novelty_score:.2f} | {novelty_rationale}"
        )
        theory = copy.deepcopy(prior_theory)
        theory.id = str(uuid4())

        daily_theory_word_count = len(theory.summary.split()) if theory.summary else 0
        daily_mechanism_count = (
            len(theory.summary_structured.mechanism_components)
            if (theory.summary_structured and theory.summary_structured.mechanism_components)
            else 0
        )
        daily_conditional_clauses_count = count_conditional_clauses(theory.summary_structured)
        daily_exceptions_added = (
            1
            if (
                theory.summary_structured
                and theory.summary_structured.unless
                and theory.summary_structured.unless != "no contrary evidence emerges"
            )
            else 0
        )
        daily_mechanisms_retired = 0
        daily_mechanisms_added = 0
        daily_mechanisms_modified = 0
        daily_mechanism_stability = 1.0

    elif decision == "REVISE":
        executor._log(
            f"[NOVELTY GATE] Decision: REVISE | Score: {novelty_score:.2f} | {novelty_rationale}"
        )
        try:
            if not prior_theory.summary_structured:
                prior_theory.summary_structured = TheoryStructured(
                    claim=prior_theory.summary,
                    if_branch=Branch(condition="always", action="observe"),
                    else_branch=Branch(condition="never", action="ignore"),
                    falsified_if="never",
                    mechanism_components=[],
                )

            for idx, comp in enumerate(prior_theory.summary_structured.mechanism_components):
                if not comp.mechanism_id:
                    comp.mechanism_id = f"MECH_{idx+1:03d}"

            prior_mechs = []
            for comp in prior_theory.summary_structured.mechanism_components:
                prior_mechs.append(
                    {
                        "mechanism_id": comp.mechanism_id,
                        "component_id": comp.component_id,
                        "description": comp.description,
                        "observable": comp.observable,
                        "expected_behavior": comp.expected_behavior,
                        "concept_tags": comp.concept_tags,
                        "relation_type": comp.relation_type,
                    }
                )
            prior_mechs_str = json.dumps(prior_mechs, indent=2)

            failed_comps = prior_attribution.components_failed if prior_attribution else []
            passed_comps = getattr(prior_attribution, "components_passed", []) if prior_attribution else []
            root_cause = getattr(prior_attribution, "root_cause_component", "Unknown") if prior_attribution else "Unknown"
            attr_reasoning = getattr(prior_attribution, "attribution_reasoning", "No attribution reasoning available.") if prior_attribution else "No attribution reasoning available."

            prompt_stage1 = f"""You are the DP theory mechanism mutation engine.
Your objective is to revise the current set of mechanism components to resolve the observed contradictions and better explain today's market behavior.

=== CURRENT MECHANISM COMPONENTS ===
{prior_mechs_str}

=== OBSERVED CONTRADICTIONS & FAILURES ===
- Failed/Falsified components: {failed_comps}
- Passed/Validated components: {passed_comps}
- Root cause component of failure: {root_cause}
- Causal analysis: {attr_reasoning}

=== CURRENT MARKET OBSERVATION ===
Observation: {market_obs.observation_text}
Regime Subtype: {regime_subtype}

=== REVISION RULES ===
1. Remove falsified mechanisms (removed_mechanism_ids must include them).
2. Promote mechanisms supported by new evidence.
3. Demote weakened mechanisms.
4. Add a new mechanism only if today's evidence cannot be explained by the existing set.
5. Merge duplicate mechanisms whenever possible.
6. Prefer simpler explanations over more complex ones.
7. Never increase complexity unless the new evidence absolutely requires it.
8. Every mechanism component must use allowed concept_tags and relation_type:
   - Core Concepts: {OntologyRegistry.CORE_CONCEPTS}
   - Relation Types: {OntologyRegistry.RELATION_TYPES}

You MUST return a JSON object conforming exactly to this structure:
{{
  "retained_mechanism_ids": ["string"],
  "removed_mechanism_ids": ["string"],
  "added_mechanisms": [
    {{
      "component_id": "string (snake_case)",
      "description": "string",
      "observable": "string",
      "expected_behavior": "string",
      "dependency": "string or null",
      "concept_tags": ["string"],
      "relation_type": "string"
    }}
  ],
  "modified_mechanisms": [
    {{
      "mechanism_id": "string",
      "component_id": "string",
      "description": "string",
      "observable": "string",
      "expected_behavior": "string",
      "dependency": "string or null",
      "concept_tags": ["string"],
      "relation_type": "string"
    }}
  ],
  "if_branch": {{"condition": "string", "action": "string"}},
  "else_branch": {{"condition": "string", "action": "string"}},
  "unless": "string",
  "falsified_if": "string",
  "falsification_conditions": ["string (format 'component_id: condition')"],
  "reasons_for_changes": {{
    "mechanism_id_or_new": "string reason..."
  }}
}}
"""
            res_raw = executor.theory_flow.client.generate(prompt_stage1, json_format=True)
            res = json.loads(res_raw)

            retained_ids = res.get("retained_mechanism_ids", [])
            removed_ids = res.get("removed_mechanism_ids", [])
            added_mechs = res.get("added_mechanisms", [])
            modified_mechs = res.get("modified_mechanisms", [])

            total_before = len(prior_theory.summary_structured.mechanism_components)
            ret_count = 0
            add_count = len(added_mechs)
            mod_count = len(modified_mechs)

            new_components = []
            modified_by_id = {m["mechanism_id"]: m for m in modified_mechs if "mechanism_id" in m}

            for comp in prior_theory.summary_structured.mechanism_components:
                if comp.mechanism_id in removed_ids:
                    continue

                if comp.mechanism_id in retained_ids or comp.mechanism_id in modified_by_id:
                    ret_count += 1
                    if comp.mechanism_id in modified_by_id:
                        mod_data = modified_by_id[comp.mechanism_id]
                        updated_comp = MechanismComponent(
                            component_id=mod_data.get("component_id", comp.component_id),
                            description=mod_data.get("description", comp.description),
                            observable=mod_data.get("observable", comp.observable),
                            expected_behavior=mod_data.get("expected_behavior", comp.expected_behavior),
                            dependency=mod_data.get("dependency", comp.dependency),
                            concept_tags=mod_data.get("concept_tags", comp.concept_tags),
                            relation_type=mod_data.get("relation_type", comp.relation_type),
                            mechanism_id=comp.mechanism_id,
                        )
                        new_components.append(updated_comp)

                        mech_obj = executor.knowledge_repository.get_mechanism(comp.mechanism_id)
                        if mech_obj:
                            mech_obj.times_modified += 1
                            mech_obj.last_seen = day_idx
                            if regime_subtype not in mech_obj.regimes_seen:
                                mech_obj.regimes_seen.append(regime_subtype)
                            executor.knowledge_repository.save_mechanism(mech_obj)
                    else:
                        new_components.append(comp)

            for add_data in added_mechs:
                mech_id = match_and_register_in_registry(
                    add_data,
                    executor.knowledge_repository,
                    step=day_idx,
                    regime=regime_subtype,
                )
                new_comp = MechanismComponent(
                    component_id=add_data.get("component_id", "new_mechanism"),
                    description=add_data.get("description", ""),
                    observable=add_data.get("observable", ""),
                    expected_behavior=add_data.get("expected_behavior", ""),
                    dependency=add_data.get("dependency"),
                    concept_tags=add_data.get("concept_tags", []),
                    relation_type=add_data.get("relation_type"),
                    mechanism_id=mech_id,
                )
                new_components.append(new_comp)

            final_mechs = [
                {
                    "mechanism_id": comp.mechanism_id,
                    "component_id": comp.component_id,
                    "description": comp.description,
                    "expected_behavior": comp.expected_behavior,
                }
                for comp in new_components
            ]
            final_mechs_str = json.dumps(final_mechs, indent=2)

            prompt_stage2 = f"""You are a scientific rendering model.
Your task is to write a concise scientific hypothesis summarizing the current market regime based ONLY on the following active mechanisms.

=== ACTIVE MECHANISMS ===
{final_mechs_str}

=== REGIME SUBTYPE ===
{regime_subtype}

=== INSTRUCTIONS ===
- Write a concise scientific hypothesis.
- Maximum 35 words.
- No historical explanation.
- No implementation details.
- No exceptions unless essential.
- One causal claim only.
- Respond with ONLY the hypothesis text. No headings, no markdown, no quotes, no JSON.
"""
            concise_narrative = executor.theory_flow.client.generate(prompt_stage2, json_format=False).strip()
            concise_narrative = concise_narrative.strip('"').strip("'").strip()

            theory = copy.deepcopy(prior_theory)
            theory.id = str(uuid4())
            if theory.summary_structured:
                theory.summary_structured.id = str(uuid4())
                theory.summary_structured.created_at = datetime.now(timezone.utc)

            def to_str(val, default="") -> str:
                if val is None:
                    return default
                if isinstance(val, list):
                    return ", ".join(str(x) for x in val)
                return str(val)

            def to_branch(branch_val, default_branch) -> Branch:
                if isinstance(branch_val, dict):
                    return Branch(
                        condition=to_str(branch_val.get("condition"), default_branch.condition),
                        action=to_str(branch_val.get("action"), default_branch.action),
                    )
                return default_branch

            theory.summary_structured.claim = concise_narrative
            theory.summary_structured.mechanism_components = new_components
            theory.summary_structured.if_branch = to_branch(res.get("if_branch"), theory.summary_structured.if_branch)
            theory.summary_structured.else_branch = to_branch(res.get("else_branch"), theory.summary_structured.else_branch)
            theory.summary_structured.unless = to_str(res.get("unless"), theory.summary_structured.unless)
            theory.summary_structured.falsified_if = to_str(res.get("falsified_if"), theory.summary_structured.falsified_if)
            theory.summary_structured.falsification_conditions = res.get("falsification_conditions", theory.summary_structured.falsification_conditions)

            theory.summary = concise_narrative
            theory.thesis = concise_narrative

            daily_theory_word_count = len(concise_narrative.split())
            daily_mechanism_count = len(new_components)
            daily_conditional_clauses_count = count_conditional_clauses(theory.summary_structured)
            daily_exceptions_added = 1 if (theory.summary_structured.unless and theory.summary_structured.unless != "no contrary evidence emerges") else 0
            daily_mechanisms_retired = len(removed_ids)
            daily_mechanisms_added = add_count
            daily_mechanisms_modified = mod_count
            daily_mechanism_stability = (ret_count / total_before) if total_before > 0 else 1.0
            daily_words_before_mutation = len(prior_theory.summary.split()) if (prior_theory and prior_theory.summary) else 0
            daily_words_after_mutation = len(concise_narrative.split())
            daily_mechanisms_before_mutation = len(prior_theory.summary_structured.mechanism_components) if (prior_theory and prior_theory.summary_structured and prior_theory.summary_structured.mechanism_components) else 0
            daily_mechanisms_after_mutation = len(new_components)

        except Exception as e:
            print(f"WARNING: Mechanism-First Theory Revision failed: {e}. Falling back to standard generation.")
            decision = "GENERATE"

    if decision == "GENERATE":
        executor._log(f"[NOVELTY GATE] Decision: GENERATE | Score: {novelty_score:.2f} | {novelty_rationale}")
        theory, branch_stats = executor.theory_flow.process(
            abstraction,
            historical_context=historical_context,
            market_memory_context=regime_context,
            current_market_observation=market_obs.observation_text,
            reflective_memory_summary=horizon_context,
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
            analog_divergence_claim=getattr(market_obs, "analog_divergence_claim", ""),
            regime_history=regime_history,
            dialectical_synthesis=active_synthesis,
            relevant_lessons=relevant_lessons,
            prior_theory=prior_theory,
            prior_attribution=prior_attribution,
            world_model_narrative=world_model_narrative,
            active_principles=active_principles,
            active_open_questions=active_open_questions,
            step=day_idx,
            knowledge_repository=executor.knowledge_repository,
        )

        daily_theory_word_count = len(theory.summary.split()) if theory.summary else 0
        daily_mechanism_count = len(theory.summary_structured.mechanism_components) if (theory.summary_structured and theory.summary_structured.mechanism_components) else 0
        daily_conditional_clauses_count = count_conditional_clauses(theory.summary_structured)
        daily_exceptions_added = 1 if (theory.summary_structured and theory.summary_structured.unless and theory.summary_structured.unless != "no contrary evidence emerges") else 0
        daily_mechanisms_retired = 0
        daily_mechanisms_added = len(theory.summary_structured.mechanism_components) if (theory.summary_structured and theory.summary_structured.mechanism_components) else 0
        daily_mechanisms_modified = 0
        daily_mechanism_stability = 1.0

    if executor.lineage_debug:
        theory_text = theory.summary_structured.claim if theory.summary_structured else theory.summary
        print("[Theory Output]", theory_text[:250])

    theory_step_info = {"created": 0, "mutated": 0, "merged": 0, "retired": 0, "revived": 0}
    lineage_record = None
    lineage_id_val = "N/A"
    audit_created = False
    audit_mutated = False
    audit_merged = False
    audit_revived = False
    audit_retired = False
    exp_create_called = False
    exp_attach_called = False
    exp_close_called = False

    abstraction_text = getattr(abstraction, "abstraction_summary", str(abstraction))
    try:
        if executor.theory_lineage:
            lineage_result = executor.theory_lineage.evolve_theory(
                abstraction=abstraction_text,
                confidence_state={
                    "empirical_confidence": getattr(theory.confidence_state, "empirical_confidence", 0.5),
                    "regime_confidence": getattr(theory.confidence_state, "regime_confidence", 0.5),
                    "reflection_confidence": getattr(theory.confidence_state, "reflection_confidence", 0.5),
                    "theoretical_coherence": getattr(theory.confidence_state, "theoretical_coherence", 0.5),
                    "contradiction_pressure": getattr(theory.confidence_state, "contradiction_pressure", 0.0),
                },
                step=day_idx,
            )
            lineage_record = lineage_result["record"]
            lineage_id_val = lineage_result.get("lineage_id", "N/A")
            theory.lineage_id = lineage_id_val
            audit_created = lineage_result.get("created", False)
            audit_mutated = lineage_result.get("mutated", False)
            audit_merged = lineage_result.get("merged", False)
            audit_revived = lineage_result.get("revived", False)

            theory_step_info["created"] = int(lineage_result["created"])
            theory_step_info["mutated"] = int(lineage_result["mutated"])
            theory_step_info["merged"] = int(lineage_result["merged"])

            if lineage_record:
                if lineage_result.get("created"):
                    regime_context_list = executor._build_experience_regime_context(
                        market_obs, obs_data, regime_subtype
                    )
                    executor.experience_engine.create_experience(
                        theory_id=theory.id,
                        lineage_id=lineage_id_val,
                        date=date_str,
                        regime_context=regime_context_list,
                        theory_subtype=regime_subtype,
                    )
                    exp_create_called = True
                elif lineage_result.get("mutated") or lineage_result.get("merged"):
                    executor.experience_engine.attach_theory(lineage_id_val, theory.id)
                    exp_attach_called = True

            if lineage_record and lineage_record.confidence_state:
                theory.confidence_state.empirical_confidence = lineage_record.confidence_state.get("empirical_confidence", 0.5)
                theory.confidence_state.regime_confidence = lineage_record.confidence_state.get("regime_confidence", 0.5)
                theory.confidence_state.reflection_confidence = lineage_record.confidence_state.get("reflection_confidence", 0.5)
                theory.confidence_state.theoretical_coherence = lineage_record.confidence_state.get("theoretical_coherence", 0.5)
                theory.confidence_state.contradiction_pressure = lineage_record.confidence_state.get("contradiction_pressure", 0.0)
    except Exception as e:
        executor._log(f"WARNING: Theory lineage evolution failed for day {date_str}: {e}")

    # Contradiction detection
    contradiction_result = executor.contradiction_detector.detect(
        current_theory=theory,
        historical_theories=recent_theories,
        validations=recent_validations,
        reflections=recent_reflections,
        current_observation=market_obs,
        historical_observations=executor._run_market_observations[-5:],
    )

    try:
        if executor.contradiction_registry and lineage_record:
            descriptions = contradiction_result.get("indicators", [])
            executor.contradiction_registry.register_contradictions(
                theory_id=lineage_record.id,
                descriptions=descriptions,
                severity=float(contradiction_result.get("score", 0.0)),
                step=day_idx,
            )
            if descriptions:
                executor.theory_lineage.record_contradictions(
                    tid=lineage_record.id,
                    descriptions=descriptions,
                    step=day_idx,
                )

        if hasattr(executor, "contradiction_graph") and executor.contradiction_graph and recent_theories:
            prior_theory = recent_theories[-1]
            prior_id = getattr(prior_theory, "id", str(prior_theory))
            curr_id = getattr(theory, "id", str(theory))
            if prior_id != curr_id:
                executor.contradiction_graph.add_contradiction(
                    source_theory_id=curr_id,
                    target_theory_id=prior_id,
                    contradiction_type="EMPIRICAL",
                    supporting_evidence=contradiction_result.get("indicators", []),
                    confidence=float(contradiction_result.get("score", 0.5)),
                    step=day_idx,
                )
                if hasattr(executor, "contradiction_resolver") and executor.contradiction_resolver:
                    theory_ctx = {
                        curr_id: {"confidence": getattr(getattr(theory, "confidence_state", None), "empirical_confidence", 0.5)},
                        prior_id: {"confidence": getattr(getattr(prior_theory, "confidence_state", None), "empirical_confidence", 0.5)},
                    }
                    executor.contradiction_resolver.resolve_conflicts(executor.contradiction_graph, theory_ctx, day_idx)

                executor.experience_engine.record_contradiction(
                    lineage_id_val, signatures=descriptions
                )
    except Exception as _exc:
        logger.error(
            "[ReplayExecutor] day=%d CRITICAL: contradiction registration failed: %s",
            day_idx, _exc, exc_info=True
        )
        degraded_steps.append({"day": day_idx, "op": "contradiction_registration", "error": str(_exc)})

    # Dialectical synthesis trigger
    contradiction_score = float(contradiction_result.get("score", 0.0))
    active_lineage_records = executor.theory_lineage.active_theories() if executor.theory_lineage else []
    active_theory_count = len(active_lineage_records)
    will_trigger = (
        active_theory_count >= 2
        and contradiction_score >= executor.contradiction_detector.CONFIG.get("threshold_synthesis", 0.35)
    )

    dialectical_data = None
    if will_trigger:
        executor.total_synthesis_triggered += 1
        component_failures = {}
        if hasattr(executor, "experience_repo") and executor.experience_repo:
            try:
                for exp in executor.experience_repo.get_all():
                    if getattr(exp, "theory_subtype", None) == regime_subtype:
                        f_counts = getattr(exp, "component_failure_counts", {}) or {}
                        for comp, count in f_counts.items():
                            component_failures[comp] = component_failures.get(comp, 0) + count
            except Exception as e:
                logger.warning(f"Failed to aggregate experience failures: {e}")

        dialectical_data = executor.dialectical_synthesizer.synthesize(
            observation_text=market_obs.observation_text,
            active_theories=active_lineage_records,
            contradiction_indicators=contradiction_result.get("indicators", []),
            regime_subtype=regime_subtype,
            falsifiability_conditions=falsifiability_conditions,
            relevant_lessons=relevant_lessons,
            component_failures=component_failures,
        )

    # Retire stale theories
    try:
        if executor.theory_lineage:
            contra_score = float(contradiction_result.get("score", 0.0))
            is_new_lineage = (lineage_record.created_at_step == day_idx) if lineage_record else False

            if not is_new_lineage or contra_score > 0.8:
                retired_records = executor.theory_lineage.retire_stale_theories(
                    step=day_idx,
                    contradiction_severity=contra_score,
                    current_record_id=(lineage_record.id if lineage_record else None),
                )
            else:
                retired_records = []

            theory_step_info["retired"] = len(retired_records)
            if executor.contradiction_registry:
                for retired_record in retired_records:
                    executor.experience_engine.close_experience(
                        retired_record.lineage_id,
                        date_str,
                        f"Theory lineage {retired_record.id} retired after {retired_record.survival_steps} steps.",
                    )
                    exp_close_called = True
                    executor.contradiction_registry.resolve_for_theory(
                        retired_record.id, day_idx
                    )
            audit_retired = len(retired_records) > 0
    except Exception as _exc:
        logger.error(
            "[ReplayExecutor] day=%d CRITICAL: theory retirement failed: %s",
            day_idx, _exc, exc_info=True
        )
        degraded_steps.append({"day": day_idx, "op": "theory_retirement", "error": str(_exc)})

    # Revive matching theories
    try:
        if executor.theory_lineage:
            revived_records = executor.theory_lineage.revive_matching_theories(
                abstraction=abstraction_text, step=day_idx
            )
            audit_revived = len(revived_records) > 0
            theory_step_info["revived"] = len(revived_records)
            for revived_record in revived_records:
                executor.experience_engine.attach_theory(revived_record.lineage_id, theory.id)
                exp_attach_called = True
    except Exception as _exc:
        logger.error(
            "[ReplayExecutor] day=%d CRITICAL: theory revival failed: %s",
            day_idx, _exc, exc_info=True
        )
        degraded_steps.append({"day": day_idx, "op": "theory_revival", "error": str(_exc)})

    action = "none"
    if exp_create_called:
        action = "create"
    elif exp_attach_called:
        action = "attach"
    elif exp_close_called:
        action = "close"

    executor._lineage_audit_table.append(
        {
            "day": date_str,
            "lineage_id": lineage_id_val,
            "created": audit_created,
            "mutated": audit_mutated,
            "merged": audit_merged,
            "revived": audit_revived,
            "experience_action": action,
        }
    )

    from cognition.schemas.validation.validation_event import ValidationEvent

    validation = ValidationEvent(
        theory_id=theory.id,
        validation_summary=f"Replay validation. {horizon_context}. {regime_context}",
        observed_behavior=market_obs.observation_text,
        expected_behavior="Market-grounded theory",
    )

    reflection = executor.reflection_flow.process(
        theory,
        validation,
        contradiction_result=contradiction_result,
        market_observation=market_obs,
        regime_subtype=regime_subtype,
        falsifiability_conditions=falsifiability_conditions,
        analog_divergence_claim=getattr(market_obs, "analog_divergence_claim", ""),
        theory_regime_subtype=getattr(theory, "regime_subtype", "neutral"),
        theory_falsifiability_conditions=getattr(theory, "falsifiability_conditions", []),
        regime_history=regime_history,
        dialectical_synthesis=(
            executor.dialectical_synthesizer.format_for_reflection(dialectical_data)
            if dialectical_data
            else None
        ),
    )

    theory_usefulness = {"score": 0.0, "label": "unknown"}
    try:
        if executor.epistemic_scoring and lineage_record:
            theory_usefulness = executor.epistemic_scoring.score_theory(
                lineage_record=lineage_record,
                regime_matches=regime_matches,
                prior_prediction_result=(
                    prior_pred_res_obj.to_dict() if prior_pred_res_obj else {}
                ),
                contradiction_score=float(contradiction_result.get("score", 0.0)),
                reflection_summary=reflection.reflection_summary,
            )
    except Exception as _exc:
        logger.warning(
            "[ReplayExecutor] day=%d theory_usefulness evaluation failed: %s — defaulting to 0.0",
            day_idx, _exc
        )
        theory_usefulness = {"score": 0.0, "label": "unknown"}

    active_exp = None
    if lineage_record and lineage_id_val != "N/A":
        active_exp = executor.experience_repo.load_by_lineage(lineage_id_val)

    intelligence_metadata = {
        "directional_persistence": {
            "3d": persistence_3d,
            "5d": persistence_5d,
            "10d": persistence_10d,
            "regime": reg_5d,
        },
        "mutation_count": active_exp.mutation_count if active_exp else 0,
        "theory_mutation_count": lineage_record.mutation_count if lineage_record else 0,
        "contradiction_count": active_exp.contradiction_count if active_exp else 0,
        "lineage_id": lineage_id_val,
        "theory_id": theory.id,
        "regime_history": regime_history,
    }

    try:
        from memory.provenance import ReasoningProvenance
        theory.reasoning_provenance = ReasoningProvenance(
            observations_used=[f"OBS_{date_str}"],
            mechanisms_used=[
                m.description
                for m in getattr(getattr(theory, "summary_structured", None), "mechanism_components", [])
                if hasattr(m, "description")
            ],
            retrieved_memories=[
                {"date": getattr(m, "date", "unknown"), "similarity": getattr(m, "similarity", 0.0)}
                for m in (regime_matches or [])
            ],
            reflections_consulted=[getattr(reflection, "summary", "")] if reflection else [],
            validation_results_incorporated=[getattr(validation, "id", "")] if validation else [],
        )
    except Exception:
        pass

    try:
        from core.event_bus import get_event_bus
        from core.events import (
            MechanismGenerated,
            ReflectionCompleted,
            TheoryCreated,
            TheoryRetired,
        )

        bus = get_event_bus()

        if audit_created or audit_mutated:
            if hasattr(executor, "predicate_engine") and executor.predicate_engine:
                executor.predicate_engine.form_predicate(theory=theory, step=day_idx, evaluation_window=1)

            bus.publish(
                TheoryCreated(
                    theory_id=getattr(theory, "id", f"TH_{day_idx}"),
                    statement=getattr(theory, "summary", "Generated theory"),
                    confidence=float(getattr(getattr(theory, "confidence_state", None), "empirical_confidence", 0.5)),
                ),
                publisher="step_theory",
            )
            bus.publish(
                MechanismGenerated(
                    mechanism_id=f"MECH_{uuid4().hex[:8]}",
                    description=getattr(theory, "summary", "Generated mechanism"),
                    confidence=float(getattr(getattr(theory, "confidence_state", None), "empirical_confidence", 0.5)),
                ),
                publisher="step_theory",
            )

        if audit_retired:
            bus.publish(
                TheoryRetired(
                    theory_id=getattr(theory, "id", f"TH_{day_idx}"),
                    reason="Theory retired in step_theory",
                ),
                publisher="step_theory",
            )

        if reflection:
            bus.publish(
                ReflectionCompleted(
                    reflection_id=getattr(reflection, "id", f"REFL_{day_idx}"),
                    insights=[getattr(reflection, "summary", "Reflection cycle completed")],
                ),
                publisher="step_theory",
            )
    except Exception as _evt_exc:
        pass

    return DailyTheoryResult(
        theory=theory,
        validation=validation,
        reflection=reflection,
        contradiction_result=contradiction_result,
        theory_usefulness=theory_usefulness,
        intelligence_metadata=intelligence_metadata,
        lineage_record=lineage_record,
        lineage_id_val=lineage_id_val,
        audit_created=audit_created,
        audit_mutated=audit_mutated,
        audit_merged=audit_merged,
        audit_revived=audit_revived,
        audit_retired=audit_retired,
        dialectical_data=dialectical_data,
        active_synthesis=active_synthesis,
    )
