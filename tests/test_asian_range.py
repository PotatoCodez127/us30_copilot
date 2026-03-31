import pandas as pd
import pytest
from src.math_engine.asian_range import calculate_asian_range

def test_calculate_asian_range():
    # 1. Create dummy market data in UTC
    # We include times before, during, and after the 00:00 - 04:00 window.
    data = {
        'datetime': [
            '2023-10-10 23:55:00', # Previous NY close
            '2023-10-10 00:15:00', # Inside Asia Session
            '2023-10-10 02:30:00', # Inside Asia Session (Highest inside)
            '2023-10-10 03:45:00', # Inside Asia Session (Lowest inside)
            '2023-10-10 04:05:00', # Just outside Asia Session
            '2023-10-10 14:30:00'  # NY Open (Highest overall, should be ignored)
        ],
        'high': [39000, 39050, 39100, 39020, 39150, 39500],
        'low':  [38950, 39000, 39050, 38900, 38850, 38800]
    }
    
    df = pd.DataFrame(data)
    # Convert string to datetime and set as index (crucial for time-series math)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    # Ensure the index is timezone-aware (UTC)
    df.index = df.index.tz_localize('UTC')

    # 2. Run our function
    result = calculate_asian_range(df)

    # 3. Assert the expected outcomes
    # The highest 'high' between 00:00 and 04:00 is 39100 (at 02:30)
    # The lowest 'low' between 00:00 and 04:00 is 38900 (at 03:45)
    assert result['asia_high'] == 39100.0, f"Expected 39100, got {result['asia_high']}"
    assert result['asia_low'] == 38900.0, f"Expected 38900, got {result['asia_low']}"
    
    print("✅ test_calculate_asian_range passed successfully.")

def test_missing_data_handling():
    # Test how the function handles an empty dataframe or missing session data
    empty_df = pd.DataFrame()
    
    with pytest.raises(ValueError):
         calculate_asian_range(empty_df)