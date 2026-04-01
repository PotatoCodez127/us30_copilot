import pandas as pd
import os

def clean_firstrate_txt(raw_filepath: str):
    print(f"🧹 Loading raw data from {raw_filepath}...")
    
    try:
        # Read the comma-separated txt file
        # Format: timestamp, open, high, low, close
        df = pd.read_csv(raw_filepath, header=None, names=['datetime', 'open', 'high', 'low', 'close'])
    except FileNotFoundError:
        print(f"❌ Error: Could not find {raw_filepath}.")
        print("Please ensure the file is in the root folder and spelled correctly.")
        return

    print("🔄 Formatting timestamps and enforcing UTC...")
    
    # 1. Convert the string to a Pandas Datetime object
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # 2. Timezone Shift: FirstRate Data is in US Eastern Time. 
    # We localize it to New York, then convert it to strict UTC for our engine.
    df['datetime'] = df['datetime'].dt.tz_localize('America/New_York', ambiguous='infer', nonexistent='shift_forward').dt.tz_convert('UTC')

    # 3. Add a dummy volume column (our engine expects it)
    df['volume'] = 0
    
    # Save it directly into the data folder, ready for the engine
    os.makedirs('data', exist_ok=True)
    clean_filepath = 'data/historical_us30_1m.csv'
    df.to_csv(clean_filepath, index=False)
    
    unique_days = len(pd.Series(df['datetime'].dt.date).unique())
    print(f"✅ Success! Cleaned {len(df)} candles across {unique_days} trading days.")
    print(f"💾 Saved engine-ready data to: {clean_filepath}")

if __name__ == "__main__":
    # Point this directly to your downloaded FirstRate file
    RAW_FILE = "DJI_full_1min.txt"
    clean_firstrate_txt(RAW_FILE)