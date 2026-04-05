import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import re
import os

from src.math_engine.pivots import calculate_daily_pivots
from src.strategy.state_machine import US30SessionTracker
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

TICKER = "^DJI"

def fetch_live_data():
    df = yf.download(TICKER, period="5d", interval="1m", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index.name = 'datetime'
    df.columns = [col.lower() for col in df.columns]
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    else:
        df.index = df.index.tz_convert('UTC')
    return df

def run_live_bot():
    print(f"{Color.CYAN}🟢 Initializing Live US30 Copilot (11 AM Sniper Mode)...{Color.RESET}")
    setup_logged_today = False
    current_trading_day = None

    while True:
        try:
            now = datetime.now(timezone.utc)
            today_str = str(now.date())
            
            if today_str != current_trading_day:
                setup_logged_today = False
                current_trading_day = today_str

            if setup_logged_today:
                print(f"[{now.strftime('%H:%M:%S')} UTC] Trade already taken today. Waiting for tomorrow...", end='\r')
                time.sleep(60)
                continue

            df = fetch_live_data()
            if df.empty:
                time.sleep(60)
                continue

            unique_dates = pd.Series(df.index.date).unique()
            if len(unique_dates) < 2:
                time.sleep(60)
                continue

            yesterday_str = str(unique_dates[-2])
            prev_day_data = df.loc[yesterday_str]
            current_day_data = df.loc[today_str] if today_str in df.index else pd.DataFrame()

            if current_day_data.empty:
                print(f"[{now.strftime('%H:%M:%S')} UTC] Market closed or no data for today yet.", end='\r')
                time.sleep(60)
                continue

            try:
                pivots = calculate_daily_pivots(
                    prev_day_data['high'].max(), 
                    prev_day_data['low'].min(), 
                    prev_day_data['close'].iloc[-1]
                )
            except ValueError:
                time.sleep(60)
                continue

            opening_range = current_day_data.loc[f"{today_str} 13:30:00":f"{today_str} 14:00:00"]
            if opening_range.empty or len(opening_range) < 30:
                print(f"[{now.strftime('%H:%M:%S')} UTC] Waiting for Opening Range to form (14:00 UTC)...", end='\r')
                time.sleep(60)
                continue
                
            or_high = opening_range['high'].max()
            or_low = opening_range['low'].min()

            if now.hour < 15:
                print(f"[{now.strftime('%H:%M:%S')} UTC] OR Formed: {or_high:.2f} / {or_low:.2f}. Waiting for 15:00 UTC Sniper Window...", end='\r')
                time.sleep(60)
                continue
            
            if now.hour >= 18:
                print(f"[{now.strftime('%H:%M:%S')} UTC] Trading window closed for the day.", end='\r')
                time.sleep(60)
                continue

            tracker = US30SessionTracker(or_high=or_high, or_low=or_low, daily_pivots=pivots)
            sniper_window_data = current_day_data.loc[f"{today_str} 15:00:00":]
            if sniper_window_data.empty:
                time.sleep(60)
                continue
                
            latest_time = sniper_window_data.index[-1]
            candle_1m = sniper_window_data.iloc[-1].to_dict()
            
            floor_5m = latest_time.floor('5min')
            current_5m_window = sniper_window_data.loc[floor_5m:latest_time]
            
            candle_5m = {
                'open': current_5m_window['open'].iloc[0],
                'high': current_5m_window['high'].max(),
                'low': current_5m_window['low'].min(),
                'close': current_5m_window['close'].iloc[-1],
            }

            print(f"[{now.strftime('%H:%M:%S')} UTC] SNIPER ACTIVE | Price: {candle_1m['close']:.2f} | Scanning tick-by-tick...", end='\r')

            payload = tracker.update_state(candle_5m, candle_1m)
            
            if payload:
                raw_entry = payload['context']['close_price']
                central_pivot = pivots['P']
                
                is_bull_trap = 'Opening Range Low' in payload['trigger'] and raw_entry > central_pivot
                is_bear_trap = 'Opening Range High' in payload['trigger'] and raw_entry < central_pivot
                
                if not is_bull_trap and not is_bear_trap:
                    print(f"\n\n{Color.MAGENTA}======================================================{Color.RESET}")
                    print(f"🚨 {Color.GREEN}LIVE SETUP DETECTED AT {latest_time}{Color.RESET} 🚨")
                    print(f"Trigger: {payload['trigger']}")
                    print(f"{Color.MAGENTA}======================================================{Color.RESET}")
                    
                    # --- THE MISSING TAPE GENERATOR ---
                    tape_start = latest_time - pd.Timedelta(minutes=15)
                    recent_tape = current_day_data.loc[tape_start:latest_time]
                    tape_str = "\n".join([
                        f"{idx.strftime('%H:%M')} | O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f}" 
                        for idx, row in recent_tape.iterrows()
                    ])
                    payload['recent_tape'] = tape_str
                    payload['mfe_points'] = "0"
                    payload['mae_points'] = "0"
                    payload['timestamp'] = str(latest_time)
                    # ----------------------------------
                    
                    print(f"{Color.CYAN}Calling AI for tape reading...{Color.RESET}")
                    ai_analysis = analyze_setup_with_ollama(payload)
                    
                    # --- SYNCHRONIZED REGEX ---
                    dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                    sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                    tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                    
                    if dir_match and dir_match.group(1).upper() in ['LONG', 'SHORT'] and sl_match and tp_match:
                        direction = dir_match.group(1).upper()
                        
                        risk = 75.0
                        reward = 125.0
                        
                        if direction == 'LONG':
                            sl = raw_entry - risk
                            tp = raw_entry + reward
                        else:
                            sl = raw_entry + risk
                            tp = raw_entry - reward
                            
                        print(f"\n{Color.YELLOW}🔔 EXECUTION PARAMETERS (MANUAL ENTRY) 🔔{Color.RESET}")
                        print(f"Direction:   {Color.GREEN if direction=='LONG' else Color.RED}{direction}{Color.RESET}")
                        print(f"Entry Price: {raw_entry:.2f} (Market Order)")
                        print(f"Stop Loss:   {sl:.2f} (75 points)")
                        print(f"Take Profit: {tp:.2f} (125 points)")
                        print('\a') 
                        
                        setup_logged_today = True 
                        print(f"\n{Color.CYAN}Bot is now locked for the remainder of the day.{Color.RESET}\n")

            time.sleep(60) 

        except Exception as e:
            print(f"\n⚠️ Live Feed Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_live_bot()