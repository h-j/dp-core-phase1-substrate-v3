from flows.synthetic_experiment.s2_experiment import (S2Environment,
                                                      check_complexity_audit)


def test_s2_generate_world_structure():
    # Test generation for each family
    for family in [1, 2, 3, 4, 5]:
        world = S2Environment.generate_world(family=family, seed=42)
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

        # Verify eligible partitions
        partitions = world["eligible_partitions"]
        for p in partitions:
            assert p["partition_id"].startswith("PART_")
            assert p["feature"].startswith("VAR_")
            assert "col_0" in p["branch_A_stats"]
            assert "col_0" in p["branch_B_stats"]


def test_evidence_compilation_precision():
    world = S2Environment.generate_world(family=1, seed=42)
    formation = world["formation_experiences"]
    parent = world["parent_belief"]

    stats = S2Environment.compute_evidence(
        formation, parent["trigger_var"], parent["target_val"]
    )

    assert stats["col_0"] == stats["col_1"] + stats["col_2"]
    if stats["col_0"] > 0:
        assert abs(stats["col_3"] - stats["col_1"] / stats["col_0"]) < 1e-4
        assert abs(stats["col_5"] - (stats["col_3"] - stats["col_4"])) < 1e-4
    assert abs(stats["col_9"] - (stats["col_8"] - stats["col_7"])) < 1e-4


def test_operation_semantics():
    world = S2Environment.generate_world(family=3, seed=42)
    parent = world["parent_belief"]
    partitions = world["eligible_partitions"]
    formation = world["formation_experiences"]

    assert len(partitions) > 0
    part = partitions[0]
    part_id = part["partition_id"]

    # 1. PRESERVE
    beliefs_pres = S2Environment.execute_op(
        "PRESERVE", None, parent, partitions, formation
    )
    assert len(beliefs_pres) == 1
    assert beliefs_pres[0] == parent

    # 2. REJECT
    beliefs_rej = S2Environment.execute_op(
        "REJECT", None, parent, partitions, formation
    )
    assert len(beliefs_rej) == 0

    # 3. REVERSE
    beliefs_rev = S2Environment.execute_op(
        "REVERSE", None, parent, partitions, formation
    )
    assert len(beliefs_rev) == 1
    assert beliefs_rev[0]["trigger_var"] == parent["trigger_var"]
    assert beliefs_rev[0]["target_val"] != parent["target_val"]
    assert beliefs_rev[0]["scope"] == parent["scope"]

    # 4. RESTRICT
    beliefs_res = S2Environment.execute_op(
        "RESTRICT", part_id, parent, partitions, formation
    )
    assert len(beliefs_res) == 1
    assert beliefs_res[0]["trigger_var"] == parent["trigger_var"]
    assert beliefs_res[0]["target_val"] == parent["target_val"]
    assert beliefs_res[0]["scope"] == {part["feature"]: 1}

    # 5. SPLIT
    beliefs_split = S2Environment.execute_op(
        "SPLIT", part_id, parent, partitions, formation
    )
    assert len(beliefs_split) == 2
    assert beliefs_split[0]["trigger_var"] == parent["trigger_var"]
    assert beliefs_split[0]["scope"] == {part["feature"]: 1}
    assert beliefs_split[1]["trigger_var"] == parent["trigger_var"]
    assert beliefs_split[1]["scope"] == {part["feature"]: 0}


def test_complexity_audit_and_reasons():
    # Family 1 (PRESERVE) should generally pass easily unless activations are tiny
    world = S2Environment.generate_world(family=1, seed=42)
    audit = check_complexity_audit(world)
    # Either passes or fails for clear reasons, but let's check its output format
    assert "status" in audit
    assert "reasons" in audit
    assert "best_op" in audit
    assert "best_util" in audit
