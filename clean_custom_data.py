import pandas as pd
import os

def clean_firstrate_txt(raw_filepath: str):
    print(f"[INFO] Loading raw data from {raw_filepath}...")
    
    try:
        df = pd.read_csv(raw_filepath)
        
        if 'timestamp' in df.columns:
            df['datetime'] = df['timestamp']
        elif 'datetime' not in df.columns:
            print("❌ Error: Could not find 'datetime' or 'timestamp' column.")
            return
    except FileNotFoundError:
        print(f"❌ Error: Could not find {raw_filepath}.")
        print("Please ensure the file is in the root folder and spelled correctly.")
        return

    print("[INFO] Formatting timestamps and enforcing UTC...")
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['datetime'] = df['datetime'].dt.tz_localize('America/New_York', ambiguous='infer', nonexistent='shift_forward').dt.tz_convert('UTC')
    df['volume'] = 0
    
    os.makedirs('data', exist_ok=True)
    clean_filepath = 'data/historical_us30_1m.csv'
    df.to_csv(clean_filepath, index=False)
    
    unique_days = len(pd.Series(df['datetime'].dt.date).unique())
    print(f"[SUCCESS] Cleaned {len(df)} candles across {unique_days} trading days.")
    print(f"[SAVED] Saved engine-ready data to: {clean_filepath}")

if __name__ == "__main__":
    RAW_FILE = "DJI_1min_sample.csv"
    clean_firstrate_txt(RAW_FILE)
