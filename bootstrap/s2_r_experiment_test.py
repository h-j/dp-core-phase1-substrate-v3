from flows.synthetic_experiment.s2_r_experiment import S2REnvironment


def test_s2_r_generate_world_structure():
    # Test generation for each family
    for family in [1, 2, 3, 4, 5]:
        world = S2REnvironment.generate_world(family=family, seed=42)
        assert world["family"] == family
        assert world["seed"] == 42

        # Verify length of experiences
        assert len(world["experiences"]) == 1000
        assert len(world["formation_experiences"]) == 500
        assert len(world["prospective_experiences"]) == 500

        # Verify feature anonymization (no "F_" keys in experience features)
        for exp in world["experiences"]:
            for k in exp["features"].keys():
                assert k.startswith("VAR_")
                assert not k.startswith("F_")
            assert exp["outcome"] in ["VAL_A", "VAL_B"]

        # Verify parent belief structure
        parent = world["parent_belief"]
        assert parent["trigger_var"].startswith("VAR_")
        assert parent["target_val"] in ["VAL_A", "VAL_B"]
        assert parent["scope"] == {}

        # Verify ex-ante ground truth
        assert "ex_ante_op" in world
        assert world["ex_ante_op"] in [
            "PRESERVE",
            "REJECT",
            "RESTRICT",
            "SPLIT",
            "REVERSE",
        ]
        if world["ex_ante_op"] in ["RESTRICT", "SPLIT"]:
            assert world["ex_ante_part"] is not None
            assert world["ex_ante_part"].startswith("PART_")
        else:
            assert world["ex_ante_part"] is None


def test_repaired_evidence_control_group():
    world = S2REnvironment.generate_world(family=3, seed=42)
    formation = world["formation_experiences"]
    parent = world["parent_belief"]

    stats = S2REnvironment.compute_evidence(
        formation, parent["trigger_var"], parent["target_val"]
    )

    # col_0 should be activations
    assert stats["col_0"] == stats["col_1"] + stats["col_2"]

    # col_3 should be p_cond
    assert abs(stats["col_3"] - stats["col_1"] / stats["col_0"]) < 1e-4

    # col_4 should be control group target rate (trigger == 0)
    trigger_anon = parent["trigger_var"]
    target_val = parent["target_val"]
    control_exps = [e for e in formation if e["features"].get(trigger_anon) == 0]
    n_ctrl = len(control_exps)
    n_ctrl_target = sum(1 for e in control_exps if e["outcome"] == target_val)
    expected_p_control = n_ctrl_target / n_ctrl
    assert abs(stats["col_4"] - expected_p_control) < 1e-4

    # col_5 should be control-group lift
    assert abs(stats["col_5"] - (stats["col_3"] - stats["col_4"])) < 1e-4


def test_repaired_utility_complexity_adjusted():
    world = S2REnvironment.generate_world(family=4, seed=42)
    parent = world["parent_belief"]
    partitions = world["eligible_partitions"]
    formation = world["formation_experiences"]
    prospective = world["prospective_experiences"]

    assert len(partitions) > 0
    part = partitions[0]
    part_id = part["partition_id"]

    # 1. PRESERVE (1 belief, 0 scope conditions -> complexity_score = 1)
    beliefs_pres = S2REnvironment.execute_op(
        "PRESERVE", None, parent, partitions, formation
    )
    eval_pres = S2REnvironment.evaluate_beliefs(beliefs_pres, prospective)
    assert eval_pres["complexity_score"] == 1.0
    assert abs(eval_pres["adjusted_utility"] - (eval_pres["raw_utility"] - 5.0)) < 1e-4

    # 2. REJECT (0 beliefs -> complexity_score = 0)
    beliefs_rej = S2REnvironment.execute_op(
        "REJECT", None, parent, partitions, formation
    )
    eval_rej = S2REnvironment.evaluate_beliefs(beliefs_rej, prospective)
    assert eval_rej["complexity_score"] == 0.0
    assert eval_rej["adjusted_utility"] == 0.0

    # 3. RESTRICT (1 belief, 1 scope condition -> complexity_score = 2)
    beliefs_rest = S2REnvironment.execute_op(
        "RESTRICT", part_id, parent, partitions, formation
    )
    eval_rest = S2REnvironment.evaluate_beliefs(beliefs_rest, prospective)
    assert eval_rest["complexity_score"] == 2.0
    assert abs(eval_rest["adjusted_utility"] - (eval_rest["raw_utility"] - 10.0)) < 1e-4

    # 4. SPLIT (2 beliefs, each with 1 scope condition -> complexity_score = 4)
    beliefs_split = S2REnvironment.execute_op(
        "SPLIT", part_id, parent, partitions, formation
    )
    eval_split = S2REnvironment.evaluate_beliefs(beliefs_split, prospective)
    assert eval_split["complexity_score"] == 4.0
    assert (
        abs(eval_split["adjusted_utility"] - (eval_split["raw_utility"] - 20.0)) < 1e-4
    )
