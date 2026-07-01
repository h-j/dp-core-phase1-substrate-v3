import unittest
import tempfile
from pathlib import Path
from market.replay.conviction_sizer import ConvictionSizer
from market.replay.paper_trader import PaperTrader


class TestConvictionSizer(unittest.TestCase):
    def setUp(self):
        self.sizer = ConvictionSizer()

    def test_default_weights_sum(self):
        # Verify that conviction weights sum to 1.0
        total_weight = (
            self.sizer.weight_calibrated
            + self.sizer.weight_contradiction
            + self.sizer.weight_empirical
            + self.sizer.weight_principles
            + self.sizer.weight_regime
        )
        self.assertAlmostEqual(total_weight, 1.0)

    def test_compute_sizer_standard(self):
        # Calibrated: 0.6, Contradiction: 0.2, Empirical: 0.5, Principles: 1 (applied), Transition: 0.1
        # Inverse contradiction: 0.8
        # Regime stability: 0.9
        # Score = 0.35*0.6 + 0.20*0.8 + 0.20*0.5 + 0.15*1 + 0.10*0.9 = 0.21 + 0.16 + 0.10 + 0.15 + 0.09 = 0.71
        # Allocation = 0.02 + 0.71 * 0.13 = 0.02 + 0.0923 = 0.1123
        alloc, score = self.sizer.compute_sizer(
            calibrated_confidence=0.6,
            contradiction_pressure=0.2,
            empirical_confidence=0.5,
            principle_support=1,
            transition_pressure=0.1,
            prediction_direction="higher",
        )
        self.assertAlmostEqual(score, 0.71)
        self.assertAlmostEqual(alloc, 0.1123)

    def test_uncertain_prediction_override(self):
        # Verify allocation is zero if direction is uncertain
        alloc, score = self.sizer.compute_sizer(
            calibrated_confidence=0.8,
            contradiction_pressure=0.1,
            empirical_confidence=0.8,
            principle_support=1,
            transition_pressure=0.0,
            prediction_direction="uncertain",
        )
        self.assertEqual(alloc, 0.0)
        self.assertTrue(score > 0.0)

    def test_contradiction_override(self):
        # Verify allocation is zero if contradiction pressure exceeds threshold (0.7)
        alloc, score = self.sizer.compute_sizer(
            calibrated_confidence=0.8,
            contradiction_pressure=0.75,
            empirical_confidence=0.8,
            principle_support=1,
            transition_pressure=0.0,
            prediction_direction="higher",
        )
        self.assertEqual(alloc, 0.0)
        self.assertTrue(score > 0.0)


