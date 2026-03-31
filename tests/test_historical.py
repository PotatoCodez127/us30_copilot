import pandas as pd
import pytest
import os
# from src.data_feed.historical import load_and_prep_data, run_backtest_day
from src.data_feed.historical import load_and_prep_data, simulate_ny_session

def test_data_loader(tmp_path):
    # 1. Create a dummy CSV file using pytest's temporary path
    dummy_csv = tmp_path / "dummy_us30.csv"
    
    # Create 20 minutes of 1-minute data
    dates = pd.date_range(start="2023-10-10 13:30:00", periods=20, freq="1min", tz="UTC")
    data = {
        'open': [39000] * 20,
        'high': [39050] * 20,
        'low': [38950] * 20,
        'close': [39010] * 20,
        'volume': [100] * 20
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'datetime'
    df.to_csv(dummy_csv)

    # 2. Test the loading function
    loaded_df = load_and_prep_data(str(dummy_csv))
    
    assert not loaded_df.empty, "DataFrame should not be empty"
    assert isinstance(loaded_df.index, pd.DatetimeIndex), "Index must be datetime"
    assert str(loaded_df.index.tz) == 'UTC', "Timezone must be converted to UTC"
    
    print("✅ test_data_loader passed successfully.")