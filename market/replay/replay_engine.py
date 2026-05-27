"""
Replay engine for deterministic historical cognition execution.

Replays cognition loop over historical NIFTY dataset.
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
from market.replay.transition_memory import TransitionMemoryStore, TransitionExample


class ReplayEngine:
    """
    Deterministic replay of cognition loop over historical NIFTY data.
    """

    def __init__(
        self, dataset_path: str = None, validate: bool = True, max_days: int = None
    ):
        """
        Initialize replay engine.

        Args:
            dataset_path: Path to NIFTY CSV (default: data/nifty_daily_3y.csv)
            validate: Run validation on load
            max_days: Limit replay to N days (for testing)
        """
        if dataset_path:
            self.dataset_path = Path(dataset_path)
        else:
            # Default path: data/ directory at project root
            self.dataset_path = (
                Path(__file__).parent.parent.parent / "data" / "nifty_daily_3y.csv"
            )

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

    def __init__(self, max_days: int = None, quiet: bool = False):
        """Initialize executor."""
        self.max_days = max_days
        self.quiet = quiet
        self.replay_dir = Path(__file__).parent.parent.parent / "memory" / "replay"
        self.base_data_snap_dir = (
            Path(__file__).parent.parent.parent / "data" / "replay_snapshots"
        )
        self._create_snapshot_dirs()

        # Initialize replay engine
        self.engine = ReplayEngine(max_days=max_days, validate=True)

        # Initialize flows and repositories (lazy loaded on first use)
        self.flows_initialized = False
        self.abstraction_flow = None
        self.theory_flow = None
        self.reflection_flow = None
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
        self._run_theories: List[object] = []
        self._run_validations: List[object] = []
        self._run_reflections: List[object] = []
        self._run_market_observations: List[object] = []
        self._prior_prediction = None
        self._prior_prediction_db_id = None
        self.decision_engine = DecisionPolicyEngine()
        self._regime_matches_by_step: List[list] = []
        self.transition_pressure_engine = TransitionPressureEngine()
        self.replay_analysis_engine = None # Will be initialized in execute
        self.prediction_repo = None
        self.transition_memory = TransitionMemoryStore()
        
        # Context for transition recording
        self._prior_transition_context = None
        self.prediction_result_repo = None
        self.transition_pressure_repo = None
        self.market_outcome_repo = None
        
        # Track IDs for relational linking
        self._prior_prediction_db_id = None

    def _create_snapshot_dirs(self):
        """Create replay snapshot directories if missing."""
        dirs = [
            self.replay_dir,
            self.replay_dir / "observations",
            self.replay_dir / "theories",
            self.replay_dir / "confidence",
            self.replay_dir / "logs",
            self.base_data_snap_dir,
        ]

        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _initialize_flows(self):
        """Lazy initialize cognition flows and repositories."""
        if self.flows_initialized:
            return

        from cognition.confidence.confidence_evolution_engine import (
            ConfidenceEvolutionEngine,
        )
        from cognition.contradiction.contradiction_detector import ContradictionDetector
        from flows.observation_flow.abstraction_flow import AbstractionFlow
        from flows.reflection_flow.reflection_flow import ReflectionFlow
        from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
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
        self.contradiction_detector = ContradictionDetector()
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
        except (ImportError, ModuleNotFoundError):
            self._log("WARNING: MarketOutcomeRepository missing; optional persistence disabled.")
            self.market_outcome_repo = None

        self.flows_initialized = True

    def _log(self, message: str):
        """Print if not quiet mode."""
        if not self.quiet:
            print(message)

    def execute(self):
        """Execute full replay with cognition loop."""
        self._initialize_flows()

        from cognition.evaluation.epistemic_quality import evaluate_epistemic_quality
        from cognition.schemas.observation.observation_event import ObservationEvent
        from cognition.schemas.validation.validation_event import ValidationEvent
        from cognition.schemas.confidence.confidence_state import ConfidenceState
        from market.replay.market_observation_synthesizer import (
            MarketObservationSynthesizer,
        )
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
            self.contradiction_registry = ContradictionRegistry(
                self.run_dir / "contradiction_registry.json"
            )
            self.regime_memory = RegimeMemoryStore()
            self.horizon_engine = HorizonCognitionEngine()
            self.epistemic_scoring = EpistemicScoringEngine()
            self.prediction_generator = PredictionProbeGenerator()
            self.capital_simulator = CapitalSimulator()
        except Exception:
            self.observer = None
            self.theory_lineage = None
            self.contradiction_registry = None
            self.regime_memory = RegimeMemoryStore()
            self.horizon_engine = HorizonCognitionEngine()
            self.epistemic_scoring = EpistemicScoringEngine()
            self.prediction_generator = PredictionProbeGenerator()
            self.capital_simulator = CapitalSimulator()

        from market.replay.replay_analysis import ReplayAnalysisEngine
        self.replay_analysis_engine = ReplayAnalysisEngine()

        # Load synthesizer
        synthesizer = MarketObservationSynthesizer(self.engine.data)

        # Initialize confidence_state for Day 0 execution
        confidence_state = ConfidenceState()

        self._log("\n" + "=" * 70)
        self._log("REPLAY EXECUTION")
        self._log("=" * 70)
        self._log(f"Dataset: {len(self.engine)} days")
        self._log(
            f"Range: {self.engine.get_date_range()[0]} to {self.engine.get_date_range()[1]}\n"
        )

        # Execute replay
        for day_idx in range(len(self.engine)):
            try:
                obs_data = self.engine.get_observation_for_day(day_idx)
                date_str = obs_data["date"]

                # Synthesize observation
                market_obs = synthesizer.synthesize(day_idx)

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
                theory = self.theory_flow.process(
                    abstraction,
                    historical_context=historical_context,
                    market_memory_context=regime_context,
                    current_market_observation=market_obs.observation_text,
                    reflective_memory_summary=horizon_context,
                )

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
                        theory_step_info["created"] = int(lineage_result["created"])
                        theory_step_info["mutated"] = int(lineage_result["mutated"])
                        theory_step_info["merged"] = int(lineage_result["merged"])

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
                except Exception:
                    pass

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
                except Exception:
                    pass

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
                        if self.contradiction_registry:
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
                except Exception:
                    pass

                # revive if matched
                try:
                    if self.theory_lineage:
                        revived_records = self.theory_lineage.revive_matching_theories(
                            abstraction=abstraction_text,
                            step=day_idx,
                        )
                        theory_step_info["revived"] = len(revived_records)
                except Exception:
                    pass

                # validate
                validation = ValidationEvent(
                    theory_id=theory.id,
                    validation_summary=(
                        "Replay validation. " f"{horizon_context}. " f"{regime_context}"
                    ),
                    observed_behavior=market_obs.observation_text,
                    expected_behavior="Market-grounded theory",
                )

                # reflect
                reflection = self.reflection_flow.process(
                    theory,
                    validation,
                    contradiction_result=contradiction_result,
                    market_observation=market_obs,
                )
                epistemic_quality = {
                    "theory": evaluate_epistemic_quality(theory.summary),
                    "reflection": evaluate_epistemic_quality(
                        reflection.reflection_summary
                    ),
                }

                # Initialize theory_usefulness (will be computed later if lineage available)
                theory_usefulness = {}

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
                    atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200)
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
                    transition_examples=similar_transitions
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
                    atr_expansion=(float(obs_data["derived"].get("atr_14", 0.0)) > 200)
                )

                prior_prediction_result = None
                if self._prior_prediction is not None:
                    prior_prediction_result = self.prediction_generator.score_actual(
                        self._prior_prediction, market_obs
                    )

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
                    outcome_validation_result={},
                    lineage_event=theory_step_info,
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
                    theory_ref = str(getattr(theory, 'id', ''))
                    reflection_ref = str(getattr(reflection, 'id', ''))
                    
                    saved_prediction = self.prediction_repo.save(
                        prediction_probe,
                        date=date_str,
                        day_index=day_idx,
                        theory_ref=theory_ref,
                        reflection_ref=reflection_ref
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
                    theory_summary=theory.summary,
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
                    # v2.0 dimensions
                    volume_state=obs_data["derived"].get("volume_state"),
                    volatility_regime=vol_regime,
                    momentum_regime=mom_regime
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
                    "momentum_regime": mom_regime
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
                                        "theory": theory.summary,
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
                )

                # WIRING FIX 1: Update prior prediction for next day's scoring
                self._prior_prediction = prediction_probe
                # Track DB ID for result linkage
                if saved_prediction and hasattr(saved_prediction, 'id'):
                    self._prior_prediction_db_id = saved_prediction.id
                else:
                    self._prior_prediction_db_id = None

            except Exception as e:
                self._log(f"✗ Day {day_idx} ({date_str}) failed: {e}")
                raise

        # Finalize
        execution_hash = self.engine.finalize_execution()

        # Finalize capital simulation and analysis
        capital_summary = self.capital_simulator.get_summary()
        self.replay_analysis_engine.set_capital_simulation_summary(capital_summary)
        # WIRING FIX 2: Transfer capital simulator daily logs to analysis engine
        self.replay_analysis_engine.set_capital_simulation_logs(
            self.capital_simulator.get_daily_logs()
        )

        # Print summary and export CSV
        self.replay_analysis_engine.print_summary()
        self.replay_analysis_engine.export_prediction_analysis_csv(
            Path(__file__).parent.parent.parent / "market" / "replay" / "output" / "prediction_analysis.csv"
        )

        # v1.6 Visualization Layer Integration
        try:
            from market.replay.visualization import generate_visualizations
            output_dir = Path(__file__).parent.parent.parent / "market" / "replay" / "output"
            generate_visualizations(
                analysis=self.replay_analysis_engine.analyze(),
                logs=self.capital_simulator.get_daily_logs(),
                tp_history=self.replay_analysis_engine.transition_pressure_history,
                output_dir=output_dir
            )
            self._log(f"Generated:")
            self._log(f"  - actual_vs_predicted_curve.png")
            self._log(f"  - policy_capital_comparison.png")
            self._log(f"  - policy_trade_frequency.png")
            self._log(f"  - confidence_calibration.png")
            self._log(f"  - transition_pressure_timeline.png")
            self._log(f"  - combined_dashboard.png")
        except Exception as e:
            self._log(f"WARNING: Optional Visualization generation failed: {e}")

        self._log(f"\n✓ Replay complete")
        self._log(f"  Execution hash: {execution_hash[:16]}...")
        self._log("=" * 70 + "\n")

        # Console summary (concise)
        try:
            total_steps = len(self.engine)
            active_theories = (
                self.theory_lineage.active_count() if self.theory_lineage else 0
            )
            new_theories = (
                sum(m.new_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            mutated_theories = (
                sum(m.mutated_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            contradicted_theories = (
                self.theory_lineage.contradicted_count() if self.theory_lineage else 0
            )
            retired_theories = (
                sum(m.retired_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            revived_theories = (
                sum(m.revived_theories for m in self.observer.metrics)
                if self.observer
                else 0
            )
            longest_survival = (
                self.theory_lineage.longest_surviving_theory()
                if self.theory_lineage
                else 0
            )
            avg_retirement_age = (
                self.theory_lineage.average_retirement_age()
                if self.theory_lineage
                else 0.0
            )
            avg_revival_latency = (
                self.theory_lineage.average_revival_latency()
                if self.theory_lineage
                else 0.0
            )
            avg_contradiction_half_life = (
                float(mean([m.contradiction_half_life for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            median_contradiction_half_life = (
                float(
                    mean(
                        [
                            m.median_contradiction_half_life
                            for m in self.observer.metrics
                        ]
                    )
                )
                if self.observer and self.observer.metrics
                else 0.0
            )
            avg_contradiction_severity = (
                float(
                    mean([m.avg_contradiction_severity for m in self.observer.metrics])
                )
                if self.observer and self.observer.metrics
                else 0.0
            )
            oldest_unresolved = (
                max(
                    (m.oldest_unresolved_contradiction for m in self.observer.metrics),
                    default=0,
                )
                if self.observer
                else 0
            )
            avg_confidence = (
                float(mean([m.avg_confidence for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            confidence_volatility = (
                float(mean([m.confidence_volatility for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            grounded_reflection = (
                float(
                    mean([m.grounded_reflection_score for m in self.observer.metrics])
                )
                if self.observer and self.observer.metrics
                else 0.0
            )
            meta_commentary = (
                float(mean([m.meta_commentary_score for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            narrative_inflation = (
                float(mean([m.inflation_relapse_score for m in self.observer.metrics]))
                if self.observer and self.observer.metrics
                else 0.0
            )
            top_recurring = (
                self.theory_lineage.top_recurring_theory()
                if self.theory_lineage
                else None
            )
            family_analytics = (
                self.theory_lineage.family_analytics() if self.theory_lineage else {}
            )
            epistemic_aggregate = (
                self.epistemic_scoring.aggregate(self.theory_lineage.theories.values())
                if self.epistemic_scoring and self.theory_lineage
                else {"avg_theory_usefulness": 0.0}
            )
            regime_recall_hit_rate = (
                self.regime_memory.recall_hit_rate() if self.regime_memory else 0.0
            )
            memory_retrieval_usefulness = (
                self.regime_memory.retrieval_usefulness(self._regime_matches_by_step)
                if self.regime_memory
                else 0.0
            )

            print("\nReplay Summary")
            print("--------------")
            print(f"Total steps: {total_steps}")
            print(f"Active theories: {active_theories}")
            print(f"New theories: {new_theories}")
            print(f"Mutated theories: {mutated_theories}")
            print(f"Contradicted theories: {contradicted_theories}")
            print(f"Retired theories: {retired_theories}")
            print(f"Revived theories: {revived_theories}")
            print("")
            print(f"Longest surviving theory: {longest_survival} steps")
            print(f"Avg retirement age: {avg_retirement_age:.2f}")
            print(f"Avg revival latency: {avg_revival_latency:.2f}")
            print("")
            print(f"Avg contradiction half-life: {avg_contradiction_half_life:.2f}")
            print(
                f"Median contradiction half-life: {median_contradiction_half_life:.2f}"
            )
            print(f"Avg contradiction severity: {avg_contradiction_severity:.2f}")
            print(f"Oldest unresolved contradiction: {oldest_unresolved} steps")
            print("")
            print(f"Avg confidence: {avg_confidence:.2f}")
            print(f"Confidence volatility: {confidence_volatility:.3f}")
            print("")
            print(
                "Best surviving family: "
                f"{family_analytics.get('best_surviving_family') or 'None'}"
            )
            print(
                "Most revived family: "
                f"{family_analytics.get('most_revived_family') or 'None'}"
            )
            print(
                "Highest contradiction family: "
                f"{family_analytics.get('highest_contradiction_family') or 'None'}"
            )
            print(
                "Most mutated family: "
                f"{family_analytics.get('most_mutated_family') or 'None'}"
            )
            print("")
            print(f"Regime recall hit rate: {regime_recall_hit_rate:.2f}")
            print(
                "Avg theory usefulness: "
                f"{epistemic_aggregate.get('avg_theory_usefulness', 0.0):.2f}"
            )
            print("Memory retrieval usefulness: " f"{memory_retrieval_usefulness:.2f}")
            print("")
            print(f"Grounded reflection score: {grounded_reflection:.3f}")
            print(f"Meta commentary score: {meta_commentary:.3f}")
            print("")
            print(f"Narrative inflation relapse: {narrative_inflation:.3f}")
            print(f"Top recurring theory: {top_recurring or 'None'}")
            print("")
        except Exception:
            pass

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
            "observation_text": snapshot_data["observation"].observation_text,
            "theory_summary": snapshot_data["theory"].summary,
            "confidence_state": {
                "empirical": snapshot_data["confidence"].empirical_confidence,
                "regime": snapshot_data["confidence"].regime_confidence,
                "reflection": snapshot_data["confidence"].reflection_confidence,
                "coherence": snapshot_data["confidence"].theoretical_coherence,
                "contradiction": snapshot_data["confidence"].contradiction_pressure,
            },
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
        }

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
    ):
        """Print formatted day log."""
        if self.quiet:
            return

        print(f"\n## DAY {day_idx} — {date_str}")
        print(f"\nObservation:")
        print(f"  {observation.observation_text}")
        print(f"  Trend: {observation.trend_state}")
        print(f"  Candle: {observation.candle_type}")
        print(f"  Participation: {observation.participation_strength}, {observation.participation_confirmation}")
        print(f"  Sentiment: {observation.macro_sentiment}")

        print(f"\nHorizon:")
        print(f"  Daily: {horizon.daily}")
        print(f"  Weekly: {horizon.weekly}")
        print(f"  Monthly: {horizon.monthly}")

        print(f"\nRegime memory:")
        if regime_matches:
            for match in regime_matches[:2]:
                print(f"  {match.date} similarity {match.similarity:.2f}")
                if match.recurring_contradiction:
                    print(f"  recurring contradiction: {match.recurring_contradiction}")
        else:
            print("  No prior regime match.")

        print(f"\nTheory:")
        print(f"  {theory.summary[:100]}...")

        print(f"\nContradictions:")
        print(f"  Score: {contradiction.get('score', 0):.2f}")
        if contradiction.get("contradictions"):
            for c in contradiction.get("contradictions", [])[:3]:
                print(f"  - {c}")

        print(f"\nConfidence:")
        print(f"  Empirical: {confidence.empirical_confidence:.2f}")
        print(f"  Coherence: {confidence.theoretical_coherence:.2f}")
        print(f"  Contradiction: {confidence.contradiction_pressure:.2f}")

        if theory_usefulness:
            print(f"\nEpistemic:")
            print(
                "  Theory usefulness: "
                f"{theory_usefulness.get('score', 0.0):.2f} "
                f"({theory_usefulness.get('label', 'unknown')})"
            )

        if transition_pressure:
            print(f"\nTransition Pressure:")
            print(f"  Direction bias: {transition_pressure.direction_bias}")
            print(f"  Pressure: {transition_pressure.pressure_score:.3f}")
            print(f"  Stability: {transition_pressure.stability_score:.3f}")
            print(f"  Breakout risk: {transition_pressure.breakout_risk}")
            if transition_pressure.drivers:
                print(f"  Drivers: {', '.join(transition_pressure.drivers[:4])}")

        if prediction:
            print(f"\nPrediction Probe:")
            print(f"  Direction: {prediction.direction.value}")
            print(f"  Confidence: {prediction.confidence:.3f}")
            print(f"  Tension: {prediction.tension}")
            print(f"  Invalidation: {prediction.invalidation}")

        if prior_prediction_result:
            print(f"\nPrior Prediction Result:")
            print(
                f"  Prior: {prior_prediction_result.prior_direction}, "
                f"Actual: {prior_prediction_result.actual_direction}, "
                f"Score: {prior_prediction_result.direction_score:.3f}"
            )
            print(f"  Invalidation triggered: {prior_prediction_result.invalidation_triggered}")

        print(f"\nReflection:")
        print(f"  {reflection.reflection_summary[:80]}...")


def main():
    """CLI entrypoint for replay engine."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Deterministic NIFTY replay engine with cognition loop"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of trading days to replay (default: 30)",
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

    args = parser.parse_args()

    try:
        # Initialize executor
        executor = ReplayExecutor(max_days=args.days, quiet=args.quiet)

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
