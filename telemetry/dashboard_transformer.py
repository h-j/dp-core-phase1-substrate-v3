"""
Dashboard Data Transformer API (Milestone 3)
Decouples report generation from live ReplayExecutor objects by pulling data strictly from persistence stores.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from telemetry.eef_evaluator import EEFEvaluator

logger = logging.getLogger("dashboard_transformer")


class DashboardDataTransformer:
    """
    Transforms persisted telemetry event snapshots and replay database records into a clean,
    JSON-serializable Dashboard v2.0 data model.
    """

    def __init__(self, run_id: str, symbol: str = "RELIANCE", run_dir: Optional[Path] = None):
        self.run_id = run_id
        self.symbol = symbol
        self.run_dir = run_dir

    def build_dashboard_data(
        self,
        predictions_history: List[Dict[str, Any]] = None,
        mechanisms_history: List[Dict[str, Any]] = None,
        lessons_history: List[Dict[str, Any]] = None,
        principles_history: List[Dict[str, Any]] = None,
        timeline_history: List[Dict[str, Any]] = None,
        epistemic_review: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        predictions_history = predictions_history or []
        mechanisms_history = mechanisms_history or []
        lessons_history = lessons_history or []
        principles_history = principles_history or []
        timeline_history = timeline_history or []
        epistemic_review = epistemic_review or {}

        days = max(len(predictions_history), 1)

        # Run EEF Evaluator Engine
        evaluator = EEFEvaluator(run_id=self.run_id, market_name=self.symbol)
        eef_dashboard = evaluator.evaluate_run(
            predictions_history=predictions_history,
            theories_history=[],
            mechanisms_history=mechanisms_history,
            lessons_history=lessons_history,
            principles_history=principles_history,
            contradictions_history=[],
        )

        overall_acc = 0.0
        if predictions_history:
            correct_count = sum(1 for p in predictions_history if p.get("is_correct", False))
            overall_acc = (correct_count / float(len(predictions_history))) * 100.0

        return {
            "symbol": self.symbol,
            "days": days,
            "date_range": f"Step 1 → Step {days}",
            "execution_hash": "eef_hash_v2",
            "git_commit": "HEAD",
            "llm_version": "llama3.2",
            "replay_version": "v3.0PersistentReflective",
            "story_summary": (
                f"Replay represents {days} days of reflective cognition experience on {self.symbol}. "
                f"Generated {len(predictions_history)} predictions, registered {len(mechanisms_history)} mechanisms, "
                f"and extracted {len(lessons_history)} active lessons."
            ),
            "metrics": {
                "accuracy": round(overall_acc, 2),
                "knowledge_debt": 0,
                "memory_usefulness": 0.65,
                "knowledge_coverage": 0.0,
                "prediction_drift": 0.0,
                "theory_drift": 0.0,
            },
            "timeline": timeline_history,
            "epistemic_review": epistemic_review,
            "eef_dashboard": eef_dashboard,
        }
