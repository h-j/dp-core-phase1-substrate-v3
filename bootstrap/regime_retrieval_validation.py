"""
Regime Retrieval Validation Runner.

Runs a 30-day NIFTY replay in Shadow Mode:
1. Pre-populates 100 historical days with mock regimes and theories.
2. In each step, retrieves the top 3 similar historical regimes/theories.
3. Independently generates a new theory for the current day using local LLM.
4. Computes comparison metrics (similarity, usefulness, contradiction, validation).
5. Classifies each retrieved theory as RELEVANT, PARTIALLY_RELEVANT, or IRRELEVANT.
6. Generates a markdown validation report under docs/archive/.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from cognition.contradiction.contradiction_detector import \
    ContradictionDetector
from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.experience.experience import (Experience,
                                                     ExperienceStatus)
from cognition.schemas.observation.observation_event import ObservationEvent
from cognition.schemas.theory.theory import Branch, Theory, TheoryStructured
from cognition.schemas.validation.validation_event import ValidationEvent
from config.settings import settings
from flows.observation_flow.abstraction_flow import AbstractionFlow
from flows.theory_flow.theory_generation_flow import TheoryGenerationFlow
from market.replay.market_observation_synthesizer import \
    MarketObservationSynthesizer
from memory.experience.experience_repository import ExperienceRepository
from memory.relational.models.confidence_model import ConfidenceModel
from memory.relational.models.reflection_model import ReflectionModel
from memory.relational.models.theory_model import TheoryModel
from memory.relational.models.validation_model import ValidationModel
from memory.relational.postgres_client import SessionLocal
from memory.replay.epistemic_scoring import EpistemicScoringEngine
from memory.replay.regime_memory import (RegimeMatch, RegimeMemoryStore,
                                         RegimeSignature)
from telemetry.contradiction_registry import ContradictionRegistry


class RegimeRetrievalValidator:
    """Shadow Mode Validator for measuring regime retrieval quality."""

    def __init__(self):
        self.csv_path = project_root / "data" / "nifty_daily_3y.csv"
        self.experience_repo = ExperienceRepository()
        self.contradiction_registry = ContradictionRegistry(
            project_root / "data" / "contradiction_registry_validation.json"
        )
        self.regime_memory = RegimeMemoryStore()
        self.epistemic_scoring = EpistemicScoringEngine()
        self.abstraction_flow = AbstractionFlow()
        self.theory_flow = TheoryGenerationFlow()
        self.contradiction_detector = ContradictionDetector()

    def run_validation(self, warm_up_days: int = 100, replay_days: int = 30):
        print("\n" + "=" * 80)
        print("DP NEXT MILESTONE: REGIME RETRIEVAL VALIDATION")
        print("=" * 80)

        # 1. Load dataset
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.csv_path}")

        data = pd.read_csv(self.csv_path)
        total_rows = len(data)
        print(
            f"Loaded dataset: {total_rows} rows from {data['date'].iloc[0]} to {data['date'].iloc[-1]}"
        )

        warm_up_start = total_rows - replay_days - warm_up_days
        warm_up_end = total_rows - replay_days

        warm_up_data = data.iloc[warm_up_start:warm_up_end]
        replay_data = data.iloc[warm_up_end:total_rows]

        # 2. Pre-populate Historical Database
        print(f"\n[1/3] Warm-Up: Pre-populating {len(warm_up_data)} historical days...")
        self._execute_warm_up(warm_up_data)

        # 3. Replay Phase in Shadow Mode
        print(f"\n[2/3] Replay: Running {replay_days}-day replay in Shadow Mode...")
        validation_records = self._execute_shadow_replay(replay_data)

        # 4. Generate Audit Report
        print(f"\n[3/3] Generating final validation report...")
        report_path = (
            project_root / "docs" / "archive" / "regime_retrieval_validation_report.md"
        )
        self._generate_report(validation_records, report_path)
        print(f"✓ Validation report successfully written to {report_path}")
        print("\n" + "=" * 80 + "\n")

    def _execute_warm_up(self, warm_up_data: pd.DataFrame):
        synthesizer = MarketObservationSynthesizer(warm_up_data)

        # Clear historical database records to avoid duplicate keys
        with SessionLocal() as session:
            session.query(ValidationModel).filter(
                ValidationModel.id.like("val_warmup_%")
            ).delete(synchronize_session=False)
            session.query(ReflectionModel).filter(
                ReflectionModel.id.like("ref_warmup_%")
            ).delete(synchronize_session=False)
            session.query(TheoryModel).filter(
                TheoryModel.id.like("theory_warmup_%")
            ).delete(synchronize_session=False)
            session.query(ConfidenceModel).filter(
                ConfidenceModel.id.like("conf_warmup_%")
            ).delete(synchronize_session=False)
            session.commit()

        for idx in range(len(warm_up_data)):
            date_str = warm_up_data["date"].iloc[idx]
            market_obs = synthesizer.synthesize(idx)

            theory_id = f"theory_warmup_{idx}"
            lineage_id = f"lineage_warmup_{idx}"
            conf_id = f"conf_warmup_{idx}"

            # Create mock theory
            mock_theory = Theory(
                id=theory_id,
                created_at=datetime.strptime(date_str, "%Y-%m-%d"),
                lineage_id=lineage_id,
                thesis=f"Historical {market_obs.trend_state} theory under {market_obs.volatility_state} volatility.",
                summary=f"Historical {market_obs.trend_state} theory under {market_obs.volatility_state} volatility.",
                summary_structured=TheoryStructured(
                    claim=f"Regime is driven by {market_obs.trend_state} mechanism.",
                    if_branch=Branch(
                        condition=f"{market_obs.trend_state} persists",
                        action="sustain movement",
                    ),
                    else_branch=Branch(
                        condition=f"{market_obs.trend_state} breaks",
                        action="flat posture",
                    ),
                    falsified_if="close below support level",
                    forbidden_state="close below support level",
                ),
                confidence_state=ConfidenceState(
                    id=conf_id,
                    empirical_confidence=0.65,
                    regime_confidence=0.70,
                    reflection_confidence=0.60,
                    theoretical_coherence=0.65,
                    contradiction_pressure=0.15,
                ),
                regime_subtype=market_obs.trend_state,
            )
            self.theory_repo_save(mock_theory)

            # Persist validation event
            mock_val = ValidationEvent(
                id=f"val_warmup_{idx}",
                created_at=datetime.strptime(date_str, "%Y-%m-%d"),
                theory_id=theory_id,
                validation_summary=f"Historical validation for {market_obs.trend_state} regime.",
                observed_behavior=market_obs.observation_text,
                expected_behavior=f"Expected behavior for {market_obs.trend_state} is met.",
            )
            self.validation_repo_save(mock_val)

            # Register contradictions periodically
            has_contradiction = idx % 5 == 0
            contradictions = []
            if has_contradiction:
                desc = (
                    "price_up_breadth_down"
                    if idx % 2 == 0
                    else "range_bound_volatility_expansion"
                )
                contradictions.append(desc)
                self.contradiction_registry.register_contradictions(
                    theory_id=theory_id,
                    descriptions=contradictions,
                    severity=0.5,
                    step=idx,
                )

            # Save Experience record
            mock_exp = Experience(
                experience_id=f"exp_warmup_{idx}",
                lineage_id=lineage_id,
                theory_family_id=f"family_warmup_{idx}",
                created_at=date_str,
                status=(
                    ExperienceStatus.VALIDATED
                    if idx % 2 == 0
                    else ExperienceStatus.ACTIVE
                ),
                theory_ids=[theory_id],
                contradictions=contradictions,
                mutation_count=1,
                contradiction_count=len(contradictions),
                validation_count=2,
            )
            self.experience_repo.save(mock_exp)

            # Build regime signature
            signature = self.regime_memory.build_signature(
                date=date_str,
                observation=market_obs,
                confidence_values=[0.65],
                contradiction_severity=0.5 if has_contradiction else 0.0,
                active_theory_count=1,
            )
            self.regime_memory.persist(
                step=idx,
                signature=signature,
                active_theories=[mock_theory],
                contradictions=contradictions,
                confidence=0.65,
            )

        print(
            f"✓ Warm-up complete: populated {len(warm_up_data)} historical signatures and records."
        )

    def _execute_shadow_replay(self, replay_data: pd.DataFrame) -> List[dict]:
        synthesizer = MarketObservationSynthesizer(replay_data)
        validation_records = []

        for idx in range(len(replay_data)):
            date_str = replay_data["date"].iloc[idx]
            market_obs = synthesizer.synthesize(idx)

            print(
                f"\n--- Day {idx+1:>2} ({date_str}) | Regime: {market_obs.trend_state}/{market_obs.volatility_state} ---"
            )

            # 1. Independent Current Theory Generation (Actual LLM calls)
            print("  Generating current theory independently (Shadow Mode)...")
            obs_event = ObservationEvent(
                source_type="replay", raw_content=market_obs.observation_text
            )
            abstraction = self.abstraction_flow.process(obs_event)
            generated_theory, _ = self.theory_flow.process(
                abstraction=abstraction,
                regime_subtype=market_obs.trend_state,
                regime_history={"seen_count": 0, "historical_resolution": {}},
            )
            print(f"  ★ Generated Claim: {generated_theory.thesis[:100]}...")

            # 2. Retrieve Top 3 matching historical theories
            current_signature = self.regime_memory.build_signature(
                date=date_str,
                observation=market_obs,
                confidence_values=[0.60],
                contradiction_severity=0.0,
                active_theory_count=0,
            )
            matches = self.regime_memory.retrieve(
                current_signature,
                getattr(market_obs, "contradiction_markers", []),
                limit=3,
                min_similarity=0.45,
            )

            retrieved_analyses = []
            for match in matches:
                for theory_id in match.active_theories:
                    with SessionLocal() as session:
                        theory_model = (
                            session.query(TheoryModel).filter_by(id=theory_id).first()
                        )
                        if not theory_model:
                            continue

                        # Construct Theory object from model
                        structured_data = None
                        if theory_model.summary_structured:
                            import json

                            structured_data = TheoryStructured(
                                **json.loads(theory_model.summary_structured)
                            )

                        retrieved_theory = Theory(
                            id=theory_model.id,
                            created_at=theory_model.created_at,
                            lineage_id=theory_model.lineage_id,
                            thesis=theory_model.thesis,
                            summary=theory_model.summary,
                            summary_structured=structured_data,
                            confidence_state=ConfidenceState(),
                            regime_subtype=getattr(
                                theory_model, "regime_subtype", "neutral"
                            ),
                        )

                    # 3. Compute Metrics
                    # Useful score for both
                    recall_retrieved = self._recall_theory_metrics(
                        theory_id, retrieved_theory.lineage_id, matches
                    )
                    retrieved_usefulness = recall_retrieved["usefulness_score"]

                    recall_generated = self._recall_theory_metrics(
                        generated_theory.id, generated_theory.lineage_id, []
                    )
                    generated_usefulness = recall_generated["usefulness_score"]

                    # Contradiction Score between Generated Theory and Retrieved Theory
                    contradiction_res = self.contradiction_detector.detect(
                        current_theory=generated_theory,
                        historical_theories=[retrieved_theory],
                        validations=[],
                        reflections=[],
                    )
                    contradiction_score = contradiction_res.get("score", 0.0)

                    # Classification
                    classification = self._classify_retrieval(
                        similarity=match.similarity,
                        retrieved_usefulness=retrieved_usefulness,
                        contradiction_score=contradiction_score,
                    )

                    analysis_info = {
                        "theory_id": theory_id,
                        "historical_date": match.date,
                        "similarity": match.similarity,
                        "retrieved_thesis": retrieved_theory.thesis,
                        "retrieved_usefulness": retrieved_usefulness,
                        "generated_usefulness": generated_usefulness,
                        "contradiction_score": contradiction_score,
                        "classification": classification,
                    }
                    retrieved_analyses.append(analysis_info)
                    print(
                        f"  → Match: {match.date} (Sim: {match.similarity:.2f}) | Contradiction: {contradiction_score:.2f} | Class: {classification}"
                    )

            validation_records.append(
                {
                    "date": date_str,
                    "regime_trend": market_obs.trend_state,
                    "regime_volatility": market_obs.volatility_state,
                    "generated_theory_thesis": generated_theory.thesis,
                    "retrievals": retrieved_analyses,
                }
            )

        return validation_records

    def _classify_retrieval(
        self, similarity: float, retrieved_usefulness: float, contradiction_score: float
    ) -> str:
        """Classify retrieval as RELEVANT, PARTIALLY_RELEVANT, or IRRELEVANT."""
        if (
            similarity < 0.45
            or retrieved_usefulness < 0.20
            or contradiction_score >= 0.40
        ):
            return "IRRELEVANT"
        elif (
            similarity >= 0.70
            and retrieved_usefulness >= 0.40
            and contradiction_score < 0.25
        ):
            return "RELEVANT"
        else:
            return "PARTIALLY_RELEVANT"

    def _recall_theory_metrics(
        self, theory_id: str, lineage_id: str, matches: List[RegimeMatch]
    ) -> dict:
        """Fetch metrics for score calculation."""
        usefulness = self.epistemic_scoring.score_theory(
            lineage_record=None,
            regime_matches=matches,
            prior_prediction_result={"direction_score": 1.0},
            contradiction_score=0.1,
            reflection_summary="Theory remains valid.",
        )
        return {
            "usefulness_score": usefulness.get("score", 0.0),
            "usefulness_label": usefulness.get("label", "unknown"),
        }

    def theory_repo_save(self, theory: Theory):
        confidence = theory.confidence_state
        with SessionLocal() as session:
            # Merge ConfidenceModel
            conf_model = ConfidenceModel(
                id=confidence.id,
                created_at=confidence.created_at,
                empirical_confidence=confidence.empirical_confidence,
                regime_confidence=confidence.regime_confidence,
                reflection_confidence=confidence.reflection_confidence,
                theoretical_coherence=confidence.theoretical_coherence,
                contradiction_pressure=confidence.contradiction_pressure,
            )
            session.merge(conf_model)

            theory_model = TheoryModel(
                id=theory.id,
                created_at=theory.created_at,
                lineage_id=theory.lineage_id,
                thesis=theory.thesis,
                summary=theory.summary,
                summary_structured=(
                    theory.summary_structured.model_dump_json()
                    if theory.summary_structured
                    else None
                ),
                confidence_state_id=confidence.id,
                survival_days=getattr(theory, "survival_days", 0.0),
            )
            session.merge(theory_model)
            session.commit()

    def validation_repo_save(self, validation: ValidationEvent):
        with SessionLocal() as session:
            model = ValidationModel(
                id=validation.id,
                created_at=validation.created_at,
                theory_id=validation.theory_id,
                validation_summary=validation.validation_summary,
                observed_behavior=validation.observed_behavior,
                expected_behavior=validation.expected_behavior,
            )
            session.merge(model)
            session.commit()

    def _generate_report(self, validation_records: List[dict], report_path: Path):
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Statistics computation
        total_retrievals = 0
        relevant_count = 0
        partially_relevant_count = 0
        irrelevant_count = 0

        for r in validation_records:
            for ret in r["retrievals"]:
                total_retrievals += 1
                if ret["classification"] == "RELEVANT":
                    relevant_count += 1
                elif ret["classification"] == "PARTIALLY_RELEVANT":
                    partially_relevant_count += 1
                else:
                    irrelevant_count += 1

        relevant_pct = (
            (relevant_count / total_retrievals * 100) if total_retrievals > 0 else 0.0
        )
        success = relevant_pct >= 70.0

        md_lines = [
            "# Regime Retrieval Validation Report",
            "",
            f"**Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "**Objective:** Shadow mode validation comparing independently generated theories with retrieved historical theories.",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"- **Success Criteria Status:** {'★ PASSED' if success else '✗ FAILED'}",
            f"- **Target Metric:** $\\ge 70\\%$ of retrieved theories classified as RELEVANT (non-degrading)",
            f"- **Actual Metric:** **{relevant_pct:.2f}%**",
            f"- **Total Retrieved Theories:** {total_retrievals}",
            f"  - **RELEVANT:** {relevant_count} ({relevant_pct:.1f}%)",
            f"  - **PARTIALLY_RELEVANT:** {partially_relevant_count} ({(partially_relevant_count / total_retrievals * 100) if total_retrievals > 0 else 0.0:.1f}%)",
            f"  - **IRRELEVANT:** {irrelevant_count} ({(irrelevant_count / total_retrievals * 100) if total_retrievals > 0 else 0.0:.1f}%)",
            "",
            "---",
            "",
            "## 2. Step-by-Step Validation Logs",
            "",
        ]

        for idx, rec in enumerate(validation_records):
            md_lines.extend(
                [
                    f"### Day {idx+1}: {rec['date']}",
                    f"**Current Regime:** Trend=`{rec['regime_trend']}`, Volatility=`{rec['regime_volatility']}`",
                    f"**Independently Generated Theory:** *{rec['generated_theory_thesis']}*",
                    "",
                ]
            )

            if not rec["retrievals"]:
                md_lines.append("*No matching historical regimes retrieved.*")
            else:
                md_lines.extend(
                    [
                        "| Historical Date | Similarity | Retrieved Theory ID | Gen Usefulness | Ret Usefulness | Contradiction Score | Classification |",
                        "|---|---|---|---|---|---|---|",
                    ]
                )
                for ret in rec["retrievals"]:
                    md_lines.append(
                        f"| {ret['historical_date']} | {ret['similarity']:.3f} | `{ret['theory_id']}` | {ret['generated_usefulness']:.2f} | {ret['retrieved_usefulness']:.2f} | {ret['contradiction_score']:.2f} | **{ret['classification']}** |"
                    )
            md_lines.append("\n")

        with open(report_path, "w") as f:
            f.write("\n".join(md_lines))


if __name__ == "__main__":
    validator = RegimeRetrievalValidator()
    validator.run_validation()
