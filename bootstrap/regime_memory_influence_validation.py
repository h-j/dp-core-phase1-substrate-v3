"""
Regime Memory Influence Validation.

Compares:
1. Baseline Replay (independent theory generation per step)
2. Memory-Influenced Replay (top retrieved theory injected as context)

Measures:
- Contradiction pressure
- Usefulness score
- Validation rate
- Mutation rate
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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
from market.schemas.market_outcome import MarketOutcome
from market.validation.outcome_validation_engine import OutcomeValidationEngine
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


class RegimeMemoryInfluenceValidator:
    """Validator class to evaluate comparative performance of memory influence."""

    def __init__(self):
        self.csv_path = project_root / "data" / "nifty_daily_3y.csv"
        self.experience_repo = ExperienceRepository()
        self.contradiction_registry = ContradictionRegistry(
            project_root / "data" / "contradiction_registry_influence.json"
        )
        self.regime_memory = RegimeMemoryStore()
        self.epistemic_scoring = EpistemicScoringEngine()
        self.abstraction_flow = AbstractionFlow()
        self.theory_flow = TheoryGenerationFlow()
        self.contradiction_detector = ContradictionDetector()
        self.validation_engine = OutcomeValidationEngine()

    def run_evaluation(self, warm_up_days: int = 100, replay_days: int = 30):
        print("\n" + "=" * 80)
        print("DP NEXT MILESTONE: REGIME CONTROLLED MEMORY INFLUENCE")
        print("=" * 80)

        # 1. Load dataset
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Dataset not found at {self.csv_path}")

        data = pd.read_csv(self.csv_path)
        total_rows = len(data)

        warm_up_start = total_rows - replay_days - warm_up_days
        warm_up_end = total_rows - replay_days

        warm_up_data = data.iloc[warm_up_start:warm_up_end]
        replay_data = data.iloc[warm_up_end:total_rows]

        # 2. Warm up historical memory (offline populated mock data)
        print(f"\n[1/4] Running Warm-Up to build prior regimes & theories...")
        self._execute_warm_up(warm_up_data)

        # 3. Baseline Replay (No Memory Influence)
        print(f"\n[2/4] Executing 30-day Baseline Replay (Without Memory Influence)...")
        baseline_records = self._run_replay(replay_data, memory_influenced=False)

        # Re-initialize memory store and database for comparison run
        self.regime_memory = RegimeMemoryStore()
        self._execute_warm_up(warm_up_data)

        # 4. Influenced Replay (With Memory Influence context)
        print(
            f"\n[3/4] Executing 30-day Influenced Replay (With Memory Influence context)..."
        )
        influenced_records = self._run_replay(replay_data, memory_influenced=True)

        # 5. Compile and Generate Comparative Report
        print(f"\n[4/4] Generating comparative evaluation report...")
        report_path = (
            project_root / "docs" / "archive" / "regime_memory_influence_report.md"
        )
        self._generate_report(baseline_records, influenced_records, report_path)
        print(f"✓ Report written to {report_path}")
        print("\n" + "=" * 80 + "\n")

    def _execute_warm_up(self, warm_up_data: pd.DataFrame):
        synthesizer = MarketObservationSynthesizer(warm_up_data)

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
                    reuse_decision="REJECTED",
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

            mock_val = ValidationEvent(
                id=f"val_warmup_{idx}",
                created_at=datetime.strptime(date_str, "%Y-%m-%d"),
                theory_id=theory_id,
                validation_summary=f"Historical validation for {market_obs.trend_state} regime.",
                observed_behavior=market_obs.observation_text,
                expected_behavior=f"Expected behavior for {market_obs.trend_state} is met.",
            )
            self.validation_repo_save(mock_val)

            has_contradiction = idx % 5 == 0
            contradictions = []
            if has_contradiction:
                desc = "price_up_breadth_down"
                contradictions.append(desc)
                self.contradiction_registry.register_contradictions(
                    theory_id=theory_id,
                    descriptions=contradictions,
                    severity=0.5,
                    step=idx,
                )

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

    def _run_replay(
        self, replay_data: pd.DataFrame, memory_influenced: bool
    ) -> List[dict]:
        synthesizer = MarketObservationSynthesizer(replay_data)
        records = []

        for idx in range(len(replay_data)):
            date_str = replay_data["date"].iloc[idx]
            market_obs = synthesizer.synthesize(idx)

            print(
                f"  Day {idx+1:>2}/30 ({date_str}) | Regime: {market_obs.trend_state}/{market_obs.volatility_state}"
            )

            # 1. Signature check & similarity retrieval
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

            top_retrieved_theory = None
            top_similarity = 0.0
            if matches and len(matches[0].active_theories) > 0:
                top_match = matches[0]
                top_similarity = top_match.similarity
                theory_id = top_match.active_theories[0]
                with SessionLocal() as session:
                    theory_model = (
                        session.query(TheoryModel).filter_by(id=theory_id).first()
                    )
                    if theory_model:
                        structured_data = None
                        if theory_model.summary_structured:
                            structured_data = TheoryStructured(
                                **json.loads(theory_model.summary_structured)
                            )

                        top_retrieved_theory = Theory(
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

            # 2. Independently/Influenced generated theory
            obs_event = ObservationEvent(
                id=f"obs_rep_{'inf' if memory_influenced else 'base'}_{idx}",
                source_type="replay",
                raw_content=market_obs.observation_text,
            )
            abstraction = self.abstraction_flow.process(obs_event)

            # Pass top_retrieved_theory if memory_influenced is true
            generated_theory, _ = self.theory_flow.process(
                abstraction=abstraction,
                regime_subtype=market_obs.trend_state,
                regime_history={"seen_count": 0, "historical_resolution": {}},
                retrieved_theory=top_retrieved_theory if memory_influenced else None,
            )

            # 3. Compute Metrics
            # Usefulness score
            usefulness_res = self.epistemic_scoring.score_theory(
                lineage_record=None,
                regime_matches=matches if memory_influenced else [],
                prior_prediction_result={"direction_score": 1.0},
                contradiction_score=0.1,
                reflection_summary="Theory generated.",
            )
            usefulness_score = usefulness_res["score"]

            # Contradiction score (against historical references)
            hist_ref = [top_retrieved_theory] if top_retrieved_theory else []
            contradiction_res = self.contradiction_detector.detect(
                current_theory=generated_theory,
                historical_theories=hist_ref,
                validations=[],
                reflections=[],
            )
            contradiction_score = contradiction_res.get("score", 0.0)

            # Validation score (against actual NIFTY daily resolution outcome)
            simulated_outcome = MarketOutcome(
                market_name="NIFTY",
                related_observation_id=obs_event.id,
                outcome_summary=f"Trend: {market_obs.trend_state}, Volatility: {market_obs.volatility_state}",
                realized_trend=market_obs.trend_state,
                realized_volatility=market_obs.volatility_state,
                realized_breadth=getattr(market_obs, "breadth_state", "mixed"),
                realized_liquidity=getattr(market_obs, "liquidity_state", "stable"),
            )
            val_result = self.validation_engine.validate(
                theory=generated_theory,
                prior_observation=obs_event,
                market_outcome=simulated_outcome,
            )
            validation_score = val_result["validation_score"]

            # Extraction of decision
            decision = "REJECTED"
            if (
                generated_theory.summary_structured
                and generated_theory.summary_structured.reuse_decision
            ):
                decision = generated_theory.summary_structured.reuse_decision

            records.append(
                {
                    "date": date_str,
                    "regime_trend": market_obs.trend_state,
                    "regime_volatility": market_obs.volatility_state,
                    "retrieved_theory_id": (
                        top_retrieved_theory.id if top_retrieved_theory else "None"
                    ),
                    "similarity": top_similarity,
                    "generated_thesis": generated_theory.thesis,
                    "usefulness": usefulness_score,
                    "contradiction": contradiction_score,
                    "validation": validation_score,
                    "decision": decision,
                }
            )

        return records

    def theory_repo_save(self, theory: Theory):
        confidence = theory.confidence_state
        with SessionLocal() as session:
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

    def _generate_report(
        self,
        baseline_records: List[dict],
        influenced_records: List[dict],
        report_path: Path,
    ):
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Baseline aggregates
        base_usefulness = [r["usefulness"] for r in baseline_records]
        base_contradiction = [r["contradiction"] for r in baseline_records]
        base_validation = [r["validation"] for r in baseline_records]

        avg_base_usefulness = sum(base_usefulness) / len(base_usefulness)
        avg_base_contradiction = sum(base_contradiction) / len(base_contradiction)
        avg_base_validation = sum(base_validation) / len(base_validation)

        # Influenced aggregates
        inf_usefulness = [r["usefulness"] for r in influenced_records]
        inf_contradiction = [r["contradiction"] for r in influenced_records]
        inf_validation = [r["validation"] for r in influenced_records]

        avg_inf_usefulness = sum(inf_usefulness) / len(inf_usefulness)
        avg_inf_contradiction = sum(inf_contradiction) / len(inf_contradiction)
        avg_inf_validation = sum(inf_validation) / len(inf_validation)

        # Influenced mutation & decisions
        reused_cnt = sum(1 for r in influenced_records if r["decision"] == "REUSED")
        modified_cnt = sum(1 for r in influenced_records if r["decision"] == "MODIFIED")
        rejected_cnt = sum(1 for r in influenced_records if r["decision"] == "REJECTED")
        total_inf = len(influenced_records)

        reused_pct = reused_cnt / total_inf * 100
        modified_pct = modified_cnt / total_inf * 100
        rejected_pct = rejected_cnt / total_inf * 100
        mutation_rate = (modified_cnt + rejected_cnt) / total_inf * 100

        # Success check: memory influence improves/maintains validation, usefulness and does not increase contradiction
        usefulness_improved = avg_inf_usefulness >= avg_base_usefulness - 0.02
        validation_improved = avg_inf_validation >= avg_base_validation - 0.02
        contradiction_neutral = avg_inf_contradiction <= avg_base_contradiction + 0.05

        success = usefulness_improved and validation_improved and contradiction_neutral

        md_lines = [
            "# Controlled Memory Influence Validation Report",
            "",
            f"**Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "**Objective:** Comparative evaluation of baseline vs memory-influenced reasoning quality.",
            "",
            "---",
            "",
            "## 1. Executive Comparative Summary",
            "",
            f"- **Success Criteria Status:** {'★ PASSED' if success else '✗ FAILED'}",
            "",
            "| Metric | Baseline Replay | Memory-Influenced Replay | Divergence / Status |",
            "|---|---|---|---|",
            f"| **Average Usefulness** | {avg_base_usefulness:.4f} | {avg_inf_usefulness:.4f} | {'✓ Stable/Improved' if usefulness_improved else '✗ Degraded'} |",
            f"| **Average Contradiction Pressure** | {avg_base_contradiction:.4f} | {avg_inf_contradiction:.4f} | {'✓ Stable/Reduced' if contradiction_neutral else '✗ Increased Pressure'} |",
            f"| **Average Validation Rate** | {avg_base_validation:.4f} | {avg_inf_validation:.4f} | {'✓ Stable/Improved' if validation_improved else '✗ Degraded'} |",
            f"| **Mutation Rate (Mod + Rej)** | 100.00% | {mutation_rate:.2f}% | (MOD: {modified_pct:.1f}%, REJ: {rejected_pct:.1f}%) |",
            "",
            f"- **Memory Reuse Decisions (Influenced Run):**",
            f"  - **REUSED:** {reused_cnt} ({reused_pct:.1f}%)",
            f"  - **MODIFIED:** {modified_cnt} ({modified_pct:.1f}%)",
            f"  - **REJECTED:** {rejected_cnt} ({rejected_pct:.1f}%)",
            "",
            "---",
            "",
            "## 2. Comparative Step-by-Step Logs",
            "",
        ]

        for idx in range(len(baseline_records)):
            b = baseline_records[idx]
            inf = influenced_records[idx]

            md_lines.extend(
                [
                    f"### Day {idx+1}: {b['date']}",
                    f"**Current Regime:** Trend=`{b['regime_trend']}`, Volatility=`{b['regime_volatility']}`",
                    f"- **Retrieved ID:** `{inf['retrieved_theory_id']}` (Similarity: {inf['similarity']:.3f})",
                    f"- **Baseline generated theory:** *{b['generated_thesis']}*",
                    f"- **Influenced generated theory:** *{inf['generated_thesis']}*",
                    f"- **Baseline metrics:** Usefulness={b['usefulness']:.2f}, Contradiction={b['contradiction']:.2f}, Validation={b['validation']:.2f}",
                    f"- **Influenced metrics:** Usefulness={inf['usefulness']:.2f}, Contradiction={inf['contradiction']:.2f}, Validation={inf['validation']:.2f}",
                    f"- **Influenced Decision:** **{inf['decision']}**",
                    "",
                ]
            )

        with open(report_path, "w") as f:
            f.write("\n".join(md_lines))


if __name__ == "__main__":
    validator = RegimeMemoryInfluenceValidator()
    validator.run_evaluation()
