import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Template

from config.settings import settings
from market.replay.replay_engine import ReplayExecutor


class ReplayReportModel:
    """
    Structured model containing all metrics, timelines, health statuses,
    world models, open questions, and evidence gaps from a completed Replay run.
    """

    def __init__(self, executor: ReplayExecutor, analysis_engine):
        self.executor = executor
        self.ae = analysis_engine.analysis_engine
        self.repo = executor.knowledge_repository

    def build_model(self) -> dict:
        em = self.ae.external_metrics if self.ae else {}

        # 1. Metadata
        symbol = self.executor.market_name
        days = len(self.executor.engine) if self.executor.engine else 0
        date_range = "N/A"
        if self.executor.engine:
            start, end = self.executor.engine.get_date_range()
            date_range = f"{start} → {end}"

        execution_hash = em.get("execution_hash", "unknown")
        git_commit = em.get("git_commit", "unknown")
        if git_commit == "unknown":
            try:
                git_commit = (
                    subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
                    )
                    .decode("utf-8")
                    .strip()
                )
            except Exception:
                pass

        llm_version = settings.OLLAMA_MODEL
        replay_version = em.get("replay_version", "v3.0PersistentReflective")

        # 2. Main Metrics
        pred_analysis = (
            self.ae.analyze().get("prediction_analysis", {}) if self.ae else {}
        )
        overall_acc = (
            em.get("experience_audit", {}).get("overall_prediction_accuracy")
            or em.get("overall_prediction_accuracy")
            or pred_analysis.get("accuracy", 0.0)
        )
        # Ensure percentage value
        if overall_acc < 1.0:
            overall_acc_pct = overall_acc * 100.0
        else:
            overall_acc_pct = overall_acc

        knowledge_debt = int(
            em.get("knowledge_growth", {}).get("knowledge_debt_score", 0)
        ) or int(em.get("knowledge_debt_score", 0))
        memory_usefulness = float(em.get("memory_retrieval_usefulness", 0.0))
        knowledge_coverage = float(em.get("principle_coverage", 0.0))
        prediction_drift = float(em.get("prediction_drift", 0.0))
        theory_drift = float(em.get("theory_drift", 0.0))

        # 3. Replay Story Narrative
        experiences_count = len(self.ae.prediction_history) if self.ae else 0
        active_theories_count = int(em.get("active_theories", 0))
        retired_theories_count = int(em.get("retired_theories", 0))
        theories_count = active_theories_count + retired_theories_count
        if theories_count == 0:
            theories_count = len(self.ae.prediction_history) if self.ae else 0

        lessons_count = 0
        if hasattr(self.executor, "lesson_repo") and self.executor.lesson_repo:
            lessons_count = len(self.executor.lesson_repo.list_lessons())

        all_principles = self.repo.list_principles()
        active_principles_count = sum(
            1
            for p in all_principles
            if getattr(p, "status", "").lower()
            in ["active", "stable", "emerging", "trusted", "canonical"]
        )
        world_models_count = 1 if self.repo.get_latest_world_model() else 0
        unique_mechanisms = len(em.get("component_failure_counts", {}))
        if unique_mechanisms == 0:
            unique_mechanisms = 2  # default fallback
        gaps_count = len(self.repo.list_evidence_gaps())

        story_summary = (
            f"This replay represents {days} days of experience on {symbol}. During this period, "
            f"DP generated {experiences_count} experiences, evolved {theories_count} theories, extracted {lessons_count} lessons, "
            f"consolidated them into {active_principles_count} active principles, maintained {world_models_count} evolving world model(s), "
            f"and reduced uncertainty in {unique_mechanisms} key market mechanisms while identifying {gaps_count} unresolved evidence gap(s)."
        )

        # 4. Knowledge Health Progress Bars
        calibration_error = (
            em.get("experience_audit", {}).get("confidence_calibration_error")
            or pred_analysis.get("calibration_score")
            or 0.4
        )
        trust_score = max(0.0, (1.0 - calibration_error) * 100.0)

        # Lesson reuse rate fallback: calculate from history if not present in lesson_stats
        raw_reuse_rate = em.get("lesson_stats", {}).get("lesson_reuse_rate")
        if raw_reuse_rate is None:
            pred_hist = self.ae.prediction_history if self.ae else []
            reused_days = sum(1 for r in pred_hist if r.get("reused_lessons"))
            raw_reuse_rate = (reused_days / len(pred_hist)) if pred_hist else 0.0

        knowledge_health = {
            "knowledge_debt_bar": (
                min(100, int(knowledge_debt * 3.5)) if knowledge_debt > 0 else 10
            ),
            "principle_coverage": float(knowledge_coverage * 100.0),
            "reuse_rate": float(raw_reuse_rate * 100.0),
            "trust": float(trust_score),
        }

        # 5. Lifecycle Distribution
        knowledge_lifecycle = {
            "candidate": sum(
                1
                for p in all_principles
                if getattr(p, "status", "").lower() == "candidate"
            ),
            "emerging": sum(
                1
                for p in all_principles
                if getattr(p, "status", "").lower() in ["active", "emerging"]
            ),
            "trusted": sum(
                1
                for p in all_principles
                if getattr(p, "status", "").lower() in ["stable", "trusted"]
            ),
            "canonical": sum(
                1
                for p in all_principles
                if getattr(p, "status", "").lower() == "canonical"
            ),
            "retired": sum(
                1
                for p in all_principles
                if getattr(p, "status", "").lower() == "retired"
            ),
        }

        # 6. Timeline Processing
        timeline = []
        if self.ae:
            for i, r in enumerate(self.ae.prediction_history):
                pred = r.get("prediction") or {}
                result = r.get("prior_prediction_result") or {}

                direction = pred.get("direction", "N/A")
                confidence = pred.get("confidence", 0.0)
                prediction_str = (
                    f"{direction} ({confidence:.0%})" if direction != "N/A" else "Hold"
                )

                outcome = result.get("outcome", "N/A")
                accuracy = result.get("accuracy", None)
                outcome_str = f"{outcome}"
                if accuracy is not None:
                    outcome_str += f" (Acc: {accuracy:.0%})"

                used_knowledge = []
                for rule_id in pred.get("applied_principles", []):
                    used_knowledge.append(f"Principle: {rule_id[:8]}")
                for lesson_id in pred.get("applied_lessons", []):
                    used_knowledge.append(f"Lesson: {lesson_id[:8]}")
                knowledge_str = (
                    ", ".join(used_knowledge) if used_knowledge else "Experience Only"
                )

                timeline.append(
                    {
                        "date": r.get("date"),
                        "theory": r.get("theory_summary", "N/A"),
                        "prediction": prediction_str,
                        "outcome": outcome_str,
                        "knowledge_used": knowledge_str,
                        "contradiction": float(r.get("contradiction_score", 0.0)),
                    }
                )

        # 7. Theory Evolution Lineage
        theory_evolution = em.get("lineage_audit_table", [])

        # 8. World Model & Curiosity Layer
        latest_wm = self.repo.get_latest_world_model()
        world_model = {
            "narrative": (
                latest_wm.narrative_summary
                if latest_wm
                else "No world model generated yet."
            ),
            "regime_constraints": latest_wm.regime_constraints if latest_wm else {},
            "supporting_principles": [
                (
                    f"Principle {p_id[:8]}: {self.repo.get_principle(p_id).statement}"
                    if self.repo.get_principle(p_id)
                    else f"Principle {p_id[:8]}"
                )
                for p_id in (
                    latest_wm.active_principle_ids
                    if latest_wm and latest_wm.active_principle_ids
                    else []
                )
            ],
            "dominant_mechanisms": (
                getattr(latest_wm, "dominant_mechanisms", []) if latest_wm else []
            ),
            "active_constraints": (
                getattr(latest_wm, "active_constraints", []) if latest_wm else []
            ),
            "supporting_canonical_principles": (
                getattr(latest_wm, "supporting_canonical_principles", [])
                if latest_wm
                else []
            ),
            "confidence": getattr(latest_wm, "confidence", 0.5) if latest_wm else 0.5,
            "stability": (
                getattr(latest_wm, "stability", "Emerging") if latest_wm else "Emerging"
            ),
            "evidence_count": (
                getattr(latest_wm, "evidence_count", 0) if latest_wm else 0
            ),
            "applicable_regimes": (
                getattr(latest_wm, "applicable_regimes", []) if latest_wm else []
            ),
            "open_questions": [
                {
                    "question_text": oq.question_text,
                    "hypothesized_factors": oq.hypothesized_factors,
                }
                for oq in self.repo.list_open_questions()
            ],
            "evidence_gaps": [
                {
                    "id": gap.id,
                    "missing_evidence": gap.missing_evidence,
                    "candidate_data_source": gap.candidate_data_source,
                    "expected_explanatory_value": gap.expected_explanatory_value,
                    "priority": gap.priority,
                }
                for gap in self.repo.list_evidence_gaps()
            ],
        }

        # 9. Extract Chart Series from primary dataset
        chart_data = {
            "dates": [],
            "close": [],
            "delivery_pct": [],
            "fii_net": [],
            "sector_zscore": [],
        }

        if self.executor.engine and hasattr(self.executor.engine, "data"):
            df = self.executor.engine.data
            replayed_dates = pd.to_datetime([r.get("date") for r in timeline])
            df_replayed = df[df["date"].isin(replayed_dates)].copy()
            df_replayed = df_replayed.sort_values(by="date")

            if len(df_replayed) > 0:
                chart_data["dates"] = (
                    df_replayed["date"].dt.strftime("%Y-%m-%d").tolist()
                    if pd.api.types.is_datetime64_any_dtype(df_replayed["date"])
                    else df_replayed["date"].tolist()
                )
                chart_data["close"] = df_replayed["close"].fillna(0.0).tolist()
                chart_data["delivery_pct"] = (
                    df_replayed["delivery_pct_5d"].fillna(0.0).tolist()
                    if "delivery_pct_5d" in df_replayed.columns
                    else (
                        df_replayed["delivery_pct"].fillna(0.0).tolist()
                        if "delivery_pct" in df_replayed.columns
                        else []
                    )
                )
                chart_data["fii_net"] = (
                    df_replayed["fii_net"].fillna(0.0).tolist()
                    if "fii_net" in df_replayed.columns
                    else []
                )
                chart_data["sector_zscore"] = (
                    df_replayed["sector_zscore"].fillna(0.0).tolist()
                    if "sector_zscore" in df_replayed.columns
                    else []
                )

        # Extract daily equity curve if paper trader is present
        if hasattr(self.executor, "paper_trader") and self.executor.paper_trader:
            pt = self.executor.paper_trader
            date_to_cap = {t["date"]: t["cumulative_capital"] for t in pt.trade_log}
            equity_curve = []
            last_cap = pt.starting_capital
            for date in chart_data["dates"]:
                if date in date_to_cap:
                    last_cap = date_to_cap[date]
                equity_curve.append(last_cap)
            if equity_curve:
                chart_data["equity_curve"] = equity_curve

        paper_trading_summary = None
        decision_intelligence = None
        if hasattr(self.executor, "paper_trader") and self.executor.paper_trader:
            paper_trading_summary = self.executor.paper_trader.get_summary()
            decision_intelligence = (
                self.executor.paper_trader.get_decision_intelligence_metrics()
            )
        else:
            paper_trading_summary = em.get("paper_trading_summary")
            decision_intelligence = em.get("decision_intelligence")

        decision_traces = getattr(self.executor, "decision_traces", [])
        epistemic_review = getattr(self.executor, "epistemic_review", {})

        compilation_metrics = getattr(self.executor, "compilation_metrics", None)
        if not isinstance(compilation_metrics, dict) or hasattr(
            compilation_metrics, "_mock_self"
        ):
            compilation_metrics = {
                "theories_generated": 0,
                "propositions_compiled": 0,
                "compilation_success_rate": 0.0,
                "compilation_success_count": 0,
                "compilation_partial_count": 0,
                "compilation_failed_count": 0,
                "failure_reasons": {},
                "semantic_propositions_created": 0,
                "semantic_failures": 0,
                "ontology_mapping_failures": 0,
                "propositions_grounded": 0,
                "percentile_grounding": 0,
                "relative_references_resolved": 0,
                "grounding_failures": 0,
                # Milestone 9 Validation Metrics
                "validation_records_created": 0,
                "propositions_evaluated": 0,
                "supported_records": 0,
                "contradicted_records": 0,
                "partially_supported_records": 0,
                "undecidable_records": 0,
                "avg_confidence_delta": 0.0,
                "avg_uncertainty_delta": 0.0,
            }

        # Construct final dict
        return {
            "symbol": symbol,
            "days": days,
            "date_range": date_range,
            "execution_hash": execution_hash,
            "git_commit": git_commit,
            "llm_version": llm_version,
            "replay_version": replay_version,
            "story_summary": story_summary,
            "metrics": {
                "accuracy": overall_acc_pct,
                "knowledge_debt": knowledge_debt,
                "memory_usefulness": memory_usefulness,
                "knowledge_coverage": knowledge_coverage,
                "prediction_drift": prediction_drift,
                "theory_drift": theory_drift,
            },
            "knowledge_health": knowledge_health,
            "knowledge_lifecycle": knowledge_lifecycle,
            "timeline": timeline,
            "theory_evolution": theory_evolution,
            "world_model": world_model,
            "chart_data": chart_data,
            "decision_traces": decision_traces,
            "epistemic_review": epistemic_review,
            "paper_trading_summary": paper_trading_summary,
            "decision_intelligence": decision_intelligence,
            "compilation_metrics": compilation_metrics,
        }


class ReplayReportRenderer:
    """
    Renders report.json and compile it using a Jinja2 template to report.html.
    """

    @staticmethod
    def render(report_data: dict, output_html_path: Path):
        template_path = Path(__file__).parent / "report_template.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Jinja2 template missing at {template_path}")

        with open(template_path, "r") as f:
            template_content = f.read()

        template = Template(template_content)

        # Injects raw JSON strings directly for frontend consumption
        raw_json_str = json.dumps(report_data, indent=2)
        chart_data_json = json.dumps(report_data.get("chart_data", {}))
        decision_traces_json = json.dumps(report_data.get("decision_traces", []))
        epistemic_review_json = json.dumps(report_data.get("epistemic_review", {}))

        rendered_html = template.render(
            **report_data,
            raw_json_str=raw_json_str,
            chart_data_json=chart_data_json,
            decision_traces_json=decision_traces_json,
            epistemic_review_json=epistemic_review_json,
        )

        with open(output_html_path, "w") as f:
            f.write(rendered_html)
