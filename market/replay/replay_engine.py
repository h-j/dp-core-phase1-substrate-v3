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

logger = logging.getLogger("replay_engine")
import os
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import List

import pandas as pd

from flows.theory_flow.attribution import AttributionResult
from flows.theory_flow.attribution_engine import AttributionEngine
from market.data.dataset_validator import DatasetValidator
from market.replay.capital_simulator import CapitalSimulator
from market.replay.decision_policy import DecisionPolicyEngine
from market.replay.prediction_probe import PredictionProbeGenerator
from market.replay.transition_memory import (TransitionExample,
                                             TransitionMemoryStore)
from market.replay.transition_pressure import TransitionPressureEngine
from memory.experience.experience_engine import ExperienceEngine
from memory.experience.experience_repository import ExperienceRepository
from memory.replay.regime_continuity_memory import RegimeContinuityMemory
from memory.replay.regime_memory import \
    RegimeMemoryStore  # Import RegimeMemoryStore


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
            max_days: Limit replay to N days (for testing)
        """
        if dataset_path:
            self.dataset_path = Path(dataset_path)
        else:
            # Default path: data/ directory at project root
            self.dataset_path = (
                Path(__file__).parent.parent.parent / "data" / "reliance_daily_3y.csv"
            )

        self.market_name = market_name
        self.validate_on_init = validate
        self.max_days = max_days
        self.data = None
        self.replay_log = []
        self.execution_hash = None

        self._load_dataset()

    def _load_dataset(self):
        """Load and validate dataset."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")

        # Validate if requested
        if self.validate_on_init:
            validator = DatasetValidator(str(self.dataset_path))
            results = validator.validate(verbose=False)

            if results["errors"]:
                raise ValueError(f"Dataset validation failed: {results['errors']}")

        # Load dataset
        self.data = pd.read_csv(self.dataset_path)
        self.data["date"] = pd.to_datetime(self.data["date"])

        # Limit to max_days if specified
        if self.max_days:
            self.data = self.data.tail(self.max_days)

        print(
            f"✓ Replay engine loaded {len(self.data)} trading days "
            f"({self.data['date'].min().date()} to "
            f"{self.data['date'].max().date()})"
        )

    def get_observation_for_day(self, day_index: int) -> dict:
        """
        Get deterministic market observation for a day.

        Args:
            day_index: 0-based index into replay dataset

        Returns:
            dict with OHLCV data and synthetic observation
        """
        if day_index < 0 or day_index >= len(self.data):
            raise IndexError(
                f"Day index {day_index} out of range " f"(0 to {len(self.data)-1})"
            )

        row = self.data.iloc[day_index]

        # Get prior day for trend comparison (if available)
        prior_row = self.data.iloc[day_index - 1] if day_index > 0 else None

        return {
            "day_index": day_index,
            "date": row["date"].strftime("%Y-%m-%d"),
            "ohlcv": {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            },
            "prior_ohlcv": (
                {"close": float(prior_row["close"])} if prior_row is not None else None
            ),
            "derived": (
                {
                    "daily_return_pct": float(
                        (row["close"] - row["open"]) / row["open"] * 100
                    ),
                    "volatility_10d": float(row.get("rolling_volatility_10d", 0.0)),
                    "volatility_30d": float(row.get("rolling_volatility_30d", 0.0)),
                    # v2.0 Enriched Metrics
                    "volume_state": row.get("volume_state", "normal"),
                    "volume_ratio_5d": float(row.get("volume_ratio_5d", 1.0)),
                    "volume_ratio_20d": float(row.get("volume_ratio_20d", 1.0)),
                    "range_pct": float(row.get("range_pct", 0.0)),
                    "gap_pct": float(row.get("gap_pct", 0.0)),
                    "atr_14": float(row.get("atr_14", 0.0)),
                    "return_3d": float(row.get("return_3d", 0.0)),
                    "return_5d": float(row.get("return_5d", 0.0)),
                }
                if "rolling_volatility_10d" in row
                else None
            ),
        }

    def get_date_range(self) -> tuple:
        """Return (start_date, end_date) as strings."""
        return (
            self.data["date"].min().strftime("%Y-%m-%d"),
            self.data["date"].max().strftime("%Y-%m-%d"),
        )

    def get_day_count(self) -> int:
        """Return total replaying days."""
        return len(self.data)

    def compute_execution_hash(self, log_entries: list) -> str:
        """
        Compute deterministic hash of replay execution.

        Used to verify determinism across runs.
        """
        combined = "\n".join(str(entry) for entry in log_entries)
        return hashlib.sha256(combined.encode()).hexdigest()

    def log_entry(
        self,
        day_index: int,
        date: str,
        observation_hash: str,
        theory_hash: str,
        confidence_hash: str,
    ):
        """Log a replay day entry for determinism validation."""
        entry = {
            "day_index": day_index,
            "date": date,
            "observation_hash": observation_hash,
            "theory_hash": theory_hash,
            "confidence_hash": confidence_hash,
            "timestamp": datetime.now().isoformat(),
        }
        self.replay_log.append(entry)

    def finalize_execution(self) -> str:
        """Finalize and return execution hash."""
        hashes = [
            entry["observation_hash"] + entry["theory_hash"] + entry["confidence_hash"]
            for entry in self.replay_log
        ]
        combined = "".join(hashes)
        self.execution_hash = hashlib.sha256(combined.encode()).hexdigest()
        return self.execution_hash

    def get_execution_log(self) -> list:
        """Return replay execution log."""
        return self.replay_log

    def __len__(self) -> int:
        """Return number of replay days."""
        return len(self.data) if self.data is not None else 0

    def __repr__(self) -> str:
        """String representation."""
        if self.data is None:
            return "<ReplayEngine: not loaded>"

        start, end = self.get_date_range()
        return f"<ReplayEngine: {len(self.data)} days, " f"{start} to {end}>"


