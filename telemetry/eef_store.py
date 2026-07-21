"""
Telemetry Relational Store Coordinator for EEF v1.0 / MVF v1.0.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from contextlib import contextmanager
from memory.relational.postgres_client import SessionLocal
from memory.relational.models.eef_telemetry_models import (
    EEFBeliefMetricModel,
    EEFHistoricalTrendModel,
    EEFMechanismLifecycleModel,
    EEFMetricSnapshotModel,
    EEFReflectionMetricModel,
    EEFReplayRunModel,
    EEFTelemetryEventModel,
    EEFTheoryLifecycleModel,
)
from telemetry.events import BaseTelemetryEvent

logger = logging.getLogger("eef_store")


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class EEFTelemetryStore:
    """
    Manages persistence of EEF telemetry events, metric snapshots, and run manifests.
    """

    def __init__(self, run_dir: Optional[Path] = None):
        self.run_dir = run_dir

    def record_run_manifest(
        self,
        run_id: str,
        market_name: str,
        start_date: str,
        end_date: str,
        total_steps: int,
        git_commit: str = "unknown",
        evidence_level: str = "LEVEL_0_STRUCTURAL",
        learning_score: float = 0.0,
        evidence_score: float = 0.0,
    ):
        """Creates or updates replay run manifest record."""
        try:
            with get_db_session() as db:
                existing = db.query(EEFReplayRunModel).filter_by(run_id=run_id).first()
                if not existing:
                    run_obj = EEFReplayRunModel(
                        run_id=run_id,
                        market_name=market_name,
                        start_date=start_date,
                        end_date=end_date,
                        total_steps=total_steps,
                        git_commit=git_commit,
                        evidence_level_achieved=evidence_level,
                        learning_score=learning_score,
                        evidence_score=evidence_score,
                    )
                    db.add(run_obj)
                else:
                    existing.evidence_level_achieved = evidence_level
                    existing.learning_score = learning_score
                    existing.evidence_score = evidence_score
                    existing.total_steps = total_steps

                db.commit()
        except Exception as e:
            logger.error(f"Failed to record EEF run manifest: {e}", exc_info=True)

    def record_event(self, event: BaseTelemetryEvent):
        """Persists a raw telemetry event."""
        try:
            with get_db_session() as db:
                evt_obj = EEFTelemetryEventModel(
                    event_id=event.event_id,
                    run_id=event.run_id,
                    step=event.step,
                    event_type=event.event_type.value,
                    payload_json=event.model_dump(mode="json"),
                )
                db.add(evt_obj)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to record EEF telemetry event: {e}", exc_info=True)

    def record_metric_snapshot(self, snapshot_data: Dict[str, Any]):
        """Persists a step-level metric snapshot."""
        try:
            with get_db_session() as db:
                snap_id = str(uuid4())
                snap_obj = EEFMetricSnapshotModel(
                    snapshot_id=snap_id,
                    run_id=snapshot_data["run_id"],
                    step=snapshot_data["step"],
                    learning_score=snapshot_data.get("learning_score", 0.0),
                    evidence_score=snapshot_data.get("evidence_score", 0.0),
                    rce=snapshot_data.get("rce", 0.0),
                    r_exec=snapshot_data.get("r_exec", 0.0),
                    s_adaptive=snapshot_data.get("s_adaptive", 0.0),
                    nmdl=snapshot_data.get("nmdl", 1.0),
                    a_anti=snapshot_data.get("a_anti", 0.0),
                    ece=snapshot_data.get("ece", 0.0),
                    fragmentation_entropy=snapshot_data.get("fragmentation_entropy", 0.0),
                )
                db.add(snap_obj)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to record EEF metric snapshot: {e}", exc_info=True)

    def get_run_snapshots(self, run_id: str) -> List[Dict[str, Any]]:
        """Fetch all metric snapshots for a replay run."""
        try:
            with get_db_session() as db:
                rows = (
                    db.query(EEFMetricSnapshotModel)
                    .filter_by(run_id=run_id)
                    .order_by(EEFMetricSnapshotModel.step.asc())
                    .all()
                )
                return [
                    {
                        "step": r.step,
                        "learning_score": r.learning_score,
                        "evidence_score": r.evidence_score,
                        "rce": r.rce,
                        "r_exec": r.r_exec,
                        "s_adaptive": r.s_adaptive,
                        "nmdl": r.nmdl,
                        "a_anti": r.a_anti,
                        "ece": r.ece,
                        "fragmentation_entropy": r.fragmentation_entropy,
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.error(f"Failed to query EEF run snapshots: {e}", exc_info=True)
            return []
