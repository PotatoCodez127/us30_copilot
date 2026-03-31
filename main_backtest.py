import pandas as pd
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.asian_range import calculate_asian_range
from src.math_engine.pivots import calculate_daily_pivots

def run_full_backtest(csv_filepath: str):
    print(f"Loading historical data from {csv_filepath}...")
    try:
        df = load_and_prep_data(csv_filepath)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {csv_filepath}. Please ensure you have a US30 1-minute CSV in the data folder.")
        return

    # Extract a list of unique dates in the dataset
    # We convert to date objects to easily iterate day by day
    unique_dates = pd.Series(df.index.date).unique()
    
    print(f"Data loaded successfully. Found {len(unique_dates)} trading days.")
    print("-" * 50)
    
    total_setups = []

    # We start from the second day (index 1) because we need the FIRST day to calculate the pivots
    for i in range(1, len(unique_dates)):
        prev_date_str = str(unique_dates[i-1])
        current_date_str = str(unique_dates[i])
        
        # 1. Calculate Daily Pivots (Using Previous Day's Data)
        prev_day_data = df.loc[prev_date_str]
        if prev_day_data.empty:
            continue
            
        prev_high = prev_day_data['high'].max()
        prev_low = prev_day_data['low'].min()
        prev_close = prev_day_data['close'].iloc[-1]
        
        try:
            pivots = calculate_daily_pivots(prev_high, prev_low, prev_close)
        except ValueError:
            continue # Skip days with bad data

        # 2. Calculate Asian Range (00:00 to 04:00 UTC of Current Day)
        current_day_data = df.loc[current_date_str]
        try:
            asia_range = calculate_asian_range(current_day_data)
        except ValueError:
            continue # Skip if no Asia session data exists (e.g., weekends/holidays)

        # 3. Run the NY Session Simulation
        # print(f"Simulating NY Session for {current_date_str}...")
        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots, asia_range)
        
        if daily_setups:
            for setup in daily_setups:
                print(f"🟢 SETUP FOUND on {current_date_str} at {setup['timestamp']}")
                print(f"   Trigger: {setup['trigger']}")
                print(f"   Narrative: {setup['narrative_confirmed']}")
            total_setups.extend(daily_setups)

    print("-" * 50)
    print(f"🏁 Backtest Complete. Found {len(total_setups)} total setups over {len(unique_dates)} days.")
    return total_setups

if __name__ == "__main__":
    # Point this to wherever you store your historical 1m CSV data
    DATA_FILE = "data/historical_us30_1m.csv"
    run_full_backtest(DATA_FILE)