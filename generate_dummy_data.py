import pandas as pd
import numpy as np
import os

def create_perfect_setup_csv():
    print("Generating synthetic data with a GUARANTEED setup...")
    
    # Create 2 days of 1-minute timestamps
    dates = pd.date_range(start="2023-10-10 00:00:00", end="2023-10-11 20:00:00", freq="1min", tz="UTC")
    
    # Initialize a flat dataframe
    df = pd.DataFrame({'datetime': dates, 'open': 39000, 'high': 39000, 'low': 39000, 'close': 39000, 'volume': 100})
    df.set_index('datetime', inplace=True)
    
    # --- DAY 1: Set the Daily Levels ---
    # We force the previous day to have specific high/low/close so the Day 2 Pivot is exactly 39,000
    df.loc['2023-10-10 10:00:00', 'high'] = 39500
    df.loc['2023-10-10 12:00:00', 'low'] = 38500
    df.loc['2023-10-10 23:59:00', 'close'] = 39000
    
    # --- DAY 2: The Setup Narrative ---
    # 1. Asian Session (00:00 to 04:00): Establish High at 39,100 and Low at 38,900
    df.loc['2023-10-11 02:00:00', 'high'] = 39100
    df.loc['2023-10-11 03:00:00', 'low'] = 38900
    
    # 2. NY Session Opens (13:30)
    # Step A: Sweep the Asia Low (Price drops to 38,880 at 13:45)
    df.loc['2023-10-11 13:45:00', ['low', 'close']] = [38880, 38890]
    
    # Step B: Test Asia High / Fakeout (Breaks 39,100 at 14:10, but 15m candle closes at 39,080 at 14:14)
    df.loc['2023-10-11 14:10:00', 'high'] = 39120
    df.loc['2023-10-11 14:14:00', 'close'] = 39080 
    
    # Step C: Pivot Bounce (Drops below 39,000 pivot at 14:35, closes above it)
    df.loc['2023-10-11 14:35:00', ['low', 'close']] = [38990, 39020]
    
    # Step D: The Trigger (15m closes above Asia High 39,100 at 14:59)
    df.loc['2023-10-11 14:55:00', 'high'] = 39150
    df.loc['2023-10-11 14:59:00', 'close'] = 39130 

    # Reset index to make it a standard column again before saving
    df.reset_index(inplace=True)
    
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/historical_us30_1m.csv', index=False)
    print("✅ Synthetic 'Perfect Setup' injected into Day 2.")

if __name__ == "__main__":
    create_perfect_setup_csv()