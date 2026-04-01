import pandas as pd
from src.strategy.state_machine import US30SessionTracker

def load_and_prep_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df.set_index('datetime', inplace=True)
    df.columns = [col.lower() for col in df.columns]
    return df.sort_index()

def simulate_ny_session(df_1m: pd.DataFrame, date_str: str, pivots: dict):
    # 1. Isolate the Opening Range (First 30 minutes of NY Session)
    opening_range = df_1m.loc[f"{date_str} 13:30:00":f"{date_str} 14:00:00"]
    
    if opening_range.empty:
        return []
        
    or_high = opening_range['high'].max()
    or_low = opening_range['low'].min()
    
    # 2. Initialize the State Machine
    tracker = US30SessionTracker(
        or_high=or_high,
        or_low=or_low,
        daily_pivots=pivots
    )
    
    # 3. Simulate the rest of the day
    trading_session = df_1m.loc[f"{date_str} 14:01:00":f"{date_str} 20:00:00"]
    setups_found = []
    
    for i in range(len(trading_session)):
        current_time = trading_session.index[i]
        candle_1m = trading_session.iloc[i].to_dict()
        
        floor_15m = current_time.floor('15min')
        current_15m_window = trading_session.loc[floor_15m:current_time]
        
        if current_15m_window.empty:
            continue
            
        candle_15m = {
            'open': current_15m_window['open'].iloc[0],
            'high': current_15m_window['high'].max(),
            'low': current_15m_window['low'].min(),
            'close': current_15m_window['close'].iloc[-1],
        }
        
        ai_payload = tracker.update_state(candle_15m, candle_1m)
        
        if ai_payload:
            ai_payload['timestamp'] = str(current_time)
            entry_price = candle_15m['close']
            
            # --- TRADE MANAGEMENT (MFE/MAE) ---
            if i + 1 < len(trading_session):
                future_data = trading_session.iloc[i+1:]
                absolute_highest = future_data['high'].max()
                absolute_lowest = future_data['low'].min()
                
                # We calculate standard Long floats for the database columns
                ai_payload['mfe_points'] = float(round(absolute_highest - entry_price, 2))
                ai_payload['mae_points'] = float(round(absolute_lowest - entry_price, 2))
                
                # Add the Short perspective into the context payload for the AI to read
                ai_payload['context']['short_mfe'] = float(round(entry_price - absolute_lowest, 2))
                ai_payload['context']['short_mae'] = float(round(entry_price - absolute_highest, 2))
            else:
                ai_payload['mfe_points'] = 0.0
                ai_payload['mae_points'] = 0.0
            
            setups_found.append(ai_payload)
            break # Lock in the first valid setup of the day
            
    return setups_found