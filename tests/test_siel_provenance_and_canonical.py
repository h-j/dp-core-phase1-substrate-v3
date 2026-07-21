import pytest
from telemetry.siel.provenance import ProvenanceTracker, MetricProvenanceRecord
from telemetry.siel.canonical_report import CanonicalReplayReport, ReportMetadata, NarrativeSummary


def test_provenance_tracker_records_metrics():
    tracker = ProvenanceTracker(run_id="run_123", execution_hash="abc456")
    rec = tracker.record(
        metric_name="learning_score",
        producer="EEFEvaluator",
        source_function="EEFEvaluator.evaluate_run()",
        value=0.45,
    )

    assert rec.metric_name == "learning_score"
    assert rec.authoritative_producer == "EEFEvaluator"
    assert rec.run_id == "run_123"
    assert rec.execution_hash == "abc456"

    payload = tracker.get_provenance_payload()
    assert len(payload) == 1
    assert payload[0]["metric_name"] == "learning_score"


def test_canonical_replay_report_immutability():
    meta = ReportMetadata(
        symbol="RELIANCE",
        days=10,
        date_range="2023-01-02 -> 2023-01-13",
        execution_hash="hash123",
        git_commit="commit456",
        llm_version="llama3.2",
        replay_version="v3.0",
    )
    narrative = NarrativeSummary(
        story_text="Summary text",
        theories_generated=10,
        propositions_compiled=10,
        lessons_extracted=6,
        principles_active=0,
        evidence_gaps_count=6,
    )
    report = CanonicalReplayReport(
        metadata=meta,
        narrative=narrative,
        metrics_kpi={"accuracy": 0.0},
    )

    assert report.metadata.symbol == "RELIANCE"
    assert report.narrative.theories_generated == 10

    # Attempt mutation on frozen Pydantic model
    with pytest.raises(Exception):
        report.metadata.symbol = "TATAMOTORS"
