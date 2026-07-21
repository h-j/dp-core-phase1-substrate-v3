"""
Epistemic Event Collector — Comprehensive diagnostics subscriber for DP-Core.

Captures epistemic events across observations, mechanisms, theories, confidence evolution,
predicate validation, contradictions, reflections, memory retrieval, and predictions.
"""
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class EpistemicEventCollector(BaseModel):
    """
    Structured collector for research diagnostics across all 9 cognition dimensions.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    observations: List[Dict[str, Any]] = Field(default_factory=list)
    mechanisms: List[Dict[str, Any]] = Field(default_factory=list)
    theories_created: List[Dict[str, Any]] = Field(default_factory=list)
    theories_retired: List[Dict[str, Any]] = Field(default_factory=list)
    theories_revived: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_reports: List[Dict[str, Any]] = Field(default_factory=list)
    predicate_evaluations: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    reflections: List[Dict[str, Any]] = Field(default_factory=list)
    memory_retrievals: List[Dict[str, Any]] = Field(default_factory=list)
    predictions: List[Dict[str, Any]] = Field(default_factory=list)

    def record_observation(self, date: str, regime: str, abstractions: List[str]):
        self.observations.append({"date": date, "regime": regime, "abstractions": abstractions})

    def record_mechanism(self, mechanism_id: str, description: str, confidence: float):
        self.mechanisms.append({"id": mechanism_id, "description": description, "confidence": confidence})

    def record_theory_created(self, theory_id: str, statement: str, confidence: float):
        self.theories_created.append({"id": theory_id, "statement": statement, "confidence": confidence})

    def record_theory_retired(self, theory_id: str, step: int, reason: str = ""):
        self.theories_retired.append({"id": theory_id, "step": step, "reason": reason})

    def record_theory_revived(self, theory_id: str, step: int, reason: str = ""):
        self.theories_revived.append({"id": theory_id, "step": step, "reason": reason})

    def record_confidence_report(self, report: Any):
        if hasattr(report, "model_dump"):
            data = report.model_dump()
        elif hasattr(report, "dict"):
            data = report.dict()
        elif isinstance(report, dict):
            data = report
        else:
            data = {"report_str": str(report)}
        self.confidence_reports.append(data)

    def record_predicate_evaluation(self, eval_res: Any):
        if hasattr(eval_res, "model_dump"):
            data = eval_res.model_dump()
        elif hasattr(eval_res, "dict"):
            data = eval_res.dict()
        elif isinstance(eval_res, dict):
            data = eval_res
        else:
            data = {"eval_str": str(eval_res)}
        self.predicate_evaluations.append(data)

    def record_contradiction(self, source_id: str, target_id: str, c_type: str, status: str):
        self.contradictions.append({
            "source_id": source_id,
            "target_id": target_id,
            "type": c_type,
            "status": status,
        })

    def record_reflection(self, summary: str, coherence_score: float, self_corrections: int = 0):
        self.reflections.append({
            "summary": summary,
            "coherence_score": coherence_score,
            "self_corrections": self_corrections,
        })

    def record_memory_retrieval(self, hit: bool, top_score: float, ignored_count: int):
        self.memory_retrievals.append({
            "hit": hit,
            "top_score": top_score,
            "ignored_count": ignored_count,
        })

    def record_prediction(self, date: str, prior_direction: str, actual_direction: str, is_correct: bool):
        self.predictions.append({
            "date": date,
            "prior_direction": prior_direction,
            "actual_direction": actual_direction,
            "is_correct": is_correct,
        })
