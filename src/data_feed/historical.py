import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

def fetch_chunk(symbol, start_str, end_str, api_key):
    """Fetches a specific chunk of data from Massive to respect the 50k limit."""
    endpoint_url = f"https://api.massive.com/v2/aggs/ticker/{symbol}/range/1/minute/{start_str}/{end_str}"
    params = {"adjusted": "true", "sort": "asc", "limit": 50000}
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(endpoint_url, params=params, headers=headers)
    response.raise_for_status()
    
    return response.json().get("results", [])

def fetch_rolling_6_months(symbol="DIA"):
    """
    Calculates the exact 6-month window from today, fetches the data in chunks,
    and returns a clean Pandas DataFrame for the evaluator.
    """
    load_dotenv()
    api_key = os.getenv("MASSIVE_API_KEY")
    
    if not api_key:
        raise ValueError("MASSIVE_API_KEY is missing from the .env file.")

    # Calculate Dates
    end_date = datetime.utcnow()
    mid_date = end_date - timedelta(days=90) # 3 months ago
    start_date = end_date - timedelta(days=180) # 6 months ago

    end_str = end_date.strftime('%Y-%m-%d')
    mid_str = mid_date.strftime('%Y-%m-%d')
    start_str = start_date.strftime('%Y-%m-%d')

    print(f"📡 Fetching ROLLING WINDOW for {symbol}: {start_str} to {end_str}")

    # Fetch in two chunks to avoid the 50,000 limit
    raw_candles = []
    raw_candles.extend(fetch_chunk(symbol, start_str, mid_str, api_key))
    raw_candles.extend(fetch_chunk(symbol, (mid_date + timedelta(days=1)).strftime('%Y-%m-%d'), end_str, api_key))

    if not raw_candles:
        raise ValueError("API returned no data for this rolling window.")

    df = pd.DataFrame(raw_candles)

    # Map schema and convert timestamps
    df = df.rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume', 't': 'timestamp'})
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    
    # Drop duplicates (if chunks overlapped) and sort
    df.drop_duplicates(subset=['timestamp'], inplace=True)
    df.sort_values('timestamp', inplace=True)
    df.set_index('timestamp', inplace=True)
    
    columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
    df = df[columns_to_keep]

    print(f"✅ Loaded {len(df)} candles for the 6-Month Walk-Forward Judge.")
    
    # Save a local cache so auto_eval.py can read it without hitting the API constantly
    os.makedirs('data', exist_ok=True)
    df.to_csv("data/rolling_train.csv")
    
    return df