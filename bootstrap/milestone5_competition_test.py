import time
from flows.minimal_learning_cycle.competition import MLCCompetitionEngine
from flows.minimal_learning_cycle.experiment import MLCExperimentRunner
from flows.minimal_learning_cycle.synthetic_worlds import MLCSyntheticWorld


def test_competition_engine_logic():
    # 1. Test pairwise selection logic directly
    c1 = {
        "proposition": {"proposition_id": "p1", "complexity_cost": 1.0},
        "prospective_res": {
            "comparative_effect": 0.25,
            "prospective_adequacy": "PASS",
            "prospective_coverage": "PASS",
        },
    }
    
    # c2 has lower lift
    c2 = {
        "proposition": {"proposition_id": "p2", "complexity_cost": 1.0},
        "prospective_res": {
            "comparative_effect": 0.10,
            "prospective_adequacy": "PASS",
            "prospective_coverage": "PASS",
        },
    }
    
    # c3 has same lift but higher complexity cost
    c3 = {
        "proposition": {"proposition_id": "p3", "complexity_cost": 2.0},
        "prospective_res": {
            "comparative_effect": 0.25,
            "prospective_adequacy": "PASS",
            "prospective_coverage": "PASS",
        },
    }
    
    # c4 is non-compliant (failed coverage)
    c4 = {
        "proposition": {"proposition_id": "p4", "complexity_cost": 0.5},
        "prospective_res": {
            "comparative_effect": 0.40,
            "prospective_adequacy": "PASS",
            "prospective_coverage": "FAIL",
        },
    }
    
    # Compliance check: compliant c1 preferred over non-compliant c4 despite c4's higher lift
    assert MLCCompetitionEngine.select_best_candidate([c1, c4]) == c1
    
    # Lift check: c1 preferred over c2 due to higher lift
    assert MLCCompetitionEngine.select_best_candidate([c1, c2]) == c1
    
    # Signed Lift check: positive lift (+0.05) outranks negative lift (-0.25) under expected_direction = 1.0
    c_pos = {
        "proposition": {"proposition_id": "pos", "expected_direction": 1.0, "complexity_cost": 1.0},
        "prospective_res": {
            "comparative_effect": 0.05,
            "prospective_adequacy": "PASS",
            "prospective_coverage": "PASS",
        },
    }
    c_neg = {
        "proposition": {"proposition_id": "neg", "expected_direction": 1.0, "complexity_cost": 1.0},
        "prospective_res": {
            "comparative_effect": -0.25,
            "prospective_adequacy": "PASS",
            "prospective_coverage": "PASS",
        },
    }
    assert MLCCompetitionEngine.select_best_candidate([c_pos, c_neg]) == c_pos
    
    # Complexity tie-breaker: c1 preferred over c3 due to lower complexity cost
    assert MLCCompetitionEngine.select_best_candidate([c1, c3]) == c1
    
    print("✓ MLCCompetitionEngine logic checks verified successfully.")


def test_runner_with_competition_and_erc():
    # 2. Test MLCExperimentRunner with competition enabled
    runner = MLCExperimentRunner()
    
    # Override budgets to ensure enough for sibling candidates
    runner.erc.budgets = {
        "COMPILATION": 10000,
        "EVIDENCE": 10000,
        "VALIDATION": 10000,
    }
    
    # Generate a sample NIFTY/synthetic world (Family A, expects ADMIT)
    world = MLCSyntheticWorld.generate_world("A", seed=42)
    
    # Record starting budget levels
    start_comp = runner.erc.budgets["COMPILATION"]
    start_ev = runner.erc.budgets["EVIDENCE"]
    start_val = runner.erc.budgets["VALIDATION"]
    
    decision = runner.run_lifecycle_with_competition(world)
    
    # Check that decisions were recorded
    assert decision["decision"] == "ADMIT"
    
    # Check budget debits
    end_comp = runner.erc.budgets["COMPILATION"]
    end_ev = runner.erc.budgets["EVIDENCE"]
    end_val = runner.erc.budgets["VALIDATION"]
    
    # 3 candidates (1 correct + 2 confounders) should have debited:
    # 3 * 10 = 30 COMPILATION
    # 3 * 20 = 60 EVIDENCE
    # Only the selected winner (c1) goes to validation: 30 VALIDATION
    assert start_comp - end_comp == 30
    assert start_ev - end_ev == 60
    assert start_val - end_val == 30
    
    # Check that winning candidate is stored in propositions/belief memory
    assert len(runner.propositions) == 1
    assert runner.propositions[0]["proposition_id"].endswith("_c1")
    assert runner.propositions[0]["alternative_group_id"] is not None
    
    print("✓ MLCExperimentRunner competition run and budget tracking verified successfully.")


def test_selection_risk_and_prospective_validation():
    # Seed 3 is a known world where a confounding candidate (c5) wins retrospectively
    world = MLCSyntheticWorld.generate_world("C2", seed=3)
    
    # 1. Without Prospective Validation (Condition B)
    runner_b = MLCExperimentRunner()
    runner_b.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
    dec_b = runner_b.run_lifecycle_with_competition(world, num_confounders=5, enable_prospective_filter=False)
    
    winner_b = runner_b.propositions[0]["proposition_id"]
    # c5 is a confounding candidate (non-causal)
    assert "_c5" in winner_b
    # Winner's decision was DEFER based on retrospective lift
    assert dec_b["decision"] == "DEFER"
    
    # Check selection optimism: retro_effect is higher than prospective_effect
    winner_retro_metrics = next(m for m in runner_b.intrinsic_measurements if m["proposition_id"] == winner_b)
    winner_prospective_metrics = next(m for m in runner_b.prospective_measurements if m["proposition_id"] == winner_b)
    optimism = winner_retro_metrics["comparative_effect"] - winner_prospective_metrics["comparative_effect"]
    # Overstatement should be positive (Selection Optimism)
    assert optimism > 0.0
    
    # 2. With Prospective Validation (Condition C)
    runner_c = MLCExperimentRunner()
    runner_c.erc.budgets = {"COMPILATION": 1000, "EVIDENCE": 1000, "VALIDATION": 1000}
    dec_c = runner_c.run_lifecycle_with_competition(world, num_confounders=5, enable_prospective_filter=True)
    
    winner_c = runner_c.propositions[0]["proposition_id"]
    assert "_c5" in winner_c
    # Winning confounder is REJECTED prospectively because its Window 3 lift is low/negative
    assert dec_c["decision"] == "REJECT"
    
    print("✓ Selection Risk (Selection Optimism) and Prospective Validation protection verified on seed 3.")


if __name__ == "__main__":
    test_competition_engine_logic()
    test_runner_with_competition_and_erc()
    test_selection_risk_and_prospective_validation()
