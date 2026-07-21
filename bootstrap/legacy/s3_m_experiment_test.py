import math

import pytest

from flows.synthetic_experiment.s3_m_experiment import S3MEnvironment


def test_world_reproducibility():
    w1 = S3MEnvironment.generate_world(family=1, seed=42)
    w2 = S3MEnvironment.generate_world(family=1, seed=42)
    assert w1["experiences"] == w2["experiences"]
    assert w1["ex_ante_truth"] == w2["ex_ante_truth"]


def test_temporal_isolation():
    world = S3MEnvironment.generate_world(family=1, seed=42)
    formation = world["formation_experiences"]
    prospective = world["prospective_experiences"]

    # Verify exact split
    assert len(formation) == 500
    assert len(prospective) == 500
    assert [e["day"] for e in formation] == list(range(1, 501))
    assert [e["day"] for e in prospective] == list(range(501, 1001))


def test_exact_redundancy_construction():
    world = S3MEnvironment.generate_world(family=1, seed=42)
    f_map = world["feature_map"]
    exps = world["experiences"]

    v0 = f_map["F_0"]
    v1 = f_map["F_1"]

    matches = sum(1 for e in exps if e["features"][v0] == e["features"][v1])
    correlation = matches / len(exps)
    assert correlation >= 0.90


def test_subsumption_construction():
    world = S3MEnvironment.generate_world(family=2, seed=42)
    f_map = world["feature_map"]
    exps = world["experiences"]

    # Prop 1 general: F_0 == 1
    # Prop 2 subsumed: F_0 == 1 AND F_2 == 1
    v0 = f_map["F_0"]
    v2 = f_map["F_2"]

    p1_active = sum(1 for e in exps if e["features"][v0] == 1)
    p2_active = sum(
        1 for e in exps if e["features"][v0] == 1 and e["features"][v2] == 1
    )

    assert p1_active > p2_active
    assert p2_active > 0


def test_independent_signal_construction():
    world = S3MEnvironment.generate_world(family=3, seed=42)
    f_map = world["feature_map"]
    exps = world["experiences"]

    v0 = f_map["F_0"]
    v2 = f_map["F_2"]

    p_v0 = sum(1 for e in exps if e["features"][v0] == 1) / len(exps)
    p_v2 = sum(1 for e in exps if e["features"][v2] == 1) / len(exps)
    p_both = sum(
        1 for e in exps if e["features"][v0] == 1 and e["features"][v2] == 1
    ) / len(exps)

    # Product of marginals should be close to joint probability (within noise threshold)
    assert abs(p_v0 * p_v2 - p_both) < 0.05


def test_complementary_interaction_construction():
    world = S3MEnvironment.generate_world(family=4, seed=42)
    f_map = world["feature_map"]
    exps = world["experiences"]

    # F_0 and F_3
    v0 = f_map["F_0"]
    v3 = f_map["F_3"]

    p_y0_f0 = sum(
        1
        for e in exps
        if e["features"][v0] == 1
        and e["features"][v3] == 0
        and e["outcome"] == world["outcome_map"]["Y0"]
    ) / sum(1 for e in exps if e["features"][v0] == 1 and e["features"][v3] == 0)
    p_y0_f3 = sum(
        1
        for e in exps
        if e["features"][v0] == 0
        and e["features"][v3] == 1
        and e["outcome"] == world["outcome_map"]["Y0"]
    ) / sum(1 for e in exps if e["features"][v0] == 0 and e["features"][v3] == 1)
    p_y0_both = sum(
        1
        for e in exps
        if e["features"][v0] == 1
        and e["features"][v3] == 1
        and e["outcome"] == world["outcome_map"]["Y0"]
    ) / sum(1 for e in exps if e["features"][v0] == 1 and e["features"][v3] == 1)

    assert p_y0_both > p_y0_f0
    assert p_y0_both > p_y0_f3
    assert p_y0_both >= 0.75


def test_null_world_construction():
    world = S3MEnvironment.generate_world(family=6, seed=42)
    exps = world["experiences"]

    p_y0 = sum(1 for e in exps if e["outcome"] == world["outcome_map"]["Y0"]) / len(
        exps
    )
    assert abs(p_y0 - 0.50) < 0.05


def test_oracle_equivalence_logic():
    p1 = {
        "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 0},
        "scope": [{"field": "VAR_1", "operator": "==", "value": 1}],
        "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
    }
    p2 = {
        "trigger": {"field": "VAR_1", "operator": "==", "value": 1, "lag": 0},
        "scope": [{"field": "VAR_0", "operator": "==", "value": 1}],
        "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
    }
    # These are interaction equivalents
    assert S3MEnvironment.check_oracle_equivalence([p1], [p2])


def test_redundancy_metric():
    # Redundancy is activation overlap
    p1 = {
        "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 0},
        "scope": [],
        "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
    }
    p2 = {
        "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 0},
        "scope": [],
        "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
    }

    world = S3MEnvironment.generate_world(family=1, seed=42)
    exps = world["experiences"]

    # Overlap of identical propositions must be equal to their active count
    overlap_count = 0
    for exp in exps:
        active_count = 0
        if S3MEnvironment.is_prop_active(p1, exp, exps):
            active_count += 1
        if S3MEnvironment.is_prop_active(p2, exp, exps):
            active_count += 1
        if active_count > 1:
            overlap_count += active_count - 1

    p1_active = sum(1 for exp in exps if S3MEnvironment.is_prop_active(p1, exp, exps))
    assert overlap_count == p1_active


