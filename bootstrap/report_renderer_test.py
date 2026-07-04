import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from market.replay.paper_trader import PaperTrader
from market.replay.report_renderer import (ReplayReportModel,
                                           ReplayReportRenderer)


class TestReportRenderer(unittest.TestCase):
    def test_report_builder_and_renderer_with_paper_trading(self):
        # 1. Mock PaperTrader
        mock_paper_trader = MagicMock(spec=PaperTrader)
        mock_paper_trader.get_summary.return_value = {
            "total_return_pct": 12.5,
            "sharpe_ratio": 1.8,
            "max_drawdown_pct": 4.2,
            "directional_accuracy_pct": 65.0,
            "commitment_accuracy_pct": 70.0,
            "avg_conviction_score": 0.72,
            "final_capital": 1125000.0,
        }
        mock_paper_trader.get_decision_intelligence_metrics.return_value = {
            "total_decisions": 10,
            "executed": 7,
            "skipped": 3,
            "high_conviction": 4,
            "low_conviction": 2,
            "decision_accuracy_pct": 75.0,
            "allocation_efficiency": 0.08,
            "avg_conviction": 0.68,
            "false_high_conviction_pct": 10.0,
            "false_low_conviction_pct": 5.0,
            "decision_stability": 0.85,
            "top_lineages": ["lineage_1", "lineage_2"],
            "top_principles": ["p_1", "p_2"],
            "top_memories": ["mem_1"],
            "top_harmful_contradictions": [],
            "knowledge_changes_count": 2,
            "avoided_bad_trades": 1,
            "ignored_opportunities": 1,
        }
        # Simulated trade log for equity curve mapping
        mock_paper_trader.starting_capital = 1000000.0
        mock_paper_trader.trade_log = [
            {"date": "2026-06-01", "cumulative_capital": 1020000.0},
            {"date": "2026-06-02", "cumulative_capital": 1010000.0},
            {"date": "2026-06-03", "cumulative_capital": 1050000.0},
        ]

        # 2. Mock ReplayExecutor
        mock_executor = MagicMock()
        mock_executor.market_name = "RELIANCE"
        mock_executor.paper_trader = mock_paper_trader
        mock_executor.knowledge_repository.list_principles.return_value = []
        mock_executor.knowledge_repository.get_latest_world_model.return_value = None
        mock_executor.knowledge_repository.list_open_questions.return_value = []
        mock_executor.knowledge_repository.list_evidence_gaps.return_value = []
        mock_executor.engine = MagicMock()
        mock_executor.engine.__len__.return_value = 3
        mock_executor.engine.get_date_range.return_value = (
            "2026-06-01",
            "2026-06-03",
        )

        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-06-01", "2026-06-02", "2026-06-03"]),
                "close": [1500.0, 1520.0, 1510.0],
                "delivery_pct_5d": [45.0, 48.0, 50.0],
                "fii_net": [100.0, -50.0, 200.0],
                "sector_zscore": [0.5, 0.8, 0.6],
            }
        )
        mock_executor.engine.data = df
        mock_executor.decision_traces = []
        mock_executor.epistemic_review = {}

        # 3. Mock AnalysisEngine
        mock_ae = MagicMock()
        mock_ae.analysis_engine.external_metrics = {}
        mock_ae.analysis_engine.prediction_history = [
            {"date": "2026-06-01", "prediction": {}, "prior_prediction_result": {}},
            {"date": "2026-06-02", "prediction": {}, "prior_prediction_result": {}},
            {"date": "2026-06-03", "prediction": {}, "prior_prediction_result": {}},
        ]
        mock_ae.analysis_engine.analyze.return_value = {"prediction_analysis": {}}

        # 4. Build Model
        report_builder = ReplayReportModel(mock_executor, mock_ae)
        report_data = report_builder.build_model()

        # Check that paper trading fields are present in the dictionary
        self.assertIn("paper_trading_summary", report_data)
        self.assertIn("decision_intelligence", report_data)
        self.assertEqual(report_data["paper_trading_summary"]["total_return_pct"], 12.5)
        self.assertEqual(report_data["decision_intelligence"]["total_decisions"], 10)

        # Check that equity_curve is populated inside chart_data
        self.assertIn("equity_curve", report_data["chart_data"])
        self.assertEqual(
            report_data["chart_data"]["equity_curve"],
            [1020000.0, 1010000.0, 1050000.0],
        )

        # 5. Render HTML
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_html_path = Path(tmp_dir) / "report.html"
            ReplayReportRenderer.render(report_data, output_html_path)
            self.assertTrue(output_html_path.exists())

            # Read and verify sections are present in compiled HTML
            with open(output_html_path, "r") as f:
                html_content = f.read()
                self.assertIn("Paper Trading Performance", html_content)
                self.assertIn("Decision Intelligence", html_content)
                self.assertIn("Paper Trading Equity", html_content)
                self.assertIn("y_equity", html_content)


if __name__ == "__main__":
    unittest.main()
