# tests/test_pivots.py

import pytest

from src.math_engine.pivots import calculate_daily_pivots


def test_calculate_daily_pivots_success():
    """Tests if standard daily floor pivots are calculated and rounded accurately."""
    high = 45000.0
    low = 44000.0
    close = 44500.0

    pivots = calculate_daily_pivots(high, low, close)

    # Validate that standard mathematical combinations evaluate to accurate floats
    assert pivots["P"] == 44500.0
    assert pivots["R1"] == 45000.0
    assert pivots["S1"] == 44000.0
    assert pivots["R2"] == 45500.0
    assert pivots["S2"] == 43500.0


def test_calculate_daily_pivots_invalid_bounds():
    """Verifies that the pivot calculator throws explicit errors on negative or zero prices."""
    with pytest.raises(ValueError, match="Price values must be greater than zero."):
        calculate_daily_pivots(0, 44000, 44500)

    with pytest.raises(ValueError, match="Price values must be greater than zero."):
        calculate_daily_pivots(45000, -100, 44500)


def test_calculate_daily_pivots_inversion():
    """Verifies that a structural error is raised if high price is lower than low price."""
    with pytest.raises(ValueError, match="High price cannot be lower than the low price."):
        calculate_daily_pivots(44000, 45000, 44500)
