import yfinance as yf
import pandas as pd
import os

def fetch_real_1m_data():
    print("[INFO] Downloading the last 7 days of real 1-minute US30 data from Yahoo Finance...")
    
    # Download the maximum allowed 1m data (7 days)
    df = yf.download("^DJI", period="7d", interval="1m", progress=False)

    if df.empty:
        print("[ERROR] Failed to download data. Yahoo Finance might be blocking the request.")
        return

    # Flatten multi-index columns if yfinance returns them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Standardize column names to lowercase for our engine
    df.index.name = 'datetime'
    df.columns = [col.lower() for col in df.columns]

    # Strictly enforce UTC Timezone
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')

    # Reset the index so 'datetime' becomes a standard column in the CSV
    df.reset_index(inplace=True)

    # Save to the data folder, overwriting our dummy data
    os.makedirs('data', exist_ok=True)
    filepath = 'data/historical_us30_1m.csv'
    df.to_csv(filepath, index=False)
    
    # We subtract 1 from columns to not count datetime, just to give a clean log
    print(f"[SUCCESS] Downloaded {len(df)} real market candles.")
    print(f"[SAVED] Saved to {filepath}")

if __name__ == "__main__":
    fetch_real_1m_data()