import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from bootstrap.knowledge_integration_test import mock_generate, mock_validate
from market.replay.benchmark_runner import BenchmarkRunner


class TestBenchmarkRunner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch(
        "flows.knowledge_flow.knowledge_compression_engine.KnowledgeCompressionEngine.validate_principle",
        mock_validate,
    )
    @patch("interfaces.ollama_client.OllamaClient.generate", side_effect=mock_generate)
    def test_benchmark_runner_e2e(self, mock_gen):
        """
        Verify the BenchmarkRunner executes the multi-asset pipeline, clusters common failure modes,
        extracts recurring principles, computes generalization scores, and persists html/json/csv reports.
        """

        # Patch output directories and history logs inside self.temp_dir to ensure clean isolation
        def mock_init(exec_self, assets_list, days, force_refresh=False):
            exec_self.assets_list = assets_list
            exec_self.days = days
            exec_self.force_refresh = force_refresh
            exec_self.benchmark_id = "bench_test_run"
            exec_self.output_dir = Path(self.temp_dir) / "output"
            exec_self.latest_dir = Path(self.temp_dir) / "latest"
            exec_self.history_path = Path(self.temp_dir) / "benchmark_history.json"
            exec_self.output_dir.mkdir(parents=True, exist_ok=True)
            exec_self.latest_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(BenchmarkRunner, "__init__", mock_init):
            runner = BenchmarkRunner(
                assets_list=["RELIANCE", "TCS"], days=2, force_refresh=False
            )

            # Patch the ReplayExecutor paths to also map to temporary folders
            from market.replay.replay_engine import ReplayExecutor

            old_exec_init = ReplayExecutor.__init__

            def mock_executor_init(exec_self, *args, **kwargs):
                old_exec_init(exec_self, *args, **kwargs)
                exec_self.base_data_snap_dir = Path(self.temp_dir) / "snapshots"
                exec_self.base_output_dir = Path(self.temp_dir) / "exec_output"
                exec_self.replay_dir = Path(self.temp_dir) / "replay"
                exec_self._create_snapshot_dirs()

            with patch("market.replay.run.ReplayExecutor.__init__", mock_executor_init):
                benchmark_data = runner.run()

                # Verify report metadata
                self.assertEqual(benchmark_data["benchmark_id"], "bench_test_run")
                self.assertIn("generalization_score", benchmark_data)
                self.assertEqual(len(benchmark_data["assets_summary"]), 2)

                # Check output report files exist
                self.assertTrue(
                    (Path(self.temp_dir) / "output" / "benchmark_report.html").exists()
                )
                self.assertTrue(
                    (Path(self.temp_dir) / "output" / "benchmark_report.json").exists()
                )
                self.assertTrue(
                    (Path(self.temp_dir) / "output" / "benchmark_report.csv").exists()
                )

                # Check latest links folder contains output files
                self.assertTrue(
                    (Path(self.temp_dir) / "latest" / "benchmark_report.html").exists()
                )

                # Check longitudinal history log was populated
                self.assertTrue(
                    (Path(self.temp_dir) / "benchmark_history.json").exists()
                )
