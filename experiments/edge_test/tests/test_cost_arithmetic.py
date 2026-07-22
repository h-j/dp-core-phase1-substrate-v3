"""
Test Cost Arithmetic for Edge Test Harness.

Verifies buy side (9.094 bps), sell side (11.394 bps), and round-trip (20.488 bps) cost calculations match spec.
"""
import math
import pytest

from experiments.edge_test.harness import PRE_REGISTERED_CONSTANTS, calculate_trade_execution_cost


def test_cost_arithmetic_exact_spec_values():
    # 1. Entry into Long (0 -> +1): Buy side cost
    cost_long_entry = calculate_trade_execution_cost(current_position=0, target_position=+1)
    assert math.isclose(cost_long_entry, 9.094, abs_tol=1e-4)

    # 2. Entry into Short (0 -> -1): Sell side cost
    cost_short_entry = calculate_trade_execution_cost(current_position=0, target_position=-1)
    assert math.isclose(cost_short_entry, 11.394, abs_tol=1e-4)

    # 3. Exit from Long to Flat (+1 -> 0): Sell side cost
    cost_long_exit = calculate_trade_execution_cost(current_position=+1, target_position=0)
    assert math.isclose(cost_long_exit, 11.394, abs_tol=1e-4)

    # 4. Exit from Short to Flat (-1 -> 0): Buy side cost
    cost_short_exit = calculate_trade_execution_cost(current_position=-1, target_position=0)
    assert math.isclose(cost_short_exit, 9.094, abs_tol=1e-4)

    # 5. Position Reversal (+1 -> -1): Full round-trip cost
    cost_reversal = calculate_trade_execution_cost(current_position=+1, target_position=-1)
    assert math.isclose(cost_reversal, 20.488, abs_tol=1e-4)

    # 6. Flat to Flat (0 -> 0): Zero cost
    cost_flat = calculate_trade_execution_cost(current_position=0, target_position=0)
    assert cost_flat == 0.0

    # 7. Hold Long (+1 -> +1): Zero cost
    cost_hold = calculate_trade_execution_cost(current_position=+1, target_position=+1)
    assert cost_hold == 0.0
