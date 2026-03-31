import pytest
from src.math_engine.pivots import calculate_daily_pivots

def test_calculate_daily_pivots():
    # 1. Define previous day's data
    prev_high = 39500.0
    prev_low = 38500.0
    prev_close = 39000.0
    
    # 2. Run our function
    pivots = calculate_daily_pivots(prev_high, prev_low, prev_close)
    
    # 3. Assert the expected outcomes based on standard pivot math
    assert pivots['P'] == 39000.0, f"Expected Pivot to be 39000, got {pivots['P']}"
    assert pivots['R1'] == 39500.0, f"Expected R1 to be 39500, got {pivots['R1']}"
    assert pivots['S1'] == 38500.0, f"Expected S1 to be 38500, got {pivots['S1']}"
    assert pivots['R2'] == 40000.0, f"Expected R2 to be 40000, got {pivots['R2']}"
    assert pivots['S2'] == 38000.0, f"Expected S2 to be 38000, got {pivots['S2']}"
    
    print("✅ test_calculate_daily_pivots passed successfully.")

def test_invalid_pivot_inputs():
    # Test how the function handles zero or negative values where they shouldn't exist
    with pytest.raises(ValueError):
         calculate_daily_pivots(-100, 38500, 39000)
    
    with pytest.raises(ValueError):
         # High cannot be lower than Low
         calculate_daily_pivots(38000, 39000, 38500)