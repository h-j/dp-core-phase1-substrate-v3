"""
Replay engine for deterministic historical cognition execution.

Replays cognition loop over historical market dataset.
Ensures:
- deterministic execution
- temporal integrity
- replayable snapshots
- offline-first operation
"""

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


import pandas as pd

# NOTE(charter): DecisionPolicyEngine and CapitalSimulator are downstream observers only.
from dp.observability.consultation_ledger import (
    ConsultationLedger,
    set_active_consultation_ledger,
)
from flows.theory_flow.attribution_engine import AttributionEngine
from market.data.dataset_validator import DatasetValidator

from market.replay.capital_simulator import CapitalSimulator
from market.replay.decision_policy import DecisionPolicyEngine
from market.replay.prediction_probe import PredictionProbeGenerator
from market.replay.replay_analysis import ReplayAnalysisEngine
from market.replay.replay_finalization import emit_cognitive_summary, generate_v1_report, save_manifest
from market.replay.replay_initialization import (
    format_historical_context,
    format_regime_context,
    initialize_flows,
    process_closed_loop_belief_updates,
    restart_clean,
)
from market.replay.step_decision import process_daily_decision
from market.replay.step_logging import print_day_log, save_step_snapshot, update_knowledge_graph_trace
from market.replay.step_observation import process_daily_observation
from market.replay.step_prediction import process_daily_prediction
from market.replay.step_theory import count_conditional_clauses, process_daily_theory
from market.replay.step_validation import process_daily_validation
from market.replay.transition_memory import TransitionExample, TransitionMemoryStore
from market.replay.transition_pressure import TransitionPressureEngine
from memory.experience.experience_engine import ExperienceEngine
from memory.experience.experience_repository import ExperienceRepository
from memory.relational.repositories.canonical_semantic_proposition_repository import (
    CanonicalSemanticPropositionRepository,
)
from memory.relational.repositories.compiled_proposition_repository import (
    CompiledPropositionRepository,
)
from memory.relational.repositories.validation_record_repository import (
    ValidationRecordRepository,
)
from memory.replay.regime_continuity_memory import RegimeContinuityMemory
from memory.replay.regime_memory import RegimeMemoryStore

logger = logging.getLogger("replay_engine")


