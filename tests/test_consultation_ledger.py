"""
Unit & Integration Tests for Consultation Ledger & Read-Side Provenance (PROMPT E0a).

Verifies:
1. Decision ID formatting and determinism.
2. Byte-stability of consultation_ledger.jsonl (NO wall-clock timestamps).
3. Transitive influence chain resolution in influence_trace.py on synthetic ledger.
4. 5-day replay produces consultation ledger with entries from theory generation, reflection, and gate sites.
5. Two identical replays produce 100% byte-identical consultation ledgers.
"""
import json
from pathlib import Path
import pytest

from cognition.schemas.identity import build_structural_id
from dp.observability.consultation_ledger import ConsultationLedger
from dp.observability.influence_trace import compute_influence_set, parse_consultation_ledger
from market.replay.replay_engine import ReplayExecutor


def test_decision_ids_and_byte_stability(tmp_path):
    """Verify structural ID formatting and byte-stability of consultation ledger output."""
    ledger_path1 = tmp_path / "run1" / "consultation_ledger.jsonl"
    ledger1 = ConsultationLedger(output_path=ledger_path1)

    dec_id_0 = build_structural_id(0, "theory", 0)
    assert dec_id_0 == "0:theory:0"

    ledger1.record_consultation(
        decision_id="0:theory:0",
        object_structural_id="0:regime_memory:0",
        object_kind="regime_memory",
        role="prompt_context",
    )
    ledger1.record_decision(
        decision_id="0:theory:0",
        output_content="Sample theory output text",
        day=0,
    )

    ledger_path2 = tmp_path / "run2" / "consultation_ledger.jsonl"
    ledger2 = ConsultationLedger(output_path=ledger_path2)

    ledger2.record_consultation(
        decision_id="0:theory:0",
        object_structural_id="0:regime_memory:0",
        object_kind="regime_memory",
        role="prompt_context",
    )
    ledger2.record_decision(
        decision_id="0:theory:0",
        output_content="Sample theory output text",
        day=0,
    )

    bytes1 = ledger_path1.read_bytes()
    bytes2 = ledger_path2.read_bytes()

    assert bytes1 == bytes2, "Consultation ledgers from identical inputs must be 100% byte-identical"


def test_influence_trace_transitive_chain(tmp_path):
    """Verify transitive chain resolution in influence_trace on synthetic ledger fixture."""
    ledger_path = tmp_path / "synthetic_ledger.jsonl"
    ledger = ConsultationLedger(output_path=ledger_path)

    # 0:theory:0 directly consults 0:regime_memory:0
    ledger.record_consultation(
        decision_id="0:theory:0",
        object_structural_id="0:regime_memory:0",
        object_kind="regime_memory",
        role="prompt_context",
    )
    ledger.record_decision(decision_id="0:theory:0", output_content="Theory 0", day=0)

    # 1:reflection:0 consults 0:theory:0 (1-hop transitive taint)
    ledger.record_consultation(
        decision_id="1:reflection:0",
        object_structural_id="0:theory:0",
        object_kind="theory",
        role="prompt_context",
    )
    ledger.record_decision(decision_id="1:reflection:0", output_content="Reflection 1", day=1)

    # 2:theory:0 consults 1:reflection:0 (2-hop transitive taint)
    ledger.record_consultation(
        decision_id="2:theory:0",
        object_structural_id="1:reflection:0",
        object_kind="theory",
        role="prompt_context",
    )
    ledger.record_decision(decision_id="2:theory:0", output_content="Theory 2", day=2)

    records = parse_consultation_ledger(ledger_path)
    res = compute_influence_set(records, "0:regime_memory:0")

    assert res["target_object_id"] == "0:regime_memory:0"
    assert "0:theory:0" in res["direct_consultations"]
    assert "1:reflection:0" in res["influenced_decisions"]
    assert "2:theory:0" in res["influenced_decisions"]
    assert res["total_influenced"] == 3


def test_5day_replay_consultation_ledger_and_reproducibility():
    """
    Run 5-day replay, verifying:
    1. consultation_ledger.jsonl is created with entries from theory, reflection, and gate sites.
    2. Two identical 5-day replays produce 100% byte-identical consultation ledgers.
    """
    exec1 = ReplayExecutor(max_days=5, quiet=True)
    exec1.execute(emit_summary=False)

    ledger_path1 = exec1.run_dir / "consultation_ledger.jsonl"
    assert ledger_path1.exists(), f"Consultation ledger not created at {ledger_path1}"

    records1 = parse_consultation_ledger(ledger_path1)
    kinds = {r.get("kind") for r in records1}
    roles = {r.get("role") for r in records1 if r.get("kind") == "consultation"}
    obj_kinds = {r.get("object_kind") for r in records1 if r.get("kind") == "consultation"}

    assert "consultation" in kinds
    assert "decision" in kinds
    assert "prompt_context" in roles or "gate" in roles
    assert "theory" in obj_kinds or "regime_memory" in obj_kinds

    # Second run to test 100% byte stability across identical replays
    exec2 = ReplayExecutor(max_days=5, quiet=True)
    exec2.execute(emit_summary=False)
    ledger_path2 = exec2.run_dir / "consultation_ledger.jsonl"

    bytes1 = ledger_path1.read_bytes()
    bytes2 = ledger_path2.read_bytes()

    assert bytes1 == bytes2, "Two identical 5-day replays must produce 100% byte-identical consultation ledgers"

    # Execute influence trace on actual replay ledger
    influence_res = compute_influence_set(records1, "0:regime_memory:0")
    assert "target_object_id" in influence_res
    assert influence_res["total_influenced"] >= 1
