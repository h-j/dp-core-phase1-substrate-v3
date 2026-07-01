from cognition.schemas.base import CognitionBase


class Decision(CognitionBase):
    """
    An intermediate decision object between prediction and execution.
    """
    date: str
    prediction_direction: str
    action: str  # "long", "short", "hold", "wait"
    allocation_pct: float
    conviction_score: float
    reason: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "date": self.date,
            "prediction_direction": self.prediction_direction,
            "action": self.action,
            "allocation_pct": self.allocation_pct,
            "conviction_score": self.conviction_score,
            "reason": self.reason,
        }
