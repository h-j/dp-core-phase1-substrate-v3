from pathlib import Path

from bootstrap.operational_hypothesis_harness import (
    OperationalHypothesisHarness, compute_target_day)


def test_harness_is_deterministic_for_identical_artifacts():
    artifact_path = Path(__file__).resolve().parents[1] / "data" / "nifty_daily_3y.csv"

    first_run = OperationalHypothesisHarness(artifact_path=artifact_path).run()
    second_run = OperationalHypothesisHarness(artifact_path=artifact_path).run()

    assert (
        first_run["formation"]["accepted_hypotheses"]
        == second_run["formation"]["accepted_hypotheses"]
    )
    assert first_run["hypotheses"] == second_run["hypotheses"]
    assert first_run["evaluation"]["metrics"] == second_run["evaluation"]["metrics"]


def test_formation_window_is_limited_to_days_1_through_10():
    artifact_path = Path(__file__).resolve().parents[1] / "data" / "nifty_daily_3y.csv"
    harness = OperationalHypothesisHarness(artifact_path=artifact_path)

    formation = harness.load_replay_artifact().iloc[:10]

    assert len(formation) == 10
    assert formation["date"].iloc[0] == harness.load_replay_artifact()["date"].iloc[0]
    assert formation["date"].iloc[-1] == harness.load_replay_artifact()["date"].iloc[9]


def test_target_time_is_derived_from_activation_time_not_source_time():
    assert compute_target_day(activation_day=11, horizon=2) == 13
    assert compute_target_day(activation_day=12, horizon=3) == 15


def test_duplicate_and_tautology_candidates_are_rejected():
    artifact_path = Path(__file__).resolve().parents[1] / "data" / "nifty_daily_3y.csv"
    harness = OperationalHypothesisHarness(artifact_path=artifact_path)
    artifact = harness.load_replay_artifact()
    formation = artifact.iloc[:10]

    duplicate_candidate = {
        "hypothesis_id": "dup-1",
        "source_provenance": "day-1",
        "freeze_time": 10,
        "trigger_predicate": {
            "field": "volume_state",
            "operator": "==",
            "value": "elevated",
        },
        "scope_predicates": [
            {"field": "daily_return_pct", "operator": "<", "value": -0.5}
        ],
        "expected_effect_predicate": {
            "field": "return_3d",
            "operator": ">",
            "value": 0.0,
        },
        "evaluation_horizon": 2,
    }
    tautology_candidate = {
        "hypothesis_id": "taut-1",
        "source_provenance": "day-2",
        "freeze_time": 10,
        "trigger_predicate": {
            "field": "daily_return_pct",
            "operator": "==",
            "value": "daily_return_pct",
        },
        "scope_predicates": [],
        "expected_effect_predicate": {
            "field": "return_3d",
            "operator": ">",
            "value": 0.0,
        },
        "evaluation_horizon": 2,
    }

    seen = set()
    duplicate_result = harness.validate_candidate(duplicate_candidate, formation, seen)
    tautology_result = harness.validate_candidate(tautology_candidate, formation, seen)

    assert duplicate_result["status"] == "rejected"
    assert duplicate_result["rejection_reason"] == "KNOWN_EFFECT"
    assert tautology_result["status"] == "rejected"
    assert tautology_result["rejection_reason"] == "TAUTOLOGY"


def test_not_applicable_and_inconclusive_remain_distinct():
    artifact_path = Path(__file__).resolve().parents[1] / "data" / "nifty_daily_3y.csv"
    harness = OperationalHypothesisHarness(artifact_path=artifact_path)

    scope_false = harness._evaluate_predicate(
        {"field": "daily_return_pct", "operator": "<", "value": -10.0},
        0,
        harness.load_replay_artifact(),
    )
    scope_unknown = harness._evaluate_predicate(
        {"field": "does_not_exist", "operator": "==", "value": 1},
        0,
        harness.load_replay_artifact(),
    )

    assert scope_false["result"] == "FALSE"
    assert scope_unknown["result"] == "UNKNOWN"


def test_unavailable_future_targets_return_inconclusive():
    artifact_path = Path(__file__).resolve().parents[1] / "data" / "nifty_daily_3y.csv"
    harness = OperationalHypothesisHarness(artifact_path=artifact_path)
    artifact = harness.load_replay_artifact()
    row = artifact.iloc[20]

    result = harness._evaluate_hypothesis_on_day(
        hypothesis={
            "trigger_predicate": {
                "field": "volume_state",
                "operator": "==",
                "value": row["volume_state"],
            },
            "scope_predicates": [],
            "expected_effect_predicate": {
                "field": "return_3d",
                "operator": ">",
                "value": 0.0,
            },
            "evaluation_horizon": 30,
        },
        day_index=10,
        artifact=artifact,
    )

    assert result["evidence_outcome"] == "INCONCLUSIVE"
    assert result["reason_code"] == "TARGET_OUTSIDE_EVALUATION_WINDOW"
