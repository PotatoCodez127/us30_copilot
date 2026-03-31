import pandas as pd
from src.math_engine.asian_range import calculate_asian_range
from src.math_engine.pivots import calculate_daily_pivots
from src.strategy.state_machine import US30SessionTracker

def load_and_prep_data(filepath: str) -> pd.DataFrame:
    """
    Loads historical 1-minute CSV data and ensures strict UTC timezone compliance.
    Expects CSV to have a 'datetime' column and standard OHLCV columns.
    """
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df.set_index('datetime', inplace=True)
    
    # Ensure column names are lowercase for consistency
    df.columns = [col.lower() for col in df.columns]
    
    return df.sort_index()

def simulate_ny_session(df_1m: pd.DataFrame, date_str: str, pivots: dict, asia_range: dict):
    """
    Simulates the NY Session (13:30 to 20:00 UTC) candle by candle.
    """
    # 1. Initialize the State Machine for the day
    tracker = US30SessionTracker(
        asia_high=asia_range['asia_high'],
        asia_low=asia_range['asia_low'],
        daily_pivots=[pivots['S2'], pivots['S1'], pivots['P'], pivots['R1'], pivots['R2']]
    )
    
    # 2. Isolate the NY Session data for this specific day
    # NY Open is 09:30 EST, which is 13:30 UTC (ignoring DST for this pure UTC logic)
    session_data = df_1m.loc[f"{date_str} 13:30:00":f"{date_str} 20:00:00"]
    
    # 3. Step through time chronologically
    # We use a 15-minute rolling window to simulate the current 15m candle forming
    setups_found = []
    
    for i in range(len(session_data)):
        current_time = session_data.index[i]
        candle_1m = session_data.iloc[i].to_dict()
        
        # Calculate the current 15-minute candle on the fly (from the top of the hour)
        # E.g., at 13:42, it groups 13:30 to 13:42
        floor_15m = current_time.floor('15min')
        current_15m_window = session_data.loc[floor_15m:current_time]
        
        candle_15m = {
            'open': current_15m_window['open'].iloc[0],
            'high': current_15m_window['high'].max(),
            'low': current_15m_window['low'].min(),
            'close': current_15m_window['close'].iloc[-1], # Current price
        }
        
        # 4. Feed the engine
        ai_payload = tracker.update_state(candle_15m, candle_1m)
        
        if ai_payload:
            # We add the timestamp so we know exactly when it triggered
            ai_payload['timestamp'] = str(current_time)
            setups_found.append(ai_payload)
            
            # Reset tracker if you only want one trade per day, or leave it to catch multiple
            break 
            
    return setups_found