import pandas as pd
import os

def clean_and_filter_massive_csv(raw_filepath: str, days_to_keep: int = 30):
    print(f"🧹 Loading massive MT4/MT5 data from {raw_filepath}...")
    
    try:
        # Read the MetaTrader CSV
        df = pd.read_csv(raw_filepath, header=None, usecols=[0, 1, 2, 3, 4, 5], 
                         names=['date', 'time', 'open', 'high', 'low', 'close'])
    except FileNotFoundError:
        print(f"❌ Error: Could not find {raw_filepath}.")
        return

    print("🔄 Reformatting timestamps and enforcing UTC...")
    df['datetime_str'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
    df['datetime'] = pd.to_datetime(df['datetime_str'], format='mixed')
    
    if df['datetime'].dt.tz is None:
         df['datetime'] = df['datetime'].dt.tz_localize('UTC')

    df['volume'] = 0
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