import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cognition.schemas.knowledge.open_question import QuestionStatus
from cognition.schemas.knowledge.principle import PrincipleStatus
from market.replay.prediction_probe import PredictionDirection
from market.replay.replay_engine import ReplayExecutor


def mock_generate(prompt: str, json_format: bool = False) -> str:
    prompt_lower = prompt.lower()
    if "concise abstraction" in prompt_lower:
        return "Constituted passive absorption regime."
    elif "target mechanism component to generalize" in prompt_lower:
        return json.dumps(
            {
                "statement": "Volume confirmation fails under range_bound regimes.",
                "applicability_filter": {"regime_subtype": "neutral"},
                "falsifiable_predictions": [
                    {
                        "target_component": "volume_confirmation",
                        "expected_status": "failed",
                        "applicability_filter": {"regime_subtype": "neutral"},
                    }
                ],
            }
        )
    elif "world model engine" in prompt_lower or "active principles" in prompt_lower:
        return json.dumps(
            {
                "narrative_summary": "System consolidated in range.",
                "regime_constraints": {
                    "range_bound": {"blocked_bias": "bullish", "max_confidence": 0.4}
                },
            }
        )
    elif "hidden causal mechanism" in prompt_lower:
        return json.dumps(
            {
                "claim": "Compression regime is driven by passive absorption; price remains range-bound despite volume expansion.",
                "mechanism": "absorption",
                "if_branch": {
                    "condition": "volatility compressed",
                    "action": "favor range persistence",
                },
                "else_branch": {
                    "condition": "participation surge",
                    "action": "favor breakout higher",
                },
                "unless": "liquidity evaporates",
                "falsified_if": "decisive close breaking HH/HL",
                "mechanism_components": [
                    {
                        "component_id": "volume_confirmation",
                        "description": "Volume confirmation fails in range",
                        "observable": "volume.daily_ratio",
                        "expected_behavior": "Volume fails to confirm",
                        "dependency": None,
                    }
                ],
                "falsification_conditions": [],
                "reuse_decision": "REJECTED",
            }
        )
    elif (
        "perform causal attribution analysis" in prompt_lower
        or "guidance" in prompt_lower
    ):
        return json.dumps(
            {
                "theory_id": "theory-123",
                "components_tested": ["volume_confirmation"],
                "components_passed": [],
                "components_failed": ["volume_confirmation"],
                "root_cause_component": "volume_confirmation",
                "attribution_reasoning": "Volume confirmation failed.",
                "mutation_guidance": "Mutate the range expectations.",
            }
        )
    return "{}"


def mock_validate(self, principle, prediction_history):
    from cognition.schemas.knowledge.principle import PrincipleStatus

    principle.status = PrincipleStatus.ACTIVE
    principle.support_count = 5
    principle.confidence = 0.8
    return principle


def mock_score_actual(self, prior_prediction, actual_observation):
    from market.replay.prediction_probe import PredictionEvaluation

    return PredictionEvaluation(
        prior_direction="range_bound",
        actual_direction="range_bound",
        direction_score=1.0,
        invalidation_triggered=False,
        confidence=0.5,
        invalidation="falsified",
    )


class TestKnowledgeIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch(
        "flows.knowledge_flow.knowledge_compression_engine.KnowledgeCompressionEngine.validate_principle",
        mock_validate,
    )
    @patch(
        "market.replay.prediction_probe.PredictionProbeGenerator.score_actual",
        mock_score_actual,
    )
    @patch("interfaces.ollama_client.OllamaClient.generate", side_effect=mock_generate)
    def test_e2e_replay_knowledge_integration(self, mock_gen):
        """Test the end-to-end replay execution integrated with Knowledge Formation loops."""
        # Setup run settings
        executor = ReplayExecutor(
            max_days=5, quiet=True, restart=True, lineage_debug=True
        )

        # Override data paths to use test run folders
        executor.base_data_snap_dir = Path(self.temp_dir) / "snapshots"
        executor.base_output_dir = Path(self.temp_dir) / "output"
        executor.replay_dir = Path(self.temp_dir) / "replay"
        executor._create_snapshot_dirs()

        # Execute the replay
        executor.execute(emit_summary=True)

        # Debug prints
        print("\nDEBUG prediction_history:")
        for r in executor.replay_analysis_engine.prediction_history:
            print(
                f"Date: {r.get('date')}, Tested: {r.get('components_tested')}, Failed: {r.get('components_failed')}, TheoryID: {r.get('theory_id')}"
            )

        # Assertions
        # 1. Verify repositories and engine components are initialized
        self.assertIsNotNone(executor.knowledge_repository)
        self.assertIsNotNone(executor.knowledge_compression_engine)
        self.assertIsNotNone(executor.world_model_engine)

        # 2. Check that periodic compression was triggered and principles were stored
        principles = executor.knowledge_repository.list_principles()
        print(f"DEBUG principles: {principles}")
        self.assertTrue(
            len(principles) > 0, "Principles should have been created and persisted."
        )

        # Assert structure of first principle
        p = principles[0]
        self.assertEqual(
            p.statement, "Volume confirmation fails under range_bound regimes."
        )
        self.assertEqual(len(p.falsifiable_predictions), 1)
        self.assertEqual(
            p.falsifiable_predictions[0].target_component, "volume_confirmation"
        )
        self.assertEqual(p.falsifiable_predictions[0].expected_status, "failed")

        # 3. Check that the World Model was consolidated
        latest_wm = executor.knowledge_repository.get_latest_world_model()
        self.assertIsNotNone(latest_wm)
        self.assertEqual(latest_wm.narrative_summary, "System consolidated in range.")
        self.assertIn("range_bound", latest_wm.regime_constraints)

        # 4. Check structured constraints
        constraints = latest_wm.regime_constraints["range_bound"]
        self.assertEqual(constraints["blocked_bias"], "bullish")
        self.assertEqual(constraints["max_confidence"], 0.4)


if __name__ == "__main__":
    unittest.main()
