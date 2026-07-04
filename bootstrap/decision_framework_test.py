import tempfile
import unittest
from pathlib import Path

from cognition.schemas.decision.decision import Decision
from cognition.schemas.decision.decision_record import DecisionRecord
from market.replay.conviction_sizer import ConvictionSizer
from market.replay.paper_trader import PaperTrader
from memory.decision.decision_journal import DecisionJournal


class TestDecisionSchemas(unittest.TestCase):
    def test_decision_and_record_init(self):
        d = Decision(
            date="2026-07-01",
            prediction_direction="higher",
            action="long",
            allocation_pct=0.12,
            conviction_score=0.75,
            reason="Strong trend persistence and principle support",
        )
        self.assertEqual(d.action, "long")
        self.assertEqual(d.allocation_pct, 0.12)

        record = DecisionRecord(
            prediction_date="2026-07-01",
            asset="RELIANCE",
            prediction="higher",
            decision=d,
            allocation=0.12,
            conviction_score=0.75,
            decision_reason="Strong trend persistence",
            supporting_principles=["P-100", "P-101"],
            conviction_breakdown={"base": 0.3, "confidence": 0.35, "empirical": 0.1},
        )
        self.assertEqual(record.asset, "RELIANCE")
        self.assertEqual(record.decision.action, "long")
        self.assertEqual(record.supporting_principles, ["P-100", "P-101"])

        # Dict roundtrip check
        r_dict = record.to_dict()
        self.assertEqual(r_dict["asset"], "RELIANCE")
        self.assertEqual(r_dict["decision"]["action"], "long")
        self.assertEqual(r_dict["conviction_breakdown"]["base"], 0.3)

        record_load = DecisionRecord.from_dict(r_dict)
        self.assertEqual(record_load.asset, "RELIANCE")
        self.assertEqual(record_load.decision.action, "long")
        self.assertEqual(record_load.conviction_breakdown["base"], 0.3)


class TestConvictionSizerExplainability(unittest.TestCase):
    def test_conviction_breakdown(self):
        sizer = ConvictionSizer()
        res = sizer.compute_sizer(
            calibrated_confidence=0.80,
            contradiction_pressure=0.10,
            empirical_confidence=0.70,
            principle_support=1,
            transition_pressure=0.20,
            prediction_direction="higher",
        )
        # Weights: confidence 0.35, empirical 0.20, principles 0.15, contradiction 0.20 (inv), regime 0.10 (inv)
        # Score = 0.35*0.80 + 0.20*0.90 + 0.20*0.70 + 0.15*1 + 0.10*0.80
        #       = 0.28 + 0.18 + 0.14 + 0.15 + 0.08 = 0.83
        # Breakdown Option B check:
        # base: 0.30
        # confidence: 0.35 * 0.8 = 0.28
        # empirical: 0.2 * 0.7 = 0.14
        # principles: 0.15 * 1.0 = 0.15
        # contradictions: -0.2 * 0.1 = -0.02
        # transition: -0.1 * 0.2 = -0.02
        # Sum = 0.30 + 0.28 + 0.14 + 0.15 - 0.02 - 0.02 = 0.83
        self.assertAlmostEqual(res.final_score, 0.83)
        breakdown = res.component_breakdown
        self.assertEqual(breakdown["base"], 0.30)
        self.assertAlmostEqual(breakdown["confidence"], 0.28)
        self.assertAlmostEqual(breakdown["empirical"], 0.14)
        self.assertAlmostEqual(breakdown["principle_support"], 0.15)
        self.assertAlmostEqual(breakdown["contradictions"], -0.02)
        self.assertAlmostEqual(breakdown["transition_pressure"], -0.02)

        # Unpacking compatibility check
        alloc, score = res
        self.assertEqual(alloc, res.allocation)
        self.assertEqual(score, res.final_score)


class TestDecisionJournal(unittest.TestCase):
    def test_save_load_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            journal = DecisionJournal(base_path=Path(tmpdir))

            d = Decision(
                date="2026-07-01",
                prediction_direction="higher",
                action="long",
                allocation_pct=0.10,
                conviction_score=0.7,
                reason="Test",
            )
            r = DecisionRecord(
                prediction_date="2026-07-01",
                asset="RELIANCE",
                prediction="higher",
                decision=d,
                allocation=0.10,
                conviction_score=0.7,
                decision_reason="Test",
            )
            journal.save(r)
            self.assertEqual(len(journal.records), 1)

            # Re-init journal to check disk load
            journal2 = DecisionJournal(base_path=Path(tmpdir))
            self.assertEqual(len(journal2.records), 1)
            loaded_rec = list(journal2.records.values())[0]
            self.assertEqual(loaded_rec.asset, "RELIANCE")
            self.assertEqual(loaded_rec.decision.action, "long")

            # Clear check
            journal2.clear()
            self.assertEqual(len(journal2.records), 0)
            self.assertEqual(len(list(journal2.journal_path.glob("*.json"))), 0)


class TestDecisionQualityMetrics(unittest.TestCase):
    def setUp(self):
        self.trader = PaperTrader()

    def test_metrics_evaluation(self):
        # 1. Correct trade with high conviction (>=0.6)
        d1 = Decision(
            date="2026-07-01",
            prediction_direction="higher",
            action="long",
            allocation_pct=0.12,
            conviction_score=0.75,
            reason="Good",
        )
        r1 = DecisionRecord(
            prediction_date="2026-07-01",
            asset="RELIANCE",
            prediction="higher",
            decision=d1,
            allocation=0.12,
            conviction_score=0.75,
            decision_reason="Good",
            calibrated_confidence=0.8,
        )
        self.trader.evaluate_decision_outcome(r1, 100.0, 105.0, 5.0, "2026-07-02")

        # 2. Incorrect trade with low conviction (<0.4)
        d2 = Decision(
            date="2026-07-02",
            prediction_direction="lower",
            action="short",
            allocation_pct=0.03,
            conviction_score=0.35,
            reason="Unsure",
        )
        r2 = DecisionRecord(
            prediction_date="2026-07-02",
            asset="RELIANCE",
            prediction="lower",
            decision=d2,
            allocation=0.03,
            conviction_score=0.35,
            decision_reason="Unsure",
            calibrated_confidence=0.3,
        )
        self.trader.evaluate_decision_outcome(r2, 100.0, 105.0, 5.0, "2026-07-03")

        # 3. Avoided bad trade (allocation 0.0, incorrect prediction direction)
        d3 = Decision(
            date="2026-07-03",
            prediction_direction="lower",
            action="hold",
            allocation_pct=0.0,
            conviction_score=0.45,
            reason="Override",
        )
        r3 = DecisionRecord(
            prediction_date="2026-07-03",
            asset="RELIANCE",
            prediction="lower",
            decision=d3,
            allocation=0.0,
            conviction_score=0.45,
            decision_reason="Override",
        )
        self.trader.evaluate_decision_outcome(r3, 100.0, 105.0, 5.0, "2026-07-04")

        summary = self.trader.get_decision_intelligence_metrics()
        self.assertEqual(summary["total_decisions"], 3)
        self.assertEqual(summary["executed"], 2)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(summary["high_conviction"], 1)
        self.assertEqual(summary["low_conviction"], 1)
        self.assertEqual(summary["avoided_bad_trades"], 1)  # (renamed or mapped)

        # Verify correctness of reflections
        self.assertIn("correct", r1.reflection_summary.lower())
        self.assertIn("incorrect", r2.reflection_summary.lower())
        self.assertTrue(
            "prediction" in r3.reflection_summary.lower()
            or "correct" in r3.reflection_summary.lower()
        )
