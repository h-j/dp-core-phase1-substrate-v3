"""
Comprehensive replay validation runner.

Orchestrates:
1. Dataset download and validation
2. 30/90/365-day replay execution
3. Determinism verification
4. Analysis and reporting
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.confidence.confidence_evolution_engine import ConfidenceEvolutionEngine
from cognition.contradiction.contradiction_detector import ContradictionDetector
from cognition.evaluation.epistemic_quality import evaluate_epistemic_quality
from cognition.schemas.observation.observation_event import ObservationEvent
from cognition.schemas.validation.validation_event import ValidationEvent
from flows.observation_flow.abstraction_flow import AbstractionFlow
from flows.reflection_flow.reflection_flow import ReflectionFlow
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from market.data.dataset_validator import DatasetValidator
from market.data.download_nifty_history import NIFTYHistoryDownloader
from market.replay.market_observation_synthesizer import MarketObservationSynthesizer
from market.replay.prediction_probe import PredictionProbeGenerator
from market.replay.capital_simulator import CapitalSimulator
from market.replay.transition_pressure import TransitionPressureEngine
from market.replay.replay_analysis import ReplayAnalysisEngine
from market.replay.replay_engine import ReplayEngine
from memory.replay.horizon_cognition import HorizonCognitionEngine
from memory.replay.regime_memory import RegimeMemoryStore
from memory.relational.repositories.abstraction_repository import AbstractionRepository
from memory.relational.repositories.confidence_repository import ConfidenceRepository
from memory.relational.repositories.observation_repository import ObservationRepository
from memory.relational.repositories.reflection_repository import ReflectionRepository
from memory.relational.repositories.theory_repository import TheoryRepository
from memory.relational.repositories.validation_repository import ValidationRepository


class ReplayValidationRunner:
    """Orchestrates comprehensive replay validation."""

    def __init__(self):
        """Initialize runner."""
        project_root = Path(__file__).parent.parent.parent
        self.data_dir = project_root / "data"
        self.csv_path = self.data_dir / "nifty_daily_3y.csv"

        # Initialize repositories
        self.observation_repo = ObservationRepository()
        self.abstraction_repo = AbstractionRepository()
        self.theory_repo = TheoryRepository()
        self.validation_repo = ValidationRepository()
        self.reflection_repo = ReflectionRepository()
        self.confidence_repo = ConfidenceRepository()

        # Initialize flows
        self.abstraction_flow = AbstractionFlow()
        self.theory_flow = TheoryGenerationFlow()
        self.reflection_flow = ReflectionFlow()

        # Initialize engines
        self.contradiction_detector = ContradictionDetector()
        self.confidence_engine = ConfidenceEvolutionEngine()
        self.prediction_generator = PredictionProbeGenerator()
        self.transition_pressure_engine = TransitionPressureEngine()
        self.horizon_engine = HorizonCognitionEngine()
        self.regime_memory = RegimeMemoryStore()
        self._run_market_observations = []
        self.capital_simulator = CapitalSimulator()
        self._prior_prediction = None

    def run_full_validation(self, skip_download: bool = False):
        """Run complete validation suite."""
        print("\n" + "=" * 70)
        print("NIFTY REPLAY VALIDATION SUITE")
        print("=" * 70)

        # Step 1: Download dataset
        if not skip_download:
            print("\n[1/5] Downloading historical NIFTY data...")
            self._download_dataset()
        else:
            print("\n[1/5] Skipping download (using existing dataset)")

        # Step 2: Validate dataset
        print("\n[2/5] Validating dataset...")
        self._validate_dataset()

        # Step 3: Run short/medium/long replays
        print("\n[3/5] Running replay scenarios...")
        self._run_replays()

        # Step 4: Verify determinism
        print("\n[4/5] Verifying determinism...")
        self._verify_determinism()

        # Step 5: Report
        print("\n[5/5] Generating final report...")
        self._generate_report()

        print("\n" + "=" * 70)
        print("✓ VALIDATION SUITE COMPLETE")
        print("=" * 70 + "\n")

    def _download_dataset(self):
        """Download NIFTY historical data."""
        try:
            downloader = NIFTYHistoryDownloader(str(self.csv_path))
            data = downloader.download()
            downloader.persist(data)
            downloader.add_derived_fields()
            print("✓ Dataset download and persistence complete")
        except Exception as e:
            print(f"✗ Download failed: {e}")
            raise

    def _validate_dataset(self):
        """Validate downloaded dataset."""
        validator = DatasetValidator(str(self.csv_path))
        results = validator.validate(verbose=True)

        if results["errors"]:
            raise ValueError(f"Dataset validation failed: {results['errors']}")

    def _run_replays(self):
        """Run short/medium/long replay scenarios."""
        scenarios = [
            {"days": 30, "label": "30-day"},
            {"days": 90, "label": "90-day"},
            {"days": 252, "label": "1-year"},  # ~252 trading days
        ]

        self.replay_results = {}

        for scenario in scenarios:
            label = scenario["label"]
            days = scenario["days"]

            print(f"\n  Running {label} replay ({days} trading days)...")

            try:
                result = self._execute_replay(days, label)
                self.replay_results[label] = result
                print(f"  ✓ {label} replay complete")
            except Exception as e:
                print(f"  ✗ {label} replay failed: {e}")
                raise

    def _execute_replay(self, max_days: int, label: str) -> dict:
        """
        Execute a replay for the specified number of days.

        Returns:
            dict with replay results and metrics
        """
        # Initialize replay engine
        engine = ReplayEngine(
            dataset_path=str(self.csv_path), validate=True, max_days=max_days
        )

        # Initialize analysis
        analysis = ReplayAnalysisEngine()

        # Load data for observation synthesis
        import pandas as pd

        replay_data = pd.read_csv(self.csv_path)
        if max_days:
            replay_data = replay_data.tail(max_days)

        synthesizer = MarketObservationSynthesizer(replay_data)

        # Execute replay
        execution_log = []
        day_outputs = []

        # Initialize confidence_state for the first day's signature building
        confidence_state = ConfidenceState()

        for day_idx in range(len(engine)):
            try:
                obs_data = engine.get_observation_for_day(day_idx)
                date_str = obs_data["date"]

                # Synthesize observation
                market_obs = synthesizer.synthesize(day_idx)

                # Create observation event
                obs_event = ObservationEvent(
                    source_type="replay", raw_content=market_obs.observation_text
                )
                self.observation_repo.save(obs_event)

                # Abstraction flow
                abstraction = self.abstraction_flow.process(obs_event)
                self.abstraction_repo.save(abstraction)

                # Theory flow
                theory = self.theory_flow.process(abstraction)
                self.theory_repo.save(theory)

                # Validation event
                validation = ValidationEvent(
                    theory_id=theory.id,
                    validation_summary="Replay validation",
                    observed_behavior=market_obs.observation_text,
                    expected_behavior="Market-grounded theory",
                )
                self.validation_repo.save(validation)

                # Reflection flow
                reflection = self.reflection_flow.process(theory, validation)
                self.reflection_repo.save(reflection)
                epistemic_quality = {
                    "theory": evaluate_epistemic_quality(theory.summary),
                    "reflection": evaluate_epistemic_quality(
                        reflection.reflection_summary
                    ),
                }

                # Contradiction detection
                recent_theories = self.theory_repo.list_recent(limit=5)
                recent_validations = self.validation_repo.list_recent(limit=5)
                recent_reflections = self.reflection_repo.list_recent(limit=5)

                contradiction_result = self.contradiction_detector.detect(
                    current_theory=theory,
                    historical_theories=recent_theories,
                    validations=recent_validations,
                    reflections=recent_reflections,
                )

                # Horizon and regime context for prediction probe
                horizon_view = self.horizon_engine.compute(
                    [*self._run_market_observations, market_obs]
                )
                regime_signature = self.regime_memory.build_signature(
                    date=date_str,
                    observation=market_obs,
                    confidence_values=[confidence_state.empirical_confidence],
                    contradiction_severity=contradiction_result.get("score", 0.0),
                    active_theory_count=0,
                )
                regime_matches = self.regime_memory.retrieve(
                    regime_signature,
                    contradiction_result.get("contradictions", []),
                )

                # Infer transition pressure (deterministic, observer-only)
                transition_pressure = self.transition_pressure_engine.infer(
                    observation=market_obs,
                    horizons=horizon_view,
                    regime_matches=regime_matches,
                    confidence_state=theory.confidence_state,
                    contradiction_result=contradiction_result,
                    reflection=reflection,
                    theory_usefulness={},
                    prior_observations=self._run_market_observations[-10:],
                )

                prediction_probe = self.prediction_generator.generate_prediction(
                    observation=market_obs,
                    horizons=horizon_view,
                    regime_matches=regime_matches,
                    theory=theory,
                    contradictions=contradiction_result,
                    reflection=reflection,
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
                    )
                elif derived:
                    self.capital_simulator.record_day_result(
                        date_str, "uncertain", 0.0, actual_ret, actual_ret
                    )

                # Update prior prediction for tomorrow's trade
                self._prior_prediction = prediction_probe

                self.regime_memory.persist(
                    step=day_idx,
                    signature=regime_signature,
                    active_theories=[],
                    contradictions=contradiction_result.get("contradictions", []),
                    confidence=confidence_state.empirical_confidence,
                )

                # Confidence evolution
                confidence_state = self.confidence_engine.evolve(
                    confidence_state=theory.confidence_state,
                    validation=validation,
                    reflection=reflection,
                    contradiction_result=contradiction_result,
                    recent_validations=recent_validations,
                    outcome_validation_result={},
                )
                self.confidence_repo.save(confidence_state)

                # Record for analysis
                analysis.record_day(
                    day_idx,
                    date_str,
                    {
                        "empirical_confidence": confidence_state.empirical_confidence,
                        "regime_confidence": confidence_state.regime_confidence,
                        "reflection_confidence": confidence_state.reflection_confidence,
                        "theoretical_coherence": confidence_state.theoretical_coherence,
                        "contradiction_pressure": confidence_state.contradiction_pressure,
                    },
                    {
                        "score": contradiction_result.get("score", 0),
                        "contradictions": contradiction_result.get("indicators", []),
                    },
                    theory.summary,
                    reflection.reflection_summary,
                    market_obs.macro_sentiment,
                    epistemic_quality,
                    prediction_probe.to_dict(),
                    prior_prediction_result.to_dict()
                    if prior_prediction_result is not None
                    else None,
                    regime_matches,
                    {"score": epistemic_quality.get("theory", {}).get("compression_score", 0), "label": "validation"},
                    transition_pressure.to_dict() if hasattr(transition_pressure, "to_dict") else transition_pressure,
                )

                # Record daily capital simulation logs for analysis
                if self.capital_simulator.get_daily_logs():
                    analysis.record_capital_simulation_day(self.capital_simulator.get_daily_logs()[-1])

                # Compute hash for determinism
                obs_hash = hashlib.sha256(
                    market_obs.observation_text.encode()
                ).hexdigest()[:16]
                theory_hash = hashlib.sha256(theory.summary.encode()).hexdigest()[:16]
                conf_hash = hashlib.sha256(
                    str(confidence_state.empirical_confidence).encode()
                ).hexdigest()[:16]

                engine.log_entry(day_idx, date_str, obs_hash, theory_hash, conf_hash)

                day_outputs.append(
                    {
                        "day": day_idx,
                        "date": date_str,
                        "obs_hash": obs_hash,
                        "theory_hash": theory_hash,
                        "conf_hash": conf_hash,
                        "epistemic_quality": epistemic_quality,
                    }
                )

            except Exception as e:
                print(f"    ✗ Day {day_idx} ({date_str}) failed: {e}")
                raise

        # Finalize
        execution_hash = engine.finalize_execution()
        capital_summary = self.capital_simulator.get_summary()
        analysis.set_capital_simulation_summary(capital_summary)
        analysis.analyze()

        return {
            "label": label,
            "days": len(engine),
            "date_range": engine.get_date_range(),
            "execution_hash": execution_hash,
            "day_outputs": day_outputs,
            "analysis": analysis,
        }

    def _verify_determinism(self):
        """Verify replay determinism by running twice."""
        if "90-day" not in self.replay_results:
            print("  Skipping determinism check (90-day replay not executed)")
            return

        print("\n  Executing 90-day replay second time for determinism check...")

        try:
            result_2 = self._execute_replay(90, "90-day-verification")

            original_hash = self.replay_results["90-day"]["execution_hash"]
            verification_hash = result_2["execution_hash"]

            if original_hash == verification_hash:
                print(f"  ✓ Determinism VERIFIED")
                print(f"    Hash (both runs): {original_hash[:16]}...")
                self.determinism_verified = True
            else:
                print(f"  ✗ Determinism FAILED")
                print(f"    Original:      {original_hash[:16]}...")
                print(f"    Verification:  {verification_hash[:16]}...")
                self.determinism_verified = False

        except Exception as e:
            print(f"  ✗ Determinism verification failed: {e}")
            self.determinism_verified = False

    def _generate_report(self):
        """Generate final validation report."""
        print("\n" + "=" * 70)
        print("REPLAY VALIDATION REPORT")
        print("=" * 70)

        print(f"\nDataset: {self.csv_path}")
        print(f"Validation Time: {datetime.now().isoformat()}")

        if hasattr(self, "replay_results"):
            print("\nReplay Results:")
            for label, result in self.replay_results.items():
                print(f"\n  {label.upper()}:")
                print(f"    Days: {result['days']}")
                print(
                    f"    Date range: {result['date_range'][0]} to {result['date_range'][1]}"
                )
                print(f"    Execution hash: {result['execution_hash'][:16]}...")

                # Print analysis summary
                result["analysis"].print_summary()

                prediction_summary = result["analysis"].analyze().get("prediction_analysis", {})
                if prediction_summary:
                    print("    Prediction probe performance:")
                    print(
                        f"      Accuracy: {prediction_summary['accuracy']:.1%} "
                        f"| Partial: {prediction_summary['partial_accuracy']:.1%} "
                        f"| Uncertain: {prediction_summary['uncertain_rate']:.1%}"
                    )
                    print(
                        f"      Invalidation rate: {prediction_summary['invalidation_rate']:.1%} "
                        f"| Mean confidence: {prediction_summary['mean_confidence']:.3f}"
                    )

                capital_summary = result["analysis"].analyze().get("capital_simulation_analysis", {})
                if capital_summary:
                    print("    Capital Simulation Summary:")
                    print(
                        f"      Ending Capital: ₹{capital_summary.get('ending_capital', 0):,.2f} "
                        f"| Return: {capital_summary.get('return_pct', 0.0):.2%} "
                        f"| Annualized: {capital_summary.get('annualized_return', 0.0):.2%}"
                    )
                    print(
                        f"      Win Rate: {capital_summary.get('win_rate', 0.0):.2%} | Max Drawdown: {capital_summary.get('max_drawdown', 0.0):.2%}"
                    )

        if hasattr(self, "determinism_verified"):
            status = "✓ PASS" if self.determinism_verified else "✗ FAIL"
            print(f"Determinism Check: {status}")

        print("\n" + "=" * 70 + "\n")

        # Export CSV for the last replay (e.g., 1-year)
        if "1-year" in self.replay_results:
            self.replay_results["1-year"]["analysis"].export_prediction_analysis_csv(Path("market/replay/output/prediction_analysis.csv"))


def main():
    """Run the validation suite."""
    runner = ReplayValidationRunner()

    # Check if dataset exists
    import os

    skip_download = os.path.exists(runner.csv_path)

    try:
        runner.run_full_validation(skip_download=skip_download)
    except Exception as e:
        print(f"\n✗ Validation suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
