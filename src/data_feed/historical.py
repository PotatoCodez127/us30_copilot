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

    # Calculate Dates (6 months = roughly 180 days)
    end_date = datetime.utcnow()
    mid_date = end_date - timedelta(days=90) 
    start_date = end_date - timedelta(days=180) 

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

    # Map Massive's schema to your AI's schema
    df = df.rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume', 't': 'timestamp'})
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    
    # Drop duplicates and sort
    df.drop_duplicates(subset=['timestamp'], inplace=True)
    df.sort_values('timestamp', inplace=True)
    df.set_index('timestamp', inplace=True)
    
    columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
    df = df[columns_to_keep]

    print(f"✅ Loaded {len(df)} candles for the 6-Month Walk-Forward Judge.")
    
    # Save a local cache so auto_eval.py can read it without hitting the API constantly
    os.makedirs('data', exist_ok=True)
    csv_path = "data/rolling_train.csv"
    df.to_csv(csv_path)
    
    return df

def load_and_prep_data(csv_filepath: str = None):
    """
    Loads the cached rolling data.
    """
    if not os.path.exists(csv_filepath):
        print("⚠️ Cached data not found. Fetching fresh rolling window...")
        return fetch_rolling_6_months()
        
    df = pd.read_csv(csv_filepath)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    return df

def simulate_ny_session(current_day_data, current_date_str, pivots):
    from src.strategy.state_machine import US30SessionTracker
    
    try:
        # Determine Opening Range using the first 15 minutes of the NY Session (09:30 - 09:45 EST -> 14:30 - 14:45 UTC)
        or_start = pd.to_datetime(f"{current_date_str} 14:30:00+00:00")
        or_end = pd.to_datetime(f"{current_date_str} 14:45:00+00:00")
        or_data = current_day_data.loc[or_start:or_end]
        
        if or_data.empty: return []

        or_high = or_data['high'].max()
        or_low = or_data['low'].min()
    except KeyError:
        return []

    tracker = US30SessionTracker(or_high, or_low, pivots)
    setups = []

    # Iterate through the rest of the NY session starting at 10:00 EST / 15:00 UTC
    session_start = pd.to_datetime(f"{current_date_str} 15:00:00+00:00")
    session_data = current_day_data.loc[session_start:]

    for idx, row in session_data.iterrows():
        # Build a synthetic 15-minute candle to check for closure confirmations
        window_start = idx - pd.Timedelta(minutes=15)
        window_data = session_data.loc[window_start:idx]
        
        if len(window_data) < 2: continue
        
        candle_15m = {
            'high': window_data['high'].max(),
            'low': window_data['low'].min(),
            'close': row['close']
        }
        
        current_1m = {'high': row['high'], 'low': row['low'], 'close': row['close']}
        
        state_update = tracker.update_state(candle_15m, current_1m)
        if state_update:
            state_update['timestamp'] = str(idx)
            setups.append(state_update)

    return setups