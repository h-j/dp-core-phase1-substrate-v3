"""
Unit & Integration Tests for E1 Counterfactual Influence Experiment (PROMPT E1).
"""
import pytest
from experiments.run_e1_counterfactual_influence import run_e1_counterfactual_experiment


@pytest.mark.requires_postgres
def test_e1_counterfactual_influence_experiment():
    """Executes E1 Counterfactual Influence Experiment and verifies outcome criteria."""
    res = run_e1_counterfactual_experiment(max_days=5, target_object_id="0:theory:0")

    assert "outcome" in res
    assert res["outcome"] in {"PASS", "NULL", "INSTRUMENTATION FAIL"}
    assert res["days_run"] == 5
    assert len(res["unpredicted_divergence_set"]) == 0, f"Unpredicted divergence detected: {res['unpredicted_divergence_set']}"

    if res["outcome"] == "PASS":
        assert len(res["predicted_divergences"]) >= 1
    elif res["outcome"] == "NULL":
        assert len(res["observed_divergence_set"]) == 0