def test_explanatory_coverage_metric():
    p1 = {
        "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 0},
        "scope": [],
        "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
    }
    world = S3MEnvironment.generate_world(family=1, seed=42)
    exps = world["experiences"]

    covered = sum(1 for e in exps if S3MEnvironment.is_prop_active(p1, e, exps))
    coverage_rate = covered / len(exps)
    assert 0.0 < coverage_rate < 1.0


def test_false_discovery_metric():
    selected = [
        {
            "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 0},
            "scope": [],
            "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
        },
        {
            "trigger": {"field": "VAR_9", "operator": "==", "value": 1, "lag": 0},
            "scope": [],
            "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
        },
    ]
    oracle = [
        {
            "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 0},
            "scope": [],
            "target": {"field": "outcome", "operator": "==", "value": "VAL_B"},
        }
    ]
    # 1 of 2 is false discovery
    matched = 0
    for s in selected:
        if any(S3MEnvironment.check_proposition_match(s, o) for o in oracle):
            matched += 1
    fdr = (len(selected) - matched) / len(selected)
    assert fdr == 0.50


def test_m1_additive_behavior():
    world = S3MEnvironment.generate_world(family=1, seed=42)
    candidates = S3MEnvironment.generate_candidate_bank(
        family=1, feature_map=world["feature_map"], outcome_map=world["outcome_map"]
    )

    # M1 should select multiple redundant candidates if they both have individual positive utility
    selected = S3MEnvironment.select_m1(
        candidates, world["formation_experiences"], k_budget=3
    )
    assert len(selected) > 0


def test_m2_residual_behavior():
    world = S3MEnvironment.generate_world(family=1, seed=42)
    candidates = S3MEnvironment.generate_candidate_bank(
        family=1, feature_map=world["feature_map"], outcome_map=world["outcome_map"]
    )

    selected, _ = S3MEnvironment.select_m2(
        candidates, world["formation_experiences"], k_budget=3
    )
    # Under M2 sequential residual utility, we should not select two identical redundant propositions since residual utility drops to 0 or negative complexity penalty
    assert len(selected) >= 1
    if len(selected) > 1:
        # verify they are not identical trigger-scope matches
        assert not S3MEnvironment.check_proposition_match(selected[0], selected[1])


def test_m2_order_sensitivity_detection():
    # If propositions are highly overlapping/redundant, presenting them in different orders shifts their sequential utility.
    world = S3MEnvironment.generate_world(family=1, seed=42)
    candidates = S3MEnvironment.generate_candidate_bank(
        family=1, feature_map=world["feature_map"], outcome_map=world["outcome_map"]
    )
    # Run M2
    _, order_sensitive = S3MEnvironment.select_m2(
        candidates, world["formation_experiences"], k_budget=3
    )
    # The runner test checks that this flag is returnable
    assert isinstance(order_sensitive, bool)


def test_m3_overlap_penalty():
    world = S3MEnvironment.generate_world(family=1, seed=42)
    candidates = S3MEnvironment.generate_candidate_bank(
        family=1, feature_map=world["feature_map"], outcome_map=world["outcome_map"]
    )

    selected_low = S3MEnvironment.select_m3(
        candidates, world["formation_experiences"], lam=0.1, k_budget=3
    )
    selected_high = S3MEnvironment.select_m3(
        candidates, world["formation_experiences"], lam=10.0, k_budget=3
    )

    # High overlap penalty should restrict overlap, resulting in fewer or zero selected props if they overlap
    assert len(selected_high) <= len(selected_low)


def test_test_m4_conditional_marginal_calculation():
    world = S3MEnvironment.generate_world(family=3, seed=42)
    candidates = S3MEnvironment.generate_candidate_bank(
        family=3, feature_map=world["feature_map"], outcome_map=world["outcome_map"]
    )

    selected = S3MEnvironment.select_m4(
        candidates, world["formation_experiences"], k_budget=3
    )
    assert len(selected) >= 1


def test_m5_complexity_penalty():
    world = S3MEnvironment.generate_world(family=4, seed=42)
    candidates = S3MEnvironment.generate_candidate_bank(
        family=4, feature_map=world["feature_map"], outcome_map=world["outcome_map"]
    )

    selected_low = S3MEnvironment.select_m5(
        candidates, world["formation_experiences"], gamma=1.0, k_budget=3
    )
    selected_high = S3MEnvironment.select_m5(
        candidates, world["formation_experiences"], gamma=50.0, k_budget=3
    )

    # High gamma should heavily penalize complexity, selecting fewer or simpler candidates
    def get_comp(subset):
        return sum(
            1.0 + len(p["scope"]) + (1.0 if p["trigger"]["lag"] == 1 else 0.0)
            for p in subset
        )

    assert get_comp(selected_high) <= get_comp(selected_low)
