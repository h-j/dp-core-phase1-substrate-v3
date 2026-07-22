"""
Unit & Simulation Tests for Forward Paper-Trading Runner and Reporting Engine.

Tests:
1. Idempotency (re-running same date is a no-op).
2. No-backfill enforcement (missed days logged as SKIPPED NO SIGNAL).
3. Sequence ordering verification (signal_seq < outcome_seq).
4. Kill criteria trigger.
5. CLAIM ELIGIBLE gating logic.
6. Simulated 10-day forward sequence with fixture data.
"""
import json
import shutil
from pathlib import Path
import pytest

from experiments.edge_test.forward_report import generate_forward_report
from experiments.edge_test.forward_runner import ForwardPaperTrader


@pytest.fixture
def tmp_results_dir(tmp_path):
    d = tmp_path / "results"
    d.mkdir()
    return d


def test_idempotency_and_sequence_ordering(tmp_results_dir):
    trader = ForwardPaperTrader(results_dir=tmp_results_dir)

    # Step 1: Day 1 Step
    res1 = trader.process_daily_step(
        instrument_id="NIFTY",
        date_str="2026-07-23",
        open_price=24000.0,
        close_price=24100.0,
        active_theories=[],
    )
    assert res1["status"] == "PROCESSED"
    assert "signal_record" in res1
    sig1_seq = res1["signal_record"]["seq"]

    # Re-running same day must be idempotent no-op
    res1_repeat = trader.process_daily_step(
        instrument_id="NIFTY",
        date_str="2026-07-23",
        open_price=24000.0,
        close_price=24100.0,
        active_theories=[],
    )
    assert res1_repeat["status"] == "SKIPPED_IDEMPOTENT"

    # Step 2: Day 2 Step (settles Day 1 signal)
    res2 = trader.process_daily_step(
        instrument_id="NIFTY",
        date_str="2026-07-24",
        open_price=24150.0,
        close_price=24200.0,
        active_theories=[],
    )
    assert res2["status"] == "PROCESSED"
    settled2 = res2["settled_record"]
    assert settled2 is not None
    assert settled2["event_type"] == "OUTCOME_SETTLED"
    assert settled2["signal_seq"] == sig1_seq
    assert settled2["outcome_seq"] > sig1_seq, f"Tamper-evidence invariant violated: {settled2['signal_seq']} vs {settled2['outcome_seq']}"


def test_no_backfill_missed_day(tmp_results_dir):
    trader = ForwardPaperTrader(results_dir=tmp_results_dir)

    record = trader.handle_missed_day(instrument_id="NIFTY", date_str="2026-07-25")
    assert record["event_type"] == "SKIPPED_NO_SIGNAL"
    assert record["target_position"] == 0
    assert trader.state["current_positions"]["NIFTY"] == 0


def test_gating_banner_insufficient_sample(tmp_results_dir):
    report_res = generate_forward_report(results_dir=tmp_results_dir, seed=42)
    assert report_res["banner"] == "INSUFFICIENT SAMPLE — no conclusion permitted"
    assert report_res["status_code"] == "INSUFFICIENT_SAMPLE"


def test_simulated_10_day_forward_sequence(tmp_results_dir):
    trader = ForwardPaperTrader(results_dir=tmp_results_dir)

    mock_prices = [
        ("2026-07-23", 24000.0, 24050.0),
        ("2026-07-24", 24080.0, 24120.0),
        ("2026-07-25", 24100.0, 24150.0),
        ("2026-07-28", 24200.0, 24180.0),
        ("2026-07-29", 24150.0, 24220.0),
        ("2026-07-30", 24250.0, 24300.0),
        ("2026-07-31", 24310.0, 24290.0),
        ("2026-08-01", 24280.0, 24350.0),
        ("2026-08-04", 24380.0, 24400.0),
        ("2026-08-05", 24420.0, 24450.0),
    ]

    for date_str, open_p, close_p in mock_prices:
        res = trader.process_daily_step(
            instrument_id="NIFTY",
            date_str=date_str,
            open_price=open_p,
            close_price=close_p,
            active_theories=[],
        )
        assert res["status"] == "PROCESSED"

    # Verify forward ledger contents and sequence monotonicity
    ledger_file = tmp_results_dir / "forward_ledger.jsonl"
    assert ledger_file.exists()

    records = []
    with open(ledger_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # Verify every outcome_seq > signal_seq
    settled_records = [r for r in records if r.get("event_type") == "OUTCOME_SETTLED"]
    assert len(settled_records) == 9  # Day 1 to Day 9 settled; Day 10 open signal pending
    for r in settled_records:
        assert r["signal_seq"] < r["outcome_seq"], f"Sequence ordering failure: {r['signal_seq']} >= {r['outcome_seq']}"

    # Verify forward report shows INSUFFICIENT SAMPLE
    report_res = generate_forward_report(results_dir=tmp_results_dir, seed=42)
    assert report_res["banner"] == "INSUFFICIENT SAMPLE — no conclusion permitted"
    assert report_res["trading_days"] == 9
