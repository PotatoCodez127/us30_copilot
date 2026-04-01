import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone

from src.math_engine.asian_range import calculate_asian_range
from src.math_engine.pivots import calculate_daily_pivots
from src.strategy.state_machine import US30SessionTracker
from src.ai_agent.ollama_client import analyze_setup_with_ollama
from src.database.supabase_client import log_setup_to_db

# Yahoo Finance ticker for the Dow Jones Industrial Average (US30)
TICKER = "^DJI"

def fetch_live_data():
    """Fetches the last 5 days of 1-minute data and formats it for our engine."""
    # We pull 5 days so we have enough history for yesterday's pivots and today's Asian Range
    df = yf.download(TICKER, period="5d", interval="1m", progress=False)
    
    # Flatten the multi-index columns that yfinance sometimes returns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df.index.name = 'datetime'
    df.columns = [col.lower() for col in df.columns]
    
    # Strictly enforce UTC Timezone
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
        
    return df

def run_live_bot():
    print("🟢 Initializing Live US30 Copilot...")
    setup_logged_today = False
    current_trading_day = None

    while True:
        try:
            now = datetime.now(timezone.utc)
            today_str = str(now.date())
            
            # Reset the lock if it's a new day
            if today_str != current_trading_day:
                setup_logged_today = False
                current_trading_day = today_str

            # 1. Fetch live market data
            df = fetch_live_data()
            if df.empty:
                print(f"[{now.strftime('%H:%M:%S')} UTC] Waiting for market data...")
                time.sleep(60)
                continue

            unique_dates = pd.Series(df.index.date).unique()
            if len(unique_dates) < 2:
                time.sleep(60)
                continue

            # 2. Extract Yesterday and Today
            yesterday_str = str(unique_dates[-2])
            prev_day_data = df.loc[yesterday_str]
            current_day_data = df.loc[today_str] if today_str in df.index else pd.DataFrame()

            if current_day_data.empty:
                print(f"[{now.strftime('%H:%M:%S')} UTC] Market closed or no data for today yet.")
                time.sleep(60)
                continue

            # 3. Calculate Daily Pivots & Asian Range
            try:
                pivots = calculate_daily_pivots(
                    prev_day_data['high'].max(), 
                    prev_day_data['low'].min(), 
                    prev_day_data['close'].iloc[-1]
                )
                asia_range = calculate_asian_range(current_day_data)
            except ValueError as e:
                # This happens if it's too early in the day (e.g., Asian session hasn't finished)
                print(f"[{now.strftime('%H:%M:%S')} UTC] Calculating levels... ({e})")
                time.sleep(60)
                continue

            # 4. Check if we are in the NY Session (After 13:30 UTC)
            ny_session_data = current_day_data.loc[f"{today_str} 13:30:00":]
            
            if ny_session_data.empty:
                print(f"[{now.strftime('%H:%M:%S')} UTC] Waiting for NY Session Open (13:30 UTC)...")
                time.sleep(60)
                continue

            print(f"[{now.strftime('%H:%M:%S')} UTC] Tracking Live NY Session | Price: {ny_session_data['close'].iloc[-1]:.2f}")

            # 5. Run the State Machine on the Live NY Data
            tracker = US30SessionTracker(
                asia_high=asia_range['asia_high'],
                asia_low=asia_range['asia_low'],
                daily_pivots=[pivots['S2'], pivots['S1'], pivots['P'], pivots['R1'], pivots['R2']]
            )

            # Replay today's NY session up to this exact minute
            for i in range(len(ny_session_data)):
                current_time = ny_session_data.index[i]
                candle_1m = ny_session_data.iloc[i].to_dict()
                
                # Build live 15m candle
                floor_15m = current_time.floor('15min')
                current_15m_window = ny_session_data.loc[floor_15m:current_time]
                
                candle_15m = {
                    'open': current_15m_window['open'].iloc[0],
                    'high': current_15m_window['high'].max(),
                    'low': current_15m_window['low'].min(),
                    'close': current_15m_window['close'].iloc[-1],
                }
                
                payload = tracker.update_state(candle_15m, candle_1m)
                
                # If a setup triggers, and we haven't logged one today yet!
                if payload and not setup_logged_today:
                    print(f"\n🚀 LIVE SETUP TRIGGERED AT {current_time}!")
                    payload['timestamp'] = str(current_time)
                    payload['mfe_points'] = 0.0 # Will update this later
                    payload['mae_points'] = 0.0
                    
                    ai_analysis = analyze_setup_with_ollama(payload)
                    payload['ai_risk_analysis'] = ai_analysis
                    
                    log_setup_to_db(payload)
                    setup_logged_today = True # Lock it so we don't spam the database
                    break # Break the loop, we got our trade for the day

            # Sleep for exactly 60 seconds before pulling the next 1-minute candle
            time.sleep(60)

        except Exception as e:
            print(f"⚠️ Live Feed Error: {e}")
            time.sleep(60) # Don't crash the bot, just wait and try again

if __name__ == "__main__":
    run_live_bot()