class ReplayEngine:
    """
    Deterministic replay of cognition loop over historical market data.
    """

    def __init__(
        self,
        dataset_path: str = None,
        market_name: str = "RELIANCE",
        validate: bool = True,
        max_days: int = None,
    ):
        """
        Initialize replay engine.

        Args:
            dataset_path: Path to market CSV (default: data/reliance_daily_3y.csv)
            market_name: Label for the market or asset being replayed
            validate: Run validation on load
            max_days: If provided, limits replay dataset to first N days
        """
        if dataset_path is None:
            dataset_path = (
                Path(__file__).parent.parent.parent
                / "data"
                / f"{market_name.lower()}_daily_3y.csv"
            )

        self.dataset_path = Path(dataset_path)
        self.market_name = market_name
        self.data: Optional[pd.DataFrame] = None
        self.max_days = max_days

        self.load_data(validate=validate)

    def load_data(self, validate: bool = True):
        """Load and validate historical market dataset."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Market dataset not found: {self.dataset_path}")

        self.data = pd.read_csv(self.dataset_path)
        self.data["date"] = pd.to_datetime(self.data["date"])
        self.data = self.data.sort_values("date").reset_index(drop=True)

        if self.max_days is not None and self.max_days > 0:
            self.data = self.data.head(self.max_days)

        if validate:
            validator = DatasetValidator(csv_path=str(self.dataset_path))
            validator.validate(verbose=False)

        logger.info(
            f"Loaded {len(self.data)} trading days for {self.market_name} "
            f"({self.data['date'].iloc[0].strftime('%Y-%m-%d')} to "
            f"{self.data['date'].iloc[-1].strftime('%Y-%m-%d')})"
        )

    def __len__(self) -> int:
        return len(self.data) if self.data is not None else 0

    def get_observation_for_day(self, day_index: int) -> dict:
        """Extract observation dictionary for a single trading day."""
        if self.data is None or day_index >= len(self.data):
            raise IndexError(f"Day index {day_index} out of bounds")

        row = self.data.iloc[day_index]
        return {
            "date": row["date"].strftime("%Y-%m-%d"),
            "ohlcv": {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            },
            "derived": {
                "daily_return_pct": float(row.get("daily_return_pct", 0.0)),
                "log_return": float(row.get("log_return", 0.0)),
                "volatility_30d": float(row.get("volatility_30d", 0.0)),
                "return_3d": float(row.get("return_3d", 0.0)),
                "return_5d": float(row.get("return_5d", 0.0)),
                "return_10d": float(row.get("return_10d", 0.0)),
                "trend_5d": str(row.get("trend_5d", "flat")),
                "trend_20d": str(row.get("trend_20d", "flat")),
                "volume_state": str(row.get("volume_state", "normal")),
                "atr_14": float(row.get("atr_14", 0.0)),
                "range_pct": float(row.get("range_pct", 0.0)),
                "volume_ratio_5d": float(row.get("volume_ratio_5d", 1.0)),
                "regime": str(row.get("regime", "mixed")),
            },
        }


class ReplayExecutor:
    """
    Orchestrates execution of the cognition loop step-by-step over historical data.
    """

    def __init__(
        self,
        engine: Optional[ReplayEngine] = None,
        verbose: bool = False,
        quiet: bool = False,
        restart: bool = False,
        lineage_debug: bool = False,
        max_days: Optional[int] = None,
        dataset_path: Optional[str] = None,
        market_name: str = "RELIANCE",
        **kwargs,
    ):
        if engine is None:
            engine = ReplayEngine(
                dataset_path=dataset_path,
                market_name=market_name,
                max_days=max_days,
            )

        self.engine = engine
        self.verbose = verbose
        self.quiet = quiet
        self.restart = restart
        self.lineage_debug = lineage_debug
        self.extra_kwargs = kwargs

        self.replay_dir = Path(__file__).parent
        self.base_data_snap_dir = Path(__file__).parent.parent.parent / "data" / "replay_snapshots"
        self.base_output_dir = self.replay_dir / "output"
        self._create_snapshot_dirs()

        self.run_dir = self.base_output_dir

        self.transition_memory = TransitionMemoryStore()
        self.regime_memory = RegimeMemoryStore()

        self.transition_pressure_engine = TransitionPressureEngine()
        self.attribution_engine = AttributionEngine()
        self.decision_engine = DecisionPolicyEngine()
        self.validation_record_repo = ValidationRecordRepository()
        self.replay_analysis_engine = ReplayAnalysisEngine(market_name=getattr(self.engine, "market_name", "RELIANCE") if hasattr(self, "engine") and self.engine else "RELIANCE")

        self.flows_initialized = False

        self._confidence_history = []
        self._run_market_observations = []
        self._run_theories = []
        self._run_validations = []
        self._run_reflections = []
        self._regime_matches_by_step = []

        self._prior_prediction = None
        self._prior_prediction_db_id = None
        self._prior_lineage_id = None
        self._prior_lessons = None
        self._prior_conviction = None
        self._prior_allocation = None
        self._prior_components = None
        self._prior_decision_record = None
        self._prior_transition_context = None
        self._prior_prediction_accepted_principles = []
        self._prior_prediction_active_mechanisms = []

        self._prior_dialectical_synthesis = None
        self._prior_dialectical_subtype = None
        self.total_synthesis_triggered = 0

        self.min_validations_for_lesson = 2
        self.min_temporal_span_for_lesson = 2
        self.min_confidence_for_lesson = 0.60
        self.max_uncertainty_for_lesson = 0.40
        self.min_success_rate_for_lesson = 0.65

        self._lifetime_predictions_count = 0
        self._lifetime_correct_predictions_count = 0.0
        self._prediction_accuracy_history = []
        self._regime_prediction_accuracy_history = {}
        self._actual_directions_val_history = []

        self._prior_confidence_state_log = None
        self._lineage_audit_table = []
        self._accumulated_attributions = []

        self.compilation_metrics = {
            "theories_generated": 0,
            "semantic_propositions_created": 0,
            "semantic_failures": 0,
            "ontology_mapping_failures": 0,
            "propositions_grounded": 0,
            "percentile_grounding": 0,
            "relative_references_resolved": 0,
            "grounding_failures": 0,
            "propositions_compiled": 0,
            "compilation_success_count": 0,
            "compilation_partial_count": 0,
            "compilation_failed_count": 0,
            "compilation_success_rate": 0.0,
            "failure_reasons": {},
            "propositions_evaluated": 0,
            "validation_records_created": 0,
            "supported_records": 0,
            "contradicted_records": 0,
            "partially_supported_records": 0,
            "undecidable_records": 0,
        }

    def _create_snapshot_dirs(self):
        """Ensure base snapshot and output directories exist."""
        if hasattr(self, "base_data_snap_dir") and self.base_data_snap_dir:
            self.base_data_snap_dir.mkdir(parents=True, exist_ok=True)
        if hasattr(self, "base_output_dir") and self.base_output_dir:
            self.base_output_dir.mkdir(parents=True, exist_ok=True)
            (self.base_output_dir / "propositions").mkdir(parents=True, exist_ok=True)
            (self.base_output_dir / "canonical_propositions").mkdir(parents=True, exist_ok=True)
            (self.base_output_dir / "validation_records").mkdir(parents=True, exist_ok=True)

    def _initialize_flows(self):
        initialize_flows(self)

    def restart_clean(self):
        restart_clean(self)

    @property
    def lineage_audit_table(self):
        return self._lineage_audit_table

    def _log(self, message: str):
        if not self.quiet:
            print(message)

    def _format_regime_context(self, regime_matches: List[Any]) -> str:
        return format_regime_context(regime_matches)

    def _format_historical_context(self, recent_validations: List[Any], recent_reflections: List[Any]) -> str:
        return format_historical_context(recent_validations, recent_reflections)

    def _process_closed_loop_belief_updates(self, day_idx: int):
        process_closed_loop_belief_updates(self, day_idx)

    def _initialize_run_dir(self, restart: bool = False):
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            self.git_commit_hash = result.stdout.strip()
        except Exception:
            self.git_commit_hash = "unknown"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"run_{timestamp}"

        snaps_dir = Path(__file__).parent.parent.parent / "data" / "replay_snapshots" / (self.engine.market_name.lower() if self.engine.market_name else "reliance")
        snaps_dir.mkdir(parents=True, exist_ok=True)
        self.run_dir = snaps_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        (self.run_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.run_dir / "propositions").mkdir(parents=True, exist_ok=True)
        (self.run_dir / "canonical_propositions").mkdir(parents=True, exist_ok=True)
        (self.run_dir / "validation_records").mkdir(parents=True, exist_ok=True)
        (self.run_dir / "experiences").mkdir(parents=True, exist_ok=True)

        self._log(f"✓ Created new run directory: {self.run_dir.name}")

    def _build_experience_regime_context(self, market_obs: Any, obs_data: Dict[str, Any], regime_subtype: str) -> List[str]:
        descriptors = getattr(market_obs, "descriptors", [])
        return [
            f"trend:{market_obs.trend_state}",
            f"volatility:{market_obs.volatility_state}",
            f"liquidity:{market_obs.liquidity_state}",
            f"regime_subtype:{regime_subtype}",
            f"volume_state:{obs_data['derived'].get('volume_state', 'normal')}",
        ] + descriptors

    def execute(self, emit_summary: bool = True):
        """Execute full replay with cognition loop."""
        from cognition.schemas.knowledge.ontology import OntologyRegistry

        OntologyRegistry.reset_metrics()
        self._initialize_flows()

        if self.restart:
            self.restart_clean()

        self._initialize_run_dir(restart=self.restart)

        self.consultation_ledger = ConsultationLedger(
            output_path=self.run_dir / "consultation_ledger.jsonl"
        )
        set_active_consultation_ledger(self.consultation_ledger)

        self.experience_repo = ExperienceRepository(base_path=self.run_dir / "experiences")

        self.experience_engine = ExperienceEngine(self.experience_repo)
        self.experience_engine.verbose = self.verbose

        from flows.knowledge_flow.knowledge_compression_engine import KnowledgeCompressionEngine
        from flows.knowledge_flow.novelty_detection_gate import NoveltyDetectionGate
        from flows.knowledge_flow.world_model_engine import WorldModelEngine
        from memory.knowledge.knowledge_repository import KnowledgeRepository

        self.knowledge_repository = KnowledgeRepository(base_path=self.run_dir)
        from flows.knowledge_flow.mechanism_engine import MechanismEngine

        self.mechanism_engine = MechanismEngine(knowledge_repo=self.knowledge_repository)
        self.knowledge_compression_engine = KnowledgeCompressionEngine()
        self.world_model_engine = WorldModelEngine()
        self.novelty_gate = NoveltyDetectionGate(llm_client=self.theory_flow.client)
        self.novelty_decision_history = []

        from market.replay.lesson_extractor import LessonExtractor
        from market.replay.lesson_repository import LessonRepository
        from market.replay.market_observation_synthesizer import MarketObservationSynthesizer

        self.lesson_repo = LessonRepository(self.run_dir / "lessons.json")
        self.lesson_extractor = LessonExtractor(self.lesson_repo, self.experience_repo)
        self.lesson_extractor.debug = self.verbose
        from memory.replay.epistemic_scoring import EpistemicScoringEngine
        from memory.replay.horizon_cognition import HorizonCognitionEngine

        try:
            from memory.lineage.theory_lineage import TheoryLineageEngine
            from telemetry.cognition_observer import CognitionObserver
            from telemetry.contradiction_registry import ContradictionRegistry

            self.observer = CognitionObserver(self.run_dir / "observability_metrics.json")
            self.theory_lineage = TheoryLineageEngine(self.run_dir / "theory_lineage.json")
            self.theory_lineage.debug = self.lineage_debug
            self.contradiction_registry = ContradictionRegistry(self.run_dir / "contradiction_registry.json")
            self.horizon_engine = HorizonCognitionEngine()
            self.epistemic_scoring = EpistemicScoringEngine(verbose=self.verbose)
            self.prediction_generator = PredictionProbeGenerator()
            self.prediction_generator.debug = self.lineage_debug
            self.experience_engine.set_lesson_extractor(self.lesson_extractor)
            self.capital_simulator = CapitalSimulator()
            from market.replay.conviction_sizer import ConvictionSizer
            from market.replay.paper_trader import PaperTrader
            from memory.decision.decision_journal import DecisionJournal

            self.conviction_sizer = ConvictionSizer()
            self.paper_trader = PaperTrader()
            self.decision_journal = DecisionJournal()
        except Exception as _exc:
            logger.error("[ReplayExecutor.__init__] Cognition infrastructure init failed: %s", _exc, exc_info=True)
            self.observer = None
            self.theory_lineage = None
            self.contradiction_registry = None
            self.horizon_engine = HorizonCognitionEngine()
            self.epistemic_scoring = EpistemicScoringEngine(verbose=self.verbose)
            self.prediction_generator = PredictionProbeGenerator()
            self.prediction_generator.debug = self.lineage_debug
            self.experience_engine.set_lesson_extractor(self.lesson_extractor)
            self.capital_simulator = CapitalSimulator()
            from market.replay.conviction_sizer import ConvictionSizer
            from market.replay.paper_trader import PaperTrader

            self.conviction_sizer = ConvictionSizer()
            self.paper_trader = PaperTrader()
            self.decision_journal = None

        synthesizer = MarketObservationSynthesizer(self.engine.data)
        num_days = len(self.engine)

        if not self.quiet:
            print("\n======================================================================")
            print("REPLAY EXECUTION")
            print("======================================================================")
            print(f"Dataset: {num_days} days")
            print(f"Range: {self.engine.data['date'].iloc[0].strftime('%Y-%m-%d')} to {self.engine.data['date'].iloc[-1].strftime('%Y-%m-%d')}\n")

        last_lineage_id = "N/A"
        _degraded_steps = []

        for day_idx in range(num_days):
            obs_data = self.engine.get_observation_for_day(day_idx)
            date_str = obs_data["date"]
            regime_subtype = obs_data["derived"].get("regime", "mixed")
            regime_history = f"{obs_data['derived'].get('trend_5d', 'flat')} -> {regime_subtype}"
            falsifiability_conditions = [
                f"volatility_expansion > 2.0 under {regime_subtype}",
                f"trend_reversal under {obs_data['derived'].get('trend_5d', 'flat')}",
            ]

            prior_theory = self._run_theories[-1] if self._run_theories else None
            prior_attribution = getattr(self, "_prior_attribution", None)

            latest_wm_obj = self.knowledge_repository.get_latest_world_model()
            world_model_narrative = (
                f"Narrative: {latest_wm_obj.narrative_summary}; "
                f"Regime Constraints: {latest_wm_obj.regime_constraints}"
                if latest_wm_obj
                else "No consolidated World Model established."
            )

            active_principles = (
                self.knowledge_repository.list_principles(status="active")
                + self.knowledge_repository.list_principles(status="stable")
                + self.knowledge_repository.list_principles(status="emerging")
                + self.knowledge_repository.list_principles(status="trusted")
                + self.knowledge_repository.list_principles(status="canonical")
            )
            active_open_questions = self.knowledge_repository.list_open_questions(status="active")
            relevant_lessons = self.lesson_repo.list_lessons() if self.lesson_repo else []
            active_synthesis = getattr(self, "_prior_dialectical_synthesis", None)

            # 1. Observation
            obs_res = process_daily_observation(
                executor=self,
                day_idx=day_idx,
                date_str=date_str,
                obs_data=obs_data,
                synthesizer=synthesizer,
            )
            market_obs = obs_res.market_obs
            obs_event = obs_res.obs_event
            abstraction = obs_res.abstraction
            horizon_view = obs_res.horizon_view
            horizon_context = obs_res.horizon_context
            regime_matches = obs_res.regime_matches
            regime_context = obs_res.regime_context
            vol_regime = obs_res.vol_regime
            mom_regime = obs_res.mom_regime
            persistence_3d = obs_res.persistence_3d
            persistence_5d = obs_res.persistence_5d
            persistence_10d = obs_res.persistence_10d
            reg_5d = obs_res.reg_5d

            recent_theories = list(reversed(self._run_theories[-5:]))
            recent_validations = list(reversed(self._run_validations[-5:]))
            recent_reflections = list(reversed(self._run_reflections[-5:]))
            historical_context = self._format_historical_context(recent_validations, recent_reflections)

            # 2. Theory & Contradiction
            theory_res = process_daily_theory(
                executor=self,
                day_idx=day_idx,
                date_str=date_str,
                obs_data=obs_data,
                market_obs=market_obs,
                abstraction=abstraction,
                horizon_view=horizon_view,
                horizon_context=horizon_context,
                regime_matches=regime_matches,
                regime_context=regime_context,
                regime_subtype=regime_subtype,
                vol_regime=vol_regime,
                mom_regime=mom_regime,
                persistence_3d=persistence_3d,
                persistence_5d=persistence_5d,
                persistence_10d=persistence_10d,
                reg_5d=reg_5d,
                historical_context=historical_context,
                recent_theories=recent_theories,
                recent_validations=recent_validations,
                recent_reflections=recent_reflections,
                prior_theory=prior_theory,
                prior_attribution=prior_attribution,
                world_model_narrative=world_model_narrative,
                active_principles=active_principles,
                active_open_questions=active_open_questions,
                relevant_lessons=relevant_lessons,
                regime_history=regime_history,
                active_synthesis=active_synthesis,
                falsifiability_conditions=falsifiability_conditions,
                last_lineage_id=last_lineage_id,
                degraded_steps=_degraded_steps,
            )

            theory = theory_res.theory
            validation = theory_res.validation
            reflection = theory_res.reflection
            contradiction_result = theory_res.contradiction_result
            theory_usefulness = theory_res.theory_usefulness
            intelligence_metadata = theory_res.intelligence_metadata
            lineage_record = theory_res.lineage_record
            lineage_id_val = theory_res.lineage_id_val
            audit_created = theory_res.audit_created
            audit_mutated = theory_res.audit_mutated
            audit_merged = theory_res.audit_merged
            audit_revived = theory_res.audit_revived
            audit_retired = theory_res.audit_retired
            dialectical_data = theory_res.dialectical_data
            current_dialectical_data = dialectical_data

            confidence_state = theory.confidence_state

            # 3. Prediction & Conviction Sizing
            pred_res = process_daily_prediction(
                executor=self,
                day_idx=day_idx,
                date_str=date_str,
                obs_data=obs_data,
                market_obs=market_obs,
                horizon_view=horizon_view,
                regime_matches=regime_matches,
                theory=theory,
                contradiction_result=contradiction_result,
                reflection=reflection,
                theory_usefulness=theory_usefulness,
                intelligence_metadata=intelligence_metadata,
                regime_subtype=regime_subtype,
                vol_regime=vol_regime,
                mom_regime=mom_regime,
                confidence_state=confidence_state,
            )
            prediction_probe = pred_res.prediction_probe
            transition_pressure = pred_res.transition_pressure
            principles_accepted = pred_res.principles_accepted
            decisions = pred_res.decisions

            # 4. Prior Prediction Scoring, Causal Attribution & Proposition Compilation
            val_res = process_daily_validation(
                executor=self,
                day_idx=day_idx,
                date_str=date_str,
                obs_data=obs_data,
                market_obs=market_obs,
                theory=theory,
                regime_subtype=regime_subtype,
                vol_regime=vol_regime,
                persistence_3d=persistence_3d,
                persistence_5d=persistence_5d,
                persistence_10d=persistence_10d,
                reg_5d=reg_5d,
            )
            prior_prediction_result = val_res.prior_prediction_result

            # 5. Paper Trading, Decision Record & Regime Persistence
            dec_res = process_daily_decision(
                executor=self,
                day_idx=day_idx,
                date_str=date_str,
                obs_data=obs_data,
                market_obs=market_obs,
                theory=theory,
                prediction_probe=prediction_probe,
                transition_pressure=transition_pressure,
                contradiction_result=contradiction_result,
                confidence_state=confidence_state,
                principles_accepted=principles_accepted,
                regime_subtype=regime_subtype,
                regime_matches=regime_matches,
                horizon_view=horizon_view,
                decisions=decisions,
                audit_created=audit_created,
                audit_mutated=audit_mutated,
                audit_merged=audit_merged,
                audit_revived=audit_revived,
                audit_retired=audit_retired,
                prior_prediction_result=prior_prediction_result,
            )

            # Persist core objects
            self.observation_repo.save(obs_event)
            self.abstraction_repo.save(abstraction)
            self.theory_repo.save(theory)
            if hasattr(self, "mechanism_engine") and self.mechanism_engine:
                self.mechanism_engine.process_theories([theory], step=day_idx, regime_subtype=regime_subtype)
            self.validation_repo.save(validation)
            self.reflection_repo.save(reflection)
            self.confidence_repo.save(confidence_state)

            saved_prediction = None
            try:
                theory_id = str(getattr(theory, "id", ""))
                reflection_id = str(getattr(reflection, "id", ""))

                saved_prediction = self.prediction_repo.save(
                    prediction_probe,
                    date=date_str,
                    day_index=day_idx,
                    theory_id=theory_id,
                    reflection_id=reflection_id,
                )
            except Exception as e:
                self._log(f"WARNING: PredictionProbe save failed: {e}")

            try:
                if prior_prediction_result and self._prior_prediction_db_id:
                    self.prediction_result_repo.save(
                        result=prior_prediction_result,
                        date=date_str,
                        day_index=day_idx,
                        prediction_id=self._prior_prediction_db_id,
                    )
            except Exception as e:
                self._log(f"WARNING: PredictionResult save failed: {e}")

            self._run_market_observations.append(market_obs)
            self._run_theories.append(theory)
            self._run_validations.append(validation)
            self._run_reflections.append(reflection)

            # 6. Streamlined Logging & Snapshotting
            active_exp = None
            if lineage_record and lineage_id_val != "N/A":
                active_exp = self.experience_repo.load_by_lineage(lineage_id_val)

            if intelligence_metadata:
                intelligence_metadata["created"] = audit_created
                intelligence_metadata["mutated"] = audit_mutated
                intelligence_metadata["merged"] = audit_merged
                intelligence_metadata["revived"] = audit_revived
                intelligence_metadata["retired"] = audit_retired

            if hasattr(self, "replay_analysis_engine") and self.replay_analysis_engine:
                def safe_dict(obj):
                    if obj is None: return {}
                    if isinstance(obj, dict): return obj
                    try:
                        if hasattr(obj, "to_dict"): return obj.to_dict()
                        if hasattr(obj, "model_dump"): return obj.model_dump()
                        if hasattr(obj, "__dict__"): return dict(obj.__dict__)
                    except Exception:
                        pass
                    return {"raw": str(obj)}

                components_failed = []
                components_tested = []
                theory_id_val = ""
                prior_attr = getattr(self, "_prior_attribution", None)
                if prior_attr:
                    components_failed = getattr(prior_attr, "components_failed", [])
                    components_tested = getattr(prior_attr, "components_tested", [])
                    theory_id_val = getattr(prior_attr, "theory_id", "")

                self.replay_analysis_engine.record_day(
                    day_index=day_idx,
                    date=date_str,
                    confidence_state=safe_dict(confidence_state),
                    contradiction_result=safe_dict(contradiction_result),
                    theory_summary=theory.to_summary() if hasattr(theory, "to_summary") else str(theory),
                    reflection_summary=reflection.reflection_summary if hasattr(reflection, "reflection_summary") else str(reflection),
                    market_regime=getattr(market_obs, "regime", "neutral"),
                    prediction=safe_dict(prediction_probe),
                    prior_prediction_result=safe_dict(prior_prediction_result),
                    regime_matches=regime_matches if isinstance(regime_matches, list) else [],
                    theory_usefulness=theory_usefulness if isinstance(theory_usefulness, dict) else {},
                    transition_pressure=transition_pressure if isinstance(transition_pressure, dict) else {},
                    intelligence_data=intelligence_metadata,
                    components_failed=components_failed,
                    components_tested=components_tested,
                    theory_id=theory_id_val,
                )

            self._print_day_log(
                day_idx,
                date_str,
                market_obs,
                theory,
                reflection,
                confidence_state,
                contradiction_result,
                horizon_view,
                regime_matches,
                theory_usefulness,
                transition_pressure,
                prediction_probe,
                prior_prediction_result,
                active_experience=active_exp,
                lesson_info=self.experience_engine.get_last_extracted_lesson_with_reason(),
                intelligence=intelligence_metadata,
            )

            self._prior_prediction = prediction_probe
            self._prior_lineage_id = lineage_id_val
            if saved_prediction and hasattr(saved_prediction, "id"):
                self._prior_prediction_db_id = saved_prediction.id
            else:
                self._prior_prediction_db_id = None

            if current_dialectical_data:
                self._prior_dialectical_synthesis = self.dialectical_synthesizer.format_for_theory(current_dialectical_data)
                self._prior_dialectical_subtype = regime_subtype
            else:
                self._prior_dialectical_synthesis = None
                self._prior_dialectical_subtype = None

            # Adaptive Reconciliation & Compression
            should_reconcile = False
            if (day_idx + 1) == len(self.engine):
                should_reconcile = True
            else:
                all_p_temp = self.knowledge_repository.list_principles()
                open_questions_temp = self.knowledge_repository.list_open_questions()
                hist_temp = getattr(self, "replay_analysis_engine", None)
                hist_list = hist_temp.prediction_history if hist_temp else []

                debt = self.knowledge_compression_engine._calculate_knowledge_debt(all_p_temp, hist_list, open_questions_temp)
                if debt > 10.0:
                    should_reconcile = True
                    self._log(f"[Adaptive Trigger] Reconciliation triggered by Knowledge Debt: {debt:.1f} > 10.0")

                contra_val = float(contradiction_result.get("score", 0.0))
                if contra_val > 0.50:
                    should_reconcile = True
                    self._log(f"[Adaptive Trigger] Reconciliation triggered by Contradiction spike: {contra_val:.2f} > 0.50")

                candidate_count = sum(1 for p in all_p_temp if getattr(p.status, "value", p.status) == "candidate")
                if candidate_count > 6:
                    should_reconcile = True
                    self._log(f"[Adaptive Trigger] Reconciliation triggered by Candidate Principle backlog: {candidate_count} > 6")

            if should_reconcile:
                self._run_knowledge_compression(step=day_idx)
                new_principles = self.mechanism_engine.discover_invariants_and_form_principles(step=day_idx)
                for p in new_principles:
                    self.knowledge_repository.save_principle(p)

                candidates = self.knowledge_repository.list_principles(status="candidate")
                hist_temp = getattr(self, "replay_analysis_engine", None)
                hist_list = hist_temp.prediction_history if hist_temp else []
                for p in candidates:
                    validated_p = self.knowledge_compression_engine.validate_principle(
                        principle=p, prediction_history=hist_list
                    )
                    self.knowledge_repository.save_principle(validated_p)

                active_principles = (
                    self.knowledge_repository.list_principles(status="active")
                    + self.knowledge_repository.list_principles(status="stable")
                    + self.knowledge_repository.list_principles(status="emerging")
                    + self.knowledge_repository.list_principles(status="trusted")
                    + self.knowledge_repository.list_principles(status="canonical")
                )
                if active_principles:
                    wm_update = self.world_model_engine.synthesize(
                        active_principles=active_principles,
                        step=day_idx,
                    )
                    self.knowledge_repository.save_world_model(wm_update)

        if emit_summary:
            self._emit_cognitive_summary()

    def _print_day_log(
        self,
        day_idx: int,
        date_str: str,
        observation,
        theory,
        reflection,
        confidence,
        contradiction,
        horizon,
        regime_matches,
        theory_usefulness,
        transition_pressure=None,
        prediction=None,
        prior_prediction_result=None,
        active_experience=None,
        lesson_info=None,
        intelligence=None,
    ):
        print_day_log(
            executor=self,
            day_idx=day_idx,
            date_str=date_str,
            market_obs=observation,
            theory=theory,
            reflection=reflection,
            confidence_state=confidence,
            contradiction_result=contradiction,
            horizon_view=horizon,
            regime_matches=regime_matches,
            theory_usefulness=theory_usefulness,
            transition_pressure=transition_pressure,
            prediction_probe=prediction,
            prior_prediction_result=prior_prediction_result,
            active_experience=active_experience,
            lesson_info=lesson_info,
            intelligence=intelligence,
        )

    def _run_knowledge_compression(self, step: int):
        if not hasattr(self, "knowledge_compression_engine") or not self.knowledge_compression_engine:
            from flows.knowledge_flow.knowledge_compression_engine import KnowledgeCompressionEngine
            self.knowledge_compression_engine = KnowledgeCompressionEngine()

        try:
            experiences = self.experience_repo.get_all() if self.experience_repo else []
            lineages = self.theory_lineage.get_all_lineages() if self.theory_lineage else []
            attributions = getattr(self, "_accumulated_attributions", [])

            new_principles = self.knowledge_compression_engine.compress(
                experiences=experiences,
                theory_lineages=lineages,
                attributions=attributions,
                step=step,
            )
            for p in new_principles:
                self.knowledge_repository.save_principle(p)
            self._log(f"[KnowledgeCompressionEngine] Step {step}: Inducted {len(new_principles)} new principle candidates.")
        except Exception as e:
            logger.warning(f"[KnowledgeCompressionEngine] Compression failed at step {step}: {e}")

    def _emit_cognitive_summary(self):
        emit_cognitive_summary(self)

    def _save_manifest(self):
        save_manifest(self)

    def _generate_v1_report(self):
        generate_v1_report(self)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DP Replay Engine CLI")
    parser.add_argument("--days", type=int, default=None, help="Number of days to replay")
    parser.add_argument("--restart", action="store_true", help="Clear previous replay database and logs")
    parser.add_argument("--nifty", action="store_true", help="Replay NIFTY index dataset")
    parser.add_argument("--verbose", action="store_true", help="Print debug logs")
    parser.add_argument("--quiet", action="store_true", help="Suppress output logs")
    parser.add_argument("--lineage-debug", action="store_true", help="Enable lineage debug logging")

    args = parser.parse_args()

    market_name = "NIFTY" if args.nifty else "RELIANCE"
    engine = ReplayEngine(market_name=market_name, max_days=args.days)
    executor = ReplayExecutor(
        engine=engine,
        verbose=args.verbose,
        quiet=args.quiet,
        restart=args.restart,
        lineage_debug=args.lineage_debug,
    )
    executor.execute(emit_summary=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
