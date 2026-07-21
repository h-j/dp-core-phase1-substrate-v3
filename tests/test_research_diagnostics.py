"""
Unit tests for diagnostics/collectors.py and diagnostics/report_generator.py.
"""
import json
import pytest
from pathlib import Path

from diagnostics.collectors import EpistemicEventCollector
from diagnostics.report_generator import ResearchReportGenerator


def test_epistemic_event_collector_aggregates_events():
    collector = EpistemicEventCollector()

    # Record 9 domain events
    collector.record_observation(date="2023-01-01", regime="compressed", abstractions=["passive_absorption"])
    collector.record_mechanism(mechanism_id="MECH_001", description="Volume Confirmation", confidence=0.75)
    collector.record_theory_created(theory_id="TH_001", statement="Price range bound", confidence=0.70)
    collector.record_theory_retired(theory_id="TH_OLD", step=2, reason="Confidence decay")
    collector.record_theory_revived(theory_id="TH_REV", step=4, reason="Regime match")
    collector.record_confidence_report({"confidence_delta": 0.05, "contributing_factors": [{"delta": 0.05, "explanation": "Strong evidence"}]})
    collector.record_predicate_evaluation({"outcome": "confirmed"})
    collector.record_contradiction(source_id="TH_001", target_id="TH_002", c_type="EMPIRICAL", status="active")
    collector.record_reflection(summary="Coherent trend synthesis", coherence_score=0.80, self_corrections=1)
    collector.record_memory_retrieval(hit=True, top_score=0.85, ignored_count=2)
    collector.record_prediction(date="2023-01-02", prior_direction="bullish", actual_direction="bullish", is_correct=True)

    assert len(collector.observations) == 1
    assert len(collector.mechanisms) == 1
    assert len(collector.theories_created) == 1
    assert len(collector.theories_retired) == 1
    assert len(collector.theories_revived) == 1
    assert len(collector.confidence_reports) == 1
    assert len(collector.predicate_evaluations) == 1
    assert len(collector.contradictions) == 1
    assert len(collector.reflections) == 1
    assert len(collector.memory_retrievals) == 1
    assert len(collector.predictions) == 1


def test_research_report_generator_dict_json_markdown(tmp_path: Path):
    collector = EpistemicEventCollector()
    collector.record_observation("2023-01-01", "compressed", ["abs1"])
    collector.record_mechanism("MECH_1", "Desc", 0.8)
    collector.record_theory_created("TH_1", "Statement", 0.7)
    collector.record_confidence_report({"confidence_delta": 0.05, "contributing_factors": [{"delta": 0.05, "explanation": "Evidence alignment"}]})
    collector.record_predicate_evaluation({"outcome": "confirmed"})
    collector.record_memory_retrieval(hit=True, top_score=0.88, ignored_count=1)
    collector.record_contradiction("TH_1", "TH_2", "EMPIRICAL", "active")
    collector.record_prediction("2023-01-01", "bullish", "bullish", True)
    collector.record_reflection("Reflection summary", 0.85, 1)

    generator = ResearchReportGenerator()
    report_dict = generator.generate_report_dict(collector)

    # 1. Verify Dictionary Sections
    assert "replay_summary" in report_dict
    assert report_dict["replay_summary"]["observations_processed"] == 1
    assert report_dict["replay_summary"]["mechanisms_generated"] == 1
    assert report_dict["replay_summary"]["theories_created"] == 1

    assert "confidence_evolution" in report_dict
    assert report_dict["confidence_evolution"]["confidence_increases"] == 1

    assert "predicate_validation" in report_dict
    assert report_dict["predicate_validation"]["confirmed"] == 1

    assert "memory_diagnostics" in report_dict
    assert report_dict["memory_diagnostics"]["retrieval_usefulness"] == 0.88

    assert "contradictions" in report_dict
    assert report_dict["contradictions"]["active_contradiction_graph"] == 1

    assert "prediction_diagnostics" in report_dict
    assert report_dict["prediction_diagnostics"]["accuracy"] == 1.0

    assert "reflection_diagnostics" in report_dict
    assert report_dict["reflection_diagnostics"]["reflection_usefulness"] == 0.85

    # 2. Verify JSON Export
    json_file = tmp_path / "research_report.json"
    json_str = generator.export_json(collector, str(json_file))
    parsed_json = json.loads(json_str)
    assert parsed_json["replay_summary"]["observations_processed"] == 1
    assert json_file.exists()

    # 3. Verify Markdown Export
    md_file = tmp_path / "research_report.md"
    md_str = generator.export_markdown(collector, str(md_file))
    assert "# Research Diagnostics Replay Report" in md_str
    assert "## Replay Summary" in md_str
    assert "## Confidence Evolution" in md_str
    assert "## Predicate Validation" in md_str
    assert "## Memory Diagnostics" in md_str
    assert "## Contradictions" in md_str
    assert "## Prediction Diagnostics" in md_str
    assert "## Reflection Diagnostics" in md_str
    assert md_file.exists()
