import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from flows.theory_flow.attribution import MechanismComponent
from flows.theory_flow.attribution_engine import AttributionEngine
from market.replay.replay_analysis import ReplayAnalysisEngine
from memory.lineage.theory_lineage import TheoryLineageEngine


class TestLearningAuditAlignment(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.lineage_path = Path(self.temp_dir) / "theory_lineage.json"

    def tearDown(self):
        if self.lineage_path.exists():
            os.remove(self.lineage_path)
        os.rmdir(self.temp_dir)

    def test_opposites_heuristic_comparative(self):
        """Verify opposites heuristic does not trigger false positive on comparative expected statements."""
        engine = AttributionEngine()

        # Scenario 1: Expected behavior contains both "up" and "down".
        # E.g. "Average volume on up days exceeds average volume on down days"
        exp = "Average volume on up days exceeds average volume on down days"

        comp1 = MechanismComponent(
            component_id="volume_confirmation",
            description="checks volume relationship",
            observable="volume comparison",
            expected_behavior=exp,
            dependency=None,
        )

        theory = MagicMock()
        theory.summary_structured = MagicMock()
        theory.summary_structured.model_dump.return_value = {
            "mechanism_components": [comp1.to_dict()]
        }

        obs = MagicMock()
        obs.observation_text = "The volume on down days was observed to be lower."
        obs.trend_state = "higher"

        res = engine.attribute(theory=theory, prediction="higher", observation=obs)
        # Should NOT fail
        self.assertEqual(len(res.components_failed), 0)

        # Scenario 2: Expected behavior contains only "up", observation has "down".
        comp2 = MechanismComponent(
            component_id="trend_check",
            description="checks trend direction",
            observable="trend state",
            expected_behavior="The trend should go up.",
            dependency=None,
        )
        theory2 = MagicMock()
        theory2.summary_structured = MagicMock()
        theory2.summary_structured.model_dump.return_value = {
            "mechanism_components": [comp2.to_dict()]
        }

        obs2 = MagicMock()
        obs2.observation_text = "The trend actually closed down."
        obs2.trend_state = "lower"

        res2 = engine.attribute(theory=theory2, prediction="higher", observation=obs2)
        # Should fail because of opposites heuristic
        self.assertIn("trend_check", res2.components_failed)

    def test_theory_retirement_mutate(self):
        """Verify parent theory is not kept perpetually active after mutation."""
        lineage = TheoryLineageEngine(self.lineage_path)

        # Create theory at step 1
        rec1 = lineage.create_theory(
            tid="theory-1",
            step=1,
            abstraction="Trend is rising.",
            confidence_state={"empirical_confidence": 0.8},
            lineage_id="theory-1",
        )
        self.assertEqual(rec1.last_seen_step, 1)

        # Mutate at step 2 to create a child
        child_rec = lineage.mutate_theory(
            tid="theory-1",
            new_abstraction="Trend is rising with volume support.",
            reason="new_evidence",
            step=2,
            confidence_state={"empirical_confidence": 0.85},
        )

        rec1_after = lineage.theories["theory-1"]
        # The parent's last_seen_step must remain 1 (not bumped to 2!)
        self.assertEqual(rec1_after.last_seen_step, 1)

        # Retire stale theories at step 3
        # Inactivity threshold is 6, so at step 3:
        # rec1's stale_age = 3 - 1 = 2
        # Since it is a parent (superseded), and stale_age >= 2, it should retire!
        retired = lineage.retire_stale_theories(
            step=3, contradiction_severity=0.0, current_record_id=child_rec.id
        )

        self.assertIn(rec1.id, [r.id for r in retired])
        self.assertEqual(rec1_after.status, "retired")

    def test_prediction_temporal_alignment(self):
        """Verify prediction history slices are correctly aligned temporally."""
        engine = ReplayAnalysisEngine(market_name="TEST_MARKET")

        # Record day 1: Predict "higher" for day 2
        engine.record_day(
            day_index=1,
            date="2026-01-01",
            confidence_state={"empirical_confidence": 0.5},
            contradiction_result={"score": 0.0},
            theory_summary="Theory 1",
            reflection_summary="",
            market_regime="up",
            prediction={"direction": "higher", "confidence": 0.8},
            prior_prediction_result=None,  # First day, no evaluation
            theory_usefulness={"score": 0.9, "label": "high"},
            transition_memory_hit=True,
        )

        # Record day 2: Predict "lower" for day 3. Outcome of day 1 is scored as correct (1.0).
        engine.record_day(
            day_index=2,
            date="2026-01-02",
            confidence_state={"empirical_confidence": 0.6},
            contradiction_result={"score": 0.1},
            theory_summary="Theory 2",
            reflection_summary="",
            market_regime="down",
            prediction={"direction": "lower", "confidence": 0.4},
            prior_prediction_result={
                "actual_direction": "higher",
                "direction_score": 1.0,
            },
            theory_usefulness={"score": 0.3, "label": "low"},
            transition_memory_hit=False,
        )

        # Record day 3: Predict "higher" for day 4. Outcome of day 2 is scored as incorrect (0.0).
        engine.record_day(
            day_index=3,
            date="2026-01-03",
            confidence_state={"empirical_confidence": 0.4},
            contradiction_result={"score": 0.2},
            theory_summary="Theory 3",
            reflection_summary="",
            market_regime="up",
            prediction={"direction": "higher", "confidence": 0.9},
            prior_prediction_result={
                "actual_direction": "higher",
                "direction_score": 0.0,
            },
            theory_usefulness={"score": 0.8, "label": "high"},
            transition_memory_hit=True,
        )

        # Analyze predictions
        metrics = engine._analyze_predictions()

        # Scored predictions count = 2 (day 1 prediction evaluated on day 2, day 2 prediction evaluated on day 3)
        self.assertEqual(metrics["scored_predictions"], 2)

        # Overall accuracy = 1 / 2 = 50%
        self.assertEqual(metrics["accuracy"], 0.5)

        # accuracy_by_direction should map "higher" prediction (day 1, confidence 0.8, correct) -> 1.0 accuracy
        # and "lower" prediction (day 2, confidence 0.4, incorrect) -> 0.0 accuracy
        dir_metrics = metrics["accuracy_by_direction"]
        self.assertEqual(dir_metrics["higher"]["count"], 1)
        self.assertEqual(dir_metrics["higher"]["accuracy"], 1.0)
        self.assertEqual(dir_metrics["higher"]["avg_confidence"], 0.8)

        self.assertEqual(dir_metrics["lower"]["count"], 1)
        self.assertEqual(dir_metrics["lower"]["accuracy"], 0.0)
        self.assertEqual(dir_metrics["lower"]["avg_confidence"], 0.4)

        # Verify transition memory hits count
        self.assertEqual(engine.transition_memory_hits, 2)


if __name__ == "__main__":
    unittest.main()
