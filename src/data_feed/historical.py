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
    Simulates the NY Session (13:30 to 20:00 UTC) candle by candle and tracks MFE/MAE.
    """
    tracker = US30SessionTracker(
        asia_high=asia_range['asia_high'],
        asia_low=asia_range['asia_low'],
        daily_pivots=[pivots['S2'], pivots['S1'], pivots['P'], pivots['R1'], pivots['R2']]
    )
    
    session_data = df_1m.loc[f"{date_str} 13:30:00":f"{date_str} 20:00:00"]
    setups_found = []
    
    for i in range(len(session_data)):
        current_time = session_data.index[i]
        candle_1m = session_data.iloc[i].to_dict()
        
        floor_15m = current_time.floor('15min')
        current_15m_window = session_data.loc[floor_15m:current_time]
        
        candle_15m = {
            'open': current_15m_window['open'].iloc[0],
            'high': current_15m_window['high'].max(),
            'low': current_15m_window['low'].min(),
            'close': current_15m_window['close'].iloc[-1],
        }
        
        ai_payload = tracker.update_state(candle_15m, candle_1m)
        
        if ai_payload:
            ai_payload['timestamp'] = str(current_time)
            
            # --- NEW: TRADE MANAGEMENT LOGIC ---
            entry_price = candle_15m['close']
            
            # Slice the dataframe to look only at the time AFTER our entry
            if i + 1 < len(session_data):
                future_data = session_data.iloc[i+1:]
                absolute_highest = future_data['high'].max()
                absolute_lowest = future_data['low'].min()
                
                # Calculate excursion points (Assuming a LONG setup)
                mfe = round(absolute_highest - entry_price, 2)
                mae = round(absolute_lowest - entry_price, 2) # This will be negative (drawdown)
            else:
                mfe, mae = 0.0, 0.0
                
            ai_payload['mfe_points'] = mfe
            ai_payload['mae_points'] = mae
            # -----------------------------------
            
            setups_found.append(ai_payload)
            break # We only track the first valid setup of the day to keep data clean
            
    return setups_found