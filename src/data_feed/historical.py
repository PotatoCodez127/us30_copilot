import pandas as pd
import os
from src.strategy.state_machine import US30SessionTracker

def load_and_prep_data(filepath):
    """
    Loads the historical 1-minute data and ensures datetime index.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Could not find data file at {filepath}")
        
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    return df

def simulate_ny_session(df_1m, date_str, pivots):
    """
    Simulates the NY Session. First calculates the Opening Range (13:30 to 14:00 UTC),
    then runs the State Machine on the rest of the session.
    """
    # 1. Isolate the Opening Range (First 30 minutes of NY Session)
    opening_range = df_1m.loc[f"{date_str} 13:30:00":f"{date_str} 14:00:00"]
    
    if opening_range.empty:
        return []
        
    or_high = opening_range['high'].max()
    or_low = opening_range['low'].min()
    
    # 2. Initialize the new State Machine
    tracker = US30SessionTracker(
        or_high=or_high,
        or_low=or_low,
        daily_pivots=pivots
    )
    
    # 3. Simulate the rest of the day (After the Opening Range establishes)
    trading_session = df_1m.loc[f"{date_str} 14:01:00":f"{date_str} 20:00:00"]
    setups_found = []
    
    for i in range(len(trading_session)):
        current_time = trading_session.index[i]
        candle_1m = trading_session.iloc[i].to_dict()
        
        # Build 15m candle
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
            
            # --- THE LIVE TAPE GENERATOR ---
            tape_start = current_time - pd.Timedelta(minutes=15)
            recent_tape = trading_session.loc[tape_start:current_time]
            
            tape_str = "\n".join([
                f"{idx.strftime('%H:%M')} | O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f}" 
                for idx, row in recent_tape.iterrows()
            ])
            ai_payload['recent_tape'] = tape_str
            # -------------------------------
            
            # --- TRADE MANAGEMENT (MFE/MAE) ---
            if i + 1 < len(trading_session):
                future_data = trading_session.iloc[i+1:]
                absolute_highest = future_data['high'].max()
                absolute_lowest = future_data['low'].min()
                
                # Calculate absolute maximums in both directions
                mfe_up = float(round(absolute_highest - entry_price, 2))
                mae_down = float(round(absolute_lowest - entry_price, 2))
                mfe_down = float(round(entry_price - absolute_lowest, 2))
                mae_up = float(round(entry_price - absolute_highest, 2))
                
                ai_payload['mfe_points'] = f"Long: {mfe_up} | Short: {mfe_down}"
                ai_payload['mae_points'] = f"Long: {mae_down} | Short: {mae_up}"
            else:
                ai_payload['mfe_points'] = "0"
                ai_payload['mae_points'] = "0"
            
            setups_found.append(ai_payload)
            break # We lock in the first valid setup of the day
            
    return setups_found