class TestPaperTrader(unittest.TestCase):
    def setUp(self):
        self.trader = PaperTrader(starting_capital=1000000.0)

    def test_initialization(self):
        self.assertEqual(self.trader.capital, 1000000.0)
        self.assertEqual(len(self.trader.trade_log), 0)

    def test_record_day_result_long_win(self):
        # Buy: 10% allocation. Capital = ₹10,00,000, trade val = ₹1,00,000.
        # Open price = 100, Close price = 105.
        # Slippage: 0.1%, entry_price = 100.1, exit_price = 104.895
        # Gross Return = (104.895 / 100.1) - 1.0 = 1.047902 - 1.0 = 0.047902
        # Fees: 2 * 0.05% = 0.10% * ₹1,00,000 = ₹100.
        # Net Return = ₹1,00,000 * 0.047902 - 100 = 4790.2 - 100 = 4690.2
        self.trader.record_day_result(
            date="2026-07-01",
            prediction="higher",
            conviction_score=0.7,
            allocation_pct=0.10,
            open_price=100.0,
            close_price=105.0,
            actual_daily_return_pct=5.0,
            components={},
        )
        self.assertEqual(len(self.trader.trade_log), 1)
        log = self.trader.trade_log[0]
        self.assertAlmostEqual(log["pnl"], 4690.21, places=1)
        self.assertAlmostEqual(self.trader.capital, 1004690.21, places=1)
        self.assertTrue(log["is_correct"])

    def test_record_day_result_short_loss(self):
        # Short: 10% allocation. Capital = ₹10,00,000, trade val = ₹1,00,000.
        # Open = 100, Close = 102 (so loss for short).
        # Slippage: 0.1%, entry_price = 99.9, exit_price = 102.102
        # Gross Return = 1.0 - (102.102 / 99.9) = 1.0 - 1.022042 = -0.022042
        # Fees = ₹100.
        # PnL = ₹1,00,000 * -0.022042 - 100 = -2204.2 - 100 = -2304.2
        self.trader.record_day_result(
            date="2026-07-01",
            prediction="lower",
            conviction_score=0.7,
            allocation_pct=0.10,
            open_price=100.0,
            close_price=102.0,
            actual_daily_return_pct=2.0,
            components={},
        )
        self.assertEqual(len(self.trader.trade_log), 1)
        log = self.trader.trade_log[0]
        self.assertAlmostEqual(log["pnl"], -2304.2, places=1)
        self.assertFalse(log["is_correct"])

    def test_range_bound_correctness(self):
        # Range bound trade (no allocation, but tracks correctness)
        # Move: 0.3% (< 0.5% range threshold) -> correct
        self.trader.record_day_result(
            date="2026-07-01",
            prediction="range_bound",
            conviction_score=0.5,
            allocation_pct=0.0,
            open_price=100.0,
            close_price=100.3,
            actual_daily_return_pct=0.3,
            components={},
        )
        self.assertTrue(self.trader.trade_log[0]["is_correct"])

        # Move: 0.6% (> 0.5% threshold) -> incorrect
        self.trader.record_day_result(
            date="2026-07-02",
            prediction="range_bound",
            conviction_score=0.5,
            allocation_pct=0.0,
            open_price=100.0,
            close_price=100.6,
            actual_daily_return_pct=0.6,
            components={},
        )
        self.assertFalse(self.trader.trade_log[1]["is_correct"])

    def test_summary_metrics(self):
        # Run two winning trades to calculate returns, Sharpe, drawdown, etc.
        self.trader.record_day_result(
            date="2026-07-01",
            prediction="higher",
            conviction_score=0.8,
            allocation_pct=0.10,
            open_price=100.0,
            close_price=105.0,
            actual_daily_return_pct=5.0,
            components={},
        )
        self.trader.record_day_result(
            date="2026-07-02",
            prediction="higher",
            conviction_score=0.8,
            allocation_pct=0.10,
            open_price=100.0,
            close_price=105.0,
            actual_daily_return_pct=5.0,
            components={},
        )

        summary = self.trader.get_summary()
        self.assertTrue(summary["total_return_pct"] > 0)
        self.assertEqual(summary["directional_accuracy_pct"], 100.0)
        self.assertEqual(summary["commitment_accuracy_pct"], 100.0)
        self.assertEqual(summary["avg_conviction_score"], 0.8)
        self.assertEqual(summary["max_drawdown_pct"], 0.0)

    def test_export_log_csv(self):
        # Verify exporting CSV file writes columns correctly
        self.trader.record_day_result(
            date="2026-07-01",
            prediction="higher",
            conviction_score=0.8,
            allocation_pct=0.10,
            open_price=100.0,
            close_price=105.0,
            actual_daily_return_pct=5.0,
            components={},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "paper_trade.csv"
            self.trader.export_log_csv(file_path)
            self.assertTrue(file_path.exists())

            # Read and verify headers
            with open(file_path, "r") as f:
                header_line = f.readline().strip()
                headers = header_line.split(",")
                self.assertIn("date", headers)
                self.assertIn("prediction", headers)
                self.assertIn("pnl", headers)
                self.assertNotIn("capital_before", headers)
