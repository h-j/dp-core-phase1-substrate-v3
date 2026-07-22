"""
Test Constants Match Assertion for Edge Test Harness.

Verifies that pre-registration verification raises ValueError / FileNotFoundError on constant mismatch or document absence.
"""
import pytest

from experiments.edge_test.harness import PRE_REGISTERED_CONSTANTS, verify_preregistered_constants


def test_verify_preregistered_constants_passes():
    # Calling with valid constants passes without error
    verify_preregistered_constants(PRE_REGISTERED_CONSTANTS)


def test_verify_preregistered_constants_fails_on_mismatch():
    invalid_constants = dict(PRE_REGISTERED_CONSTANTS)
    invalid_constants["ALL_IN_ROUND_TRIP_COST_BPS"] = 15.0  # Mismatch!

    with pytest.raises(ValueError) as exc_info:
        verify_preregistered_constants(invalid_constants)

    assert "Pre-registered constant mismatch" in str(exc_info.value)
    assert "ALL_IN_ROUND_TRIP_COST_BPS" in str(exc_info.value)
