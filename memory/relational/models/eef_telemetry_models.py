"""
SQLAlchemy ORM Models for EEF v1.0 / MVF v1.0 Relational Telemetry Store.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from memory.relational.base import Base


class EEFReplayRunModel(Base):
    __tablename__ = "eef_replay_runs"

    run_id = Column(String(64), primary_key=True)
    market_name = Column(String(32), nullable=False)
    start_date = Column(String(32), nullable=False)
    end_date = Column(String(32), nullable=False)
    total_steps = Column(Integer, nullable=False, default=0)
    git_commit = Column(String(40), nullable=False, default="unknown")
    evidence_level_achieved = Column(String(32), nullable=False, default="LEVEL_0_STRUCTURAL")
    learning_score = Column(Float, nullable=False, default=0.0)
    evidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EEFTelemetryEventModel(Base):
    __tablename__ = "eef_telemetry_events"

    event_id = Column(String(36), primary_key=True)
    run_id = Column(String(64), ForeignKey("eef_replay_runs.run_id", ondelete="CASCADE"), nullable=False)
    step = Column(Integer, nullable=False)
    event_type = Column(String(32), nullable=False)
    payload_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("idx_events_run_step", "run_id", "step"),)


class EEFMetricSnapshotModel(Base):
    __tablename__ = "eef_metric_snapshots"

    snapshot_id = Column(String(36), primary_key=True)
    run_id = Column(String(64), ForeignKey("eef_replay_runs.run_id", ondelete="CASCADE"), nullable=False)
    step = Column(Integer, nullable=False)
    learning_score = Column(Float, nullable=False, default=0.0)
    evidence_score = Column(Float, nullable=False, default=0.0)
    rce = Column(Float, nullable=False, default=0.0)
    r_exec = Column(Float, nullable=False, default=0.0)
    s_adaptive = Column(Float, nullable=False, default=0.0)
    nmdl = Column(Float, nullable=False, default=1.0)
    a_anti = Column(Float, nullable=False, default=0.0)
    ece = Column(Float, nullable=False, default=0.0)
    fragmentation_entropy = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (Index("idx_snapshots_run_step", "run_id", "step", unique=True),)


class EEFTheoryLifecycleModel(Base):
    __tablename__ = "eef_theory_lifecycle"

    theory_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("eef_replay_runs.run_id", ondelete="CASCADE"), nullable=False)
    lineage_id = Column(String(64), nullable=False)
    created_at_step = Column(Integer, nullable=False)
    retired_at_step = Column(Integer, nullable=True)
    survival_steps = Column(Integer, default=0)
    mutation_count = Column(Integer, default=0)
    status = Column(String(32), nullable=False, default="active")
    thesis = Column(Text, nullable=False, default="")
    initial_confidence = Column(Float, nullable=False, default=0.50)

    __table_args__ = (Index("idx_theory_lineage", "run_id", "lineage_id"),)


class EEFMechanismLifecycleModel(Base):
    __tablename__ = "eef_mechanism_lifecycle"

    mechanism_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("eef_replay_runs.run_id", ondelete="CASCADE"), nullable=False)
    canonical_name = Column(String(64), nullable=False)
    first_seen_step = Column(Integer, nullable=False)
    last_seen_step = Column(Integer, nullable=False)
    times_reused = Column(Integer, default=0)
    times_modified = Column(Integer, default=0)
    times_retired = Column(Integer, default=0)
    support_count = Column(Integer, default=0)
    falsification_count = Column(Integer, default=0)
    prediction_helped = Column(Integer, default=0)
    prediction_harmed = Column(Integer, default=0)
    status = Column(String(32), nullable=False, default="candidate")


class EEFBeliefMetricModel(Base):
    __tablename__ = "eef_belief_metrics"

    metric_id = Column(String(36), primary_key=True)
    run_id = Column(String(64), ForeignKey("eef_replay_runs.run_id", ondelete="CASCADE"), nullable=False)
    step = Column(Integer, nullable=False)
    empirical_confidence = Column(Float, nullable=False, default=0.50)
    regime_confidence = Column(Float, nullable=False, default=0.50)
    reflection_confidence = Column(Float, nullable=False, default=0.50)
    theoretical_coherence = Column(Float, nullable=False, default=0.50)
    contradiction_pressure = Column(Float, nullable=False, default=0.0)
    ece = Column(Float, nullable=False, default=0.0)
    rce = Column(Float, nullable=False, default=0.0)
    fragmentation_entropy = Column(Float, nullable=False, default=0.0)


class EEFReflectionMetricModel(Base):
    __tablename__ = "eef_reflection_metrics"

    reflection_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("eef_replay_runs.run_id", ondelete="CASCADE"), nullable=False)
    step = Column(Integer, nullable=False)
    trigger_reason = Column(Text, nullable=False, default="")
    pre_accuracy_5d = Column(Float, nullable=False, default=0.5)
    post_accuracy_5d = Column(Float, nullable=False, default=0.5)
    payoff_ratio = Column(Float, nullable=False, default=1.0)


class EEFHistoricalTrendModel(Base):
    __tablename__ = "eef_historical_trends"

    trend_id = Column(String(36), primary_key=True)
    run_id = Column(String(64), ForeignKey("eef_replay_runs.run_id", ondelete="CASCADE"), nullable=False)
    horizon_days = Column(Integer, nullable=False)
    accuracy_kendall_tau = Column(Float, nullable=False, default=0.0)
    accuracy_p_value = Column(Float, nullable=False, default=1.0)
    is_stationary = Column(Boolean, nullable=False, default=False)
    cusum_alert_triggered = Column(Boolean, nullable=False, default=False)
