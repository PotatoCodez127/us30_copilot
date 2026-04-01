import pandas as pd
import MetaTrader5 as mt5
from src.math_engine.asian_range import calculate_asian_range
from src.math_engine.pivots import calculate_daily_pivots
from src.strategy.state_machine import US30SessionTracker
from src.ai_agent.ollama_client import analyze_setup_with_ollama
from src.database.supabase_client import log_setup_to_db

def fetch_data():
    """Fetches 1-minute US30 data from MT5 for 10 days."""
    if not mt5.initialize():
        return None
    
    rates = mt5.copy_rates_from_pos("US30", mt5.TIMEFRAME_M1, 0, 14400)
    mt5.shutdown()
    
    if rates is None:
        return None
    
    df = pd.DataFrame(rates)
    df = df.rename(columns={'time': 'datetime', 'tick_volume': 'volume'})
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
    df.set_index('datetime', inplace=True)
    df.index = df.index.tz_localize('UTC')
    df = df[['open', 'high', 'low', 'close', 'volume']]
    
    return df

def simulate_ny_session(current_day_data, date_str, pivots, asia_range):
    tracker = US30SessionTracker(
        asia_high=asia_range['asia_high'],
        asia_low=asia_range['asia_low'],
        daily_pivots=[pivots['S2'], pivots['S1'], pivots['P'], pivots['R1'], pivots['R2']]
    )
    
    session_data = current_day_data.loc[date_str + " 13:30:00":date_str + " 20:00:00"]
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
            entry_price = candle_15m['close']
            
            if i + 1 < len(session_data):
                future_data = session_data.iloc[i+1:]
                mfe = float(round(future_data['high'].max() - entry_price, 2))
                mae = float(round(future_data['low'].min() - entry_price, 2))
            else:
                mfe, mae = 0.0, 0.0
                
            ai_payload['mfe_points'] = mfe
            ai_payload['mae_points'] = mae
            setups_found.append(ai_payload)
            break
            
    return setups_found

def run_cash_miner():
    print("[OK] SCRIPT INITIATED")
    
    df = fetch_data()
    if df is None:
        print("[ERROR] Failed to fetch data")
        return

    unique_dates = pd.Series(df.index.date).unique()
    print(f"[INFO] Found {len(unique_dates)} trading days from MT5")
    print("-" * 60)
    
    all_setups = []

    for i in range(1, len(unique_dates)):
        prev_date_str = str(unique_dates[i-1])
        current_date_str = str(unique_dates[i])
        
        prev_day_data = df.loc[prev_date_str]
        if prev_day_data.empty: continue
            
        try:
            pivots = calculate_daily_pivots(
                prev_day_data['high'].max(), 
                prev_day_data['low'].min(), 
                prev_day_data['close'].iloc[-1]
            )
        except ValueError: continue

        current_day_data = df.loc[current_date_str]
        try:
            asia_range = calculate_asian_range(current_day_data)
        except ValueError: continue

        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots, asia_range)
        
        if daily_setups:
            for setup in daily_setups:
                print(f"[SETUP]: {current_date_str} at {setup['timestamp']}")
                
                ai_analysis = analyze_setup_with_ollama(setup)
                setup['ai_risk_analysis'] = ai_analysis
                
                try:
                    log_setup_to_db(setup)
                except Exception as e:
                    print(f"[WARN] DB log failed: {e}")
                
                all_setups.append(setup)

    output_file = "discovery_setups.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Discovery Complete! Found {len(all_setups)} High-Probability Setups.\n")
        f.write("=" * 60 + "\n\n")
        for i, setup in enumerate(all_setups):
            f.write(f"#{i+1} | {setup['timestamp']} | {setup.get('trigger', 'Unknown')}\n")
            f.write(f"    Entry: at {setup['timestamp']} | Profit: +{setup.get('mfe_points', 'N/A')} | Drawdown: {setup.get('mae_points', 'N/A')}\n")
            f.write(f"    AI Analysis: {setup.get('ai_risk_analysis', 'N/A')[:150]}\n")
            f.write("-" * 60 + "\n")

    print(f"[SAVED] Saved all {len(all_setups)} setups to {output_file}")
    print("-" * 60)

if __name__ == "__main__":
    run_cash_miner()
