from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MetricProvenanceRecord(BaseModel):
    """
    Immutable provenance metadata record establishing complete scientific traceability.
    """
    metric_name: str
    authoritative_producer: str
    source_function: str
    run_id: str
    execution_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "v1.0"

    def to_dict(self) -> dict:
        return self.model_dump()


class ProvenanceTracker:
    """
    Tracks and records provenance metadata for all key scientific metrics in a replay run.
    """

    def __init__(self, run_id: str = "UNKNOWN", execution_hash: str = "UNKNOWN"):
        self.run_id = run_id
        self.execution_hash = execution_hash
        self.records: List[MetricProvenanceRecord] = []

    def record(
        self,
        metric_name: str,
        producer: str,
        source_function: str,
        value: Optional[Any] = None,
    ) -> MetricProvenanceRecord:
        rec = MetricProvenanceRecord(
            metric_name=metric_name,
            authoritative_producer=producer,
            source_function=source_function,
            run_id=self.run_id,
            execution_hash=self.execution_hash,
        )
        self.records.append(rec)
        return rec

    def get_provenance_payload(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records]
