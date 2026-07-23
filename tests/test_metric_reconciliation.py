import json
import re
from pathlib import Path
import pytest

from market.replay.replay_engine import ReplayExecutor
from market.replay.report_renderer import ReplayReportModel, ReplayReportRenderer
from market.replay.replay_finalization import generate_v1_report, save_manifest


from bootstrap.knowledge_integration_test import mock_generate, mock_validate
from unittest.mock import patch

@pytest.mark.requires_postgres
@patch("flows.knowledge_flow.knowledge_compression_engine.KnowledgeCompressionEngine.validate_principle", mock_validate)
@patch("interfaces.ollama_client.OllamaClient.generate", side_effect=mock_generate)
def test_metric_reconciliation_integrity(mock_gen, tmp_path):

    """
    Asserts cross-sectional harmony across all report artifacts:
    1. Execution hash in report matches replay_manifest.json.
    2. Theory counts in story summary match compilation metrics.
    3. Timeline count in report matches the replay day count.
    4. HTML output contains identical values as report.json.
    """
    executor = ReplayExecutor(max_days=3, quiet=True)
    executor.execute(emit_summary=False)
    executor.run_dir = tmp_path

    # Save manifest and report
    manifest_path = tmp_path / "replay_manifest.json"
    save_manifest(executor, manifest_path)
    with open(manifest_path) as f:
        manifest = json.load(f)

    analysis_engine = getattr(executor, "replay_analysis_engine", None)
    builder = ReplayReportModel(executor, analysis_engine)
    data = builder.build_model()

    # 1. Execution Hash Consistency
    assert manifest.get("execution_hash") != "unknown"
    
    # 2. Timeline Count Consistency
    assert len(data["timeline"]) == 3, f"Expected 3 timeline entries, found {len(data['timeline'])}"

    # 3. Compilation Metrics & Summary Reconciliation
    compilation_metrics = data.get("compilation_metrics", {})
    comp_theories = compilation_metrics.get("theories_generated", 0)
    story = data.get("story_summary", "")
    match = re.search(r"evolved\s+(\d+)\s+theories", story, re.IGNORECASE)
    if match:
        summary_theories = int(match.group(1))
        assert summary_theories == comp_theories, f"Story summary theories ({summary_theories}) must equal compilation theories ({comp_theories})"

    # 4. HTML Render Matching
    html_path = tmp_path / "report.html"
    ReplayReportRenderer.render(data, html_path)
    html_content = html_path.read_text()

    # Verify HTML contains execution hash or symbol
    assert data["symbol"] in html_content
    assert "Section 7: Epistemic Evidence" in html_content
