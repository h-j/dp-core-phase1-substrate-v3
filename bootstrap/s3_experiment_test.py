from flows.synthetic_experiment.s3_experiment import S3Environment


def test_s3_generate_world():
    for fam in [1, 2, 3, 4, 5]:
        world = S3Environment.generate_world(family=fam, seed=42)
        assert world["family"] == fam
        assert len(world["experiences"]) == 1000
        assert len(world["formation_experiences"]) == 500
        assert len(world["prospective_experiences"]) == 500

        # Verify features are anonymized
        for exp in world["experiences"]:
            for k in exp["features"].keys():
                assert k.startswith("VAR_")
            assert exp["outcome"] in ["VAL_A", "VAL_B"]

        # Verify ground truth
        assert "ex_ante_truth" in world
        if fam == 5:
            assert len(world["ex_ante_truth"]) == 0
        else:
            assert len(world["ex_ante_truth"]) > 0


def test_s3_compute_residual_evidence():
    world = S3Environment.generate_world(family=2, seed=42)
    res = S3Environment.compute_residual_evidence(
        world["formation_experiences"],
        world["active_beliefs"],
        world["feature_map"],
        world["outcome_map"],
    )

    assert "unexplained_associations" in res
    assert "belief_failure_associations" in res
    assert "temporal_lag_associations" in res

    # Verify values exist
    assert "VAL_A" in res["unexplained_associations"]
    assert "VAL_B" in res["unexplained_associations"]


def test_s3_validate_proposition():
    world = S3Environment.generate_world(family=1, seed=42)
    all_feats = [f"VAR_{i}" for i in range(10)]

    # Valid
    p_valid = {
        "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 0},
        "scope": [{"field": "VAR_1", "operator": "==", "value": 1}],
        "target": {"field": "outcome", "operator": "==", "value": "VAL_A"},
    }
    assert S3Environment.validate_proposition(
        p_valid, world["active_beliefs"], all_feats
    )

    # Duplicate of active belief (since active belief has VAR_trigger == 1 expects Y0, empty scope)
    # Our active_beliefs has VAR corresponding to F_0
    trigger_var = world["active_beliefs"][0]["trigger_var"]
    target_val = world["active_beliefs"][0]["target_val"]
    p_dup = {
        "trigger": {"field": trigger_var, "operator": "==", "value": 1, "lag": 0},
        "scope": [],
        "target": {"field": "outcome", "operator": "==", "value": target_val},
    }
    assert not S3Environment.validate_proposition(
        p_dup, world["active_beliefs"], all_feats
    )


def test_s3_evaluate_propositions():
    world = S3Environment.generate_world(family=3, seed=42)
    p = {
        "trigger": {"field": "VAR_0", "operator": "==", "value": 1, "lag": 1},
        "scope": [],
        "target": {"field": "outcome", "operator": "==", "value": "VAL_A"},
    }

    res = S3Environment.evaluate_propositions([p], world["prospective_experiences"])
    assert "raw_utility" in res
    assert "complexity_score" in res
    assert "adjusted_utility" in res

    # Complexity of lag-1 trigger is 2.0 (1.0 base + 1.0 lag)
    assert res["complexity_score"] == 2.0
