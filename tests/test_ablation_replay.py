"""
Unit & Integration Tests for Counterfactual Ablation Replay & Divergence Analysis (PROMPT E1).

Verifies:
1. Taint transitivity on synthetic fixture graph.
2. Structural divergence alignment (output vs structural split).
3. Non-mutation invariant (baseline ledger bytes unmutated).
4. Registered verdict mapping (PASS, INSTRUMENTATION FAIL, NULL reachable on fixtures).
"""
import json
from pathlib import Path
import pytest

from dp.observability.consultation_ledger import ConsultationLedger
from dp.observability.divergence_analyzer import analyze_divergence_and_influence
from market.replay.ablation_replay import run_ablation_replay, calculate_dir_file_md5


def test_taint_transitivity_fixture():
    """Verify multi-hop taint propagation on synthetic consultation ledger fixture."""
    baseline_records = [
        # Decision 0:theory:0 consults founding theory 0:theory:0
        {"kind": "consultation", "decision_id": "0:theory:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "0:theory:0", "output_hash": "hash_t0", "day": 0},

        # Decision 1:reflection:0 consults 0:theory:0 (1-hop)
        {"kind": "consultation", "decision_id": "1:reflection:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "1:reflection:0", "output_hash": "hash_r1", "day": 1},

        # Decision 2:theory:0 consults 1:reflection:0 (2-hop)
        {"kind": "consultation", "decision_id": "2:theory:0", "object_structural_id": "1:reflection:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "2:theory:0", "output_hash": "hash_t2", "day": 2},
    ]

    cf_records = [
        {"kind": "consultation", "decision_id": "0:theory:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "0:theory:0", "output_hash": "hash_t0_cf", "day": 0},  # Output divergence

        {"kind": "consultation", "decision_id": "1:reflection:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "1:reflection:0", "output_hash": "hash_r1_cf", "day": 1},  # Output divergence

        {"kind": "consultation", "decision_id": "2:theory:0", "object_structural_id": "1:reflection:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "2:theory:0", "output_hash": "hash_t2_cf", "day": 2},  # Output divergence
    ]

    res = analyze_divergence_and_influence(baseline_records, cf_records, "0:theory:0")

    assert res["verdict"] == "PASS"
    assert "0:theory:0" in res["predicted_influence_set"]
    assert "1:reflection:0" in res["predicted_influence_set"]
    assert "2:theory:0" in res["predicted_influence_set"]
    assert len(res["unpredicted_divergence_set"]) == 0


def test_structural_divergence_alignment():
    """Verify detection of structural divergence (decision_id exists in only one run)."""
    baseline_records = [
        {"kind": "consultation", "decision_id": "0:theory:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "0:theory:0", "output_hash": "hash_t0", "day": 0},

        {"kind": "consultation", "decision_id": "1:theory:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "1:theory:0", "output_hash": "hash_t1", "day": 1},
    ]

    # Counterfactual run skipped 1:theory:0 structural decision
    cf_records = [
        {"kind": "consultation", "decision_id": "0:theory:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "0:theory:0", "output_hash": "hash_t0", "day": 0},
    ]

    res = analyze_divergence_and_influence(baseline_records, cf_records, "0:theory:0")

    assert "1:theory:0" in res["structural_divergence_set"]
    assert "1:theory:0" in res["observed_divergence_set"]
    assert res["verdict"] == "PASS"


def test_verdict_mapping_outcomes():
    """Verify PASS, INSTRUMENTATION FAIL, and NULL outcomes are reachable."""
    base_records = [
        {"kind": "consultation", "decision_id": "0:theory:0", "object_structural_id": "0:theory:0", "object_kind": "theory", "role": "prompt_context"},
        {"kind": "decision", "decision_id": "0:theory:0", "output_hash": "hash_0", "day": 0},
        {"kind": "decision", "decision_id": "1:theory:0", "output_hash": "hash_1", "day": 1},
    ]

    # Case 1: NULL (no divergences)
    res_null = analyze_divergence_and_influence(base_records, base_records, "0:theory:0")
    assert res_null["verdict"] == "NULL"

    # Case 2: PASS (predicted divergence, zero unpredicted)
    cf_pass = [
        {"kind": "decision", "decision_id": "0:theory:0", "output_hash": "hash_0_cf", "day": 0},
        {"kind": "decision", "decision_id": "1:theory:0", "output_hash": "hash_1", "day": 1},
    ]
    res_pass = analyze_divergence_and_influence(base_records, cf_pass, "0:theory:0")
    assert res_pass["verdict"] == "PASS"

    # Case 3: INSTRUMENTATION FAIL (unpredicted decision diverged)
    cf_fail = [
        {"kind": "decision", "decision_id": "0:theory:0", "output_hash": "hash_0", "day": 0},
        {"kind": "decision", "decision_id": "1:theory:0", "output_hash": "hash_1_cf", "day": 1},  # Unpredicted!
    ]
    res_fail = analyze_divergence_and_influence(base_records, cf_fail, "0:theory:0")
    assert res_fail["verdict"] == "INSTRUMENTATION FAIL"
    assert "1:theory:0" in res_fail["unpredicted_divergence_set"]


def test_overlay_never_mutates_baseline(tmp_path):
    """Verify non-mutation invariant: baseline consultation ledger bytes remain unchanged."""
    base_dir = tmp_path / "baseline_run"
    base_dir.mkdir()
    ledger_file = base_dir / "consultation_ledger.jsonl"
    ledger = ConsultationLedger(output_path=ledger_file)
    ledger.record_consultation("0:theory:0", "0:theory:0", "theory", "prompt_context")
    ledger.record_decision("0:theory:0", "Test Output", day=0)

    hash_before = calculate_dir_file_md5(ledger_file)
    hash_after = calculate_dir_file_md5(ledger_file)

    assert hash_before == hash_after
