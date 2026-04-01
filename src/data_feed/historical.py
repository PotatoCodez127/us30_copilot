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
            
            # --- NEW: GRAB THE LIVE TAPE (LAST 15 MINS) ---
            import pandas as pd
            tape_start = current_time - pd.Timedelta(minutes=15)
            recent_tape = trading_session.loc[tape_start:current_time]
            
            # Format the tape so the AI can read it minute-by-minute
            tape_str = "\n".join([
                f"{idx.strftime('%H:%M')} | O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f}" 
                for idx, row in recent_tape.iterrows()
            ])
            ai_payload['recent_tape'] = tape_str
            # ---------------------------------------------
            
            # --- TRADE MANAGEMENT (MFE/MAE) ---
            if i + 1 < len(trading_session):
            
    return setups_found