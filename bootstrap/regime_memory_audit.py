"""
Regime Memory Retrieval Audit Runner.

Demonstrates that DP can reuse prior knowledge when similar market regimes recur.
1. Populates memory with 100 days of mock historical regimes & theories.
2. Runs a 30-day replay of observation synthesis.
3. Retrieves similar historical regimes.
4. Performs detailed Theory Recall (usefulness, validations, contradictions, experience status).
5. Generates a markdown report for human review.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from cognition.schemas.confidence.confidence_state import ConfidenceState
from cognition.schemas.experience.experience import (Experience,
                                                     ExperienceOutcome,
                                                     ExperienceStatus)
from cognition.schemas.reflection.reflection_event import ReflectionEvent
from cognition.schemas.theory.theory import Branch, Theory, TheoryStructured
from cognition.schemas.validation.validation_event import ValidationEvent
from config.settings import settings
from market.data.dataset_validator import DatasetValidator
from market.replay.market_observation_synthesizer import \
    MarketObservationSynthesizer
from market.replay.replay_engine import ReplayEngine
from memory.experience.experience_repository import ExperienceRepository
from memory.relational.models.reflection_model import ReflectionModel
from memory.relational.models.theory_model import TheoryModel
from memory.relational.models.validation_model import ValidationModel
from memory.relational.postgres_client import SessionLocal
from memory.replay.epistemic_scoring import EpistemicScoringEngine
from memory.replay.regime_memory import (RegimeMatch, RegimeMemoryStore,
                                         RegimeSignature)
from telemetry.contradiction_registry import ContradictionRegistry


class RegimeMemoryAuditor:
    """Orchestrates regime similarity search and theory recall validation."""

    def __init__(self):
        self.csv_path = project_root / "data" / "nifty_daily_3y.csv"
        self.experience_repo = ExperienceRepository()
        self.contradiction_registry = ContradictionRegistry(
            project_root / "data" / "contradiction_registry_audit.json"
        )
        self.regime_memory = RegimeMemoryStore()
        self.epistemic_scoring = EpistemicScoringEngine()

    def run_audit(self, warm_up_days: int = 100, replay_days: int = 30):
        print("\n" + "=" * 80)
        print("DP NEXT MILESTONE: REGIME MEMORY RETRIEVAL AUDIT")
        print("=" * 80)

        # 1. Load and slice dataset
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

        # 2. Warm-Up Phase (Offline-first pre-population)
        print(
            f"\n[1/3] Warm-Up Phase: Pre-populating {warm_up_days} historical days..."
        )
        self._execute_warm_up(warm_up_data)

        # 3. Replay Phase (Similarity search and Recall)
        print(
            f"\n[2/3] Replay Phase: Running {replay_days}-day replay & auditing retrieval..."
        )
        audit_records = self._execute_replay_audit(replay_data)

        # 4. Generate Report
        print(f"\n[3/3] Generating final audit report...")
        report_path = (
            project_root / "docs" / "archive" / "regime_memory_replay_audit.md"
        )
        self._generate_report(audit_records, report_path)
        print(f"✓ Audit report successfully written to {report_path}")
        print("\n" + "=" * 80 + "\n")

    def _execute_warm_up(self, warm_up_data: pd.DataFrame):
        synthesizer = MarketObservationSynthesizer(warm_up_data)

        # Clear database records first to keep warm-up clean
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
            session.commit()

        for idx in range(len(warm_up_data)):
            date_str = warm_up_data["date"].iloc[idx]
            market_obs = synthesizer.synthesize(idx)

            # Construct mock theory representing this historical state
            theory_id = f"theory_warmup_{idx}"
            lineage_id = f"lineage_warmup_{idx}"

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

            # Register mock contradictions periodically to simulate conflicts
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

            # Persist experiences
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

            # Save in RegimeMemoryStore
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
            f"✓ Successfully persisted {len(warm_up_data)} signatures and associated database records."
        )

    def _execute_replay_audit(self, replay_data: pd.DataFrame) -> List[dict]:
        synthesizer = MarketObservationSynthesizer(replay_data)
        audit_log = []

        for idx in range(len(replay_data)):
            date_str = replay_data["date"].iloc[idx]
            market_obs = synthesizer.synthesize(idx)

            # Build current signature
            current_signature = self.regime_memory.build_signature(
                date=date_str,
                observation=market_obs,
                confidence_values=[0.60],
                contradiction_severity=0.0,
                active_theory_count=0,
            )

            # Retrieve top matches
            matches = self.regime_memory.retrieve(
                current_signature,
                getattr(market_obs, "contradiction_markers", []),
                limit=3,
                min_similarity=0.45,
            )

            retrieved_theories = []
            revived_id = "None"

            for match in matches:
                # Retrieve details of the associated theories
                for theory_id in match.active_theories:
                    # Look up theory and compute metrics
                    with SessionLocal() as session:
                        theory_model = (
                            session.query(TheoryModel).filter_by(id=theory_id).first()
                        )
                        if not theory_model:
                            continue

                        lineage_id = theory_model.lineage_id

                    recall_data = self._recall_theory_metrics(
                        theory_id, lineage_id, matches
                    )

                    theory_info = {
                        "id": theory_id,
                        "similarity": match.similarity,
                        "regime_date": match.date,
                        "usefulness_score": recall_data["usefulness_score"],
                        "usefulness_label": recall_data["usefulness_label"],
                        "validation_count": len(recall_data["validations"]),
                        "contradiction_count": len(recall_data["contradictions"]),
                        "experience_status": recall_data["experience_status"],
                        "claim": theory_model.thesis,
                    }
                    retrieved_theories.append(theory_info)

                    # Revival Strategy: if similarity >= 0.70 and theory is strong/useful, mark as revived candidate
                    if (
                        match.similarity >= 0.70
                        and recall_data["usefulness_score"] >= 0.35
                        and revived_id == "None"
                    ):
                        revived_id = theory_id

            audit_log.append(
                {
                    "date": date_str,
                    "current_regime": {
                        "trend": current_signature.trend,
                        "volatility": current_signature.volatility_state,
                        "sentiment": current_signature.sentiment,
                        "breadth": current_signature.breadth_proxy,
                    },
                    "matches": [
                        {
                            "date": m.date,
                            "similarity": m.similarity,
                            "contradictions": m.contradictions,
                        }
                        for m in matches
                    ],
                    "retrieved_theories": retrieved_theories,
                    "revived_theory_id": revived_id,
                }
            )

            # Print step-by-step logs for verification
            print(
                f"Day {idx+1:>2} ({date_str}) | Regime: {current_signature.trend}/{current_signature.volatility_state}"
            )
            if matches:
                for t in retrieved_theories:
                    print(
                        f"  → Match: {t['regime_date']} (Sim: {t['similarity']:.2f}) | Theory: {t['id']} | Usefulness: {t['usefulness_score']:.2f} ({t['usefulness_label']}) | Exp: {t['experience_status']}"
                    )
                if revived_id != "None":
                    print(f"  ★ REVIVED: {revived_id}")
            else:
                print("  → No matching historical regimes found.")

        return audit_log

    def _recall_theory_metrics(
        self, theory_id: str, lineage_id: str, matches: List[RegimeMatch]
    ) -> dict:
        """Recall theory stats from PostgreSQL, Registry, and Experience repositories."""
        # 1. Compute usefulness score
        usefulness = self.epistemic_scoring.score_theory(
            lineage_record=None,
            regime_matches=matches,
            prior_prediction_result={"direction_score": 1.0},
            contradiction_score=0.1,
            reflection_summary="Theory remains structurally valid.",
        )

        # 2. Fetch Validation history
        validations_list = []
        with SessionLocal() as session:
            val_models = (
                session.query(ValidationModel).filter_by(theory_id=theory_id).all()
            )
            for v in val_models:
                validations_list.append(
                    {
                        "summary": v.validation_summary,
                        "observed": v.observed_behavior,
                        "expected": v.expected_behavior,
                    }
                )

        # 3. Fetch Contradiction history
        contradictions_list = []
        for rec in self.contradiction_registry.all_records():
            if rec.theory_id == theory_id:
                contradictions_list.append(
                    {
                        "description": rec.description,
                        "status": rec.status,
                        "severity": rec.severity,
                    }
                )

        # 4. Fetch Experience Status
        exp = self.experience_repo.load_by_lineage(lineage_id)
        exp_status = exp.status.value if exp else "none"

        return {
            "usefulness_score": usefulness.get("score", 0.0),
            "usefulness_label": usefulness.get("label", "unknown"),
            "validations": validations_list,
            "contradictions": contradictions_list,
            "experience_status": exp_status,
        }

    def theory_repo_save(self, theory: Theory):
        """Standard SQL persistence shim for Theory."""
        confidence = theory.confidence_state
        with SessionLocal() as session:
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
        """Standard SQL persistence shim for ValidationEvent."""
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

    def _generate_report(self, audit_records: List[dict], report_path: Path):
        """Write structured audit logs into a markdown file."""
        report_path.parent.mkdir(parents=True, exist_ok=True)

        md_lines = [
            "# Regime Memory Retrieval Audit Report",
            "",
            f"**Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "**Objective:** Verify retrieval quality and historical recall of matching market regimes and theories.",
            "",
            "---",
            "",
            "## 1. Retrieval Summary Statistics",
            "",
        ]

        total_steps = len(audit_records)
        steps_with_matches = sum(1 for r in audit_records if r["matches"])
        steps_with_revival = sum(
            1 for r in audit_records if r["revived_theory_id"] != "None"
        )

        md_lines.extend(
            [
                f"- **Total Replay Steps:** {total_steps}",
                f"- **Steps with Matches:** {steps_with_matches} ({steps_with_matches/total_steps:.1%})",
                f"- **Steps with Revivals:** {steps_with_revival} ({steps_with_revival/total_steps:.1%})",
                "",
                "---",
                "",
                "## 2. Step-by-Step Audit Logs",
                "",
            ]
        )

        for idx, rec in enumerate(audit_records):
            md_lines.extend(
                [
                    f"### Day {idx+1}: {rec['date']}",
                    f"**Current Regime:** Trend=`{rec['current_regime']['trend']}`, Volatility=`{rec['current_regime']['volatility']}`, Sentiment=`{rec['current_regime']['sentiment']}`, Breadth=`{rec['current_regime']['breadth']}`",
                    "",
                ]
            )

            if not rec["matches"]:
                md_lines.append("*No matching historical signatures found.*")
            else:
                md_lines.extend(
                    [
                        "| Historical Date | Similarity | Retrieved Theory ID | Usefulness Score | Experience Status |",
                        "|---|---|---|---|---|",
                    ]
                )
                for t in rec["retrieved_theories"]:
                    md_lines.append(
                        f"| {t['regime_date']} | {t['similarity']:.3f} | `{t['id']}` | {t['usefulness_score']:.2f} ({t['usefulness_label']}) | `{t['experience_status']}` |"
                    )
                md_lines.append("")
                if rec["revived_theory_id"] != "None":
                    md_lines.append(
                        f"★ **Revived Candidate Theory ID:** `{rec['revived_theory_id']}`"
                    )

            md_lines.append("\n")

        with open(report_path, "w") as f:
            f.write("\n".join(md_lines))


if __name__ == "__main__":
    auditor = RegimeMemoryAuditor()
    auditor.run_audit()
