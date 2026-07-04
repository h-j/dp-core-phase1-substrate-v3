from typing import Dict, List, Optional

from cognition.schemas.base import CognitionBase
from cognition.schemas.decision.decision import Decision


class DecisionRecord(CognitionBase):
    """
    Complete immutable snapshot of a cognitive decision and its metadata/outcomes.
    """

    prediction_date: str
    evaluation_date: Optional[str] = None
    asset: str
    prediction: str
    decision: Decision
    allocation: float
    conviction_score: float
    decision_reason: str
    supporting_lineages: List[str] = []
    supporting_principles: List[str] = []
    retrieved_memories: List[str] = []
    novelty_score: float = 0.0
    contradiction_pressure: float = 0.0
    transition_pressure: float = 0.0
    calibrated_confidence: float = 0.0
    empirical_confidence: float = 0.0
    reflection_confidence: float = 0.0
    regime_confidence: float = 0.0
    expected_scenarios: List[str] = []
    actual_outcome: Optional[str] = None
    decision_result: Optional[str] = (
        None  # "correct", "incorrect", "avoided_bad_trade", "ignored_opportunity", "neutral"
    )
    pnl: float = 0.0
    reflection_summary: Optional[str] = None
    knowledge_changes: List[str] = []
    conviction_breakdown: Dict[str, float] = {}

    @property
    def decision_id(self) -> str:
        return self.id

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "prediction_date": self.prediction_date,
            "evaluation_date": self.evaluation_date,
            "asset": self.asset,
            "prediction": self.prediction,
            "decision": self.decision.to_dict() if self.decision else None,
            "allocation": self.allocation,
            "conviction_score": self.conviction_score,
            "decision_reason": self.decision_reason,
            "supporting_lineages": self.supporting_lineages,
            "supporting_principles": self.supporting_principles,
            "retrieved_memories": self.retrieved_memories,
            "novelty_score": self.novelty_score,
            "contradiction_pressure": self.contradiction_pressure,
            "transition_pressure": self.transition_pressure,
            "calibrated_confidence": self.calibrated_confidence,
            "empirical_confidence": self.empirical_confidence,
            "reflection_confidence": self.reflection_confidence,
            "regime_confidence": self.regime_confidence,
            "expected_scenarios": self.expected_scenarios,
            "actual_outcome": self.actual_outcome,
            "decision_result": self.decision_result,
            "pnl": self.pnl,
            "reflection_summary": self.reflection_summary,
            "knowledge_changes": self.knowledge_changes,
            "conviction_breakdown": self.conviction_breakdown,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DecisionRecord":
        # Handle conversion from dict for nested Decision object
        d_data = data.get("decision")
        decision_obj = None
        if isinstance(d_data, dict):
            decision_obj = Decision(**d_data)
        elif isinstance(d_data, Decision):
            decision_obj = d_data

        record = cls(
            id=data.get("id"),
            prediction_date=data.get("prediction_date"),
            evaluation_date=data.get("evaluation_date"),
            asset=data.get("asset"),
            prediction=data.get("prediction"),
            decision=decision_obj,
            allocation=data.get("allocation", 0.0),
            conviction_score=data.get("conviction_score", 0.0),
            decision_reason=data.get("decision_reason", ""),
            supporting_lineages=data.get("supporting_lineages", []),
            supporting_principles=data.get("supporting_principles", []),
            retrieved_memories=data.get("retrieved_memories", []),
            novelty_score=data.get("novelty_score", 0.0),
            contradiction_pressure=data.get("contradiction_pressure", 0.0),
            transition_pressure=data.get("transition_pressure", 0.0),
            calibrated_confidence=data.get("calibrated_confidence", 0.0),
            empirical_confidence=data.get("empirical_confidence", 0.0),
            reflection_confidence=data.get("reflection_confidence", 0.0),
            regime_confidence=data.get("regime_confidence", 0.0),
            expected_scenarios=data.get("expected_scenarios", []),
            actual_outcome=data.get("actual_outcome"),
            decision_result=data.get("decision_result"),
            pnl=data.get("pnl", 0.0),
            reflection_summary=data.get("reflection_summary"),
            knowledge_changes=data.get("knowledge_changes", []),
            conviction_breakdown=data.get("conviction_breakdown", {}),
        )
        if "created_at" in data and data["created_at"]:
            from datetime import datetime

            try:
                record.created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                pass
        return record
