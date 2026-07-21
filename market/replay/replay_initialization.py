"""
Initialization and context helper module for ReplayExecutor.
"""

import logging
import os
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger("replay_engine.initialization")


def initialize_flows(executor: Any):
    """Lazy initialize cognition flows and repositories on ReplayExecutor."""
    if executor.flows_initialized:
        return

    from cognition.confidence.confidence_evolution_engine import ConfidenceEvolutionEngine
    from cognition.contradiction.contradiction_detector import ContradictionDetector
    from flows.observation_flow.abstraction_flow import AbstractionFlow
    from flows.proposition_flow.proposition_compiler import MarketPropositionCompiler
    from flows.reflection_flow.reflection_flow import ReflectionFlow
    from flows.theory_flow.dialectical_synthesizer import DialecticalTheorySynthesizer
    from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
    from memory.relational.repositories.abstraction_repository import AbstractionRepository
    from memory.relational.repositories.canonical_semantic_proposition_repository import (
        CanonicalSemanticPropositionRepository,
    )
    from memory.relational.repositories.compiled_proposition_repository import (
        CompiledPropositionRepository,
    )
    from memory.relational.repositories.confidence_repository import ConfidenceRepository
    from memory.relational.repositories.observation_repository import ObservationRepository
    from memory.relational.repositories.prediction_repository import PredictionRepository
    from memory.relational.repositories.prediction_result_repository import PredictionResultRepository
    from memory.relational.repositories.reflection_repository import ReflectionRepository
    from memory.relational.repositories.theory_repository import TheoryRepository
    from memory.relational.repositories.transition_pressure_repository import TransitionPressureRepository
    from memory.relational.repositories.validation_repository import ValidationRepository

    executor.abstraction_flow = AbstractionFlow()
    executor.theory_flow = TheoryGenerationFlow()
    executor.reflection_flow = ReflectionFlow(verbose=executor.verbose)
    executor.dialectical_synthesizer = DialecticalTheorySynthesizer()
    executor.attribution_engine.llm = executor.theory_flow.client
    executor.contradiction_detector = ContradictionDetector(verbose=executor.verbose)
    executor.theory_flow.debug = executor.lineage_debug
    executor.confidence_engine = ConfidenceEvolutionEngine()

    executor.observation_repo = ObservationRepository()
    executor.abstraction_repo = AbstractionRepository()
    executor.theory_repo = TheoryRepository()
    executor.validation_repo = ValidationRepository()
    executor.reflection_repo = ReflectionRepository()
    executor.confidence_repo = ConfidenceRepository()

    executor.prediction_repo = PredictionRepository()
    executor.prediction_result_repo = PredictionResultRepository()
    executor.transition_pressure_repo = TransitionPressureRepository()

    try:
        from memory.relational.repositories.market_outcome_repository import MarketOutcomeRepository
        executor.market_outcome_repo = MarketOutcomeRepository()
    except (ImportError, ModuleNotFoundError):
        executor._log("WARNING: MarketOutcomeRepository missing; optional persistence disabled.")
        executor.market_outcome_repo = None

    executor.proposition_compiler = MarketPropositionCompiler(client=executor.theory_flow.client)
    from flows.proposition_flow.validation_engine import ValidationEngine
    executor.validation_engine = ValidationEngine()
    executor.compiled_proposition_repo = CompiledPropositionRepository()
    executor.canonical_semantic_proposition_repo = CanonicalSemanticPropositionRepository()

    from flows.proposition_flow.belief_dynamics_engine import BeliefDynamicsEngine
    from flows.proposition_flow.pattern_consolidation_engine import PatternConsolidationEngine
    from memory.relational.repositories.belief_state_repository import BeliefStateRepository

    executor.belief_state_repo = BeliefStateRepository()
    executor.belief_dynamics_engine = BeliefDynamicsEngine(
        belief_repo=executor.belief_state_repo,
        learning_rate=0.15,
        uncertainty_rate=0.10,
        decay_rate=0.01,
    )
    executor.pattern_consolidation_engine = PatternConsolidationEngine(
        min_validations=executor.min_validations_for_lesson,
        min_temporal_span=executor.min_temporal_span_for_lesson,
        min_confidence=executor.min_confidence_for_lesson,
        max_uncertainty=executor.max_uncertainty_for_lesson,
        min_success_rate=executor.min_success_rate_for_lesson,
        belief_repo=executor.belief_state_repo,
        val_record_repo=executor.validation_record_repo,
        comp_prop_repo=executor.compiled_proposition_repo,
    )

    executor.flows_initialized = True


