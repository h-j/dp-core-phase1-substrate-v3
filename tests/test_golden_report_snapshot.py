"""
Golden Report Snapshot Test (Milestone 6)
Ensures that ReplayReportRenderer renders complete HTML with Section 7 and 3-Tab navigation cleanly.
"""

from pathlib import Path
from market.replay.report_renderer import ReplayReportRenderer


def test_golden_report_rendering(tmp_path: Path):
    mock_data = {
        "symbol": "RELIANCE",
        "days": 10,
        "date_range": "2023-01-02 → 2023-01-13",
        "execution_hash": "golden_hash_123",
        "git_commit": "golden_commit_456",
        "llm_version": "llama3.2",
        "replay_version": "v3.0PersistentReflective",
        "story_summary": "Golden test replay story narrative.",
        "metrics": {
            "accuracy": 50.0,
            "knowledge_debt": 0,
            "memory_usefulness": 0.75,
            "knowledge_coverage": 0.80,
            "prediction_drift": 0.10,
            "theory_drift": 0.05,
        },
        "knowledge_health": {
            "knowledge_debt_bar": 10,
            "principle_coverage": 80.0,
            "reuse_rate": 50.0,
            "trust": 75.0,
        },
        "knowledge_lifecycle": {
            "candidate": 1,
            "emerging": 2,
            "trusted": 3,
            "canonical": 1,
            "retired": 0,
        },
        "timeline": [],
        "theory_evolution": [],
        "world_model": {},
        "chart_data": {},
        "decision_traces": [],
        "epistemic_review": {},
        "eef_dashboard": {
            "evidence_level_achieved": "LEVEL_4_MECHANISTIC",
            "verdict": "PARTIALLY_SUPPORTED",
            "verdict_reason": "Golden test verdict active.",
            "composite_scores": {"learning_score": 0.75, "evidence_score": 0.80},
            "layer_metrics": {
                "layer_1_structural": {"mechanism_creation_count": 5, "mechanism_reuse_rate": 0.50, "compression_ratio": 2.0},
                "layer_2_epistemic": {"ece": 0.10, "rce": 0.15, "explanation_stability_adaptive": 0.70, "nmdl": 0.85},
                "layer_3_generalization": {"cross_regime_survival_rate": 0.50, "active_principles_count": 2},
                "layer_4_reflective": {"mechanism_refinement_ratio": 0.60, "lessons_count": 4},
                "layer_5_world_model": {"graph_coherence_index": 0.80, "anti_correlational_counterfactual_acc": 0.55},
            },
        },
    }

    out_file = tmp_path / "golden_report.html"
    ReplayReportRenderer.render(mock_data, out_file)

    assert out_file.exists()
    html_content = out_file.read_text()

    assert "EEF v1.0 / MVF v1.0 Platform" in html_content
    assert "LEVEL_4_MECHANISTIC" in html_content
    assert "PARTIALLY_SUPPORTED" in html_content
    assert "switchTab('epistemic')" in html_content
    print("✓ Golden Report Snapshot Test Passed!")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