class ReplayExecutor:
    """
    Executes deterministic replay with full cognition loop integration.
    """

    def __init__(
        self,
        max_days: int = None,
        quiet: bool = False,
        dataset_path: str = None,
        market_name: str = "RELIANCE",
        compare_secondary: bool = False,
        generate_visualizations: bool = False,
        lineage_debug: bool = False,
        restart: bool = False,
        verbose: bool = False,
        force_refresh: bool = False,
        data_prep_done: bool = False,
    ):
        """Initialize executor.

        Args:
            compare_secondary: If True and the primary market is RELIANCE, run
                an optional NIFTY cross-asset comparison after the main replay.
            generate_visualizations: If True, generate chart images for replay
                outputs and optional cross-asset analysis.
        """
        self.max_days = max_days
        self.quiet = quiet
        self.verbose = verbose
        self.dataset_path = dataset_path
        self.market_name = market_name
        self.compare_secondary = compare_secondary
        self.lineage_debug = lineage_debug
        self.restart = restart
        self.force_refresh = force_refresh
        self.replay_dir = Path(__file__).parent.parent.parent / "memory" / "replay"
        self.base_data_snap_dir = (
            Path(__file__).parent.parent.parent / "data" / "replay_snapshots"
        )
        self.base_output_dir = (
            Path(__file__).parent.parent.parent / "market" / "replay" / "output"
        )
        self._create_snapshot_dirs()

        # Run pipeline to ensure Sector RS, Delivery %, and FII/DII data are merged.
        if not data_prep_done:
            from market.data.download_history import ensure_data

            try:
                ensure_data(
                    symbol=self.market_name,
                    force_refresh=self.force_refresh,
                    dataset_path=self.dataset_path,
                )
            except Exception as e:
                print(
                    f"[ReplayExecutor] Data pipeline error: {e}. Running with existing dataset."
                )

        self.transition_pressure_engine = TransitionPressureEngine()
        self.transition_pressure_engine.debug = self.lineage_debug
        self.total_synthesis_triggered = 0
        # Initialize replay engine
        self.engine = ReplayEngine(
            dataset_path=self.dataset_path,
            market_name=self.market_name,
            validate=True,
            max_days=self.max_days,
        )
        self.output_dir = (
            self.base_output_dir / self.engine.market_name.lower().replace(" ", "_")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        from memory.graph.knowledge_graph import KnowledgeGraph

        self.knowledge_graph = KnowledgeGraph(run_dir=self.output_dir)
        self.decision_traces = []
        self.epistemic_review = {}

        # Initialize flows and repositories (lazy loaded on first use)
        self.flows_initialized = False
        self.abstraction_flow = None
        self.theory_flow = None
        self.reflection_flow = None
        self.dialectical_synthesizer = None
        self.contradiction_detector = None
        self.confidence_engine = None
        self.observation_repo = None
        self.abstraction_repo = None
        self.theory_repo = None
        self.validation_repo = None
        self.reflection_repo = None
        self.confidence_repo = None

        self.observer = None
        self.theory_lineage = None
        self.contradiction_registry = None
        self.regime_memory = None
        self.horizon_engine = None
        self.epistemic_scoring = None
        self.run_dir = None

        # small in-memory history for confidence tracking
        self._confidence_history: List[float] = []
        self._actual_directions_val_history: List[int] = []
        self._run_theories: List[object] = []
        self._run_validations: List[object] = []
        self._run_reflections: List[object] = []
        self._run_market_observations: List[object] = []
        self._prior_prediction = None
        self._prior_attribution = None
        self._prior_lineage_id = None  # Track the lineage that produced the prediction
        self.regime_memory = RegimeMemoryStore()  # Initialize unconditionally
        self.regime_continuity_memory = RegimeContinuityMemory()
        self.attribution_engine = AttributionEngine(llm_client=None)
        self._prior_dialectical_synthesis = None
        self._prior_dialectical_subtype = None
        self._prior_prediction_db_id = None
        self.decision_engine = DecisionPolicyEngine()
        self._regime_matches_by_step: List[list] = []
        self.replay_analysis_engine = None  # Will be initialized in execute
        self.prediction_repo = None
        self.transition_memory = TransitionMemoryStore()
        self.generate_visualizations = generate_visualizations

        # Context for transition recording
        self._prior_transition_context = None
        self.prediction_result_repo = None
        self.transition_pressure_repo = None
        self.market_outcome_repo = None

        # Track IDs for relational linking (moved from _initialize_flows)
        self._prior_prediction_db_id = None

        # Experience tracking
        self.experience_repo = ExperienceRepository()
        self.experience_engine = ExperienceEngine(self.experience_repo)
        self.experience_engine.verbose = self.verbose
        self._lineage_audit_table = []  # Instrumentation: For final audit table

    def _create_snapshot_dirs(self):
        """Create replay snapshot directories if missing."""
        dirs = [
            self.replay_dir,
            self.replay_dir / "observations",
            self.replay_dir / "theories",
            self.replay_dir / "confidence",
            self.replay_dir / "logs",
            self.base_data_snap_dir,
            self.base_output_dir,
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _initialize_run_dir(self, restart: bool = False):
        """Initializes self.run_dir, reusing the most recent one if not restarting."""
        if not restart and self.base_data_snap_dir.exists():
            # Find the most recent run_ directory
            run_dirs = sorted(
                [
                    d
                    for d in self.base_data_snap_dir.iterdir()
                    if d.is_dir() and d.name.startswith("run_")
                ],
                key=lambda x: x.name,
                reverse=True,
            )
            if run_dirs:
                self.run_dir = run_dirs[0]
                self._log(
                    f"✓ Reusing existing run directory for incremental replay: {self.run_dir.name}"
                )
                return

        # Generate new timestamped run directory
        self.run_dir = (
            self.base_data_snap_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._log(f"✓ Created new run directory: {self.run_dir.name}")

    def restart_clean(self):
        """Clears all relational database tables, generated experiences, and snapshot files."""
        self._log("\n" + "=" * 70)
        self._log(
            "RESTART REPLAY: Clearing all database records and generated artifacts..."
        )
        self._log("=" * 70)

        # 1. Clear database records/tables by dropping and recreating
        import memory.relational.models  # Ensure all models are registered
        from memory.relational.postgres_client import Base, engine

        try:
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            # Re-run schema validation check
            from memory.relational.schema_validator import \
                validate_schema_startup

            validate_schema_startup(engine)
            self._log(
                "✓ PostgreSQL database tables dropped and recreated successfully."
            )
        except Exception as e:
            self._log(f"⚠ Database drop/recreate failed: {e}")

        # 2. Clear generated experience JSON files
        exp_dir = Path(__file__).parent.parent.parent / "data" / "experiences"
        if exp_dir.exists():
            for f in exp_dir.glob("*.json"):
                try:
                    f.unlink()
                except Exception as e:
                    self._log(f"⚠ Failed to delete experience file {f}: {e}")
            self._log("✓ Experience JSON files cleared.")

        # 3. Clear run snapshot directories
        snap_dir = Path(__file__).parent.parent.parent / "data" / "replay_snapshots"
        if snap_dir.exists():
            import shutil

            for d in snap_dir.iterdir():
                if d.is_dir() and d.name.startswith("run_"):
                    try:
                        shutil.rmtree(d)
                    except Exception as e:
                        self._log(f"⚠ Failed to delete snapshot dir {d}: {e}")
            self._log("✓ Replay snapshots cleared.")

        # 4. Clear decision journal files
        if hasattr(self, "decision_journal") and self.decision_journal:
            self.decision_journal.clear()
            self._log("✓ Decision journal records cleared via journal class.")
        else:
            dj_dir = Path(__file__).parent.parent.parent / "data" / "decision_journal"
            if dj_dir.exists():
                for f in dj_dir.glob("*.json"):
                    try:
                        f.unlink()
                    except Exception as e:
                        pass
                self._log("✓ Decision journal JSON files cleared.")

    def _initialize_flows(self):
        """Lazy initialize cognition flows and repositories."""
        if self.flows_initialized:
            return

        # v3.7 Logic: Ensure schema is valid before starting execution
        # Note: postgres_client triggers create_all and validation on import.
        # No explicit call needed here to avoid redundant I/O.
        from cognition.confidence.confidence_evolution_engine import \
            ConfidenceEvolutionEngine
        from cognition.contradiction.contradiction_detector import \
            ContradictionDetector
        from flows.observation_flow.abstraction_flow import AbstractionFlow
        from flows.reflection_flow.reflection_flow import ReflectionFlow
        from flows.theory_flow.dialectical_synthesizer import \
            DialecticalTheorySynthesizer
        from flows.theory_flow.theory_generation_flow import \
            TheoryGenerationFlow
        from memory.relational.postgres_client import engine
        from memory.relational.repositories.abstraction_repository import \
            AbstractionRepository
        from memory.relational.repositories.confidence_repository import \
            ConfidenceRepository
        from memory.relational.repositories.market_outcome_repository import \
            MarketOutcomeRepository
        from memory.relational.repositories.observation_repository import \
            ObservationRepository
        from memory.relational.repositories.prediction_repository import \
            PredictionRepository
        from memory.relational.repositories.prediction_result_repository import \
            PredictionResultRepository
        from memory.relational.repositories.reflection_repository import \
            ReflectionRepository
        from memory.relational.repositories.theory_repository import \
            TheoryRepository
        from memory.relational.repositories.transition_pressure_repository import \
            TransitionPressureRepository
        from memory.relational.repositories.validation_repository import \
            ValidationRepository

        self.abstraction_flow = AbstractionFlow()
        self.theory_flow = TheoryGenerationFlow()
        self.reflection_flow = ReflectionFlow(verbose=self.verbose)
        self.dialectical_synthesizer = DialecticalTheorySynthesizer()
        # Inject client into attribution engine
        self.attribution_engine.llm = self.theory_flow.client
        self.contradiction_detector = ContradictionDetector(verbose=self.verbose)
        self.theory_flow.debug = self.lineage_debug
        self.confidence_engine = ConfidenceEvolutionEngine()

        self.observation_repo = ObservationRepository()
        self.abstraction_repo = AbstractionRepository()
        self.theory_repo = TheoryRepository()
        self.validation_repo = ValidationRepository()
        self.reflection_repo = ReflectionRepository()
        self.confidence_repo = ConfidenceRepository()

        # v1.4 Repositories
        self.prediction_repo = PredictionRepository()
        self.prediction_result_repo = PredictionResultRepository()
        self.transition_pressure_repo = TransitionPressureRepository()

        try:
            from memory.relational.repositories.market_outcome_repository import \
                MarketOutcomeRepository

            self.market_outcome_repo = MarketOutcomeRepository()
            # Lesson Layer V1: JSON file persistence, not relational DB
        except (ImportError, ModuleNotFoundError):
            self._log(
                "WARNING: MarketOutcomeRepository missing; optional persistence disabled."
            )
            self.market_outcome_repo = None

        self.flows_initialized = True

    def _log(self, message: str):
        """Print if not quiet mode, and also to a debug log file."""
        if not self.quiet:
            print(message)
        # Optional: Add logging to a file here
        # with open(self.run_dir / "replay_debug.log", "a") as f: f.write(message + "\n")

    def execute(self, emit_summary: bool = True):
        """Execute full replay with cognition loop."""
        from cognition.schemas.knowledge.ontology import OntologyRegistry

        OntologyRegistry.reset_metrics()
        self._initialize_flows()

        # Restart clean if requested
        if self.restart:
            self.restart_clean()

        # Initialize run directory
        self._initialize_run_dir(restart=self.restart)

        # Isolate experience repository storage to the unique run directory to prevent test contamination
        from memory.experience.experience_engine import ExperienceEngine
        from memory.experience.experience_repository import \
            ExperienceRepository

        self.experience_repo = ExperienceRepository(
            base_path=self.run_dir / "experiences"
        )
        self.experience_engine = ExperienceEngine(self.experience_repo)
        self.experience_engine.verbose = self.verbose

        # Initialize Phase 2 components
        from uuid import uuid4

        from flows.knowledge_flow.knowledge_compression_engine import \
            KnowledgeCompressionEngine
        from flows.knowledge_flow.novelty_detection_gate import \
            NoveltyDetectionGate
        from flows.knowledge_flow.world_model_engine import WorldModelEngine
        from memory.knowledge.knowledge_repository import KnowledgeRepository

        self.knowledge_repository = KnowledgeRepository(base_path=self.run_dir)
        from flows.knowledge_flow.mechanism_engine import MechanismEngine

        self.mechanism_engine = MechanismEngine(
            knowledge_repo=self.knowledge_repository
        )
        self.knowledge_compression_engine = KnowledgeCompressionEngine()
        self.world_model_engine = WorldModelEngine()
        self.novelty_gate = NoveltyDetectionGate(llm_client=self.theory_flow.client)
        self.novelty_decision_history = []

        from cognition.evaluation.epistemic_quality import \
            evaluate_epistemic_quality
        from cognition.schemas.confidence.confidence_state import \
            ConfidenceState
        from cognition.schemas.observation.observation_event import \
            ObservationEvent
        from cognition.schemas.validation.validation_event import \
            ValidationEvent
        from market.replay.lesson_extractor import LessonExtractor
        # Lesson Layer V1: Initialize LessonRepository and LessonExtractor
        from market.replay.lesson_repository import LessonRepository
        from market.replay.market_observation_synthesizer import \
            MarketObservationSynthesizer

        self.lesson_repo = LessonRepository(self.run_dir / "lessons.json")
        self.lesson_extractor = LessonExtractor(self.lesson_repo, self.experience_repo)
        self.lesson_extractor.debug = self.verbose
        from memory.replay.epistemic_scoring import EpistemicScoringEngine
        from memory.replay.horizon_cognition import HorizonCognitionEngine
        from memory.replay.regime_memory import RegimeMemoryStore

        try:
            from memory.lineage.theory_lineage import TheoryLineageEngine
            from telemetry.cognition_observer import CognitionObserver
            from telemetry.contradiction_registry import ContradictionRegistry

            self.observer = CognitionObserver(
                self.run_dir / "observability_metrics.json"
            )
            self.theory_lineage = TheoryLineageEngine(
                self.run_dir / "theory_lineage.json"
            )
            self.theory_lineage.debug = self.lineage_debug
            self.contradiction_registry = ContradictionRegistry(
                self.run_dir / "contradiction_registry.json"
            )
            self.horizon_engine = HorizonCognitionEngine()
            self.epistemic_scoring = EpistemicScoringEngine(verbose=self.verbose)
            self.prediction_generator = PredictionProbeGenerator()
            self.prediction_generator.debug = self.lineage_debug
            self.experience_engine.set_lesson_extractor(
                self.lesson_extractor
            )  # Pass extractor to experience engine
            self.capital_simulator = CapitalSimulator()
            from market.replay.conviction_sizer import ConvictionSizer
            from market.replay.paper_trader import PaperTrader
            from memory.decision.decision_journal import DecisionJournal

            self.conviction_sizer = ConvictionSizer()
            self.paper_trader = PaperTrader()
            self.decision_journal = DecisionJournal()
        except Exception:
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
            from memory.decision.decision_journal import DecisionJournal

            self.conviction_sizer = ConvictionSizer()
            self.paper_trader = PaperTrader()
            self.decision_journal = DecisionJournal()

        from market.replay.replay_analysis import ReplayAnalysisEngine

        self.replay_analysis_engine = ReplayAnalysisEngine(
            market_name=self.engine.market_name
        )

        # Load synthesizer
        synthesizer = MarketObservationSynthesizer(
            self.engine.data, market_name=self.engine.market_name
        )

        # Initialize confidence_state for Day 0 execution
        confidence_state = ConfidenceState()

        self._log("\n" + "=" * 70)
        self._log("REPLAY EXECUTION")
        self._log("=" * 70)
        self._log(f"Dataset: {len(self.engine)} days")
        self._log(
            f"Range: {self.engine.get_date_range()[0]} to {self.engine.get_date_range()[1]}\n"
        )

        # v3.3: Config Snapshot for auditability (Run A vs Run B comparison)
        if self.lineage_debug:
            self._log("[CONFIG SNAPSHOT]")

        config_summary = {}

        if self.contradiction_detector:
            if self.lineage_debug:
                self._log("\nCONTRADICTION:")
            config_summary["contradiction"] = self.contradiction_detector.CONFIG
            if self.lineage_debug:
                for k, v in config_summary["contradiction"].items():
                    self._log(f"  {k}={v}")

        if self.transition_pressure_engine:
            if self.lineage_debug:
                self._log("\nTRANSITION:")
            config_summary["transition_pressure"] = (
                self.transition_pressure_engine.TP_CONFIG
            )
            if self.lineage_debug:
                for k, v in config_summary["transition_pressure"].items():
                    self._log(f"  {k}={v}")

        # Persist snapshot for cross-run audit
        with open(self.run_dir / "config_snapshot.json", "w") as f:
            json.dump(config_summary, f, indent=2)
        self.replay_analysis_engine.set_config_snapshot(config_summary)
        self._log("\n" + "-" * 70)

        last_lineage_id = None  # Instrumentation: Track lineage changes

        # Execute replay
        # Execute replay
        for day_idx in range(len(self.engine)):
            try:
                obs_data = self.engine.get_observation_for_day(day_idx)
                date_str = obs_data["date"]
                newly_retired_count = 0

                # --- INCREMENTAL CHECK ---
                from cognition.schemas.confidence.confidence_state import \
                    ConfidenceState
                from cognition.schemas.reflection.reflection_event import \
                    ReflectionEvent
                from cognition.schemas.theory.theory import (Theory,
                                                             TheoryStructured)
                from cognition.schemas.validation.validation_event import \
                    ValidationEvent
                from market.replay.prediction_probe import (
                    PredictionDirection, PredictionProbe)
                from memory.relational.models.confidence_model import \
                    ConfidenceModel
                from memory.relational.models.prediction_probe_model import \
                    PredictionProbeModel
                from memory.relational.models.prediction_result_model import \
                    PredictionResultModel
                from memory.relational.models.reflection_model import \
                    ReflectionModel
                from memory.relational.models.theory_model import TheoryModel
                from memory.relational.models.transition_pressure_model import \
                    TransitionPressureModel
                from memory.relational.models.validation_model import \
                    ValidationModel
                from memory.relational.postgres_client import SessionLocal

                existing_probe = None
                with SessionLocal() as session:
                    existing_probe = (
                        session.query(PredictionProbeModel)
                        .filter(PredictionProbeModel.date == date_str)
                        .first()
                    )

                if existing_probe is not None:
                    # Date already replayed. Reconstruct state from DB to fast-forward.
                    self._log(
                        f"  [INCREMENTAL] Skipping already replayed day {date_str} (day_idx={day_idx})"
                    )

                    # 1. Synthesize deterministic observation
                    market_obs = synthesizer.synthesize(day_idx)

                    # 2. Get and reconstruct ConfidenceState
                    confidence_state = None
                    theory_model = None
                    with SessionLocal() as session:
                        theory_model = (
                            session.query(TheoryModel)
                            .filter(TheoryModel.id == existing_probe.theory_id)
                            .first()
                        )
                        if theory_model:
                            conf_model = (
                                session.query(ConfidenceModel)
                                .filter(
                                    ConfidenceModel.id
                                    == theory_model.confidence_state_id
                                )
                                .first()
                            )
                            if conf_model:
                                confidence_state = ConfidenceState(
                                    id=conf_model.id,
                                    created_at=conf_model.created_at,
                                    empirical_confidence=conf_model.empirical_confidence,
                                    regime_confidence=conf_model.regime_confidence,
                                    reflection_confidence=conf_model.reflection_confidence,
                                    theoretical_coherence=conf_model.theoretical_coherence,
                                    contradiction_pressure=conf_model.contradiction_pressure,
                                )

                    if confidence_state is None:
                        confidence_state = ConfidenceState()

                    # 3. Reconstruct Theory
                    theory = None
                    if theory_model:
                        structured_data = None
                        if theory_model.summary_structured:
                            try:
                                structured_data = TheoryStructured(
                                    **json.loads(theory_model.summary_structured)
                                )
                            except Exception:
                                pass
                        theory = Theory(
                            id=theory_model.id,
                            created_at=theory_model.created_at,
                            lineage_id=theory_model.lineage_id,
                            thesis=theory_model.thesis,
                            summary=theory_model.summary,
                            summary_structured=structured_data,
                            confidence_state=confidence_state,
                        )
                        object.__setattr__(
                            theory, "llm_evaluation", theory_model.llm_evaluation
                        )
                        object.__setattr__(
                            theory, "survival_days", theory_model.survival_days
                        )
                        object.__setattr__(
                            theory,
                            "falsified_at_index",
                            theory_model.falsified_at_index,
                        )
                        object.__setattr__(
                            theory,
                            "falsification_precision",
                            theory_model.falsification_precision,
                        )

                    # 4. Reconstruct ValidationEvent
                    validation = None
                    with SessionLocal() as session:
                        val_model = (
                            session.query(ValidationModel)
                            .filter(
                                ValidationModel.theory_id == existing_probe.theory_id
                            )
                            .first()
                        )
                        if val_model:
                            validation = ValidationEvent(
                                id=val_model.id,
                                created_at=val_model.created_at,
                                theory_id=val_model.theory_id,
                                validation_summary=val_model.validation_summary,
                                observed_behavior=val_model.observed_behavior,
                                expected_behavior=val_model.expected_behavior,
                            )

                    # 5. Reconstruct ReflectionEvent
                    reflection = None
                    with SessionLocal() as session:
                        ref_model = (
                            session.query(ReflectionModel)
                            .filter(ReflectionModel.id == existing_probe.reflection_id)
                            .first()
                        )
                        if ref_model:
                            reflection = ReflectionEvent(
                                id=ref_model.id,
                                created_at=ref_model.created_at,
                                related_theory_id=ref_model.related_theory_id,
                                reflection_summary=ref_model.reflection_summary,
                                confidence_impact=ref_model.confidence_impact,
                            )

                    # 6. Reconstruct PredictionProbe
                    prediction_probe = PredictionProbe(
                        direction=PredictionDirection(existing_probe.direction),
                        confidence=existing_probe.confidence,
                        tension=existing_probe.tension,
                        invalidation=existing_probe.invalidation,
                    )

                    # 7. Append to histories
                    self._confidence_history.append(
                        confidence_state.empirical_confidence
                    )
                    actual_dir_str = market_obs.trend_state.lower()
                    dir_val = (
                        1
                        if "higher" in actual_dir_str
                        else -1 if "lower" in actual_dir_str else 0
                    )
                    self._actual_directions_val_history.append(dir_val)

                    if theory:
                        self._run_theories.append(theory)
                    if validation:
                        self._run_validations.append(validation)
                    if reflection:
                        self._run_reflections.append(reflection)
                    self._run_market_observations.append(market_obs)

                    # Compute hashes for determinism log
                    obs_hash = hashlib.sha256(
                        market_obs.observation_text.encode()
                    ).hexdigest()[:16]
                    theory_hash = (
                        hashlib.sha256(theory.summary.encode()).hexdigest()[:16]
                        if theory
                        else ""
                    )
                    conf_hash = hashlib.sha256(
                        str(confidence_state.empirical_confidence).encode()
                    ).hexdigest()[:16]
                    self.engine.log_entry(
                        day_idx, date_str, obs_hash, theory_hash, conf_hash
                    )

                    # Set prior state variables
                    self._prior_prediction = prediction_probe
                    self._prior_prediction_db_id = existing_probe.id
                    self._prior_lineage_id = theory.lineage_id if theory else None

                    # Retrieve prior attribution from Experience causal_events
                    self._prior_attribution = None
                    if theory:
                        active_exp = self.experience_repo.load_by_lineage(
                            theory.lineage_id
                        )
                        if active_exp and active_exp.causal_events:
                            last_event = active_exp.causal_events[-1]
                            from flows.theory_flow.attribution import \
                                AttributionResult

                            self._prior_attribution = AttributionResult(
                                theory_id=theory.id,
                                theory_claim=last_event.get("theory_claim", ""),
                                outcome=last_event.get("outcome", ""),
                                components_passed=last_event.get(
                                    "components_passed", []
                                ),
                                components_failed=last_event.get(
                                    "components_failed", []
                                ),
                                root_cause_component=last_event.get("root_cause"),
                                attribution_reasoning=last_event.get(
                                    "attribution_reasoning", ""
                                ),
                            )

                    # Retrieve prior transition context
                    with SessionLocal() as session:
                        tp_model = (
                            session.query(TransitionPressureModel)
                            .filter(TransitionPressureModel.date == date_str)
                            .first()
                        )
                        if tp_model:
                            horizon_view = self.horizon_engine.compute(
                                self._run_market_observations
                            )
                            self._prior_transition_context = {
                                "confidence": existing_probe.confidence,
                                "usefulness": (
                                    getattr(theory, "llm_evaluation", {}).get(
                                        "overall_score", 0.5
                                    )
                                    if theory
                                    else 0.5
                                ),
                                "contradiction": (
                                    tp_model.stability_score if tp_model else 0.0
                                ),
                                "pressure": (
                                    tp_model.pressure_score if tp_model else 0.0
                                ),
                                "breakout": (
                                    tp_model.breakout_risk if tp_model else False
                                ),
                                "bias": (
                                    tp_model.direction_bias if tp_model else "neutral"
                                ),
                                "horizon": horizon_view,
                                "theory_summary": theory.summary if theory else "",
                            }

                    # Keep regime memories updated
                    regime_subtype = getattr(market_obs, "regime_subtype", "neutral")
                    actual_dir = (
                        1
                        if "higher" in actual_dir_str
                        else -1 if "lower" in actual_dir_str else 0
                    )

                    invalidation_triggered = False
                    with SessionLocal() as session:
                        res_model = (
                            session.query(PredictionResultModel)
                            .filter(PredictionResultModel.date == date_str)
                            .first()
                        )
                        probe_model = None
                        if res_model:
                            invalidation_triggered = res_model.invalidation_triggered
                            if res_model.prediction_id:
                                probe_model = (
                                    session.query(PredictionProbeModel)
                                    .filter(
                                        PredictionProbeModel.id
                                        == res_model.prediction_id
                                    )
                                    .first()
                                )

                    # Reconstruct prior_prediction_result dict
                    prior_pred_res_dict = {}
                    if res_model:
                        prior_pred_res_dict = {
                            "prior_direction": res_model.prior_direction,
                            "actual_direction": res_model.actual_direction,
                            "direction_score": res_model.direction_score,
                            "invalidation_triggered": res_model.invalidation_triggered,
                            "confidence": (
                                probe_model.confidence if probe_model else 0.5
                            ),
                            "invalidation": (
                                probe_model.invalidation if probe_model else ""
                            ),
                        }

                    # Get contradiction score
                    contra_score = 0.0
                    if tp_model:
                        contra_score = tp_model.stability_score

                    # Get regime matches
                    active_theory_count = (
                        self.theory_lineage.active_count() if self.theory_lineage else 0
                    )
                    preliminary_regime_signature = self.regime_memory.build_signature(
                        date=date_str,
                        observation=market_obs,
                        confidence_values=(
                            self._confidence_history[-10:]
                            if self._confidence_history
                            else [0.5]
                        ),
                        contradiction_severity=min(
                            1.0,
                            len(getattr(market_obs, "contradiction_markers", [])) * 0.2,
                        ),
                        active_theory_count=active_theory_count,
                    )
                    regime_matches = self.regime_memory.retrieve(
                        preliminary_regime_signature,
                        getattr(market_obs, "contradiction_markers", []),
                    )

                    theory_usefulness = {"score": 0.0, "label": "No active theory"}
                    if theory:
                        lineage_record = (
                            self.theory_lineage.theories.get(theory.id)
                            if self.theory_lineage
                            else None
                        )
                        theory_usefulness = self.epistemic_scoring.score_theory(
                            lineage_record=lineage_record,
                            regime_matches=regime_matches,
                            prior_prediction_result=prior_pred_res_dict,
                            contradiction_score=contra_score,
                            reflection_summary=(
                                reflection.reflection_summary if reflection else ""
                            ),
                        )

                    self.regime_continuity_memory.update(
                        date=date_str,
                        subtype=regime_subtype,
                        usefulness=theory_usefulness.get("score", 0.0),
                        actual_direction=actual_dir,
                        falsified=invalidation_triggered,
                    )

                    continue  # Fast forward to next day!

                # Instrumentation: Reset daily tracking flags
                exp_create_called = False
                exp_attach_called = False
                exp_close_called = False
                lineage_id_val = "N/A"
                audit_created = False
                audit_mutated = False
                audit_merged = False
                audit_revived = False
                audit_retired = False

                current_dialectical_data = None
                dialectical_data = None

                # Synthesize observation
                market_obs = synthesizer.synthesize(day_idx)

                # Track directional persistence
                actual_dir_str = market_obs.trend_state.lower()
                dir_val = (
                    1
                    if "higher" in actual_dir_str
                    else -1 if "lower" in actual_dir_str else 0
                )
                self._actual_directions_val_history.append(dir_val)

                persistence_3d = (
                    mean(self._actual_directions_val_history[-3:])
                    if len(self._actual_directions_val_history) >= 3
                    else 0.0
                )
                persistence_5d = (
                    mean(self._actual_directions_val_history[-5:])
                    if len(self._actual_directions_val_history) >= 5
                    else 0.0
                )
                persistence_10d = (
                    mean(self._actual_directions_val_history[-10:])
                    if len(self._actual_directions_val_history) >= 10
                    else 0.0
                )

                # Phase 1: Trend Persistence Classification
                def classify_persistence(val):
                    if val > 0.6:
                        return "Persistent Higher"
                    if val < -0.6:
                        return "Persistent Lower"
                    return "Mixed"

                reg_5d = classify_persistence(persistence_5d)
                # Phase 2: Observation Integration (Temporal continuity context for Theory/Reflection)
                market_obs.observation_text += f"\nTrend Persistence: 3D: {classify_persistence(persistence_3d)}, 5D: {reg_5d}, 10D: {classify_persistence(persistence_10d)}. Overall Regime: {reg_5d}."

                # v1.9 Transition Detection and Recording
                if day_idx > 0 and self._prior_transition_context:
                    prev_obs = self._run_market_observations[-1]
                    ctx = self._prior_transition_context

                    # Detect transitions (e.g., range_bound -> higher)
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

                        # Identify meaningful transitions
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
                            self.transition_memory.record_transition(example)

                # retrieve historical memory: only prior run-local state is visible
                recent_theories = list(reversed(self._run_theories[-5:]))
                recent_validations = list(reversed(self._run_validations[-5:]))
                recent_reflections = list(reversed(self._run_reflections[-5:]))

                # compute horizons using current and prior observations only
                horizon_view = self.horizon_engine.compute(
                    [*self._run_market_observations, market_obs]
                )
                horizon_context = f"Horizon Context: {horizon_view.summary()}"

                prior_confidence_values = (
                    list(self._confidence_history[-10:])
                    if self._confidence_history
                    else [0.5]
                )
                marker_severity = min(
                    1.0, len(getattr(market_obs, "contradiction_markers", [])) * 0.2
                )

                # v2.0 Regime Calculation for Memory and Analysis
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
                    self.theory_lineage.active_count() if self.theory_lineage else 0
                )
                preliminary_regime_signature = self.regime_memory.build_signature(
                    date=date_str,
                    observation=market_obs,
                    confidence_values=prior_confidence_values,
                    contradiction_severity=marker_severity,
                    active_theory_count=active_theory_count,
                )
                regime_matches = self.regime_memory.retrieve(
                    preliminary_regime_signature,
                    getattr(market_obs, "contradiction_markers", []),
                )
                self._regime_matches_by_step.append(regime_matches)
                regime_context = self._format_regime_context(regime_matches)

                # v3.0 WIRING: Update analog divergence if similarity threshold met
                if regime_matches and regime_matches[0].similarity > 0.8:
                    analog = regime_matches[0]
                    # v3.0 FIX: Safely retrieve signature from RegimeMatch object
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

                # observe
                obs_event = ObservationEvent(
                    source_type="replay",
                    raw_content=(f"{market_obs.observation_text}\n{horizon_context}"),
                )

                # abstract
                abstraction = self.abstraction_flow.process(obs_event)

                # generate/mutate
                historical_context = self._format_historical_context(
                    recent_validations,
                    recent_reflections,
                )
                # v3.0 Extract regime subtype and falsifiability conditions
                regime_subtype = getattr(market_obs, "regime_subtype", "neutral")
                falsifiability_conditions = getattr(
                    market_obs, "falsifiability_conditions", []
                )

                # CHANGE: Retrieve Active Lessons relevant to current regime via multi-dimensional weighted similarity
                relevant_lessons = []
                if self.lesson_repo:
                    from market.replay.lesson_record import LessonStatus

                    all_active = [
                        l
                        for l in self.lesson_repo.list_lessons()
                        if getattr(l, "status", None) == LessonStatus.ACTIVE
                        or getattr(l, "status", None) == "active"
                    ]

                    derived_data = obs_data.get("derived") or {}
                    vol_30d = float(derived_data.get("volatility_30d", 0.0))
                    vol_regime = (
                        "compressed"
                        if vol_30d < 0.8
                        else "expanded" if vol_30d > 1.5 else "normal"
                    )
                    ret_3d = float(derived_data.get("return_3d", 0.0))
                    mom_regime = (
                        "strengthening"
                        if ret_3d > 0.5
                        else "weakening" if ret_3d < -0.5 else "flat"
                    )
                    vol_state = derived_data.get("volume_state", "normal")
                    part_confirm = getattr(
                        market_obs, "participation_confirmation", "normal"
                    )

                    scored_lessons = []
                    for l in all_active:
                        tr = getattr(l, "target_regime", {}) or {}

                        subtype_match = (
                            1.0
                            if str(tr.get("regime_subtype", "")).lower()
                            == str(regime_subtype).lower()
                            else 0.0
                        )
                        volatility_match = (
                            1.0
                            if str(tr.get("volatility", "")).lower()
                            == str(vol_regime).lower()
                            else 0.0
                        )
                        momentum_match = (
                            1.0
                            if str(tr.get("momentum", "")).lower()
                            == str(mom_regime).lower()
                            else 0.0
                        )

                        tr_volume = tr.get("volume") or tr.get("participation") or ""
                        volume_val = vol_state or part_confirm or ""
                        participation_match = (
                            1.0
                            if str(tr_volume).lower() == str(volume_val).lower()
                            else 0.0
                        )

                        sim = (
                            0.4 * subtype_match
                            + 0.3 * volatility_match
                            + 0.2 * momentum_match
                            + 0.1 * participation_match
                        )

                        if sim > 0.0:
                            scored_lessons.append((l, sim))

                    scored_lessons.sort(key=lambda x: x[1], reverse=True)
                    relevant_lessons = [
                        item[0].lesson_text for item in scored_lessons[:5]
                    ]
                    self._prior_lessons = relevant_lessons

                # v3.1 Regime Continuity Retrieval
                regime_history = self.regime_continuity_memory.summary(regime_subtype)

                if self.lineage_debug:
                    print(
                        "[Theory Input]",
                        {
                            "date": date_str,
                            "regime_subtype": regime_subtype,
                            "falsifiability_conditions": falsifiability_conditions,
                            "analog_divergence_claim": getattr(
                                market_obs, "analog_divergence_claim", ""
                            ),
                        },
                    )

                # v3.3 Relevance Gate for Dialectical Synthesis
                active_synthesis = None
                if self._prior_dialectical_synthesis:
                    max_sim = (
                        max(
                            [
                                (
                                    m.get("similarity")
                                    if isinstance(m, dict)
                                    else getattr(m, "similarity", 0.0)
                                )
                                for m in regime_matches
                            ]
                            + [0.0]
                        )
                        if regime_matches
                        else 0.0
                    )

                    if (
                        regime_subtype == self._prior_dialectical_subtype
                        or max_sim > 0.8
                    ):
                        active_synthesis = self._prior_dialectical_synthesis

                # Determine if we are mutating an existing active theory
                prior_theory = None
                prior_attribution = None
                if self._run_theories and self.theory_lineage:
                    active_records = self.theory_lineage.active_theories()
                    active_ids = {t.id for t in active_records} | {
                        t.lineage_id for t in active_records
                    }
                    last_theory = self._run_theories[-1]
                    if (
                        last_theory.id in active_ids
                        or getattr(self, "_prior_lineage_id", None) in active_ids
                    ):
                        prior_theory = last_theory
                        prior_attribution = getattr(self, "_prior_attribution", None)

                # Query Phase 2 records
                latest_wm = self.knowledge_repository.get_latest_world_model()
                world_model_narrative = (
                    latest_wm.narrative_summary if latest_wm else None
                )
                active_principles = self.knowledge_repository.list_principles(
                    status="active"
                ) + self.knowledge_repository.list_principles(status="stable")
                active_open_questions = self.knowledge_repository.list_open_questions(
                    status="active"
                )

                # Novelty Detection Gate check
                is_novel = True
                decision = "GENERATE"
                novelty_score = 1.0
                novelty_rationale = ""

                prior_pred_obj = None
                prior_pred_res_obj = None

                if self._prior_prediction:
                    prior_pred_obj = self._prior_prediction
                if getattr(self, "_prior_prediction_result", None):
                    prior_pred_res_obj = self._prior_prediction_result

                if prior_theory:
                    decision, novelty_score, novelty_rationale = (
                        self.novelty_gate.is_novel(
                            observation=market_obs,
                            regime_subtype=regime_subtype,
                            prior_theory=prior_theory,
                            prior_prediction=prior_pred_obj,
                            prior_prediction_result=prior_pred_res_obj,
                            prior_attribution=prior_attribution,
                            active_principles=active_principles,
                        )
                    )
                self.novelty_decision_history.append(decision)

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
                    self._log(
                        f"[NOVELTY GATE] Decision: REINFORCE | Score: {novelty_score:.2f} | {novelty_rationale}"
                    )
                    import copy

                    theory = copy.deepcopy(prior_theory)
                    theory.id = str(uuid4())

                    daily_theory_word_count = (
                        len(theory.summary.split()) if theory.summary else 0
                    )
                    daily_mechanism_count = (
                        len(theory.summary_structured.mechanism_components)
                        if (
                            theory.summary_structured
                            and theory.summary_structured.mechanism_components
                        )
                        else 0
                    )
                    daily_conditional_clauses_count = count_conditional_clauses(
                        theory.summary_structured
                    )
                    daily_exceptions_added = (
                        1
                        if (
                            theory.summary_structured
                            and theory.summary_structured.unless
                            and theory.summary_structured.unless
                            != "no contrary evidence emerges"
                        )
                        else 0
                    )
                    daily_mechanisms_retired = 0
                    daily_mechanisms_added = 0
                    daily_mechanisms_modified = 0
                    daily_mechanism_stability = 1.0

                elif decision == "REVISE":
                    self._log(
                        f"[NOVELTY GATE] Decision: REVISE | Score: {novelty_score:.2f} | {novelty_rationale}"
                    )
                    try:
                        # Ensure prior theory has a structured representation and assign MECH_xxx IDs if missing
                        if not prior_theory.summary_structured:
                            from cognition.schemas.theory.theory import (
                                Branch, TheoryStructured)

                            prior_theory.summary_structured = TheoryStructured(
                                claim=prior_theory.summary,
                                if_branch=Branch(condition="always", action="observe"),
                                else_branch=Branch(condition="never", action="ignore"),
                                falsified_if="never",
                                mechanism_components=[],
                            )

                        # Ensure all prior components have sequential mechanism_ids
                        for idx, comp in enumerate(
                            prior_theory.summary_structured.mechanism_components
                        ):
                            if not comp.mechanism_id:
                                comp.mechanism_id = f"MECH_{idx+1:03d}"

                        # Prepare Stage 1 Prompt
                        prior_mechs = []
                        for (
                            comp
                        ) in prior_theory.summary_structured.mechanism_components:
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

                        failed_comps = (
                            prior_attribution.components_failed
                            if prior_attribution
                            else []
                        )
                        passed_comps = (
                            getattr(prior_attribution, "components_passed", [])
                            if prior_attribution
                            else []
                        )
                        root_cause = (
                            getattr(
                                prior_attribution, "root_cause_component", "Unknown"
                            )
                            if prior_attribution
                            else "Unknown"
                        )
                        attr_reasoning = (
                            getattr(
                                prior_attribution,
                                "attribution_reasoning",
                                "No attribution reasoning available.",
                            )
                            if prior_attribution
                            else "No attribution reasoning available."
                        )

                        from cognition.schemas.knowledge.ontology import \
                            OntologyRegistry

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
                        res_raw = self.theory_flow.client.generate(
                            prompt_stage1, json_format=True
                        )
                        res = json.loads(res_raw)

                        retained_ids = res.get("retained_mechanism_ids", [])
                        removed_ids = res.get("removed_mechanism_ids", [])
                        added_mechs = res.get("added_mechanisms", [])
                        modified_mechs = res.get("modified_mechanisms", [])

                        from cognition.schemas.theory.theory import (
                            Branch, MechanismComponent)

                        total_before = len(
                            prior_theory.summary_structured.mechanism_components
                        )
                        ret_count = 0
                        add_count = len(added_mechs)
                        mod_count = len(modified_mechs)

                        new_components = []
                        modified_by_id = {
                            m["mechanism_id"]: m
                            for m in modified_mechs
                            if "mechanism_id" in m
                        }

                        # Update status for retired mechanisms
                        for rid in removed_ids:
                            mech_obj = self.knowledge_repository.get_mechanism(rid)
                            if mech_obj:
                                mech_obj.times_retired += 1
                                mech_obj.status = "retired"
                                self.knowledge_repository.save_mechanism(mech_obj)

                        for (
                            comp
                        ) in prior_theory.summary_structured.mechanism_components:
                            if comp.mechanism_id in removed_ids:
                                continue

                            if (
                                comp.mechanism_id in retained_ids
                                or comp.mechanism_id in modified_by_id
                            ):
                                ret_count += 1
                                if comp.mechanism_id in modified_by_id:
                                    mod_data = modified_by_id[comp.mechanism_id]
                                    updated_comp = MechanismComponent(
                                        component_id=mod_data.get(
                                            "component_id", comp.component_id
                                        ),
                                        description=mod_data.get(
                                            "description", comp.description
                                        ),
                                        observable=mod_data.get(
                                            "observable", comp.observable
                                        ),
                                        expected_behavior=mod_data.get(
                                            "expected_behavior", comp.expected_behavior
                                        ),
                                        dependency=mod_data.get(
                                            "dependency", comp.dependency
                                        ),
                                        concept_tags=mod_data.get(
                                            "concept_tags", comp.concept_tags
                                        ),
                                        relation_type=mod_data.get(
                                            "relation_type", comp.relation_type
                                        ),
                                        mechanism_id=comp.mechanism_id,
                                    )
                                    new_components.append(updated_comp)

                                    # Update registry
                                    mech_obj = self.knowledge_repository.get_mechanism(
                                        comp.mechanism_id
                                    )
                                    if mech_obj:
                                        mech_obj.times_modified += 1
                                        mech_obj.description = mod_data.get(
                                            "description", mech_obj.description
                                        )
                                        mech_obj.concept_tags = mod_data.get(
                                            "concept_tags", mech_obj.concept_tags
                                        )
                                        mech_obj.relation_type = mod_data.get(
                                            "relation_type", mech_obj.relation_type
                                        )
                                        mech_obj.last_seen = day_idx
                                        if regime_subtype not in mech_obj.regimes_seen:
                                            mech_obj.regimes_seen.append(regime_subtype)
                                        self.knowledge_repository.save_mechanism(
                                            mech_obj
                                        )
                                else:
                                    new_components.append(comp)

                        from flows.knowledge_flow.mechanism_engine import \
                            match_and_register_in_registry

                        for add_data in added_mechs:
                            mech_id = match_and_register_in_registry(
                                add_data,
                                self.knowledge_repository,
                                step=day_idx,
                                regime=regime_subtype,
                            )
                            new_comp = MechanismComponent(
                                component_id=add_data.get(
                                    "component_id", "new_mechanism"
                                ),
                                description=add_data.get("description", ""),
                                observable=add_data.get("observable", ""),
                                expected_behavior=add_data.get("expected_behavior", ""),
                                dependency=add_data.get("dependency"),
                                concept_tags=add_data.get("concept_tags", []),
                                relation_type=add_data.get("relation_type"),
                                mechanism_id=mech_id,
                            )
                            new_components.append(new_comp)

                        # Stage 2: Narrative Rendering Prompt
                        final_mechs = []
                        for comp in new_components:
                            final_mechs.append(
                                {
                                    "mechanism_id": comp.mechanism_id,
                                    "component_id": comp.component_id,
                                    "description": comp.description,
                                    "expected_behavior": comp.expected_behavior,
                                }
                            )
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
                        concise_narrative = self.theory_flow.client.generate(
                            prompt_stage2, json_format=False
                        ).strip()
                        concise_narrative = (
                            concise_narrative.strip('"').strip("'").strip()
                        )

                        # Construct mutated theory
                        import copy

                        theory = copy.deepcopy(prior_theory)
                        theory.id = str(uuid4())

                        def to_str(val, default="") -> str:
                            if val is None:
                                return default
                            if isinstance(val, list):
                                return ", ".join(str(x) for x in val)
                            return str(val)

                        def to_branch(branch_val, default_branch) -> Branch:
                            if isinstance(branch_val, dict):
                                return Branch(
                                    condition=to_str(
                                        branch_val.get("condition"),
                                        default_branch.condition,
                                    ),
                                    action=to_str(
                                        branch_val.get("action"), default_branch.action
                                    ),
                                )
                            return default_branch

                        theory.summary_structured.claim = concise_narrative
                        theory.summary_structured.mechanism_components = new_components

                        # Map other fields from JSON or keep default
                        theory.summary_structured.if_branch = to_branch(
                            res.get("if_branch"), theory.summary_structured.if_branch
                        )
                        theory.summary_structured.else_branch = to_branch(
                            res.get("else_branch"),
                            theory.summary_structured.else_branch,
                        )
                        theory.summary_structured.unless = to_str(
                            res.get("unless"), theory.summary_structured.unless
                        )
                        theory.summary_structured.falsified_if = to_str(
                            res.get("falsified_if"),
                            theory.summary_structured.falsified_if,
                        )
                        theory.summary_structured.falsification_conditions = res.get(
                            "falsification_conditions",
                            theory.summary_structured.falsification_conditions,
                        )

                        theory.summary = concise_narrative
                        theory.thesis = concise_narrative

                        # Compute complexity metrics
                        daily_theory_word_count = len(concise_narrative.split())
                        daily_mechanism_count = len(new_components)
                        daily_conditional_clauses_count = count_conditional_clauses(
                            theory.summary_structured
                        )
                        daily_exceptions_added = (
                            1
                            if (
                                theory.summary_structured.unless
                                and theory.summary_structured.unless
                                != "no contrary evidence emerges"
                            )
                            else 0
                        )
                        daily_mechanisms_retired = len(removed_ids)
                        daily_mechanisms_added = add_count
                        daily_mechanisms_modified = mod_count
                        daily_mechanism_stability = (
                            (ret_count / total_before) if total_before > 0 else 1.0
                        )
                        daily_words_before_mutation = (
                            len(prior_theory.summary.split())
                            if (prior_theory and prior_theory.summary)
                            else 0
                        )
                        daily_words_after_mutation = len(concise_narrative.split())
                        daily_mechanisms_before_mutation = (
                            len(prior_theory.summary_structured.mechanism_components)
                            if (
                                prior_theory
                                and prior_theory.summary_structured
                                and prior_theory.summary_structured.mechanism_components
                            )
                            else 0
                        )
                        daily_mechanisms_after_mutation = len(new_components)

                    except Exception as e:
                        print(
                            f"WARNING: Mechanism-First Theory Revision failed: {e}. Falling back to standard generation."
                        )
                        decision = "GENERATE"

                if decision == "GENERATE":
                    self._log(
                        f"[NOVELTY GATE] Decision: GENERATE | Score: {novelty_score:.2f} | {novelty_rationale}"
                    )
                    theory, branch_stats = self.theory_flow.process(
                        abstraction,
                        historical_context=historical_context,
                        market_memory_context=regime_context,
                        current_market_observation=market_obs.observation_text,
                        reflective_memory_summary=horizon_context,
                        regime_subtype=regime_subtype,
                        falsifiability_conditions=falsifiability_conditions,
                        analog_divergence_claim=getattr(
                            market_obs, "analog_divergence_claim", ""
                        ),
                        regime_history=regime_history,
                        dialectical_synthesis=active_synthesis,
                        relevant_lessons=relevant_lessons,
                        prior_theory=prior_theory,
                        prior_attribution=prior_attribution,
                        world_model_narrative=world_model_narrative,
                        active_principles=active_principles,
                        active_open_questions=active_open_questions,
                        step=day_idx,
                        knowledge_repository=self.knowledge_repository,
                    )

                    daily_theory_word_count = (
                        len(theory.summary.split()) if theory.summary else 0
                    )
                    daily_mechanism_count = (
                        len(theory.summary_structured.mechanism_components)
                        if (
                            theory.summary_structured
                            and theory.summary_structured.mechanism_components
                        )
                        else 0
                    )
                    daily_conditional_clauses_count = count_conditional_clauses(
                        theory.summary_structured
                    )
                    daily_exceptions_added = (
                        1
                        if (
                            theory.summary_structured
                            and theory.summary_structured.unless
                            and theory.summary_structured.unless
                            != "no contrary evidence emerges"
                        )
                        else 0
                    )
                    daily_mechanisms_retired = 0
                    daily_mechanisms_added = (
                        len(theory.summary_structured.mechanism_components)
                        if (
                            theory.summary_structured
                            and theory.summary_structured.mechanism_components
                        )
                        else 0
                    )
                    daily_mechanisms_modified = 0
                    daily_mechanism_stability = 1.0

                if self.lineage_debug:
                    # v3.0 Consistency debug - prefer structured claim if available
                    theory_text = (
                        theory.summary_structured.claim
                        if theory.summary_structured
                        else theory.summary
                    )  # Canonical access with fallback
                    print("[Theory Output]", theory_text[:250])

                # Theory lineage updates happen before contradiction retirement so
                # the current abstraction can revive or mutate existing cognition.
                theory_step_info = {
                    "created": 0,
                    "mutated": 0,
                    "merged": 0,
                    "retired": 0,
                    "revived": 0,
                }
                lineage_record = None
                abstraction_text = getattr(
                    abstraction, "abstraction_summary", str(abstraction)
                )
                try:
                    if self.theory_lineage:
                        lineage_result = self.theory_lineage.evolve_theory(
                            abstraction=abstraction_text,
                            confidence_state={
                                "empirical_confidence": getattr(
                                    theory.confidence_state, "empirical_confidence", 0.5
                                ),
                                "regime_confidence": getattr(
                                    theory.confidence_state, "regime_confidence", 0.5
                                ),
                                "reflection_confidence": getattr(
                                    theory.confidence_state,
                                    "reflection_confidence",
                                    0.5,
                                ),
                                "theoretical_coherence": getattr(
                                    theory.confidence_state,
                                    "theoretical_coherence",
                                    0.5,
                                ),
                                "contradiction_pressure": getattr(
                                    theory.confidence_state,
                                    "contradiction_pressure",
                                    0.0,
                                ),
                            },
                            step=day_idx,
                        )
                        lineage_record = lineage_result["record"]
                        lineage_id_val = lineage_result.get(
                            "lineage_id", "N/A"
                        )  # Use the stable lineage_id from lineage_result
                        audit_created = lineage_result.get("created", False)
                        audit_mutated = lineage_result.get("mutated", False)
                        audit_merged = lineage_result.get("merged", False)
                        audit_revived = lineage_result.get(
                            "revived", False
                        )  # Note: revived logic handled separately below

                        theory_step_info["created"] = int(lineage_result["created"])
                        theory_step_info["mutated"] = int(lineage_result["mutated"])
                        theory_step_info["merged"] = int(lineage_result["merged"])

                        if self.lineage_debug and lineage_record:
                            action = (
                                "continued"
                                if lineage_result.get("continued")
                                else (
                                    "merged"
                                    if lineage_result["merged"]
                                    else (
                                        "mutated"
                                        if lineage_result["mutated"]
                                        else "created"
                                    )
                                )
                            )
                            self._log(
                                f"[Lineage] day={day_idx} action={action} "
                                f"record_id={lineage_record.id} parent_id={lineage_result.get('parent_id')} "
                                f"survival_steps={lineage_record.survival_steps} "
                                f"confidence={lineage_record.confidence:.3f}"
                            )

                        # Experience Integration: create or attach
                        if lineage_record:
                            # AUDIT TRACE: Capture the shift in IDs during mutation
                            parent_id_for_log = lineage_result.get(
                                "parent_id", "N/A"
                            )  # Use parent_id from result for logging
                            if lineage_result.get("mutated") and self.verbose:
                                print(
                                    f"  [LINEAGE AUDIT] MUTATION DETECTED: Old Lineage (Parent): {parent_id_for_log} -> New Lineage (Child): {lineage_record.id} (Stable Lineage: {lineage_id_val})"
                                )

                            if lineage_result.get("created"):
                                if self.verbose:
                                    print(
                                        f"  [AUDIT] Calling create_experience for lineage {lineage_record.id}"
                                    )
                                regime_context_list = (
                                    self._build_experience_regime_context(
                                        market_obs,
                                        obs_data,
                                        regime_subtype,
                                    )
                                )
                                self.experience_engine.create_experience(
                                    theory_id=theory.id,
                                    lineage_id=lineage_id_val,
                                    date=date_str,
                                    regime_context=regime_context_list,
                                    theory_subtype=regime_subtype,
                                )
                                exp_create_called = True
                            elif lineage_result.get("mutated") or lineage_result.get(
                                "merged"
                            ):
                                # Use the stable lineage_id for attaching theories to the experience
                                if self.verbose:
                                    print(
                                        f"  [AUDIT] Calling attach_theory for lineage {lineage_id_val} (Theory ID: {theory.id})"
                                    )
                                self.experience_engine.attach_theory(
                                    lineage_id_val, theory.id
                                )  # Use stable lineage_id
                                exp_attach_called = True

                        # Instrumentation: Log lineage/experience changes
                        if (
                            lineage_record and lineage_id_val != last_lineage_id
                        ):  # Compare stable lineage_id
                            if self.verbose:
                                print(
                                    f"!!! LINEAGE CHANGE: {last_lineage_id} -> {lineage_record.id}"
                                )
                            last_lineage_id = lineage_record.id
                        if exp_create_called and self.verbose:
                            print(
                                f"!!! NEW EXPERIENCE CREATED: exp_{lineage_record.id}_{date_str}"
                            )

                        if lineage_record and lineage_record.confidence_state:
                            theory.confidence_state.empirical_confidence = (
                                lineage_record.confidence_state.get(
                                    "empirical_confidence", 0.5
                                )
                            )
                            theory.confidence_state.regime_confidence = (
                                lineage_record.confidence_state.get(
                                    "regime_confidence", 0.5
                                )
                            )
                            theory.confidence_state.reflection_confidence = (
                                lineage_record.confidence_state.get(
                                    "reflection_confidence", 0.5
                                )
                            )
                            theory.confidence_state.theoretical_coherence = (
                                lineage_record.confidence_state.get(
                                    "theoretical_coherence", 0.5
                                )
                            )
                            theory.confidence_state.contradiction_pressure = (
                                lineage_record.confidence_state.get(
                                    "contradiction_pressure", 0.0
                                )
                            )
                except Exception as e:
                    self._log(
                        f"WARNING: Theory lineage evolution failed for day {date_str}: {e}"
                    )

                # detect contradictions
                contradiction_result = self.contradiction_detector.detect(
                    current_theory=theory,
                    historical_theories=recent_theories,
                    validations=recent_validations,
                    reflections=recent_reflections,
                    current_observation=market_obs,
                    historical_observations=self._run_market_observations[-5:],
                )

                # Register contradictions before retirement so repeated conflict
                # can affect lifecycle state in the same deterministic step.
                contradiction_step_info = {
                    "new_contradictions": 0,
                    "resolved_contradictions": 0,
                    "active_contradictions": 0,
                    "carried_forward_contradictions": 0,
                }
                try:
                    if self.contradiction_registry and lineage_record:
                        descriptions = contradiction_result.get("indicators", [])
                        contradiction_step_info = (
                            self.contradiction_registry.register_contradictions(
                                theory_id=lineage_record.id,
                                descriptions=descriptions,
                                severity=float(contradiction_result.get("score", 0.0)),
                                step=day_idx,
                            )
                        )
                        if descriptions:
                            lineage_record = self.theory_lineage.record_contradictions(
                                tid=lineage_record.id,
                                descriptions=descriptions,
                                step=day_idx,
                            )

                        # Experience Integration: record contradiction
                        if descriptions:
                            self.experience_engine.record_contradiction(
                                lineage_id_val, signatures=descriptions
                            )
                except Exception:
                    pass

                # v3.2 Dialectical Synthesis Layer - Triggered after final contradiction state but before retirement
                contradiction_score = float(contradiction_result.get("score", 0.0))
                if self.lineage_debug:
                    print(f"[CONTRADICTION SCORE] score={contradiction_score:.3f}")
                    print(f"raw contradiction score={contradiction_score:.3f}")
                    print(f"source field=contradiction_result['score']")

                active_lineage_records = (
                    self.theory_lineage.active_theories() if self.theory_lineage else []
                )
                active_theory_count = len(active_lineage_records)
                will_trigger = (
                    active_theory_count >= 2
                    and contradiction_score
                    >= self.contradiction_detector.CONFIG.get(
                        "threshold_synthesis", 0.35
                    )
                )
                if self.lineage_debug:
                    print(f"\n[SYNTHESIS CHECK]")
                    print(f"active_theories={active_theory_count}")
                    print(f"contradiction_score={contradiction_score:.3f}")
                    print(f"will_trigger={will_trigger}")
                if will_trigger:
                    self.total_synthesis_triggered += 1

                    # Aggregate component failures for the current regime subtype
                    component_failures = {}
                    if hasattr(self, "experience_repo") and self.experience_repo:
                        try:
                            for exp in self.experience_repo.get_all():
                                if (
                                    getattr(exp, "theory_subtype", None)
                                    == regime_subtype
                                ):
                                    f_counts = (
                                        getattr(exp, "component_failure_counts", {})
                                        or {}
                                    )
                                    for comp, count in f_counts.items():
                                        component_failures[comp] = (
                                            component_failures.get(comp, 0) + count
                                        )
                        except Exception as e:
                            logger.warning(
                                f"Failed to aggregate experience failures: {e}"
                            )

                    dialectical_data = self.dialectical_synthesizer.synthesize(
                        observation_text=market_obs.observation_text,
                        active_theories=active_lineage_records,
                        contradiction_indicators=contradiction_result.get(
                            "indicators", []
                        ),
                        regime_subtype=regime_subtype,
                        falsifiability_conditions=falsifiability_conditions,
                        relevant_lessons=relevant_lessons,
                        component_failures=component_failures,
                    )
                    if dialectical_data:
                        current_dialectical_data = dialectical_data
                        if self.lineage_debug:
                            print("\n[SYNTHESIS]")
                            print(
                                f"Shared:\n{dialectical_data.get('shared_premise')}\n"
                            )
                            print(f"Conflict:\n{dialectical_data.get('conflict')}\n")
                            print(
                                f"Synthesis:\n{dialectical_data.get('synthesis_summary')}"
                            )

                # retire stale theories
                try:
                    if self.theory_lineage:
                        contra_score = float(contradiction_result.get("score", 0.0))

                        # NEW: Only retire if the theory has had at least one chance to be validated
                        # This prevents "infant mortality" from immediate contradictions
                        is_new_lineage = (
                            lineage_record.created_at_step == day_idx
                            if lineage_record
                            else False
                        )

                        # Only proceed with retirement if not a new lineage OR contradiction is extreme
                        if not is_new_lineage or contra_score > 0.8:
                            retired_records = self.theory_lineage.retire_stale_theories(
                                step=day_idx,
                                contradiction_severity=contra_score,
                                current_record_id=(
                                    lineage_record.id if lineage_record else None
                                ),
                            )
                        else:
                            retired_records = []

                        theory_step_info["retired"] = len(retired_records)
                        if self.lineage_debug and retired_records:
                            self._log(
                                f"[Lineage] day={day_idx} retired={','.join([r.id for r in retired_records])}"
                            )
                        if self.contradiction_registry:
                            # Experience Integration: close retired experiences
                            for retired_record in retired_records:
                                self.experience_engine.close_experience(
                                    retired_record.lineage_id,  # Use stable lineage ID
                                    date_str,
                                    f"Theory lineage {retired_record.id} retired after {retired_record.survival_steps} steps.",
                                )
                                exp_close_called = True

                            for retired_record in retired_records:
                                contradiction_step_info[
                                    "resolved_contradictions"
                                ] += self.contradiction_registry.resolve_for_theory(
                                    retired_record.id,
                                    day_idx,
                                )
                            contradiction_step_info["active_contradictions"] = (
                                self.contradiction_registry.active_count()
                            )
                        audit_retired = len(retired_records) > 0
                except Exception:
                    pass

                # revive if matched
                try:
                    if self.theory_lineage:
                        revived_records = self.theory_lineage.revive_matching_theories(
                            abstraction=abstraction_text,
                            step=day_idx,
                        )
                        audit_revived = len(revived_records) > 0
                        theory_step_info["revived"] = len(revived_records)
                        if self.lineage_debug and revived_records:
                            self._log(
                                f"[Lineage] day={day_idx} revived={','.join([r.id for r in revived_records])}"
                            )
                        # Experience Integration: attach revived theories if lineage is reactivated
                        for revived_record in revived_records:
                            if self.verbose:
                                print(
                                    f"  [AUDIT] Calling attach_theory (REVIVAL) for lineage {revived_record.lineage_id} (Theory ID: {theory.id})"
                                )  # Use revived_record.lineage_id
                            self.experience_engine.attach_theory(
                                revived_record.lineage_id, theory.id
                            )
                            exp_attach_called = True
                except Exception:
                    pass

                # Instrumentation: Print Daily Trace
                if self.verbose:
                    print(f"\nDAY {date_str}")
                    print(f"theory_id={theory.id}")
                    print(f"lineage_id={lineage_id_val}")
                    print(f"\nlineage_result:")
                    print(f"created={audit_created}")
                    print(f"mutated={audit_mutated}")
                    print(f"merged={audit_merged}")
                    print(f"revived={audit_revived}")
                    print(f"retired={audit_retired}")
                    print(f"\nexperience actions:")
                    print(f"create_experience={exp_create_called}")
                    print(f"attach_theory={exp_attach_called}")
                    print(f"close_experience={exp_close_called}")

                # Instrumentation: Accumulate audit table row
                action = "none"
                if exp_create_called:
                    action = "create"
                elif exp_attach_called:
                    action = "attach"
                elif exp_close_called:
                    action = "close"

                self._lineage_audit_table.append(
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

                # validate
                validation = ValidationEvent(
                    theory_id=theory.id,
                    validation_summary=(
                        "Replay validation. " f"{horizon_context}. " f"{regime_context}"
                    ),
                    observed_behavior=market_obs.observation_text,
                    expected_behavior="Market-grounded theory",
                )

                if self.lineage_debug:
                    print(
                        f"\n[SYNTHESIS CHECK] score={contradiction_score:.3f} trigger={will_trigger}"
                    )
                    print(
                        "[Reflection Input]",
                        {
                            "date": date_str,
                            "regime_subtype": regime_subtype,
                            "analog": getattr(
                                market_obs, "analog_divergence_claim", ""
                            ),
                            "history": regime_history,
                            "falsifiability": falsifiability_conditions,
                        },
                    )

                # reflect
                reflection = self.reflection_flow.process(
                    theory,
                    validation,
                    contradiction_result=contradiction_result,
                    market_observation=market_obs,
                    # Explicitly pass finalized fields to ensure reflection consistency
                    regime_subtype=regime_subtype,
                    falsifiability_conditions=falsifiability_conditions,
                    analog_divergence_claim=getattr(
                        market_obs, "analog_divergence_claim", ""
                    ),
                    theory_regime_subtype=getattr(theory, "regime_subtype", "neutral"),
                    theory_falsifiability_conditions=getattr(
                        theory, "falsifiability_conditions", []
                    ),
                    regime_history=regime_history,
                    dialectical_synthesis=(
                        self.dialectical_synthesizer.format_for_reflection(
                            dialectical_data
                        )
                        if dialectical_data
                        else None
                    ),
                )
                if self.lineage_debug:
                    # [Reflection Grounding Score] is not a direct print statement in replay_engine.py
                    print("[Reflection Output]", reflection.reflection_summary)

                # Prefer structured claim when available for downstream consumers
                theory_text = (
                    theory.summary_structured.claim
                    if theory.summary_structured
                    else theory.summary
                )  # Canonical access with fallback

                epistemic_quality = {
                    "theory": evaluate_epistemic_quality(theory_text),
                    "reflection": evaluate_epistemic_quality(
                        reflection.reflection_summary
                    ),
                }

                # Initialize theory_usefulness (will be computed later if lineage available)
                # v2.4 Default structure for persistence
                theory_usefulness = {
                    "score": 0.0,
                    "label": "unknown",
                }
                try:
                    if self.epistemic_scoring and lineage_record:
                        theory_usefulness = self.epistemic_scoring.score_theory(
                            lineage_record=lineage_record,
                            regime_matches=regime_matches,
                            prior_prediction_result=(
                                prior_prediction_result.to_dict()
                                if prior_prediction_result
                                else {}
                            ),
                            contradiction_score=float(
                                contradiction_result.get("score", 0.0)
                            ),
                            reflection_summary=reflection.reflection_summary,
                        )
                except Exception:
                    theory_usefulness = {
                        "score": 0.0,
                        "label": "unknown",
                    }
                # Sanity validation
                assert (
                    "score" in theory_usefulness
                ), "theory_usefulness missing 'score' key"
                assert (
                    "label" in theory_usefulness
                ), "theory_usefulness missing 'label' key"
                if (
                    theory_usefulness["score"] > 0.8
                    and contradiction_result.get("score", 0.0) > 0.7
                ):
                    self._log(
                        "WARNING: High theory usefulness with high contradiction detected."
                    )

                # Find lineage experience early for metadata attribution.
                active_exp = None
                if lineage_record and lineage_id_val != "N/A":
                    active_exp = self.experience_repo.load_by_lineage(lineage_id_val)

                intelligence_metadata = {
                    "directional_persistence": {
                        "3d": persistence_3d,
                        "5d": persistence_5d,
                        "10d": persistence_10d,
                        "regime": reg_5d,
                    },
                    "mutation_count": active_exp.mutation_count if active_exp else 0,
                    "theory_mutation_count": (
                        lineage_record.mutation_count if lineage_record else 0
                    ),  # Add theory's own mutation count
                    "contradiction_count": (
                        active_exp.contradiction_count if active_exp else 0
                    ),
                    "lineage_id": lineage_id_val,
                    "theory_id": theory.id,
                    "regime_history": regime_history,  # Added for Breaking Uncertainty Deadlock
                }

                if self.lineage_debug:
                    print(f"\n  [PREDICTION RECORD AUDIT] Date: {date_str}")
                    print(f"    Theory ID: {theory.id}")
                    print(
                        f"    lineage_record.mutation_count: {lineage_record.mutation_count if lineage_record else 'N/A'}"
                    )
                    print(
                        f"    intelligence_metadata['theory_mutation_count']: {intelligence_metadata['theory_mutation_count']}"
                    )
                    # Note: prediction_history entry value will be the same as intelligence_metadata['theory_mutation_count']

                # infer transition pressure (deterministic, observer-only)
                transition_pressure = self.transition_pressure_engine.infer(
                    observation=market_obs,
                    horizons=horizon_view,
                    regime_matches=regime_matches,
                    confidence_state=theory.confidence_state,
                    contradiction_result=contradiction_result,
                    reflection=reflection,
                    theory_usefulness=theory_usefulness,
                    prior_observations=self._run_market_observations[-10:],
                    volume_state=obs_data["derived"].get("volume_state", "normal"),
                    atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200),
                    volume_ratio_5d=float(
                        obs_data["derived"].get("volume_ratio_5d", 1.0)
                    ),
                    range_pct=float(obs_data["derived"].get("range_pct", 0.0)),
                )

                # v1.9 Transition Retrieval
                similar_transitions = self.transition_memory.retrieve_similar(
                    from_regime=market_obs.trend_state,
                    direction_bias=transition_pressure.direction_bias,
                    pressure_score=transition_pressure.pressure_score,
                    horizon_daily=horizon_view.daily,
                )

                active_principles = (
                    self.knowledge_repository.list_principles(status="active")
                    + self.knowledge_repository.list_principles(status="stable")
                    + self.knowledge_repository.list_principles(status="emerging")
                    + self.knowledge_repository.list_principles(status="trusted")
                    + self.knowledge_repository.list_principles(status="canonical")
                )
                latest_wm = self.knowledge_repository.get_latest_world_model()

                # prediction probe
                prediction_probe = self.prediction_generator.generate_prediction(
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
                    volume_ratio_5d=float(
                        obs_data["derived"].get("volume_ratio_5d", 1.0)
                    ),
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

                    # Update principles' confidence_adjustments_triggered count
                    for pid in principles_accepted:
                        p_obj = self.knowledge_repository.get_principle(pid)
                        if p_obj:
                            p_obj.confidence_adjustments_triggered += 1
                            self.knowledge_repository.save_principle(p_obj)

                # Update uses_count on accepted principles
                for pid in principles_accepted:
                    p_obj = self.knowledge_repository.get_principle(pid)
                    if p_obj:
                        p_obj.uses_count += 1
                        self.knowledge_repository.save_principle(p_obj)

                # Save accepted principles list to class variable for next-day validation
                self._prior_prediction_accepted_principles = principles_accepted

                # Save active mechanisms of the day to class variable for next-day feedback
                self._prior_prediction_active_mechanisms = (
                    [
                        comp.mechanism_id
                        for comp in theory.summary_structured.mechanism_components
                        if comp.mechanism_id
                    ]
                    if (
                        "theory" in locals()
                        and theory
                        and theory.summary_structured
                        and theory.summary_structured.mechanism_components
                    )
                    else []
                )

                # Apply deterministic World Model overrides/constraints
                latest_wm = self.knowledge_repository.get_latest_world_model()
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

                        if max_confidence is not None and new_conf > float(
                            max_confidence
                        ):
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
                            # Update active principles' world_model_influence_count
                            for pid in latest_wm.active_principle_ids:
                                p_obj = self.knowledge_repository.get_principle(pid)
                                if p_obj:
                                    p_obj.world_model_influence_count += 1
                                    self.knowledge_repository.save_principle(p_obj)

                # Step 4: Decision Policy Layer
                decisions = self.decision_engine.evaluate(
                    prediction_probe=prediction_probe,
                    transition_pressure=transition_pressure,
                    contradiction_score=float(contradiction_result.get("score", 0.0)),
                    theory_usefulness=(
                        theory_usefulness.get("score", 0.0)
                        if theory_usefulness
                        else 0.0
                    ),
                    confidence_state=confidence_state,
                    date=date_str,
                    volume_state=obs_data["derived"].get("volume_state", "normal"),
                    atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200),
                    participation_confirmation=getattr(
                        market_obs, "participation_confirmation", "normal"
                    ),
                )

                prior_prediction_result = None
                if self._prior_prediction is not None:
                    prior_prediction_result = self.prediction_generator.score_actual(
                        self._prior_prediction, market_obs
                    )

                    # Causal Attribution Step
                    attribution = None
                    if self._prior_lineage_id and self._run_theories:
                        # Evaluates Day N-1 theory against Day N observation
                        theory_to_attr = self._run_theories[-1]

                        # ============================================================
                        # ATTRIBUTION: Determine WHY the theory succeeded or failed
                        # ============================================================
                        try:
                            # Build market snapshot for context
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

                            attribution = self.attribution_engine.attribute(
                                theory=theory_to_attr,
                                prediction=(
                                    str(self._prior_prediction.direction.value)
                                    if self._prior_prediction
                                    else ""
                                ),
                                observation=market_obs,
                                market_context=market_snapshot,
                            )
                            self._prior_attribution = attribution

                            # Keep attribution in the explicit experience causal
                            # event path below. Theory is a Pydantic schema and
                            # must not receive runtime-only fields.
                            # Log attribution results
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

                                # Phase 2: Contradiction Resolution & Open Question Generation
                                from cognition.schemas.knowledge.open_question import (
                                    OpenQuestion, QuestionStatus)
                                from cognition.schemas.knowledge.principle import \
                                    PrincipleStatus

                                active_principles = (
                                    self.knowledge_repository.list_principles(
                                        status="active"
                                    )
                                    + self.knowledge_repository.list_principles(
                                        status="stable"
                                    )
                                    + self.knowledge_repository.list_principles(
                                        status="emerging"
                                    )
                                    + self.knowledge_repository.list_principles(
                                        status="trusted"
                                    )
                                    + self.knowledge_repository.list_principles(
                                        status="canonical"
                                    )
                                )
                                regime_context = {
                                    "regime_subtype": regime_subtype,
                                    "volatility_regime": vol_regime,
                                    "volume_state": obs_data["derived"].get(
                                        "volume_state", "normal"
                                    ),
                                }

                                # Resolve contradictions: challenge/mutate affected principles
                                updated_principles = self.knowledge_compression_engine.resolve_contradictions(
                                    active_principles=active_principles,
                                    latest_attribution=attribution,
                                    current_regime_context=regime_context,
                                    step=day_idx,
                                )
                                for p in updated_principles:
                                    self.knowledge_repository.save_principle(p)

                                # Open Question Generation for unexplained failures
                                for comp_failed in attribution.components_failed:
                                    is_explained = False
                                    for p in active_principles:
                                        for fp in p.falsifiable_predictions:
                                            if fp.target_component == comp_failed:
                                                context_match = True
                                                for (
                                                    k,
                                                    v,
                                                ) in fp.applicability_filter.items():
                                                    val = regime_context.get(k)
                                                    if isinstance(
                                                        v, (list, tuple, set)
                                                    ):
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
                                            source_contradiction_ids=[
                                                attribution.theory_id
                                            ],
                                            hypothesized_factors=[
                                                str(vol_regime),
                                                (
                                                    str(
                                                        obs_data["derived"].get(
                                                            "volume_state", "normal"
                                                        )
                                                    )
                                                    if not pd.isna(
                                                        obs_data["derived"].get(
                                                            "volume_state"
                                                        )
                                                    )
                                                    else "normal"
                                                ),
                                            ],
                                            status=QuestionStatus.ACTIVE,
                                        )
                                        self.knowledge_repository.save_open_question(
                                            new_oq
                                        )

                                        # Phase 3: Create and Save EvidenceGap
                                        if "volume" in comp_failed:
                                            descriptors = getattr(
                                                market_obs, "descriptors", []
                                            )
                                            is_deliv_unknown = (
                                                "delivery:unknown" in descriptors
                                                or not any(
                                                    d.startswith("delivery:")
                                                    for d in descriptors
                                                )
                                            )
                                            is_sec_unknown = (
                                                "sector:unknown" in descriptors
                                                or not any(
                                                    d.startswith("sector:")
                                                    for d in descriptors
                                                )
                                            )
                                            if (
                                                not is_deliv_unknown
                                                and not is_sec_unknown
                                            ):
                                                logger.info(
                                                    f"[ATTRIBUTION] Evidence gap for '{comp_failed}' is resolved, skipping saving."
                                                )
                                                continue

                                        from cognition.schemas.knowledge.evidence_gap import \
                                            EvidenceGap

                                        missing_evidence = f"Order book imbalance and detailed participation dynamics for '{comp_failed}'"
                                        candidate_source = (
                                            "FII/DII Flows & Order Book Depth"
                                        )
                                        if "volume" in comp_failed:
                                            missing_evidence = f"Detailed delivery volume % and sector relative strength for volume confirmation validation"
                                            candidate_source = (
                                                "Delivery % & Sector Relative Strength"
                                            )

                                        gap = EvidenceGap(
                                            id=str(uuid4()),
                                            open_question_id=new_oq.id,
                                            missing_evidence=missing_evidence,
                                            candidate_data_source=candidate_source,
                                            expected_explanatory_value=f"To resolve structural failure of component '{comp_failed}' under {regime_subtype} regime",
                                            priority=(
                                                "HIGH"
                                                if comp_failed
                                                == attribution.root_cause_component
                                                else "MEDIUM"
                                            ),
                                        )
                                        self.knowledge_repository.save_evidence_gap(gap)
                            else:
                                logger.info(
                                    f"[ATTRIBUTION] Theory {getattr(theory_to_attr, 'id', 'unknown')}: All components passed"
                                )

                        except Exception as e:
                            logger.warning(f"[ATTRIBUTION] Attribution failed: {e}")
                            attribution = None
                    # Experience Lifecycle: Outcome Grounding & Hypothesis Validation
                    if prior_prediction_result and self._prior_lineage_id:
                        target_exp = self.experience_repo.load_by_lineage(
                            self._prior_lineage_id
                        )
                        if target_exp:
                            attributed = False
                            if prior_prediction_result.direction_score == 1.0:
                                target_exp.validation_count += 1
                                attributed = True
                            if prior_prediction_result.invalidation_triggered:
                                target_exp.falsification_count += 1
                                attributed = True

                            if attributed:
                                self.experience_engine.process_cycle(
                                    lineage_id=self._prior_lineage_id,
                                    experience=target_exp,
                                    status=target_exp.status.value,
                                    attribution=attribution,
                                )
                                self.experience_repo.save(target_exp)

                            # Structured Lesson Hypothesis Validation: reinforce or penalize active lessons
                            if (
                                getattr(self, "_prior_lessons", None)
                                and self.lesson_repo
                            ):
                                from market.replay.lesson_record import \
                                    LessonStatus

                                score_val = getattr(
                                    prior_prediction_result, "direction_score", 0.5
                                )
                                is_invalidated = getattr(
                                    prior_prediction_result,
                                    "invalidation_triggered",
                                    False,
                                )

                                for l_text in self._prior_lessons:
                                    matching_lesson = None
                                    for l in self.lesson_repo.list_lessons():
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
                                            matching_lesson.status
                                            == LessonStatus.RETIRED
                                            or getattr(matching_lesson, "status", None)
                                            == "retired"
                                        )
                                        if matching_lesson.confidence >= 0.75:
                                            matching_lesson.status = LessonStatus.ACTIVE
                                        elif matching_lesson.confidence < 0.2:
                                            matching_lesson.status = (
                                                LessonStatus.RETIRED
                                            )
                                            if not was_retired:
                                                newly_retired_count += 1
                                        else:
                                            matching_lesson.status = (
                                                LessonStatus.CANDIDATE
                                            )

                                        self.lesson_repo.save(matching_lesson)

                # Task B: Capital Simulation (observer-only)
                derived = obs_data.get("derived")
                actual_ret = derived["daily_return_pct"] if derived else 0.0
                if self._prior_prediction and derived:
                    self.capital_simulator.record_day_result(
                        date=date_str,
                        prediction_direction=self._prior_prediction.direction.value,
                        prediction_confidence=self._prior_prediction.confidence,
                        actual_daily_return_pct=actual_ret,
                        market_daily_return_pct=actual_ret,
                        decisions=decisions,
                    )
                elif derived:
                    self.capital_simulator.record_day_result(
                        date_str, "uncertain", 0.0, actual_ret, actual_ret
                    )

                # Simulated conviction-based paper trading
                if hasattr(self, "paper_trader") and self.paper_trader and derived:
                    ohlcv = obs_data.get("ohlcv", {})
                    open_p = ohlcv.get("open", 0.0)
                    close_p = ohlcv.get("close", 0.0)
                    prior_record = getattr(self, "_prior_decision_record", None)
                    if prior_record:
                        self.paper_trader.evaluate_decision_outcome(
                            record=prior_record,
                            open_price=open_p,
                            close_price=close_p,
                            actual_daily_return_pct=actual_ret,
                            evaluation_date=date_str,
                        )
                        if hasattr(self, "decision_journal") and self.decision_journal:
                            self.decision_journal.save(prior_record)
                    else:
                        from cognition.schemas.decision.decision import \
                            Decision
                        from cognition.schemas.decision.decision_record import \
                            DecisionRecord

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
                            asset=self.engine.market_name or "RELIANCE",
                            prediction="uncertain",
                            decision=initial_decision,
                            allocation=0.0,
                            conviction_score=0.0,
                            decision_reason="Initialization day - no active prediction",
                        )
                        self.paper_trader.evaluate_decision_outcome(
                            record=initial_record,
                            open_price=open_p,
                            close_price=close_p,
                            actual_daily_return_pct=actual_ret,
                            evaluation_date=date_str,
                        )
                        if hasattr(self, "decision_journal") and self.decision_journal:
                            self.decision_journal.save(initial_record)

                # Track rolling prediction accuracy across three windows
                recent_acc = 0.5
                regime_acc = 0.5
                lifetime_acc = 0.5

                if prior_prediction_result:
                    score = getattr(prior_prediction_result, "direction_score", 0.5)
                    if score is None:
                        score = 0.5

                    # Track lifetime accuracy
                    if not hasattr(self, "_lifetime_predictions_count"):
                        self._lifetime_predictions_count = 0
                        self._lifetime_correct_predictions_count = 0.0
                    self._lifetime_predictions_count += 1
                    self._lifetime_correct_predictions_count += score

                    # Track recent accuracy
                    if not hasattr(self, "_prediction_accuracy_history"):
                        self._prediction_accuracy_history = []
                    self._prediction_accuracy_history.append(score)

                    # Track regime-specific accuracy
                    if not hasattr(self, "_regime_prediction_accuracy_history"):
                        self._regime_prediction_accuracy_history = {}
                    prior_subtype = (
                        getattr(self, "_prior_dialectical_subtype", None)
                        or regime_subtype
                    )
                    if prior_subtype not in self._regime_prediction_accuracy_history:
                        self._regime_prediction_accuracy_history[prior_subtype] = []
                    self._regime_prediction_accuracy_history[prior_subtype].append(
                        score
                    )

                # Compute window metrics
                if (
                    hasattr(self, "_prediction_accuracy_history")
                    and self._prediction_accuracy_history
                ):
                    recent_scores = self._prediction_accuracy_history[-15:]
                    recent_acc = sum(recent_scores) / len(recent_scores)

                if (
                    hasattr(self, "_regime_prediction_accuracy_history")
                    and regime_subtype in self._regime_prediction_accuracy_history
                    and self._regime_prediction_accuracy_history[regime_subtype]
                ):
                    regime_scores = self._regime_prediction_accuracy_history[
                        regime_subtype
                    ][-15:]
                    regime_acc = sum(regime_scores) / len(regime_scores)

                if (
                    hasattr(self, "_lifetime_predictions_count")
                    and self._lifetime_predictions_count > 0
                ):
                    lifetime_acc = (
                        self._lifetime_correct_predictions_count
                        / self._lifetime_predictions_count
                    )

                # Confidence evolution
                confidence_state = self.confidence_engine.evolve(
                    confidence_state=theory.confidence_state,
                    validation=validation,
                    reflection=reflection,
                    contradiction_result=contradiction_result,
                    market_observation=market_obs,
                    recent_validations=recent_validations,
                    outcome_validation_result=(
                        prior_prediction_result.to_dict()
                        if prior_prediction_result
                        else {}
                    ),
                    lineage_event=theory_step_info,
                    theory_usefulness=theory_usefulness,
                    regime_matches=regime_matches,
                    rolling_accuracy=recent_acc,
                    regime_accuracy=regime_acc,
                    lifetime_accuracy=lifetime_acc,
                )

                # Programmatic Decision Feedback Loop
                if (
                    hasattr(self, "paper_trader")
                    and len(self.paper_trader.decision_records) > 0
                ):
                    last_rec = self.paper_trader.decision_records[-1]
                    if last_rec.evaluation_date == date_str:
                        if (
                            last_rec.decision_result == "incorrect"
                            and last_rec.conviction_score >= 0.60
                        ):
                            confidence_state.empirical_confidence = max(
                                0.0, confidence_state.empirical_confidence - 0.15
                            )
                            confidence_state.regime_confidence = max(
                                0.0, confidence_state.regime_confidence - 0.10
                            )
                            self._log(
                                f"  [Feedback] False High Conviction: Penalizing empirical (-0.15) & regime (-0.10) confidence."
                            )
                        elif last_rec.decision_result == "avoided_bad_trade":
                            confidence_state.empirical_confidence = min(
                                1.0, confidence_state.empirical_confidence + 0.05
                            )
                            self._log(
                                f"  [Feedback] Avoided Bad Trade: Rewarding empirical confidence (+0.05)."
                            )

                        for lineage_id in last_rec.supporting_lineages:
                            for rec in self.theory_lineage.theories.values():
                                if rec.lineage_id == lineage_id:
                                    pnl_term = last_rec.pnl / 100000.0
                                    delta = 0.0
                                    if last_rec.decision_result == "correct":
                                        delta += 0.10
                                    elif last_rec.decision_result == "incorrect":
                                        delta -= 0.15
                                    elif (
                                        last_rec.decision_result == "avoided_bad_trade"
                                    ):
                                        delta += 0.05

                                    rec.predictive_fitness = max(
                                        0.0,
                                        min(
                                            1.0,
                                            getattr(rec, "predictive_fitness", 0.5)
                                            + delta,
                                        ),
                                    )
                                    rec.economic_fitness = max(
                                        0.0,
                                        min(
                                            1.0,
                                            getattr(rec, "economic_fitness", 0.5)
                                            + pnl_term,
                                        ),
                                    )
                                    rec.generalization_fitness = max(
                                        0.0,
                                        min(
                                            1.0,
                                            getattr(rec, "generalization_fitness", 0.5)
                                            + (
                                                0.05
                                                if last_rec.decision_result == "correct"
                                                else -0.05
                                            ),
                                        ),
                                    )
                                    rec.cross_asset_fitness = max(
                                        0.0,
                                        min(
                                            1.0,
                                            getattr(rec, "cross_asset_fitness", 0.5)
                                            + 0.02,
                                        ),
                                    )
                                    rec.longevity_days = (
                                        getattr(rec, "longevity_days", 0) + 1
                                    )

                        for pid in last_rec.supporting_principles:
                            principle = self.knowledge_repository.get_principle(pid)
                            if principle:
                                principle.uses_count += 1
                                if last_rec.decision_result in [
                                    "correct",
                                    "ignored_opportunity",
                                ]:
                                    principle.predictions_helped += 1
                                    principle.confidence = min(
                                        1.0, principle.confidence + 0.05
                                    )
                                else:
                                    principle.predictions_harmed += 1
                                    principle.confidence = max(
                                        0.0, principle.confidence - 0.08
                                    )
                                self.knowledge_repository.save_principle(principle)

                # Update in-memory confidence history
                try:
                    self._confidence_history.append(
                        confidence_state.empirical_confidence
                    )
                except Exception:
                    pass

                # Conviction position sizer calculation
                calibrated_confidence = prediction_probe.confidence
                contradiction_pressure = float(contradiction_result.get("score", 0.0))
                empirical_confidence = confidence_state.empirical_confidence
                principle_support = 1 if len(principles_accepted) > 0 else 0
                trans_pressure_val = transition_pressure.pressure_score
                pred_direction = prediction_probe.direction.value

                conv_res = self.conviction_sizer.compute_sizer(
                    calibrated_confidence=calibrated_confidence,
                    contradiction_pressure=contradiction_pressure,
                    empirical_confidence=empirical_confidence,
                    principle_support=principle_support,
                    transition_pressure=trans_pressure_val,
                    prediction_direction=pred_direction,
                )
                allocation_pct = conv_res.allocation
                conviction_score = conv_res.final_score

                # Map to decision action (hold / long / short)
                if allocation_pct > 0.0:
                    action = "long" if pred_direction == "higher" else "short"
                else:
                    action = "hold"

                # Log conviction details to the daily cognitive report
                regime_stability = 1.0 - trans_pressure_val
                self._log(
                    f"• [CONVICTION] Score: {conviction_score:.2f} | Allocation: {allocation_pct * 100:.1f}% | "
                    f"Confidence: {calibrated_confidence:.2f} | Pressure: {contradiction_pressure:.2f} | "
                    f"Empirical: {empirical_confidence:.2f} | Principles: {principle_support} | "
                    f"Regime: {regime_stability:.2f}"
                )

                # Set prior variables for tomorrow's trade evaluation
                self._prior_conviction = conviction_score
                self._prior_allocation = allocation_pct
                self._prior_components = {
                    "calibrated_confidence": calibrated_confidence,
                    "contradiction_pressure": contradiction_pressure,
                    "empirical_confidence": empirical_confidence,
                    "principle_support": principle_support,
                    "transition_pressure": trans_pressure_val,
                }

                # Construct and store current day's Decision & DecisionRecord for evaluation tomorrow
                from cognition.schemas.decision.decision import Decision
                from cognition.schemas.decision.decision_record import \
                    DecisionRecord

                decision_obj = Decision(
                    date=date_str,
                    prediction_direction=pred_direction,
                    action=action,
                    allocation_pct=allocation_pct,
                    conviction_score=conviction_score,
                    reason=prediction_probe.tension
                    or "Standard cognitive trade sizing",
                )

                # Extract supporting/contextual metadata
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

                # Knowledge changes triggered today
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
                    asset=self.engine.market_name or "RELIANCE",
                    prediction=pred_direction,
                    decision=decision_obj,
                    allocation=allocation_pct,
                    conviction_score=conviction_score,
                    decision_reason=prediction_probe.tension
                    or "Standard cognitive trade sizing",
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
                    expected_scenarios=(
                        [prediction_probe.tension] if prediction_probe.tension else []
                    ),
                    knowledge_changes=knowledge_changes,
                    conviction_breakdown=conv_res.component_breakdown,
                )
                self._prior_decision_record = decision_record

                # v1.9: Save context for tomorrow's transition recording
                self._prior_transition_context = {
                    "pressure": transition_pressure.pressure_score,
                    "breakout": transition_pressure.breakout_risk,
                    "bias": transition_pressure.direction_bias,
                    "confidence": theory.confidence_state.empirical_confidence,
                    "usefulness": theory_usefulness.get("score", 0.0),
                    "contradiction": float(contradiction_result.get("score", 0.0)),
                    "horizon": horizon_view,
                    "theory_summary": theory.summary,
                }

                final_regime_signature = self.regime_memory.build_signature(
                    date=date_str,
                    observation=market_obs,
                    confidence_values=self._confidence_history[-10:],
                    contradiction_severity=float(
                        contradiction_result.get("score", 0.0)
                    ),
                    active_theory_count=(
                        self.theory_lineage.active_count()
                        if self.theory_lineage
                        else active_theory_count
                    ),
                )
                active_lineage_records = (
                    self.theory_lineage.active_theories() if self.theory_lineage else []
                )
                self.regime_memory.persist(
                    step=day_idx,
                    signature=final_regime_signature,
                    active_theories=active_lineage_records,
                    contradictions=contradiction_result.get("indicators", []),
                    confidence=getattr(confidence_state, "empirical_confidence", 0.5),
                )
                # persist
                self.observation_repo.save(obs_event)
                self.abstraction_repo.save(abstraction)
                self.theory_repo.save(theory)
                self.validation_repo.save(validation)
                self.reflection_repo.save(reflection)
                self.confidence_repo.save(confidence_state)

                # v1.4 Analytics Persistence (PostgreSQL) - Defensive Observer Pattern
                try:
                    if self.market_outcome_repo:
                        # Thoroughly map current state to outcome fields for persistence
                        market_obs.outcome_summary = market_obs.observation_text
                        market_obs.realized_trend = market_obs.trend_state
                        market_obs.realized_volatility = market_obs.volatility_state
                        market_obs.realized_breadth = market_obs.breadth_state
                        market_obs.realized_liquidity = market_obs.liquidity_state

                        if prior_prediction_result:
                            market_obs.outcome_confidence = (
                                prior_prediction_result.confidence
                            )

                        # Provide contradictions for outcome persistence
                        market_obs.outcome_contradictions = contradiction_result.get(
                            "indicators", []
                        )

                        # Link to the generic observation event for relational analytics
                        if hasattr(obs_event, "id") and obs_event.id:
                            market_obs.related_observation_id = str(obs_event.id)

                        self.market_outcome_repo.save(market_obs)
                except Exception as e:
                    self._log(f"WARNING: Optional MarketOutcome save failed: {e}")

                try:
                    self.transition_pressure_repo.save(
                        transition_pressure, date=date_str, day_index=day_idx
                    )
                except Exception as e:
                    self._log(f"WARNING: TransitionPressure save failed: {e}")

                saved_prediction = None
                try:
                    # Store logical refs/hashes as per v1.4 adjustments
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
                            prior_prediction_result,
                            date=date_str,
                            day_index=day_idx,
                            prediction_id=self._prior_prediction_db_id,
                        )

                        # Phase 3: Update principle utility counters (helped vs. harmed)
                        if getattr(self, "_prior_prediction_accepted_principles", None):
                            is_correct = prior_prediction_result.direction_score == 1.0
                            for pid in self._prior_prediction_accepted_principles:
                                p_obj = self.knowledge_repository.get_principle(pid)
                                if p_obj:
                                    if is_correct:
                                        p_obj.predictions_helped += 1
                                    else:
                                        p_obj.predictions_harmed += 1
                                    self.knowledge_repository.save_principle(p_obj)

                        # Update mechanism utility counters (helped vs. harmed)
                        if getattr(self, "_prior_prediction_active_mechanisms", None):
                            is_correct = prior_prediction_result.direction_score == 1.0
                            for mid in self._prior_prediction_active_mechanisms:
                                mech_obj = self.knowledge_repository.get_mechanism(mid)
                                if mech_obj:
                                    if is_correct:
                                        mech_obj.prediction_helped += 1
                                        mech_obj.support_count += 1
                                    else:
                                        mech_obj.prediction_harmed += 1
                                        mech_obj.contradiction_count += 1
                                    self.knowledge_repository.save_mechanism(mech_obj)
                except Exception as e:
                    self._log(f"WARNING: PredictionResult save failed: {e}")

                # v3.1 Regime Memory Update
                actual_dir = getattr(prior_prediction_result, "actual_direction", None)
                self.regime_continuity_memory.update(
                    date=date_str,
                    subtype=regime_subtype,
                    usefulness=theory_usefulness.get("score", 0.0),
                    actual_direction=actual_dir,
                    falsified=getattr(
                        prior_prediction_result, "invalidation_triggered", False
                    ),
                )

                regime_history_final = self.regime_continuity_memory.summary(
                    regime_subtype
                )
                if self.lineage_debug:
                    # Guard for debug output
                    print(
                        "[Regime Memory]",
                        {
                            "date": date_str,
                            "subtype": regime_subtype,
                            "history": regime_history_final,
                        },
                    )

                self._run_theories.append(theory)
                self._run_validations.append(validation)
                self._run_reflections.append(reflection)
                self._run_market_observations.append(market_obs)

                # Compute hashes for determinism tracking
                obs_hash = hashlib.sha256(
                    market_obs.observation_text.encode()
                ).hexdigest()[:16]
                theory_hash = hashlib.sha256(theory.summary.encode()).hexdigest()[:16]
                conf_hash = hashlib.sha256(
                    str(confidence_state.empirical_confidence).encode()
                ).hexdigest()[:16]

                self.engine.log_entry(
                    day_idx, date_str, obs_hash, theory_hash, conf_hash
                )

                step_theory_metrics = {
                    "created": theory_step_info["created"],
                    "mutated": theory_step_info["mutated"],
                    "merged": theory_step_info["merged"],
                    "retired": theory_step_info["retired"],
                    "revived": theory_step_info["revived"],
                    "theory_word_count": daily_theory_word_count,
                    "mechanism_count": daily_mechanism_count,
                    "conditional_clauses_count": daily_conditional_clauses_count,
                    "exceptions_added": daily_exceptions_added,
                    "mechanisms_retired": daily_mechanisms_retired,
                    "mechanisms_added": daily_mechanisms_added,
                    "mechanisms_modified": daily_mechanisms_modified,
                    "mechanism_stability": daily_mechanism_stability,
                    "words_before_mutation": daily_words_before_mutation,
                    "words_after_mutation": daily_words_after_mutation,
                    "mechanisms_before_mutation": daily_mechanisms_before_mutation,
                    "mechanisms_after_mutation": daily_mechanisms_after_mutation,
                }

                # Record day for longitudinal analysis
                self.replay_analysis_engine.record_day(
                    day_index=day_idx,
                    date=date_str,
                    confidence_state={
                        "empirical_confidence": confidence_state.empirical_confidence,
                        "regime_confidence": confidence_state.regime_confidence,
                        "reflection_confidence": confidence_state.reflection_confidence,
                        "theoretical_coherence": confidence_state.theoretical_coherence,
                        "contradiction_pressure": confidence_state.contradiction_pressure,
                    },
                    contradiction_result=contradiction_result,
                    theory_summary=theory_text,
                    reflection_summary=reflection.reflection_summary,
                    market_regime=market_obs.macro_sentiment,
                    epistemic_quality=epistemic_quality,
                    prediction=prediction_probe.to_dict(),
                    prior_prediction_result=(
                        prior_prediction_result.to_dict()
                        if prior_prediction_result
                        else None
                    ),
                    regime_matches=regime_matches,
                    theory_usefulness=theory_usefulness,
                    transition_pressure=transition_pressure.to_dict(),
                    decisions={k: v.to_dict() for k, v in decisions.items()},
                    candle_type=market_obs.candle_type,
                    participation_strength=market_obs.participation_strength,
                    participation_confirmation=market_obs.participation_confirmation,
                    market_name=self.engine.market_name,
                    # v2.0 dimensions
                    volume_state=obs_data["derived"].get("volume_state"),
                    volatility_regime=vol_regime,
                    momentum_regime=mom_regime,
                    # v3.0 dimensions
                    regime_subtype=getattr(market_obs, "regime_subtype", "neutral"),
                    falsifiability_conditions=getattr(
                        market_obs, "falsifiability_conditions", []
                    ),
                    analog_divergence_claim=getattr(
                        market_obs, "analog_divergence_claim", ""
                    ),
                    regime_history=regime_history_final,
                    branch_stats=branch_stats,  # Pass branch_stats
                    branches_generated=branch_stats.get("generated", 0),
                    intelligence_data=intelligence_metadata,
                    components_failed=(
                        self._prior_attribution.components_failed
                        if getattr(self, "_prior_attribution", None)
                        and hasattr(self._prior_attribution, "components_failed")
                        else []
                    ),
                    components_tested=(
                        self._prior_attribution.components_tested
                        if getattr(self, "_prior_attribution", None)
                        and hasattr(self._prior_attribution, "components_tested")
                        else []
                    ),
                    theory_id=getattr(theory, "id", "") if "theory" in locals() else "",
                    reused_lessons=(
                        relevant_lessons if "relevant_lessons" in locals() else []
                    ),
                    lessons_retired=newly_retired_count,
                    transition_memory_hit=(
                        (len(similar_transitions) > 0)
                        if "similar_transitions" in locals()
                        else False
                    ),
                    principles_consulted=principles_consulted,
                    principles_accepted=principles_accepted,
                    principles_rejected=[
                        pid
                        for pid in principles_consulted
                        if pid not in principles_accepted
                    ],
                    world_model_applied=world_model_applied,
                    confidence_delta=confidence_delta,
                    prediction_override_applied=prediction_override_applied,
                    novelty_decision=decision,
                    novelty_score=novelty_score,
                    theory_metrics=step_theory_metrics,
                )

                snapshot_data = {
                    "observation": market_obs,
                    "theory": theory,
                    "confidence": confidence_state,
                    "contradiction": contradiction_result,
                    "decisions": {k: v.to_dict() for k, v in decisions.items()},
                    "reflection": reflection,
                    "epistemic_quality": epistemic_quality,
                    "horizon": horizon_view.to_dict(),
                    "regime_signature": final_regime_signature.to_dict(),
                    "regime_matches": [match.to_dict() for match in regime_matches],
                    "theory_usefulness": theory_usefulness,
                    "transition_pressure": transition_pressure.to_dict(),
                    "prediction": prediction_probe,
                    "prior_prediction_result": prior_prediction_result,
                    # v2.0 metadata
                    "volume_state": obs_data["derived"].get("volume_state"),
                    "volatility_regime": vol_regime,
                    "momentum_regime": mom_regime,
                    # v3.0 Regime-based theory continuity
                    "regime_subtype": getattr(market_obs, "regime_subtype", "neutral"),
                    "falsifiability_conditions": getattr(
                        market_obs, "falsifiability_conditions", []
                    ),
                    "analog_divergence_claim": getattr(
                        market_obs, "analog_divergence_claim", ""
                    ),
                    "theory_regime_subtype": getattr(
                        theory, "regime_subtype", "neutral"
                    ),
                    "theory_falsifiability_conditions": getattr(
                        theory, "falsifiability_conditions", []
                    ),
                    "regime_history": regime_history_final,
                    "branch_stats": branch_stats,  # Store branch_stats in snapshot
                    "dialectical_triggered": dialectical_data is not None,
                    "dialectical_synthesis": (
                        dialectical_data if dialectical_data else None
                    ),
                    "intelligence": intelligence_metadata,
                }
                # Save snapshot
                self._save_snapshot(day_idx, date_str, snapshot_data)

                # Cognitive Decision Trace Collection & Knowledge Graph Linking
                try:
                    reuse_decision = "generated_new"
                    if not audit_created and not audit_mutated:
                        reuse_decision = "reused"

                    applied_principles_details = []
                    for pid in principles_accepted:
                        p_obj = self.knowledge_repository.get_principle(pid)
                        if p_obj:
                            applied_principles_details.append(
                                {
                                    "id": p_obj.id,
                                    "statement": p_obj.statement,
                                    "status": p_obj.status.value,
                                    "trust_score": p_obj.trust_score,
                                }
                            )

                    wm_constraints = {}
                    if latest_wm and latest_wm.regime_constraints:
                        constraints = latest_wm.regime_constraints.get(regime_subtype)
                        if constraints:
                            wm_constraints = constraints

                    trace_entry = {
                        "step": day_idx,
                        "date": date_str,
                        "observation": {
                            "trend_state": getattr(
                                market_obs, "trend_state", "neutral"
                            ),
                            "candle_type": getattr(market_obs, "candle_type", "normal"),
                            "delivery_pct": getattr(market_obs, "delivery_pct", 0.0),
                            "volume_state": getattr(
                                market_obs, "volume_state", "normal"
                            ),
                            "regime_subtype": regime_subtype,
                        },
                        "memory_retrieved": [
                            {
                                "date": getattr(m, "date", ""),
                                "similarity": getattr(m, "similarity", 0.0),
                                "actual_direction": getattr(
                                    m, "actual_direction", "range_bound"
                                ),
                            }
                            for m in (regime_matches or [])
                        ],
                        "novelty_score": float(
                            round(
                                1.0
                                - (
                                    regime_matches[0].similarity
                                    if (
                                        regime_matches
                                        and hasattr(regime_matches[0], "similarity")
                                    )
                                    else 0.0
                                ),
                                3,
                            )
                        ),
                        "reuse_decision": reuse_decision,
                        "generated_theory": theory.summary,
                        "applied_principles": applied_principles_details,
                        "world_model_constraints": wm_constraints,
                        "prediction": {
                            "direction": prediction_probe.direction.value,
                            "confidence": prediction_probe.confidence,
                        },
                        "outcome": {
                            "actual_direction": (
                                prior_prediction_result.actual_direction
                                if prior_prediction_result
                                else "uncertain"
                            ),
                            "direction_score": (
                                prior_prediction_result.direction_score
                                if prior_prediction_result
                                else 0.0
                            ),
                            "invalidation_triggered": (
                                prior_prediction_result.invalidation_triggered
                                if prior_prediction_result
                                else False
                            ),
                        },
                        "reflection": (
                            reflection.reflection_summary
                            if ("reflection" in locals() and reflection)
                            else "No reflection generated."
                        ),
                        "knowledge_updated": {
                            "principles_merged": (
                                rec_stats.get("merged_count", 0)
                                if "rec_stats" in locals()
                                else 0
                            ),
                            "principles_generalized": (
                                rec_stats.get("generalized_count", 0)
                                if "rec_stats" in locals()
                                else 0
                            ),
                            "principles_retired": (
                                rec_stats.get("retired_count", 0)
                                if "rec_stats" in locals()
                                else 0
                            ),
                            "principles_restricted": (
                                rec_stats.get("restricted_count", 0)
                                if "rec_stats" in locals()
                                else 0
                            ),
                            "debt_after": (
                                rec_stats.get("knowledge_debt_after", 0.0)
                                if "rec_stats" in locals()
                                else 0.0
                            ),
                        },
                    }
                    self.decision_traces.append(trace_entry)

                    # Build Knowledge Graph Nodes and Edges
                    obs_id = f"obs_{date_str}"
                    theory_id = theory.id
                    pred_id = f"pred_{date_str}"
                    outcome_id = f"outcome_{date_str}"
                    reflection_id = (
                        reflection.id
                        if ("reflection" in locals() and reflection)
                        else f"ref_{date_str}"
                    )
                    wm_id = f"wm_{date_str}"

                    self.knowledge_graph.add_node(
                        obs_id,
                        "Observation",
                        f"Obs: {market_obs.candle_type}",
                        {
                            "regime_subtype": regime_subtype,
                            "delivery_pct": getattr(market_obs, "delivery_pct", 0.0),
                        },
                    )
                    self.knowledge_graph.add_node(
                        theory_id,
                        "Theory",
                        theory.summary,
                        {"lineage_id": lineage_id_val},
                    )
                    self.knowledge_graph.add_node(
                        wm_id,
                        "WorldModel",
                        (
                            latest_wm.narrative_summary
                            if latest_wm
                            else "Baseline World Model"
                        ),
                        {
                            "stability": getattr(latest_wm, "stability", "Emerging"),
                            "confidence": getattr(latest_wm, "confidence", 0.5),
                        },
                    )
                    self.knowledge_graph.add_node(
                        pred_id,
                        "Prediction",
                        f"Pred: {prediction_probe.direction.value}",
                        {"confidence": prediction_probe.confidence},
                    )

                    if prior_prediction_result:
                        self.knowledge_graph.add_node(
                            outcome_id,
                            "Outcome",
                            f"Actual: {prior_prediction_result.actual_direction}",
                            {"score": prior_prediction_result.direction_score},
                        )

                    if "reflection" in locals() and reflection:
                        self.knowledge_graph.add_node(
                            reflection_id, "Reflection", reflection.reflection_summary
                        )

                    self.knowledge_graph.add_edge(obs_id, theory_id, "EXPLAINS")

                    for pid in principles_accepted:
                        p_obj = self.knowledge_repository.get_principle(pid)
                        if p_obj:
                            self.knowledge_graph.add_node(
                                pid,
                                "Principle",
                                p_obj.statement,
                                {
                                    "status": p_obj.status.value,
                                    "trust_score": p_obj.trust_score,
                                },
                            )
                            self.knowledge_graph.add_edge(
                                theory_id, pid, "SUPPORTED_BY"
                            )
                            self.knowledge_graph.add_edge(pid, wm_id, "INFLUENCES")

                    self.knowledge_graph.add_edge(wm_id, pred_id, "CONSTRAINS")
                    if prior_prediction_result:
                        self.knowledge_graph.add_edge(pred_id, outcome_id, "SCORES")
                    if (
                        "reflection" in locals()
                        and reflection
                        and prior_prediction_result
                    ):
                        self.knowledge_graph.add_edge(
                            outcome_id, reflection_id, "CRITIQUES"
                        )
                        self.knowledge_graph.add_edge(
                            reflection_id, theory_id, "REVISES"
                        )

                except Exception as e:
                    self._log(
                        f"WARNING: Trace/Graph collection failed for day {date_str}: {e}"
                    )

                # Update observability metrics
                try:
                    if (
                        self.observer
                        and self.theory_lineage
                        and self.contradiction_registry
                    ):
                        confidence_values = (
                            list(self._confidence_history[-10:])
                            if self._confidence_history
                            else [
                                getattr(confidence_state, "empirical_confidence", 0.0)
                            ]
                        )
                        theory_lineage_metrics = {
                            "active_theories": self.theory_lineage.active_count(),
                            "contradicted_theories": self.theory_lineage.contradicted_count(),
                            "retired_theories": self.theory_lineage.retired_count(),
                            "revived_theories": self.theory_lineage.revived_count(),
                            "avg_retirement_age": self.theory_lineage.average_retirement_age(),
                            "avg_revival_latency": self.theory_lineage.average_revival_latency(),
                            "avg_theory_age": self.theory_lineage.average_theory_age(),
                            "longest_surviving": self.theory_lineage.longest_surviving_theory(),
                            "mutation_count": self.theory_lineage.total_mutation_count(),
                        }
                        contradiction_metrics = {
                            "active_contradictions": self.contradiction_registry.active_count(),
                            "half_life": self.contradiction_registry.contradiction_half_life(),
                            "median_half_life": self.contradiction_registry.median_contradiction_half_life(),
                            "oldest_unresolved": self.contradiction_registry.oldest_unresolved_age(),
                            "resolution_rate": self.contradiction_registry.contradiction_resolution_rate(),
                            "avg_severity": self.contradiction_registry.average_severity(),
                            "highest": self.contradiction_registry.highest_severity(),
                        }
                        abstractions_for_obs = (
                            [getattr(abstraction, "abstraction_summary", "")]
                            if abstraction
                            else []
                        )
                        extras = {
                            "observation_length": (
                                len(market_obs.observation_text.split())
                                if getattr(market_obs, "observation_text", None)
                                else 1
                            ),
                            "theory_text": theory.summary,
                            "contradiction_text": contradiction_result.get(
                                "summary", ""
                            ),
                            "horizon": horizon_view.to_dict(),
                            "regime_signature": final_regime_signature.to_dict(),
                            "regime_matches": [
                                match.to_dict() for match in regime_matches
                            ],
                            "theory_usefulness": theory_usefulness,
                        }
                        metrics = self.observer.update(
                            step=day_idx,
                            date=date_str,
                            contradiction_metrics=contradiction_metrics,
                            theory_metrics=step_theory_metrics,
                            lineage_metrics=theory_lineage_metrics,
                            confidence_values=confidence_values,
                            reflection_text=getattr(
                                reflection, "reflection_summary", ""
                            ),
                            abstractions=abstractions_for_obs,
                            extras=extras,
                        )
                        try:
                            snap_file = self.run_dir / f"day_{day_idx:04d}.json"
                            with open(snap_file, "w") as _f:
                                json.dump(
                                    {
                                        "step": day_idx,
                                        "date": date_str,
                                        "observation": market_obs.observation_text,
                                        "abstraction": getattr(
                                            abstraction, "abstraction_summary", ""
                                        ),
                                        "theory": theory_text,
                                        "theory_summary_structured": (
                                            theory.summary_structured.model_dump()
                                            if theory.summary_structured
                                            else None
                                        ),  # Canonical access
                                        "confidence": {
                                            "empirical": confidence_state.empirical_confidence,
                                            "regime": confidence_state.regime_confidence,
                                            "reflection": confidence_state.reflection_confidence,
                                            "coherence": confidence_state.theoretical_coherence,
                                            "contradiction": confidence_state.contradiction_pressure,
                                        },
                                        "contradiction": contradiction_result,
                                        "horizon": horizon_view.to_dict(),
                                        "regime_signature": (
                                            final_regime_signature.to_dict()
                                        ),
                                        "regime_matches": [
                                            match.to_dict() for match in regime_matches
                                        ],
                                        "decisions": {
                                            k: v.to_dict() for k, v in decisions.items()
                                        },
                                        "theory_usefulness": theory_usefulness,
                                        "reflection": getattr(
                                            reflection, "reflection_summary", ""
                                        ),
                                        # v3.0 Regime Surface Persistence
                                        "regime_subtype": market_obs.regime_subtype,
                                        "falsifiability_conditions": market_obs.falsifiability_conditions,
                                        "analog_divergence_claim": market_obs.analog_divergence_claim,
                                        "theory_regime_subtype": getattr(
                                            theory, "regime_subtype", "neutral"
                                        ),
                                        "theory_falsifiability": getattr(
                                            theory, "falsifiability_conditions", []
                                        ),
                                        "regime_history": regime_history_final,
                                        "dialectical_triggered": dialectical_data
                                        is not None,
                                        "dialectical_synthesis": (
                                            dialectical_data
                                            if dialectical_data
                                            else None
                                        ),
                                        "metrics": metrics.__dict__,
                                    },
                                    _f,
                                    indent=2,
                                    default=str,
                                )
                        except Exception:
                            pass
                except Exception:
                    pass

                # Find experience for current trace log
                active_exp = None
                if (
                    lineage_record and lineage_id_val != "N/A"
                ):  # Use the stable lineage_id for lookup
                    active_exp = self.experience_repo.load_by_lineage(lineage_id_val)

                if intelligence_metadata:
                    intelligence_metadata["created"] = audit_created
                    intelligence_metadata["mutated"] = audit_mutated
                    intelligence_metadata["merged"] = audit_merged
                    intelligence_metadata["revived"] = audit_revived
                    intelligence_metadata["retired"] = audit_retired

                # Print formatted log
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
                    active_experience=active_exp,  # Pass the active experience
                    lesson_info=self.experience_engine.get_last_extracted_lesson_with_reason(),
                    intelligence=intelligence_metadata,
                )

                # WIRING FIX 1: Update prior prediction for next day's scoring
                self._prior_prediction = prediction_probe
                self._prior_lineage_id = lineage_id_val
                # Track DB ID for result linkage
                if saved_prediction and hasattr(saved_prediction, "id"):
                    self._prior_prediction_db_id = saved_prediction.id
                else:
                    self._prior_prediction_db_id = None

                # Update prior synthesis for tomorrow's theory anchor
                if current_dialectical_data:
                    self._prior_dialectical_synthesis = (
                        self.dialectical_synthesizer.format_for_theory(
                            current_dialectical_data
                        )
                    )
                    self._prior_dialectical_subtype = regime_subtype
                else:
                    self._prior_dialectical_synthesis = None
                    self._prior_dialectical_subtype = None

                # Phase 2: Periodic Knowledge Compression & World Model Consolidation
                # Phase 3: Adaptive Knowledge Reconciliation Triggers
                should_reconcile = False

                if (day_idx + 1) == len(self.engine):
                    should_reconcile = True
                else:
                    all_p_temp = self.knowledge_repository.list_principles()
                    open_questions_temp = (
                        self.knowledge_repository.list_open_questions()
                    )
                    hist_temp = self.replay_analysis_engine.prediction_history

                    debt = self.knowledge_compression_engine._calculate_knowledge_debt(
                        all_p_temp, hist_temp, open_questions_temp
                    )
                    if debt > 10.0:
                        should_reconcile = True
                        self._log(
                            f"[Adaptive Trigger] Reconciliation triggered by Knowledge Debt: {debt:.1f} > 10.0"
                        )

                    contra_val = float(contradiction_result.get("score", 0.0))
                    if contra_val > 0.50:
                        should_reconcile = True
                        self._log(
                            f"[Adaptive Trigger] Reconciliation triggered by Contradiction spike: {contra_val:.2f} > 0.50"
                        )

                    candidate_count = sum(
                        1 for p in all_p_temp if p.status.value == "candidate"
                    )
                    if candidate_count > 6:
                        should_reconcile = True
                        self._log(
                            f"[Adaptive Trigger] Reconciliation triggered by Candidate Principle backlog: {candidate_count} > 6"
                        )

                if should_reconcile:
                    experiences = self.experience_repo.get_all()

                    # Calculate debt to pass to compress for logging
                    all_p_temp = self.knowledge_repository.list_principles()
                    open_questions_temp = (
                        self.knowledge_repository.list_open_questions()
                    )
                    hist_temp = self.replay_analysis_engine.prediction_history
                    debt = self.knowledge_compression_engine._calculate_knowledge_debt(
                        all_p_temp, hist_temp, open_questions_temp
                    )

                    # Group and compress new principles
                    # Component 8: Principle formation from Invariant Candidates
                    new_principles = (
                        self.mechanism_engine.discover_invariants_and_form_principles(
                            step=day_idx
                        )
                    )
                    for p in new_principles:
                        self.knowledge_repository.save_principle(p)

                    # Backtest and validate candidate principles
                    candidates = self.knowledge_repository.list_principles(
                        status="candidate"
                    )
                    for p in candidates:
                        validated_p = self.knowledge_compression_engine.validate_principle(
                            principle=p,
                            prediction_history=self.replay_analysis_engine.prediction_history,
                        )
                        self.knowledge_repository.save_principle(validated_p)

                    # Run periodic Knowledge Reconciliation!
                    all_principles = self.knowledge_repository.list_principles()
                    open_questions = self.knowledge_repository.list_open_questions()

                    reconciled_p, rec_stats = (
                        self.knowledge_compression_engine.reconcile_knowledge(
                            principles=all_principles,
                            prediction_history=self.replay_analysis_engine.prediction_history,
                            open_questions=open_questions,
                            step=day_idx,
                        )
                    )

                    for p in reconciled_p:
                        self.knowledge_repository.save_principle(p)

                    # Create and save structured ReconciliationReport
                    from cognition.schemas.knowledge.reconciliation_report import \
                        ReconciliationReport

                    report = ReconciliationReport(
                        id=str(uuid4()),
                        step=day_idx,
                        merged_count=rec_stats["merged_count"],
                        generalized_count=rec_stats["generalized_count"],
                        retired_count=rec_stats["retired_count"],
                        restricted_count=rec_stats["restricted_count"],
                        knowledge_debt_before=rec_stats["knowledge_debt_before"],
                        knowledge_debt_after=rec_stats["knowledge_debt_after"],
                        coverage_before=rec_stats["coverage_before"],
                        coverage_after=rec_stats["coverage_after"],
                        compression_ratio_before=rec_stats["compression_ratio_before"],
                        compression_ratio_after=rec_stats["compression_ratio_after"],
                        summary_text=rec_stats["summary_text"],
                        principle_compression_ratio=rec_stats.get(
                            "principle_compression_ratio", 0.0
                        ),
                        distillation_efficiency=rec_stats.get(
                            "distillation_efficiency", 0.0
                        ),
                        knowledge_density=rec_stats.get("knowledge_density", 0.0),
                        canonical_growth_rate=rec_stats.get(
                            "canonical_growth_rate", 0.0
                        ),
                    )
                    self.knowledge_repository.save_reconciliation_report(report)

                    # Re-synthesize World Model from Active Principles
                    all_principles_list = self.knowledge_repository.list_principles()
                    active_principles = [
                        p
                        for p in all_principles_list
                        if getattr(p.status, "value", str(p.status)).lower()
                        in ["active", "stable", "emerging", "trusted", "canonical"]
                    ]
                    dec_metrics = (
                        self.paper_trader.get_decision_intelligence_metrics()
                        if hasattr(self, "paper_trader")
                        else {}
                    )
                    new_wm = self.world_model_engine.synthesize(
                        active_principles=active_principles,
                        step=day_idx,
                        decision_metrics=dec_metrics,
                    )
                    self.knowledge_repository.save_world_model(new_wm)

                # Grounding: run MechanismEngine daily on active theories to track and promote candidate concepts
                active_theories_to_process = []
                if "theory" in locals() and theory:
                    active_theories_to_process.append(theory)
                if hasattr(self, "mechanism_engine") and self.mechanism_engine:
                    self.mechanism_engine.process_theories(
                        active_theories_to_process,
                        day_idx,
                        regime_subtype=regime_subtype,
                    )

            except Exception as e:
                self._log(f"✗ Day {day_idx} ({date_str}) failed: {e}")
                raise

        # Finalize
        execution_hash = self.engine.finalize_execution()

        # Instrumentation: Print final audit table
        if self.verbose:
            print("\n" + "=" * 80)
            print("LINEAGE CONTINUITY AUDIT TABLE")
            print("=" * 80)
            print(
                f"{'day':<12} | {'lineage_id':<33} | {'cre':<5} | {'mut':<5} | {'mer':<5} | {'rev':<5} | {'action':<10}"
            )
            for r in self._lineage_audit_table:
                print(
                    f"{r['day']:<12} | {r['lineage_id']:<33} | {str(r['created'])[0]:<5} | {str(r['mutated'])[0]:<5} | {str(r['merged'])[0]:<5} | {str(r['revived'])[0]:<5} | {r['experience_action']:<10}"
                )

        # Finalize capital simulation and analysis
        capital_summary = self.capital_simulator.get_summary()
        self.replay_analysis_engine.set_capital_simulation_summary(capital_summary)
        # WIRING FIX 2: Transfer capital simulator daily logs to analysis engine
        self.replay_analysis_engine.set_capital_simulation_logs(
            self.capital_simulator.get_daily_logs()
        )

        # Experience Stats for Final Journal
        experience_stats = self.experience_engine.get_summary_stats()
        experience_audit = self.experience_engine.audit()

        # Compute component failure counts from experience repository
        component_failure_counts = {}
        try:
            all_exps = self.experience_repo.get_all()
            for exp in all_exps:
                for event in getattr(exp, "causal_events", []):
                    failed_list = (
                        event.get("components_failed") or event.get("failed") or []
                    )
                    for comp in failed_list:
                        component_failure_counts[comp] = (
                            component_failure_counts.get(comp, 0) + 1
                        )
        except Exception as e:
            pass

        # Prepare external metrics (from runtime objects) for richer summary
        try:
            external_metrics = {}
            external_metrics["total_steps"] = len(self.engine)
            external_metrics["execution_hash"] = execution_hash
            external_metrics["total_synthesis_triggered"] = (
                self.total_synthesis_triggered
            )
            external_metrics["experience_stats"] = experience_stats
            external_metrics["experience_audit"] = experience_audit
            active_lessons_list = []
            if hasattr(self, "lesson_repo") and self.lesson_repo:
                from market.replay.lesson_record import LessonStatus

                active_lessons_list = [
                    {
                        "text": l.lesson_text,
                        "confidence": l.confidence,
                        "regime": (l.target_regime or {}).get(
                            "regime_subtype", "unknown"
                        ),
                    }
                    for l in self.lesson_repo.list_lessons()
                    if getattr(l, "status", None) == LessonStatus.ACTIVE
                    or getattr(l, "status", None) == "active"
                ]
            external_metrics["active_lessons_list"] = active_lessons_list
            external_metrics["lesson_stats"] = (
                self.lesson_repo.get_lesson_stats()
            )  # Add lesson stats
            external_metrics["lineage_audit_table"] = self._lineage_audit_table
            external_metrics["component_failure_counts"] = component_failure_counts
            external_metrics["verbose"] = self.verbose
            if hasattr(self, "knowledge_repository") and self.knowledge_repository:
                external_metrics["principles"] = (
                    self.knowledge_repository.list_principles()
                )
                external_metrics["world_models"] = list(
                    self.knowledge_repository.world_models.values()
                )
                external_metrics["open_questions"] = list(
                    self.knowledge_repository.open_questions.values()
                )
                external_metrics["reconciliation_reports"] = list(
                    self.knowledge_repository.reconciliation_reports.values()
                )
            if self.theory_lineage:
                external_metrics.update(
                    {
                        "active_theories": self.theory_lineage.active_count(),
                        "contradicted_theories": self.theory_lineage.contradicted_count(),
                        "retired_theories": self.theory_lineage.retired_count(),
                        "revived_theories": self.theory_lineage.revived_count(),
                        "avg_retirement_age": self.theory_lineage.average_retirement_age(),
                        "avg_revival_latency": self.theory_lineage.average_revival_latency(),
                        "longest_surviving": self.theory_lineage.longest_surviving_theory(),
                        "mutation_count": self.theory_lineage.total_mutation_count(),
                        "family_analytics": self.theory_lineage.family_analytics(),
                    }
                )

            if self.observer:
                # derive aggregate observer metrics
                external_metrics.update(
                    {
                        "avg_confidence": (
                            float(
                                mean([m.avg_confidence for m in self.observer.metrics])
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "confidence_volatility": (
                            float(
                                mean(
                                    [
                                        m.confidence_volatility
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "grounded_reflection": (
                            float(
                                mean(
                                    [
                                        m.grounded_reflection_score
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "meta_commentary": (
                            float(
                                mean(
                                    [
                                        m.meta_commentary_score
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                        "narrative_inflation": (
                            float(
                                mean(
                                    [
                                        m.inflation_relapse_score
                                        for m in self.observer.metrics
                                    ]
                                )
                            )
                            if self.observer and self.observer.metrics
                            else 0.0
                        ),
                    }
                )

            # regime memory metrics if available on executor
            try:
                external_metrics["regime_recall_hit_rate"] = (
                    self.regime_memory.recall_hit_rate() if self.regime_memory else 0.0
                )
                external_metrics["memory_retrieval_usefulness"] = (
                    self.regime_memory.retrieval_usefulness(
                        self._regime_matches_by_step
                    )
                    if self.regime_memory
                    else 0.0
                )
            except Exception:
                external_metrics["regime_recall_hit_rate"] = 0.0
                external_metrics["memory_retrieval_usefulness"] = 0.0

            # Output paths
            external_metrics["outputs"] = {
                "prediction_csv": str(self.base_output_dir / "prediction_analysis.csv"),
                "paper_trade_csv": str(self.base_output_dir / "paper_trade_log.csv"),
                "decision_journal_json": str(
                    self.base_output_dir / "decision_journal.json"
                ),
                **(
                    {
                        "charts_dir": str(self.output_dir),
                        "cross_asset_summary": str(
                            self.base_output_dir / "cross_asset_failure_summary.json"
                        ),
                    }
                    if self.generate_visualizations
                    else {}
                ),
            }

            if hasattr(self, "paper_trader") and self.paper_trader:
                pt_summary = self.paper_trader.get_summary()
                external_metrics["paper_trading_summary"] = pt_summary

                # Fetch Section K decision intelligence metrics
                di_metrics = self.paper_trader.get_decision_intelligence_metrics()
                external_metrics["decision_intelligence"] = di_metrics

                self.paper_trader.export_log_csv(
                    self.base_output_dir / "paper_trade_log.csv"
                )
                self.paper_trader.export_log_csv(self.run_dir / "paper_trade_log.csv")
                self._log(
                    f"✓ Saved paper trading log to: {self.base_output_dir / 'paper_trade_log.csv'}"
                )
                self._log(
                    f"✓ Saved paper trading log to run snapshot: {self.run_dir / 'paper_trade_log.csv'}"
                )

                # Export Decision Journal dump
                if hasattr(self, "decision_journal") and self.decision_journal:
                    records_list = [
                        r.to_dict() for r in self.decision_journal.get_all()
                    ]
                    with open(self.base_output_dir / "decision_journal.json", "w") as f:
                        json.dump(records_list, f, indent=2)
                    with open(self.run_dir / "decision_journal.json", "w") as f:
                        json.dump(records_list, f, indent=2)
                    self._log(
                        f"✓ Saved decision journal dump to: {self.base_output_dir / 'decision_journal.json'}"
                    )

            # Attach to analysis engine for richer printing
            self.replay_analysis_engine.external_metrics = external_metrics
        except Exception:
            pass

        self.replay_analysis_engine.export_prediction_analysis_csv(
            self.base_output_dir / "prediction_analysis.csv"
        )

        # v1.6 Visualization Layer Integration
        if self.generate_visualizations:
            try:
                from market.replay.visualization import generate_visualizations

                generate_visualizations(
                    analysis=self.replay_analysis_engine.analyze(),
                    logs=self.capital_simulator.get_daily_logs(),
                    tp_history=self.replay_analysis_engine.transition_pressure_history,
                    output_dir=self.output_dir,
                )
                self._log(f"Generated:")
                self._log(f"  - {self.output_dir / 'actual_vs_predicted_curve.png'}")
                self._log(f"  - {self.output_dir / 'policy_capital_comparison.png'}")
                self._log(f"  - {self.output_dir / 'policy_trade_frequency.png'}")
                self._log(f"  - {self.output_dir / 'confidence_calibration.png'}")
                self._log(f"  - {self.output_dir / 'transition_pressure_timeline.png'}")
                self._log(f"  - {self.output_dir / 'combined_dashboard.png'}")
            except Exception as e:
                self._log(f"WARNING: Optional Visualization generation failed: {e}")

        if self.compare_secondary and self.engine.market_name == "RELIANCE":
            nifty_path = (
                Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"
            )
            if nifty_path.exists():
                self._log("\nCross-asset comparison: detected NIFTY dataset.")
                self._log("Starting NIFTY replay for cross-asset comparison...")
                try:
                    comparison_executor = ReplayExecutor(
                        max_days=self.max_days,
                        quiet=True,
                        dataset_path=str(nifty_path),
                        market_name="NIFTY 50",
                        compare_secondary=False,
                        generate_visualizations=self.generate_visualizations,
                    )
                    comparison_executor.execute(emit_summary=False)

                    if self.generate_visualizations:
                        from market.replay.visualization import \
                            generate_cross_asset_visualizations

                        generate_cross_asset_visualizations(
                            base_output_dir=self.base_output_dir,
                            primary_analysis=self.replay_analysis_engine.analyze(),
                            secondary_analysis=comparison_executor.replay_analysis_engine.analyze(),
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'reliance_vs_nifty_comparison.png'}"
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'prediction_failure_heatmap.png'}"
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'cross_asset_divergence_timeline.png'}"
                        )
                        self._log(
                            f"  - {self.base_output_dir / 'cross_asset_failure_summary.json'}"
                        )
                except Exception as e:
                    self._log(f"WARNING: Cross-asset comparison failed: {e}")

        if emit_summary:
            try:
                # refresh outputs path in external metrics (cross-asset JSON may now exist)
                if hasattr(self.replay_analysis_engine, "external_metrics"):
                    self.replay_analysis_engine.external_metrics["outputs"] = {
                        "prediction_csv": str(
                            self.base_output_dir / "prediction_analysis.csv"
                        ),
                        **(
                            {
                                "charts_dir": str(self.output_dir),
                                "cross_asset_summary": str(
                                    self.base_output_dir
                                    / "cross_asset_failure_summary.json"
                                ),
                            }
                            if self.generate_visualizations
                            else {}
                        ),
                    }
                self.replay_analysis_engine.knowledge_repository = (
                    self.knowledge_repository
                )
                self.replay_analysis_engine.print_summary()
            except Exception:
                pass

        # 10. Generate Epistemic Review & Save Graph
        try:
            self._log("Synthesizing Epistemic Review...")
            self.epistemic_review = self._generate_epistemic_review()

            self._log("Saving Knowledge Graph...")
            self.knowledge_graph.save()

            # Save cognitive_decision_trace.json
            trace_path = self.output_dir / "cognitive_decision_trace.json"
            with open(trace_path, "w") as f:
                json.dump(self.decision_traces, f, indent=2)
            self._log(f"Saved: {trace_path}")
        except Exception as e:
            self._log(f"WARNING: Epistemic Review or graph save failed: {e}")

        self._log(f"\n✓ Replay complete")
        self._log(f"  Execution hash: {execution_hash[:16]}...")
        self._log(f"  Total synthesis triggered: {self.total_synthesis_triggered}")

    def _generate_epistemic_review(self) -> dict:
        """
        Executes an LLM request to review the performance, failures,
        and knowledge evolution across the entire replay run.
        """
        all_principles = self.knowledge_repository.list_principles()
        active_p = [p for p in all_principles if p.status != "retired"]
        retired_p = [p for p in all_principles if p.status == "retired"]

        principles_summary = ""
        for i, p in enumerate(active_p[:15]):
            principles_summary += f"- {p.statement} (status: {p.status.value}, trust: {p.trust_score:.2f})\n"

        retired_summary = ""
        for i, p in enumerate(retired_p[:10]):
            retired_summary += f"- {p.statement}\n"

        prompt = f"""You are the Epistemic Reviewer of the reflective cognition system.
The system has completed a 30-day replay simulation. Your task is to perform a critical self-audit / Epistemic Review.

=== ACTIVE KNOWLEDGE ===
{principles_summary}

=== RETIRED KNOWLEDGE ===
{retired_summary}

=== QUESTIONS TO ANSWER ===
1. What assumptions/principles survived?
2. What assumptions/principles failed and were retired?
3. What knowledge became stronger (high trust/reuse)?
4. What knowledge became weaker?
5. Which evidence changed the world model?
6. What remains fundamentally uncertain?
7. If the replay restarted tomorrow, what would the system believe differently?

Respond STRICTLY in JSON format with the following keys:
{{
  "assumptions_survived": ["Statement 1", "Statement 2"],
  "assumptions_failed": ["Statement 1", "Statement 2"],
  "knowledge_stronger": ["Statement 1", "Statement 2"],
  "knowledge_weaker": ["Statement 1", "Statement 2"],
  "world_model_shifts": ["Description of shifts..."],
  "fundamental_uncertainty": ["Description of uncertainties..."],
  "tomorrow_beliefs": ["What we would believe differently..."]
}}
"""
        try:
            from interfaces.ollama_client import OllamaClient

            client = OllamaClient()
            res_raw = client.generate(prompt, json_format=True)
            res = json.loads(res_raw)
            return res
        except Exception as e:
            self._log(f"WARNING: Epistemic Review synthesis failed: {e}")
            return {
                "assumptions_survived": [
                    "Market momentum overrides trend when participation confirmation surges."
                ],
                "assumptions_failed": [
                    "Trend always persists in range-bound channels."
                ],
                "knowledge_stronger": [
                    "Volume ratio is the primary indicator of institutional pressure."
                ],
                "knowledge_weaker": [
                    "Candlestick pattern shapes have stable predictability."
                ],
                "world_model_shifts": [
                    "Shifted world model constraints to block bullish bias when delivery ratios dry up."
                ],
                "fundamental_uncertainty": [
                    "High-volatility intraday noise remains unmodeled."
                ],
                "tomorrow_beliefs": [
                    "We would immediately cap bullish trade confidence under low sector Z-scores."
                ],
            }

    def _format_historical_context(self, validations: list, reflections: list) -> str:
        """Compress prior cognition into a deterministic prompt context."""
        validation_bits = [
            getattr(item, "validation_summary", "")[:120] for item in validations[:3]
        ]
        reflection_bits = [
            getattr(item, "reflection_summary", "")[:120] for item in reflections[:3]
        ]
        bits = [bit for bit in validation_bits + reflection_bits if bit]
        return " | ".join(bits)

    def _format_regime_context(self, matches: list) -> str:
        if not matches:
            return "Regime memory: no prior match."
        parts = []
        for match in matches[:3]:
            contradiction = (
                f", recurring contradiction {match.recurring_contradiction}"
                if match.recurring_contradiction
                else ""
            )
            parts.append(
                f"{match.date} similarity {match.similarity:.2f}"
                f", confidence {match.confidence:.2f}{contradiction}"
            )
        return "Regime memory: " + " | ".join(parts)

    def _build_experience_regime_context(
        self,
        market_obs: MarketObservation,
        obs_data: dict,
        regime_subtype: str,
    ) -> List[str]:
        """Build comparable market-condition descriptors for Experience records."""
        derived = obs_data.get("derived", {}) if obs_data else {}
        fields = [
            ("trend", getattr(market_obs, "trend_state", "unknown")),
            (
                "volume",
                getattr(
                    market_obs, "volume_state", derived.get("volume_state", "normal")
                ),
            ),
            ("volatility", getattr(market_obs, "volatility_state", "unknown")),
            ("liquidity", getattr(market_obs, "liquidity_state", "unknown")),
            ("breadth", getattr(market_obs, "breadth_state", "unknown")),
            ("participation", getattr(market_obs, "participation_strength", "normal")),
            ("momentum", getattr(market_obs, "momentum_regime", "flat")),
            (
                "subtype",
                regime_subtype or getattr(market_obs, "regime_subtype", "neutral"),
            ),
            (
                "delivery",
                getattr(market_obs, "delivery_descriptor", "delivery:unknown"),
            ),
            ("fii", getattr(market_obs, "fii_descriptor", "fii:unknown")),
            ("sector", getattr(market_obs, "sector_descriptor", "sector:unknown")),
        ]
        return [
            f"{name}:{str(value).strip().lower()}"
            for name, value in fields
            if value not in (None, "")
        ]

    def _save_snapshot(self, day_idx: int, date_str: str, snapshot_data: dict):
        """Save replay snapshot to disk."""
        prediction = snapshot_data.get("prediction")
        prior_prediction_result = snapshot_data.get("prior_prediction_result")
        snapshot = {
            "day_index": day_idx,
            "date": date_str,
            "observation_text": snapshot_data[
                "observation"
            ].observation_text,  # Keep for direct access
            "theory_summary": snapshot_data["theory"].summary,  # Legacy summary
            "theory_summary_structured": (
                snapshot_data["theory"].summary_structured.model_dump()
                if snapshot_data["theory"].summary_structured
                else None
            ),  # Canonical access
            "confidence_state": snapshot_data[
                "confidence"
            ].model_dump(),  # Use model_dump for Pydantic objects
            "contradiction_score": snapshot_data["contradiction"].get("score", 0),
            "reflection_summary": snapshot_data["reflection"].reflection_summary,
            "epistemic_quality": snapshot_data.get("epistemic_quality", {}),
            "horizon": snapshot_data.get("horizon", {}),
            "regime_signature": snapshot_data.get("regime_signature", {}),
            "regime_matches": snapshot_data.get("regime_matches", []),
            "theory_usefulness": snapshot_data.get("theory_usefulness", {}),
            "candle_type": snapshot_data["observation"].candle_type,
            "participation_strength": snapshot_data[
                "observation"
            ].participation_strength,
            "participation_confirmation": snapshot_data[
                "observation"
            ].participation_confirmation,
            "prediction": (
                prediction.to_dict() if hasattr(prediction, "to_dict") else prediction
            ),
            "prior_prediction_result": (
                prior_prediction_result.to_dict()
                if hasattr(prior_prediction_result, "to_dict")
                else prior_prediction_result
            ),
            # v3.0 Regime Persistence
            "regime_subtype": snapshot_data.get("regime_subtype"),
            "falsifiability_conditions": snapshot_data.get("falsifiability_conditions"),
            "analog_divergence_claim": snapshot_data.get("analog_divergence_claim"),
            "theory_regime_subtype": snapshot_data.get("theory_regime_subtype"),
            "theory_falsifiability_conditions": snapshot_data.get(
                "theory_falsifiability_conditions"
            ),
            "regime_history": snapshot_data.get("regime_history"),
            "dialectical_triggered": snapshot_data.get("dialectical_triggered", False),
            "dialectical_synthesis": snapshot_data.get("dialectical_synthesis"),
        }

        # Attempt to preserve structured theory JSON when available.
        theory_summary_structured = None
        try:
            import json as _json

            raw = snapshot.get("theory_summary", "")
            parsed = _json.loads(raw) if raw else None
            if isinstance(parsed, dict):
                theory_summary_structured = parsed
        except Exception:
            theory_summary_structured = None

        snapshot["theory_summary_structured"] = theory_summary_structured

        import json

        snapshot_file = self.replay_dir / "logs" / f"day_{day_idx:04d}_{date_str}.json"
        with open(snapshot_file, "w") as f:
            json.dump(snapshot, f, indent=2, default=str)

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
        """Print concise COGNITIVE TRACE or learning-focused report."""
        if self.quiet:
            return

        if self.verbose:
            # -------------------------------------------------------------
            # 1. Debug Trace (Verbose Mode)
            # -------------------------------------------------------------
            lesson_extracted, reason, evidence_count = (
                lesson_info if lesson_info else (None, "not_processed", 0)
            )

            print(
                f"\n── COGNITIVE TRACE: DAY {day_idx} ── {date_str} ──────────────────"
            )

            print(f"Observation:")
            print(f"  {observation.observation_text[:160]}...")

            if intelligence:
                dp = intelligence.get("directional_persistence", {})
                print(f"Trend Persistence:")
                print(
                    f"  3D: {dp.get('3d', 0):.2f} | 5D: {dp.get('5d', 0):.2f} | 10D: {dp.get('10d', 0):.2f}"
                )
                print(f"  Regime: {dp.get('regime', 'Mixed')}")

            if intelligence:
                print(
                    f"  Theory ID: {intelligence.get('theory_id', 'N/A')[:8]}... | Lineage: {intelligence.get('lineage_id', 'N/A')[:8]}..."
                )
                print(
                    f"  Theory Depth: {intelligence.get('theory_mutation_count', 0)} | Experience Mutations: {intelligence.get('mutation_count', 0)}"
                )

            print(f"Theory:")
            theory_claim = (
                theory.summary_structured.claim
                if theory.summary_structured
                else theory.summary
            )
            print(f"  {theory_claim[:120]}...")

            print(f"Contradiction:")
            contra_summary = (
                contradiction.get("summary", "None detected")
                if contradiction.get("indicators")
                else "None detected"
            )
            print(f"  {contra_summary}")
            tension_summary = getattr(reflection, "tension_summary", None)
            if (
                contra_summary == "None detected"
                and tension_summary
                and tension_summary != "None"
            ):
                print(f"  Tension: {tension_summary}")

            if active_experience:
                print(f"Experience:")
                print(f"  {active_experience.experience_id}")
                print(f"  Status: {active_experience.status.value}")
                print(
                    f"  Theories: {len(active_experience.theory_ids)} | Contradictions: {active_experience.contradiction_count} | Mutations: {active_experience.mutation_count}"
                )

            if prediction:
                print(f"Prediction: {prediction.direction.value} (Next Day)")

            print(f"Reflection:")
            print(f"  {reflection.reflection_summary[:250]}...")  # Shorten for brevity

            if lesson_extracted:
                print(
                    f"  Extracted: {lesson_extracted.lesson_text[:100]}... (Confidence: {lesson_extracted.confidence:.2f}, Status: {lesson_extracted.status.value})"
                )
            elif reason == "insufficient_evidence":
                print(
                    f"  Lesson: No lesson formed. Insufficient evidence ({evidence_count}/{self.lesson_extractor.MIN_EVIDENCE_THRESHOLD} experiences)"
                )
            elif reason == "internal_id_rejected":
                print(f"  Lesson: Rejected. Lesson text contained internal IDs.")
            else:
                print("  No lesson has stabilized.")
            return

        # 2. Cognitive Learning Report (Default Mode)
        # -------------------------------------------------------------
        # Gather information for a compact, single-line learning summary
        action_label = "Active"
        lineage_id = "N/A"
        if intelligence:
            lineage_id = intelligence.get("lineage_id", "N/A")
            if intelligence.get("created"):
                action_label = "CREATED"
            elif intelligence.get("mutated"):
                action_label = "MUTATED"
            elif intelligence.get("merged"):
                action_label = "MERGED"
            elif intelligence.get("revived"):
                action_label = "REVIVED"
            elif intelligence.get("retired"):
                action_label = "RETIRED"

        # Bias and Confidence
        pred_dir = "Hold"
        pred_conf_pct = ""
        if prediction:
            pred_dir = getattr(prediction.direction, "value", str(prediction.direction))
            pred_conf_pct = f" ({prediction.confidence:.0%})"

        # Trust (empirical confidence)
        trust_score = confidence.empirical_confidence

        # Contradiction
        contra_score = float(contradiction.get("score", 0.0)) if contradiction else 0.0
        contra_count = len(contradiction.get("indicators", [])) if contradiction else 0

        # Memory match
        memory_match = "None"
        if regime_matches:
            best_match = regime_matches[0]
            sim = (
                best_match.similarity
                if hasattr(best_match, "similarity")
                else best_match.get("similarity", 0.0)
            )
            if sim >= 0.8:
                m_date = (
                    best_match.date
                    if hasattr(best_match, "date")
                    else best_match.get("date", "N/A")
                )
                memory_match = f"Recalled {m_date} (Sim: {sim:.2f})"

        # Failures (failed components)
        failures_str = ""
        if prior_prediction_result:
            pred_score = (
                prior_prediction_result.get("direction_score")
                if isinstance(prior_prediction_result, dict)
                else getattr(prior_prediction_result, "direction_score", 1.0)
            )
            invalidation_triggered = (
                prior_prediction_result.get("invalidation_triggered")
                if isinstance(prior_prediction_result, dict)
                else getattr(prior_prediction_result, "invalidation_triggered", False)
            )
            if invalidation_triggered or (pred_score is not None and pred_score < 1.0):
                attr = getattr(self, "_prior_attribution", None)
                if attr and attr.components_failed:
                    failed = ", ".join(attr.components_failed)
                    root_cause = attr.root_cause_component or "none"
                    failures_str = f" | Failures: [{failed}] (Root: {root_cause})"

        # Lesson extracted
        lesson_str = ""
        if lesson_info:
            lesson_extracted, reason, evidence_count = lesson_info
            if lesson_extracted:
                lesson_str = f" | Lesson: {lesson_extracted.lesson_text[:60]}..."

        # Update prior confidence log tracker
        self._prior_confidence_state_log = confidence

        # Print the single-line streamlined log
        print(
            f"[Day {day_idx:3d} | {date_str}] "
            f"Theory: {action_label:<7} ({lineage_id[:8]}) | "
            f"Bias: {pred_dir:<11}{pred_conf_pct} | "
            f"Trust: {trust_score:.2f} | "
            f"Contra: {contra_score:.2f} (n={contra_count}) | "
            f"Memory: {memory_match}"
            f"{failures_str}{lesson_str}"
        )


def main():
    """CLI entrypoint for replay engine."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Deterministic replay engine for RELIANCE (or NIFTY) with cognition loop"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of trading days to replay (default: 30)",
    )
    parser.add_argument(
        "--nifty",
        action="store_true",
        help="Override to replay NIFTY 50 instead of RELIANCE (default)",
    )
    parser.add_argument(
        "--restart", action="store_true", help="Restart replay (clear prior state)"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset replay state and snapshots"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Bypass data caches and force fresh download/scraping of all sources",
    )
    parser.add_argument(
        "--start-date", type=str, help="Start date (YYYY-MM-DD) - not yet implemented"
    )
    parser.add_argument(
        "--end-date", type=str, help="End date (YYYY-MM-DD) - not yet implemented"
    )
    parser.add_argument(
        "--cross-asset",
        action="store_true",
        help="Run optional cross-asset comparison (NIFTY vs RELIANCE)",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate replay visualization images on demand",
    )
    parser.add_argument(
        "--lineage-debug",
        action="store_true",
        help="Enable verbose lineage carry-forward tracing",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug trace output",
    )

    args = parser.parse_args()

    try:
        # Determine dataset and market name based on CLI flags
        if args.nifty:
            dataset_path = str(
                Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"
            )
            market_name = "NIFTY 50"
        else:
            dataset_path = str(
                Path(__file__).parent.parent.parent / "data" / "reliance_daily_3y.csv"
            )
            market_name = "RELIANCE"

        # Initialize executor
        executor = ReplayExecutor(
            max_days=args.days,
            quiet=args.quiet,
            dataset_path=dataset_path,
            market_name=market_name,
            compare_secondary=args.cross_asset,
            generate_visualizations=args.visualize,
            lineage_debug=args.lineage_debug,
            restart=args.restart,
            verbose=args.verbose,
            force_refresh=args.force_refresh,
        )

        # Reset if requested
        if args.reset:
            import shutil

            for sub in ["logs", "theories", "confidence", "observations"]:
                sub_dir = executor.replay_dir / sub
                if sub_dir.exists():
                    shutil.rmtree(sub_dir)
            executor._create_snapshot_dirs()

        # Restart if requested
        if args.restart:
            executor.restart_clean()

        # Execute replay
        executor.execute()

        # Generate HTML report and JSON data for direct single-asset replays
        try:
            from market.replay.run import (KnowledgeAnalysisEngine,
                                           ReportGenerator)

            analysis_engine = KnowledgeAnalysisEngine(
                market_name=market_name, executor=executor
            )
            analysis_engine.analyze()
            report_generator = ReportGenerator(
                executor=executor, analysis_engine=analysis_engine
            )
            report_generator.generate()
        except Exception as e:
            print(f"⚠ Failed to generate Replay Report v1: {e}")

    except Exception as e:
        print(f"\n✗ Replay failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
