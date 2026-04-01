import pandas as pd
import os

def clean_and_filter_massive_csv(raw_filepath: str, days_to_keep: int = 30):
    print(f"🧹 Loading massive MT4/MT5 data from {raw_filepath}...")
    
    try:
        # Read the MetaTrader CSV using the correct UTF-16 encoding
        # Mapping: Col 0 = DateTime, Col 1 = Open, Col 2 = High, Col 3 = Low, Col 4 = Close, Col 5 = TickVolume
        df = pd.read_csv(raw_filepath, header=None, usecols=[0, 1, 2, 3, 4, 5], 
                         names=['datetime', 'open', 'high', 'low', 'close', 'volume'],
                         encoding='utf-16')
    except FileNotFoundError:
        print(f"❌ Error: Could not find {raw_filepath}.")
        return

    print("🔄 Reformatting timestamps and enforcing UTC...")
    
    # Parse the exact MT5 format (e.g., "2025.12.17 03:03")
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y.%m.%d %H:%M')
    
    if df['datetime'].dt.tz is None:
         df['datetime'] = df['datetime'].dt.tz_localize('UTC')

    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    
    # --- ISOLATE THE LAST 30 DAYS ---
    unique_dates = df['datetime'].dt.date.unique()
    
    if len(unique_dates) > days_to_keep:
        print(f"✂️ File contains {len(unique_dates)} days. Trimming to the most recent {days_to_keep} days...")
        cutoff_date = unique_dates[-days_to_keep]
        df = df[df['datetime'].dt.date >= cutoff_date]
    # --------------------------------
    
    os.makedirs('data', exist_ok=True)
    clean_filepath = 'data/historical_us30_1m.csv'
    df.to_csv(clean_filepath, index=False)
    
    final_days = len(df['datetime'].dt.date.unique())
    print(f"✅ Success! Cleaned {len(df)} candles across {final_days} trading days.")
    print(f"💾 Saved engine-ready data to: {clean_filepath}")

if __name__ == "__main__":
    RAW_FILE = "US30M1.csv"
    clean_and_filter_massive_csv(RAW_FILE, days_to_keep=30)