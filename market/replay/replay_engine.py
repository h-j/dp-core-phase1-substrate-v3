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
import os
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import List

import pandas as pd

from market.data.dataset_validator import DatasetValidator
from market.replay.prediction_probe import PredictionProbeGenerator
from market.replay.capital_simulator import CapitalSimulator
from market.replay.transition_pressure import TransitionPressureEngine
from market.replay.decision_policy import DecisionPolicyEngine
from memory.replay.regime_memory import RegimeMemoryStore # Import RegimeMemoryStore
from flows.theory_flow.regime_continuity_memory import RegimeContinuityMemory
from market.replay.transition_memory import TransitionMemoryStore, TransitionExample
from experience.experience_engine import ExperienceEngine
from experience.experience_repository import ExperienceRepository


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
        self.dataset_path = dataset_path
        self.market_name = market_name
        self.compare_secondary = compare_secondary
        self.lineage_debug = lineage_debug
        self.replay_dir = Path(__file__).parent.parent.parent / "memory" / "replay"
        self.base_data_snap_dir = (
            Path(__file__).parent.parent.parent / "data" / "replay_snapshots"
        )
        self.base_output_dir = Path(__file__).parent.parent.parent / "market" / "replay" / "output"
        self._create_snapshot_dirs()

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
        self.output_dir = self.base_output_dir / self.engine.market_name.lower().replace(" ", "_")
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        self._prior_lineage_id = None # Track the lineage that produced the prediction
        self.regime_memory = RegimeMemoryStore() # Initialize unconditionally
        self.regime_continuity_memory = RegimeContinuityMemory()
        self._prior_dialectical_synthesis = None
        self._prior_dialectical_subtype = None
        self._prior_prediction_db_id = None
        self.decision_engine = DecisionPolicyEngine()
        self._regime_matches_by_step: List[list] = []
        self.replay_analysis_engine = None # Will be initialized in execute
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

    def _initialize_flows(self):
        """Lazy initialize cognition flows and repositories."""
        if self.flows_initialized:
            return

        # v3.7 Logic: Ensure schema is valid before starting execution
        from memory.relational.postgres_client import engine
        # Note: postgres_client triggers create_all and validation on import.
        # No explicit call needed here to avoid redundant I/O.

        from cognition.confidence.confidence_evolution_engine import (
            ConfidenceEvolutionEngine,
        )
        from cognition.contradiction.contradiction_detector import ContradictionDetector
        from flows.observation_flow.abstraction_flow import AbstractionFlow
        from flows.reflection_flow.reflection_flow import ReflectionFlow
        from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
        from flows.theory_flow.dialectical_synthesizer import DialecticalTheorySynthesizer
        from memory.relational.repositories.abstraction_repository import (
            AbstractionRepository,
        )
        from memory.relational.repositories.confidence_repository import (
            ConfidenceRepository,
        )
        from memory.relational.repositories.observation_repository import (
            ObservationRepository,
        )
        from memory.relational.repositories.reflection_repository import (
            ReflectionRepository,
        )
        from memory.relational.repositories.theory_repository import TheoryRepository
        from memory.relational.repositories.validation_repository import (
            ValidationRepository,
        )
        from memory.relational.repositories.prediction_repository import PredictionRepository
        from memory.relational.repositories.prediction_result_repository import PredictionResultRepository
        from memory.relational.repositories.transition_pressure_repository import TransitionPressureRepository
        from memory.relational.repositories.market_outcome_repository import MarketOutcomeRepository

        self.abstraction_flow = AbstractionFlow()
        self.theory_flow = TheoryGenerationFlow()
        self.reflection_flow = ReflectionFlow()
        self.dialectical_synthesizer = DialecticalTheorySynthesizer()
        self.contradiction_detector = ContradictionDetector()
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
            from memory.relational.repositories.market_outcome_repository import MarketOutcomeRepository
            self.market_outcome_repo = MarketOutcomeRepository()
            # Lesson Layer V1: JSON file persistence, not relational DB
        except (ImportError, ModuleNotFoundError):
            self._log("WARNING: MarketOutcomeRepository missing; optional persistence disabled.")
            self.market_outcome_repo = None

        self.flows_initialized = True

    def _log(self, message: str):
        """Print if not quiet mode, and also to a debug log file."""
        if not self.quiet: print(message)
        # Optional: Add logging to a file here
        # with open(self.run_dir / "replay_debug.log", "a") as f: f.write(message + "\n")

    def execute(self, emit_summary: bool = True):
        """Execute full replay with cognition loop."""
        self._initialize_flows()

        # Create a run-isolated snapshot directory for this replay.
        self.run_dir = (
            self.base_data_snap_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.run_dir.mkdir(parents=True, exist_ok=True)

        from cognition.evaluation.epistemic_quality import evaluate_epistemic_quality
        from cognition.schemas.observation.observation_event import ObservationEvent
        from cognition.schemas.validation.validation_event import ValidationEvent
        from cognition.schemas.confidence.confidence_state import ConfidenceState
        from market.replay.market_observation_synthesizer import (
            MarketObservationSynthesizer,
        )
        # Lesson Layer V1: Initialize LessonRepository and LessonExtractor
        from market.replay.lesson_repository import LessonRepository
        from market.replay.lesson_extractor import LessonExtractor
        self.lesson_repo = LessonRepository(self.run_dir / "lessons.json")
        self.lesson_extractor = LessonExtractor(self.lesson_repo, self.experience_repo)
        from memory.replay.epistemic_scoring import EpistemicScoringEngine
        from memory.replay.horizon_cognition import HorizonCognitionEngine
        from memory.replay.regime_memory import RegimeMemoryStore

        # Create a run-isolated snapshot directory for this replay.
        self.run_dir = (
            self.base_data_snap_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.run_dir.mkdir(parents=True, exist_ok=True)

        try:
            from dp.observability.cognition_observer import CognitionObserver
            from dp.observability.contradiction_registry import ContradictionRegistry
            from dp.theory.theory_lineage import TheoryLineageEngine

            self.observer = CognitionObserver(
                self.run_dir / "observability_metrics.json"
            )
            self.theory_lineage = TheoryLineageEngine(
                self.run_dir / "theory_lineage.json"
            )
            self.theory_lineage.debug = self.lineage_debug
            self.contradiction_registry = ContradictionRegistry(
                self.run_dir / "contradiction_registry.json")
            self.horizon_engine = HorizonCognitionEngine()
            self.epistemic_scoring = EpistemicScoringEngine()
            self.prediction_generator = PredictionProbeGenerator()
            self.prediction_generator.debug = self.lineage_debug
            self.experience_engine.set_lesson_extractor(self.lesson_extractor) # Pass extractor to experience engine
            self.capital_simulator = CapitalSimulator()
        except Exception:
            self.observer = None
            self.theory_lineage = None
            self.contradiction_registry = None
            self.horizon_engine = HorizonCognitionEngine()
            self.epistemic_scoring = EpistemicScoringEngine()
            self.prediction_generator = PredictionProbeGenerator()
            self.prediction_generator.debug = self.lineage_debug
            self.experience_engine.set_lesson_extractor(self.lesson_extractor)
            self.capital_simulator = CapitalSimulator()

        from market.replay.replay_analysis import ReplayAnalysisEngine
        self.replay_analysis_engine = ReplayAnalysisEngine(market_name=self.engine.market_name)

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
            if self.lineage_debug: self._log("\nCONTRADICTION:")
            config_summary["contradiction"] = self.contradiction_detector.CONFIG
            if self.lineage_debug:
                for k, v in config_summary["contradiction"].items():
                    self._log(f"  {k}={v}")
        
        if self.transition_pressure_engine:
            if self.lineage_debug: self._log("\nTRANSITION:")
            config_summary["transition_pressure"] = self.transition_pressure_engine.TP_CONFIG
            if self.lineage_debug:
                for k, v in config_summary["transition_pressure"].items():
                    self._log(f"  {k}={v}")
        
        # Persist snapshot for cross-run audit
        with open(self.run_dir / "config_snapshot.json", "w") as f:
            json.dump(config_summary, f, indent=2)
        self.replay_analysis_engine.set_config_snapshot(config_summary)
        self._log("\n" + "-" * 70)

        last_lineage_id = None # Instrumentation: Track lineage changes

        # Execute replay
        for day_idx in range(len(self.engine)):
            try:
                obs_data = self.engine.get_observation_for_day(day_idx)
                date_str = obs_data["date"]
                
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
                dir_val = 1 if "higher" in actual_dir_str else -1 if "lower" in actual_dir_str else 0
                self._actual_directions_val_history.append(dir_val)
                
                persistence_3d = mean(self._actual_directions_val_history[-3:]) if len(self._actual_directions_val_history) >= 3 else 0.0
                persistence_5d = mean(self._actual_directions_val_history[-5:]) if len(self._actual_directions_val_history) >= 5 else 0.0
                persistence_10d = mean(self._actual_directions_val_history[-10:]) if len(self._actual_directions_val_history) >= 10 else 0.0

                # Phase 1: Trend Persistence Classification
                def classify_persistence(val):
                    if val > 0.6: return "Persistent Higher"
                    if val < -0.6: return "Persistent Lower"
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
                            date=prev_obs.observation_source.replace("replay_engine_", ""),
                            day_index=day_idx - 1,
                            from_regime=prev_obs.trend_state,
                            to_regime=market_obs.trend_state,
                            confidence=ctx['confidence'],
                            theory_usefulness=ctx['usefulness'],
                            contradiction_score=ctx['contradiction'],
                            pressure_score=ctx['pressure'],
                            breakout_risk=ctx['breakout'],
                            direction_bias=ctx['bias'],
                            horizon_daily=ctx['horizon'].daily,
                            horizon_weekly=ctx['horizon'].weekly,
                            horizon_monthly=ctx['horizon'].monthly,
                            theory_summary=ctx['theory_summary']
                        )
                        
                        # Identify meaningful transitions
                        meaningful = (
                            (example.from_regime == "range_bound" and example.to_regime in ["closed_higher", "extended_higher", "closed_lower", "extended_lower"]) or
                            (example.from_regime.startswith("closed_higher") and "lower" in example.to_regime) or
                            (example.from_regime.startswith("closed_lower") and "higher" in example.to_regime)
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
                vol_regime = "compressed" if vol_30d < 0.8 else "expanded" if vol_30d > 1.5 else "normal"
                ret_3d = float(obs_data["derived"].get("return_3d", 0.0))
                mom_regime = "strengthening" if ret_3d > 0.5 else "weakening" if ret_3d < -0.5 else "flat"

                active_theory_count = (
                    self.theory_lineage.active_count() if self.theory_lineage else 0
                )
                preliminary_regime_signature = self.regime_memory.build_signature(
                    date=date_str,
                    observation=market_obs,
                    confidence_values=prior_confidence_values,
                    contradiction_severity=marker_severity,
                    active_theory_count=active_theory_count
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
                    analog_sig = analog.to_dict().get('signature', {}) if hasattr(analog, 'to_dict') else {}
                    diffs = []
                    
                    if getattr(market_obs, 'participation_strength', 'normal') != analog_sig.get('participation_strength', 'normal'):
                        diffs.append(f"participation is {market_obs.participation_strength} (prior was {analog_sig.get('participation_strength', 'normal')})")
                        
                    if getattr(market_obs, 'liquidity_state', 'normal') != analog_sig.get('liquidity_state', 'normal'):
                        diffs.append(f"liquidity is {market_obs.liquidity_state} (prior was {analog_sig.get('liquidity_state', 'normal')})")

                    if getattr(market_obs, 'volatility_state', 'normal') != analog_sig.get('volatility_state', 'normal'):
                        diffs.append(f"volatility is {market_obs.volatility_state} (prior was {analog_sig.get('volatility_state', 'normal')})")

                    market_obs.analog_divergence_claim = f"Analog to {analog.date}: " + ", ".join(diffs) if diffs else "Analog continuity"

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
                falsifiability_conditions = getattr(market_obs, "falsifiability_conditions", [])

                # v3.1 Regime Continuity Retrieval
                regime_history = self.regime_continuity_memory.summary(regime_subtype)

                if self.lineage_debug:
                    print(
                    "[Theory Input]",
                    {
                        "date": date_str,
                        "regime_subtype": regime_subtype,
                        "falsifiability_conditions": falsifiability_conditions,
                        "analog_divergence_claim": getattr(market_obs, "analog_divergence_claim", ""),
                    },
                )

                # v3.3 Relevance Gate for Dialectical Synthesis
                active_synthesis = None
                if self._prior_dialectical_synthesis:
                    max_sim = max([
                        (m.get("similarity") if isinstance(m, dict) else getattr(m, "similarity", 0.0))
                        for m in regime_matches
                    ] + [0.0]) if regime_matches else 0.0
                    
                    if regime_subtype == self._prior_dialectical_subtype or max_sim > 0.8:
                        active_synthesis = self._prior_dialectical_synthesis
                
                theory, branch_stats = self.theory_flow.process(
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
                )

                if self.lineage_debug:
                    # v3.0 Consistency debug - prefer structured claim if available
                    theory_text = theory.summary_structured.claim if theory.summary_structured else theory.summary # Canonical access with fallback
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
                        lineage_id_val = lineage_result.get("lineage_id", "N/A") # Use the stable lineage_id from lineage_result
                        audit_created = lineage_result.get("created", False)
                        audit_mutated = lineage_result.get("mutated", False)
                        audit_merged = lineage_result.get("merged", False)
                        audit_revived = lineage_result.get("revived", False) # Note: revived logic handled separately below

                        theory_step_info["created"] = int(lineage_result["created"])
                        theory_step_info["mutated"] = int(lineage_result["mutated"])
                        theory_step_info["merged"] = int(lineage_result["merged"])

                        if self.lineage_debug and lineage_record:
                            action = (
                                'continued' if lineage_result.get('continued') else
                                'merged' if lineage_result['merged'] else
                                'mutated' if lineage_result['mutated'] else
                                'created'
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
                            parent_id_for_log = lineage_result.get("parent_id", "N/A") # Use parent_id from result for logging
                            if lineage_result.get("mutated"):
                                print(f"  [LINEAGE AUDIT] MUTATION DETECTED: Old Lineage (Parent): {parent_id_for_log} -> New Lineage (Child): {lineage_record.id} (Stable Lineage: {lineage_id_val})")

                            if lineage_result.get("created"):
                                print(f"  [AUDIT] Calling create_experience for lineage {lineage_record.id}")
                                self.experience_engine.create_experience(theory.id, lineage_id_val, date_str) # Use stable lineage_id
                                exp_create_called = True
                            elif lineage_result.get("mutated") or lineage_result.get("merged"):
                                # Use the stable lineage_id for attaching theories to the experience
                                print(f"  [AUDIT] Calling attach_theory for lineage {lineage_id_val} (Theory ID: {theory.id})")
                                self.experience_engine.attach_theory(lineage_id_val, theory.id) # Use stable lineage_id
                                exp_attach_called = True

                        # Instrumentation: Log lineage/experience changes
                        if lineage_record and lineage_id_val != last_lineage_id: # Compare stable lineage_id
                            print(f"!!! LINEAGE CHANGE: {last_lineage_id} -> {lineage_record.id}")
                            last_lineage_id = lineage_record.id
                        if exp_create_called:
                            print(f"!!! NEW EXPERIENCE CREATED: exp_{lineage_record.id}_{date_str}")

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
                    self._log(f"WARNING: Theory lineage evolution failed for day {date_str}: {e}")

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
                            self.experience_engine.record_contradiction(lineage_id_val)
                except Exception:
                    pass

                # v3.2 Dialectical Synthesis Layer - Triggered after final contradiction state but before retirement
                contradiction_score = float(contradiction_result.get("score", 0.0))
                if self.lineage_debug:
                    print(f"[CONTRADICTION SCORE] score={contradiction_score:.3f}")
                    print(f"raw contradiction score={contradiction_score:.3f}")
                    print(f"source field=contradiction_result['score']")

                active_lineage_records = self.theory_lineage.active_theories() if self.theory_lineage else []
                active_theory_count = len(active_lineage_records)
                will_trigger = active_theory_count >= 2 and contradiction_score >= self.contradiction_detector.CONFIG.get("threshold_synthesis", 0.35)
                if self.lineage_debug:
                    print(f"\n[SYNTHESIS CHECK]")
                    print(f"active_theories={active_theory_count}")
                    print(f"contradiction_score={contradiction_score:.3f}")
                    print(f"will_trigger={will_trigger}")

                if will_trigger:
                    self.total_synthesis_triggered += 1
                    dialectical_data = self.dialectical_synthesizer.synthesize(
                        observation_text=market_obs.observation_text,
                        active_theories=active_lineage_records,
                        contradiction_indicators=contradiction_result.get("indicators", []),
                        regime_subtype=regime_subtype,
                        falsifiability_conditions=falsifiability_conditions
                    )
                    if dialectical_data:
                        current_dialectical_data = dialectical_data
                        if self.lineage_debug:
                            print("\n[SYNTHESIS]")
                            print(f"Shared:\n{dialectical_data.get('shared_premise')}\n")
                            print(f"Conflict:\n{dialectical_data.get('conflict')}\n")
                            print(f"Synthesis:\n{dialectical_data.get('synthesis_summary')}")

                # retire stale theories
                try:
                    if self.theory_lineage:
                        retired_records = self.theory_lineage.retire_stale_theories(
                            step=day_idx,
                            contradiction_severity=float(
                                contradiction_result.get("score", 0.0)
                            ),
                            current_record_id=(
                                lineage_record.id if lineage_record else None
                            ),
                        )
                        theory_step_info["retired"] = len(retired_records)
                        if self.lineage_debug and retired_records:
                            self._log(
                                f"[Lineage] day={day_idx} retired={','.join([r.id for r in retired_records])}"
                            )
                        if self.contradiction_registry:
                            # Experience Integration: close retired experiences
                            for retired_record in retired_records:
                                self.experience_engine.close_experience(
                                    retired_record.lineage_id, # Use stable lineage ID
                                    date_str,
                                    f"Theory lineage {retired_record.id} retired after {retired_record.survival_steps} steps."
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
                            print(f"  [AUDIT] Calling attach_theory (REVIVAL) for lineage {revived_record.lineage_id} (Theory ID: {theory.id})") # Use revived_record.lineage_id
                            self.experience_engine.attach_theory(
                                revived_record.lineage_id, theory.id
                            )
                            exp_attach_called = True
                except Exception:
                    pass

                # Instrumentation: Print Daily Trace
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
                if exp_create_called: action = "create"
                elif exp_attach_called: action = "attach"
                elif exp_close_called: action = "close"

                self._lineage_audit_table.append({
                    "day": date_str,
                    "lineage_id": lineage_id_val,
                    "created": audit_created,
                    "mutated": audit_mutated,
                    "merged": audit_merged,
                    "revived": audit_revived,
                    "experience_action": action
                })

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
                    print(f"\n[SYNTHESIS CHECK] score={contradiction_score:.3f} trigger={will_trigger}")
                    print(
                        "[Reflection Input]",
                        {
                            "date": date_str,
                            "regime_subtype": regime_subtype,
                            "analog": getattr(market_obs, "analog_divergence_claim", ""),
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
                    analog_divergence_claim=getattr(market_obs, "analog_divergence_claim", ""),
                    theory_regime_subtype=getattr(theory, "regime_subtype", "neutral"),
                    theory_falsifiability_conditions=getattr(theory, "falsifiability_conditions", []),
                    regime_history=regime_history,
                    dialectical_synthesis=self.dialectical_synthesizer.format_for_reflection(dialectical_data) 
                    if dialectical_data else None,
                )
                if self.lineage_debug:
                    # [Reflection Grounding Score] is not a direct print statement in replay_engine.py
                    print("[Reflection Output]", reflection.reflection_summary)

                # Prefer structured claim when available for downstream consumers
                theory_text = theory.summary_structured.claim # Canonical access

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
                            contradiction_score=float(contradiction_result.get("score", 0.0)),
                            reflection_summary=reflection.reflection_summary,
                        )
                except Exception:
                    theory_usefulness = {
                        "score": 0.0,
                        "label": "unknown",
                    }
                # Sanity validation
                assert "score" in theory_usefulness, "theory_usefulness missing 'score' key"
                assert "label" in theory_usefulness, "theory_usefulness missing 'label' key"
                if theory_usefulness["score"] > 0.8 and contradiction_result.get("score", 0.0) > 0.7:
                    self._log("WARNING: High theory usefulness with high contradiction detected.")

                # Find lineage experience early for metadata attribution.
                active_exp = None
                if lineage_record and lineage_id_val != "N/A":
                    active_exp = self.experience_repo.load_by_lineage(lineage_id_val)

                intelligence_metadata = {
                    "directional_persistence": {
                        "3d": persistence_3d, 
                        "5d": persistence_5d, 
                        "10d": persistence_10d,
                        "regime": reg_5d
                    },
                    "mutation_count": active_exp.mutation_count if active_exp else 0,
                    "theory_mutation_count": lineage_record.mutation_count if lineage_record else 0, # Add theory's own mutation count
                    "contradiction_count": active_exp.contradiction_count if active_exp else 0,
                    "lineage_id": lineage_id_val,
                    "theory_id": theory.id
                }

                if self.lineage_debug:
                    print(f"\n  [PREDICTION RECORD AUDIT] Date: {date_str}")
                    print(f"    Theory ID: {theory.id}")
                    print(f"    lineage_record.mutation_count: {lineage_record.mutation_count if lineage_record else 'N/A'}")
                    print(f"    intelligence_metadata['theory_mutation_count']: {intelligence_metadata['theory_mutation_count']}")
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
                    volume_ratio_5d=float(obs_data["derived"].get("volume_ratio_5d", 1.0)),
                    range_pct=float(obs_data["derived"].get("range_pct", 0.0)),
                )

                # v1.9 Transition Retrieval
                similar_transitions = self.transition_memory.retrieve_similar(
                    from_regime=market_obs.trend_state,
                    direction_bias=transition_pressure.direction_bias,
                    pressure_score=transition_pressure.pressure_score,
                    horizon_daily=horizon_view.daily
                )

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
                    volume_ratio_5d=float(obs_data["derived"].get("volume_ratio_5d", 1.0)),
                    return_3d=float(obs_data["derived"].get("return_3d", 0.0)),
                    return_5d=float(obs_data["derived"].get("return_5d", 0.0)),
                    close_position_pct=getattr(market_obs, "close_position_pct", 0.5),
                    participation_confirmation=getattr(market_obs, "participation_confirmation", "normal"),
                    theory_usefulness=theory_usefulness,
                    intelligence_data=intelligence_metadata,
                )

                # Step 4: Decision Policy Layer
                decisions = self.decision_engine.evaluate(
                    prediction_probe=prediction_probe,
                    transition_pressure=transition_pressure,
                    contradiction_score=float(contradiction_result.get("score", 0.0)),
                    theory_usefulness=theory_usefulness.get("score", 0.0) if theory_usefulness else 0.0,
                    confidence_state=confidence_state,
                    date=date_str,
                    volume_state=obs_data["derived"].get("volume_state", "normal"),
                    atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200),
                    participation_confirmation=getattr(market_obs, "participation_confirmation", "normal"),
                )

                prior_prediction_result = None
                if self._prior_prediction is not None:
                    prior_prediction_result = self.prediction_generator.score_actual(
                        self._prior_prediction, market_obs
                    )
                    
                    # Experience Lifecycle: Outcome Grounding
                    if prior_prediction_result and self._prior_lineage_id:
                        if prior_prediction_result.direction_score == 1.0:
                            self.experience_engine.record_validation(self._prior_lineage_id)
                        if prior_prediction_result.invalidation_triggered:
                            self.experience_engine.record_falsification(self._prior_lineage_id)

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
                        decisions=decisions
                    )
                elif derived:
                    self.capital_simulator.record_day_result(
                        date_str, "uncertain", 0.0, actual_ret, actual_ret)
                
                # Confidence evolution
                confidence_state = self.confidence_engine.evolve(
                    confidence_state=theory.confidence_state,
                    validation=validation,
                    reflection=reflection,
                    contradiction_result=contradiction_result,
                    market_observation=market_obs,
                    recent_validations=recent_validations,
                    outcome_validation_result=prior_prediction_result.to_dict() if prior_prediction_result else {},
                    lineage_event=theory_step_info,
                    theory_usefulness=theory_usefulness,
                    regime_matches=regime_matches,
                )

                # Update in-memory confidence history
                try:
                    self._confidence_history.append(
                        confidence_state.empirical_confidence
                    )
                except Exception:
                    pass

                # v1.9: Save context for tomorrow's transition recording
                self._prior_transition_context = {
                    "pressure": transition_pressure.pressure_score,
                    "breakout": transition_pressure.breakout_risk,
                    "bias": transition_pressure.direction_bias,
                    "confidence": theory.confidence_state.empirical_confidence,
                    "usefulness": theory_usefulness.get("score", 0.0),
                    "contradiction": float(contradiction_result.get("score", 0.0)),
                    "horizon": horizon_view,
                    "theory_summary": theory.summary
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
                            market_obs.outcome_confidence = prior_prediction_result.confidence

                        # Provide contradictions for outcome persistence
                        market_obs.outcome_contradictions = contradiction_result.get("indicators", [])
                        
                        # Link to the generic observation event for relational analytics
                        if hasattr(obs_event, 'id') and obs_event.id:
                            market_obs.related_observation_id = str(obs_event.id)

                        self.market_outcome_repo.save(market_obs)
                except Exception as e:
                    self._log(f"WARNING: Optional MarketOutcome save failed: {e}")

                try:
                    self.transition_pressure_repo.save(transition_pressure, date=date_str, day_index=day_idx)
                except Exception as e:
                    self._log(f"WARNING: TransitionPressure save failed: {e}")
                
                saved_prediction = None
                try:
                    # Store logical refs/hashes as per v1.4 adjustments
                    theory_id = str(getattr(theory, 'id', ''))
                    reflection_id = str(getattr(reflection, 'id', ''))
                    
                    saved_prediction = self.prediction_repo.save(
                        prediction_probe,
                        date=date_str,
                        day_index=day_idx,
                        theory_id=theory_id,
                        reflection_id=reflection_id
                    )
                except Exception as e:
                    self._log(f"WARNING: PredictionProbe save failed: {e}")

                try:
                    if prior_prediction_result and self._prior_prediction_db_id:
                        self.prediction_result_repo.save(
                            prior_prediction_result,
                            date=date_str,
                            day_index=day_idx,
                            prediction_id=self._prior_prediction_db_id
                        )
                except Exception as e:
                    self._log(f"WARNING: PredictionResult save failed: {e}")

                # v3.1 Regime Memory Update
                actual_dir = getattr(prior_prediction_result, "actual_direction", None)
                self.regime_continuity_memory.update(
                    date=date_str,
                    subtype=regime_subtype,
                    usefulness=theory_usefulness.get("score", 0.0),
                    actual_direction=actual_dir,
                    falsified=getattr(prior_prediction_result, "invalidation_triggered", False),
                )
                
                regime_history_final = self.regime_continuity_memory.summary(regime_subtype)
                if self.lineage_debug:
                    # Guard for debug output
                    print("[Regime Memory]", {"date": date_str, "subtype": regime_subtype, "history": regime_history_final})

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
                    prior_prediction_result=prior_prediction_result.to_dict() if prior_prediction_result else None,
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
                    falsifiability_conditions=getattr(market_obs, "falsifiability_conditions", []),
                    analog_divergence_claim=getattr(market_obs, "analog_divergence_claim", ""),
                    regime_history=regime_history_final,
                    branch_stats=branch_stats, # Pass branch_stats
                    branches_generated=branch_stats.get("generated", 0),
                    intelligence_data=intelligence_metadata,
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
                    "falsifiability_conditions": getattr(market_obs, "falsifiability_conditions", []),
                    "analog_divergence_claim": getattr(market_obs, "analog_divergence_claim", ""),
                    "theory_regime_subtype": getattr(theory, "regime_subtype", "neutral"),
                    "theory_falsifiability_conditions": getattr(theory, "falsifiability_conditions", []),
                    "regime_history": regime_history_final,
                    "branch_stats": branch_stats, # Store branch_stats in snapshot
                    "dialectical_triggered": dialectical_data is not None,
                    "dialectical_synthesis": dialectical_data if dialectical_data else None,
                    "intelligence": intelligence_metadata,
                }
                # Save snapshot
                self._save_snapshot(day_idx, date_str, snapshot_data)

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
                        step_theory_metrics = {
                            "created": theory_step_info["created"],
                            "mutated": theory_step_info["mutated"],
                            "merged": theory_step_info["merged"],
                            "retired": theory_step_info["retired"],
                            "revived": theory_step_info["revived"],
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
                                        "theory_summary_structured": theory.summary_structured.model_dump() if theory.summary_structured else None,  # Canonical access
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
                                        "decisions": {k: v.to_dict() for k, v in decisions.items()},
                                        "theory_usefulness": theory_usefulness,
                                        "reflection": getattr(
                                            reflection, "reflection_summary", ""
                                        ),
                                        # v3.0 Regime Surface Persistence
                                        "regime_subtype": market_obs.regime_subtype,
                                        "falsifiability_conditions": market_obs.falsifiability_conditions,
                                        "analog_divergence_claim": market_obs.analog_divergence_claim,
                                        "theory_regime_subtype": getattr(theory, "regime_subtype", "neutral"),
                                        "theory_falsifiability": getattr(theory, "falsifiability_conditions", []),
                                        "regime_history": regime_history_final,
                                        "dialectical_triggered": dialectical_data is not None,
                                        "dialectical_synthesis": dialectical_data if dialectical_data else None,
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
                if lineage_record and lineage_id_val != "N/A": # Use the stable lineage_id for lookup
                    active_exp = self.experience_repo.load_by_lineage(lineage_id_val)

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
                    active_experience=active_exp, # Pass the active experience
                    lesson_info=self.experience_engine.get_last_extracted_lesson_with_reason(),
                    intelligence=intelligence_metadata
                )

                # WIRING FIX 1: Update prior prediction for next day's scoring
                self._prior_prediction = prediction_probe
                self._prior_lineage_id = lineage_id_val
                # Track DB ID for result linkage
                if saved_prediction and hasattr(saved_prediction, 'id'):
                    self._prior_prediction_db_id = saved_prediction.id
                else:
                    self._prior_prediction_db_id = None

                # Update prior synthesis for tomorrow's theory anchor
                if current_dialectical_data:
                    self._prior_dialectical_synthesis = self.dialectical_synthesizer.format_for_theory(current_dialectical_data)
                    self._prior_dialectical_subtype = regime_subtype
                else:
                    self._prior_dialectical_synthesis = None
                    self._prior_dialectical_subtype = None

            except Exception as e:
                self._log(f"✗ Day {day_idx} ({date_str}) failed: {e}")
                raise

        # Finalize
        execution_hash = self.engine.finalize_execution()
        
        # Instrumentation: Print final audit table
        print("\n" + "="*80)
        print("LINEAGE CONTINUITY AUDIT TABLE")
        print("="*80)
        print(f"{'day':<12} | {'lineage_id':<33} | {'cre':<5} | {'mut':<5} | {'mer':<5} | {'rev':<5} | {'action':<10}")
        for r in self._lineage_audit_table:
            print(f"{r['day']:<12} | {r['lineage_id']:<33} | {str(r['created'])[0]:<5} | {str(r['mutated'])[0]:<5} | {str(r['merged'])[0]:<5} | {str(r['revived'])[0]:<5} | {r['experience_action']:<10}")

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

        # Prepare external metrics (from runtime objects) for richer summary
        try:
            external_metrics = {}
            external_metrics["total_steps"] = len(self.engine)
            external_metrics["execution_hash"] = execution_hash
            external_metrics["total_synthesis_triggered"] = self.total_synthesis_triggered
            external_metrics["experience_stats"] = experience_stats
            external_metrics["experience_audit"] = experience_audit
            external_metrics["lesson_stats"] = self.lesson_repo.get_lesson_stats() # Add lesson stats
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
                        "avg_confidence": float(
                            mean([m.avg_confidence for m in self.observer.metrics])
                        )
                        if self.observer and self.observer.metrics
                        else 0.0,
                        "confidence_volatility": float(
                            mean([m.confidence_volatility for m in self.observer.metrics])
                        )
                        if self.observer and self.observer.metrics
                        else 0.0,
                        "grounded_reflection": float(
                            mean([m.grounded_reflection_score for m in self.observer.metrics])
                        )
                        if self.observer and self.observer.metrics
                        else 0.0,
                        "meta_commentary": float(
                            mean([m.meta_commentary_score for m in self.observer.metrics])
                        )
                        if self.observer and self.observer.metrics
                        else 0.0,
                        "narrative_inflation": float(
                            mean([m.inflation_relapse_score for m in self.observer.metrics])
                        )
                        if self.observer and self.observer.metrics
                        else 0.0,
                    }
                )

            # regime memory metrics if available on executor
            try:
                external_metrics["regime_recall_hit_rate"] = (
                    self.regime_memory.recall_hit_rate()
                    if self.regime_memory
                    else 0.0
                )
                external_metrics["memory_retrieval_usefulness"] = (
                    self.regime_memory.retrieval_usefulness(self._regime_matches_by_step)
                    if self.regime_memory
                    else 0.0
                )
            except Exception:
                external_metrics["regime_recall_hit_rate"] = 0.0
                external_metrics["memory_retrieval_usefulness"] = 0.0

            # Output paths
            external_metrics["outputs"] = {
                "prediction_csv": str(self.base_output_dir / "prediction_analysis.csv"),
                **(
                    {
                        "charts_dir": str(self.output_dir),
                        "cross_asset_summary": str(self.base_output_dir / "cross_asset_failure_summary.json"),
                    }
                    if self.generate_visualizations
                    else {}
                ),
            }

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
                from market.replay.visualization import (
                    generate_visualizations,
                )

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
            nifty_path = Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"
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
                        from market.replay.visualization import (
                            generate_cross_asset_visualizations,
                        )
                        generate_cross_asset_visualizations(
                            base_output_dir=self.base_output_dir,
                            primary_analysis=self.replay_analysis_engine.analyze(),
                            secondary_analysis=comparison_executor.replay_analysis_engine.analyze(),
                        )
                        self._log(f"  - {self.base_output_dir / 'reliance_vs_nifty_comparison.png'}")
                        self._log(f"  - {self.base_output_dir / 'prediction_failure_heatmap.png'}")
                        self._log(f"  - {self.base_output_dir / 'cross_asset_divergence_timeline.png'}")
                        self._log(f"  - {self.base_output_dir / 'cross_asset_failure_summary.json'}")
                except Exception as e:
                    self._log(f"WARNING: Cross-asset comparison failed: {e}")

        if emit_summary:
            try:
                # refresh outputs path in external metrics (cross-asset JSON may now exist)
                if hasattr(self.replay_analysis_engine, "external_metrics"):
                    self.replay_analysis_engine.external_metrics["outputs"] = {
                        "prediction_csv": str(self.base_output_dir / "prediction_analysis.csv"),
                        **(
                            {
                                "charts_dir": str(self.output_dir),
                                "cross_asset_summary": str(self.base_output_dir / "cross_asset_failure_summary.json"),
                            }
                            if self.generate_visualizations
                            else {}
                        ),
                    }
                self.replay_analysis_engine.print_summary()
            except Exception:
                pass

        self._log(f"\n✓ Replay complete")
        self._log(f"  Execution hash: {execution_hash[:16]}...")
        self._log(f"  Total synthesis triggered: {self.total_synthesis_triggered}")

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

    def _save_snapshot(self, day_idx: int, date_str: str, snapshot_data: dict):
        """Save replay snapshot to disk."""
        prediction = snapshot_data.get("prediction")
        prior_prediction_result = snapshot_data.get("prior_prediction_result")
        snapshot = {
            "day_index": day_idx,
            "date": date_str,
            "observation_text": snapshot_data["observation"].observation_text, # Keep for direct access
            "theory_summary": snapshot_data["theory"].summary,  # Legacy summary
            "theory_summary_structured": snapshot_data["theory"].summary_structured.model_dump() if snapshot_data["theory"].summary_structured else None,  # Canonical access
            "confidence_state": snapshot_data["confidence"].model_dump(), # Use model_dump for Pydantic objects
            "contradiction_score": snapshot_data["contradiction"].get("score", 0),
            "reflection_summary": snapshot_data["reflection"].reflection_summary,
            "epistemic_quality": snapshot_data.get("epistemic_quality", {}),
            "horizon": snapshot_data.get("horizon", {}),
            "regime_signature": snapshot_data.get("regime_signature", {}),
            "regime_matches": snapshot_data.get("regime_matches", []),
            "theory_usefulness": snapshot_data.get("theory_usefulness", {}),
            "candle_type": snapshot_data["observation"].candle_type,
            "participation_strength": snapshot_data["observation"].participation_strength,
            "participation_confirmation": snapshot_data["observation"].participation_confirmation,
            "prediction": prediction.to_dict() if hasattr(prediction, "to_dict") else prediction,
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
            "theory_falsifiability_conditions": snapshot_data.get("theory_falsifiability_conditions"),
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
        """Print concise COGNITIVE TRACE."""
        if self.quiet:
            return
            
        lesson_extracted, reason, evidence_count = lesson_info if lesson_info else (None, "not_processed", 0)

        print(f"\n── COGNITIVE TRACE: DAY {day_idx} ── {date_str} ──────────────────")
        
        print(f"Observation:")
        print(f"  {observation.observation_text[:160]}...")

        if intelligence:
            dp = intelligence.get("directional_persistence", {})
            print(f"Trend Persistence:")
            print(f"  3D: {dp.get('3d', 0):.2f} | 5D: {dp.get('5d', 0):.2f} | 10D: {dp.get('10d', 0):.2f}")
            print(f"  Regime: {dp.get('regime', 'Mixed')}")

        if intelligence:
            print(f"  Theory ID: {intelligence.get('theory_id', 'N/A')[:8]}... | Lineage: {intelligence.get('lineage_id', 'N/A')[:8]}...")
            print(f"  Theory Depth: {intelligence.get('theory_mutation_count', 0)} | Experience Mutations: {intelligence.get('mutation_count', 0)}")

        print(f"Theory:")
        theory_claim = theory.summary_structured.claim if theory.summary_structured else theory.summary
        print(f"  {theory_claim[:120]}...")

        print(f"Contradiction:")
        contra_summary = contradiction.get('summary', 'None detected') if contradiction.get('indicators') else "None detected"
        print(f"  {contra_summary}")
        tension_summary = getattr(reflection, 'tension_summary', None)
        if contra_summary == "None detected" and tension_summary and tension_summary != "None":
            print(f"  Tension: {tension_summary}")

        if active_experience:
            print(f"Experience:")
            print(f"  {active_experience.experience_id}")
            print(f"  Status: {active_experience.status.value}")
            print(f"  Theories: {len(active_experience.theory_ids)} | Contradictions: {active_experience.contradiction_count} | Mutations: {active_experience.mutation_count}")
        
        if prediction:
            print(f"Prediction: {prediction.direction.value} (Next Day)")

        print(f"Reflection:")
        print(f"  {reflection.reflection_summary[:250]}...") # Shorten for brevity

        if lesson_extracted:
            print(f"  Extracted: {lesson_extracted.lesson_text[:100]}... (Confidence: {lesson_extracted.confidence:.2f}, Status: {lesson_extracted.status.value})")
        elif reason == "insufficient_evidence":
            print(f"  Lesson: No lesson formed. Insufficient evidence ({evidence_count}/3 experiences)")
        elif reason == "internal_id_rejected":
            print(f"  Lesson: Rejected. Lesson text contained internal IDs.")
        else:
            print("  No lesson has stabilized.")


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

    args = parser.parse_args()

    try:
        # Determine dataset and market name based on CLI flags
        if args.nifty:
            dataset_path = str(Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv")
            market_name = "NIFTY 50"
        else:
            dataset_path = str(Path(__file__).parent.parent.parent / "data" / "reliance_daily_3y.csv")
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
        )

        # Reset if requested
        if args.reset:
            import shutil

            if executor.replay_dir.exists():
                shutil.rmtree(executor.replay_dir)
            executor._create_snapshot_dirs()

        # Execute replay
        executor.execute()

    except Exception as e:
        print(f"\n✗ Replay failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
