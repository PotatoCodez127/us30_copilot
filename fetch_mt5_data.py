import MetaTrader5 as mt5
import pandas as pd
import os

def fetch_mt5_data(days: int = 10):
    """
    Fetches 1-minute US30 data from MetaTrader 5.
    Includes 24-hour data for Asian session analysis (00:00-24:00 UTC).
    """
    print("[INFO] Initializing MetaTrader5...")
    
    if not mt5.initialize():
        print(f"[ERROR] MT5 initialization failed")
        return None
    
    symbol = "US30"
    
    # Get rates from position 0 (most recent) for specified days worth
    candles_per_day = 1440
    total_candles = days * candles_per_day + 100
    
    print(f"[INFO] Fetching {total_candles} candles for the last {days} days...")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, total_candles)
    mt5.shutdown()
    
    if rates is None or len(rates) == 0:
        print("[ERROR] No data returned from MT5")
        return None
    
    print(f"[SUCCESS] Retrieved {len(rates)} candles")
    
    # Create DataFrame
    df = pd.DataFrame(rates)
    df = df.rename(columns={
        'time': 'datetime',
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'tick_volume': 'volume'
    })
    
    # Convert timestamp to datetime and set index
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
    df.set_index('datetime', inplace=True)
    
    # Ensure UTC timezone
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    filepath = 'data/us30_mt5_1m.csv'
    df.to_csv(filepath, index=True)
    
    unique_days = len(pd.Series(df.index.date).unique())
    print(f"[SAVED] Saved {len(df)} candles across {unique_days} days to {filepath}")
    
    return df

if __name__ == "__main__":
    fetch_mt5_data(10)
