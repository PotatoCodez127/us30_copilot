import pandas as pd
import os

def clean_metatrader_csv(raw_filepath: str):
    print(f"🧹 Loading massive MT4/MT5 data from {raw_filepath}...")
    
    try:
        # MT4/MT5 CSVs usually have no headers: Date, Time, Open, High, Low, Close, TickVol, Vol, Spread
        # We grab the first 6 columns.
        df = pd.read_csv(raw_filepath, header=None, usecols=[0, 1, 2, 3, 4, 5], 
                         names=['date', 'time', 'open', 'high', 'low', 'close'])
    except FileNotFoundError:
        print(f"❌ Error: Could not find {raw_filepath}.")
        print("Please place your downloaded CSV in the root folder and name it 'US30M1.csv'")
        return

    print("🔄 Reformatting timestamps and enforcing UTC...")
    
    # 1. Combine Date and Time
    df['datetime_str'] = df['date'].astype(str) + ' ' + df['time'].astype(str)
    
    # 2. Convert to Datetime. 
    # MT server time is usually EET (UTC+2 or UTC+3). For simplicity in our pure 
    # math backtester, we will treat it as UTC, or shift it if you prefer. 
    # Assuming strict parsing here:
    df['datetime'] = pd.to_datetime(df['datetime_str'], format='mixed')
    
    # Localize to UTC to satisfy our engine
    if df['datetime'].dt.tz is None:
         df['datetime'] = df['datetime'].dt.tz_localize('UTC')

    # Add a dummy volume column
    df['volume'] = 0
    
    # Reorder
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    
    os.makedirs('data', exist_ok=True)
    clean_filepath = 'data/historical_us30_1m.csv'
    df.to_csv(clean_filepath, index=False)
    
    unique_days = len(pd.Series(df['datetime'].dt.date).unique())
    print(f"✅ Success! Cleaned {len(df)} candles across {unique_days} trading days.")
    print(f"💾 Saved engine-ready data to: {clean_filepath}")

if __name__ == "__main__":
    # Point this to your massive file
    RAW_FILE = "US30M1.csv"
    clean_metatrader_csv(RAW_FILE)