def restart_clean(executor: Any):
    """Clean all tables, experience files, snapshots, and decision journal files."""
    executor._log("\n======================================================================")
    executor._log("RESTART REPLAY: Clearing all database records and generated artifacts...")
    executor._log("======================================================================\n")

    try:
        from memory.relational.base import Base
        from memory.relational.postgres_client import engine

        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        executor._log("✓ PostgreSQL database tables dropped and recreated successfully.")
    except Exception as e:
        executor._log(f"⚠ PostgreSQL drop/recreate tables failed: {e}")

    try:
        if hasattr(executor, "experience_repo") and executor.experience_repo:
            executor.experience_repo.clear()
            executor._log("✓ Experience JSON files cleared via repository.")
        else:
            exp_dir = Path(__file__).parent.parent.parent / "data" / "experiences"
            if exp_dir.exists():
                for f in exp_dir.glob("*.json"):
                    try:
                        f.unlink()
                    except Exception:
                        pass
                executor._log("✓ Experience JSON files cleared.")
    except Exception as e:
        executor._log(f"⚠ Failed to clear experience JSON files: {e}")

    snap_dirs = [
        executor.replay_dir / "logs",
        executor.base_output_dir / "propositions",
        executor.base_output_dir / "canonical_propositions",
        executor.base_output_dir / "validation_records",
    ]
    for d in snap_dirs:
        if d.exists():
            for f in d.glob("*.json"):
                try:
                    f.unlink()
                except Exception as e:
                    executor._log(f"⚠ Failed to delete snapshot file {f}: {e}")

    if hasattr(executor, "decision_journal") and executor.decision_journal:
        executor.decision_journal.clear()
        executor._log("✓ Decision journal records cleared via journal class.")
    else:
        dj_dir = Path(__file__).parent.parent.parent / "data" / "decision_journal"
        if dj_dir.exists():
            for f in dj_dir.glob("*.json"):
                try:
                    f.unlink()
                except Exception:
                    pass
            executor._log("✓ Decision journal JSON files cleared.")


def format_regime_context(regime_matches: List[Any]) -> str:
    """Formats top regime match into context string."""
    if not regime_matches:
        return "Regime Context: No historical regime matches found (first encounter)."

    match = regime_matches[0]
    sim = getattr(match, "similarity", 0.0) if not isinstance(match, dict) else match.get("similarity", 0.0)
    m_date = getattr(match, "date", "N/A") if not isinstance(match, dict) else match.get("date", "N/A")
    m_subtype = getattr(match, "regime_subtype", "mixed") if not isinstance(match, dict) else match.get("regime_subtype", "mixed")
    return f"Regime Context: High similarity ({sim:.2f}) to prior historical period on {m_date} ({m_subtype} regime)."


def format_historical_context(recent_validations: List[Any], recent_reflections: List[Any]) -> str:
    """Formats recent validations and reflections into prompt context."""
    val_texts = [f"- {v.validation_summary}" for v in recent_validations]
    ref_texts = [f"- {r.reflection_summary}" for r in recent_reflections]
    return f"Recent Validations:\n" + "\n".join(val_texts) + "\n\nRecent Reflections:\n" + "\n".join(ref_texts)


def process_closed_loop_belief_updates(executor: Any, day_idx: int):
    """Executes Milestone 10 closed-loop belief updates."""
    if day_idx <= 0:
        return

    prior_step = day_idx - 1
    if executor.lineage_debug:
        print(f"\n--- CLOSED-LOOP BELIEF UPDATE (Step {prior_step} -> Step {day_idx}) ---")

    compiled_props = executor.compiled_proposition_repo.query_by_replay_step(prior_step)
    val_records = executor.validation_record_repo.query_by_replay_step(prior_step)

    if executor.lineage_debug:
        print(f"Found {len(compiled_props)} compiled propositions from Step {prior_step}.")

    for comp_prop in compiled_props:
        prop_val_records = [vr for vr in val_records if vr.proposition_id == comp_prop.id]
        for vr in prop_val_records:
            try:
                executor.belief_dynamics_engine.process_validation(
                    val_record=vr,
                    compiled_prop=comp_prop,
                    history_df=executor.engine.data,
                    current_step=day_idx,
                )
            except Exception as _exc:
                logger.debug(f"Belief transition event processing skipped: {_exc}")

    lesson_candidates = executor.pattern_consolidation_engine.consolidate_patterns(
        history_df=executor.engine.data, current_step=day_idx
    )
    if executor.lineage_debug:
        print(f"Pattern Consolidation Engine nominated {len(lesson_candidates)} Lesson candidates.")

    wm_update = executor.world_model_engine.synthesize(
        active_principles=executor.knowledge_repository.list_principles(status="active"),
        step=day_idx,
    )
    if executor.lineage_debug:
        print(
            f"World Model updated at Step {day_idx}: "
            f"Active Constraints={len(getattr(wm_update, 'active_constraints', []))} | "
            f"Regime Constraints={len(getattr(wm_update, 'regime_constraints', {}))} | "
            f"Explanatory Constraints={len(getattr(wm_update, 'explanatory_constraints', []))}"
        )
