import time
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import re
import os
import chromadb

from src.math_engine.pivots import calculate_daily_pivots
from src.strategy.state_machine import US30SessionTracker
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

TICKER = "^DJI"

def build_semantic_tape(current_day_data, trigger_time):
    """Translates raw OHLC numbers into a semantic story for the LLM."""
    tape_start = trigger_time - pd.Timedelta(minutes=15)
    recent_tape = current_day_data.loc[tape_start:trigger_time]

    tape_lines = []
    for idx, row in recent_tape.iterrows():
        time_str = idx.strftime('%H:%M')
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        
        point_change = c - o
        total_range = h - l
        body = abs(c - o)
        if total_range == 0: total_range = 0.1
        
        direction = "Bullish" if point_change > 0 else "Bearish" if point_change < 0 else "Neutral"
        
        if body <= (total_range * 0.25):
            shape = "Indecision/Doji"
        elif body >= (total_range * 0.75):
            shape = "Strong Momentum"
        else:
            shape = "Standard Candle"
            
        vol = "High Volatility" if total_range > 30 else "Low Volatility" if total_range < 10 else "Normal Volatility"
        
        tape_lines.append(f"[{time_str}] Close: {c:.1f} | {direction} | Net: {point_change:+.1f} pts | {shape} | {vol}")
        
    return "\n".join(tape_lines)

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
    print(f"{Color.CYAN}🟢 Initializing Live US30 Copilot (RAG-Powered Edition)...{Color.RESET}")
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

            # =======================================================
            # 🛡️ THE QUANTITATIVE FILTERS
            # =======================================================
            if now.strftime('%A') == 'Wednesday':
                print(f"[{now.strftime('%H:%M:%S')} UTC] Mid-Week Chop Protocol: Bot sleeps on Wednesdays.", end='\r')
                time.sleep(60)
                continue

            if now.hour < 15:
                print(f"[{now.strftime('%H:%M:%S')} UTC] OR Formed: {or_high:.2f} / {or_low:.2f}. Waiting for 15:00 UTC Sniper Window...", end='\r')
                time.sleep(60)
                continue
            
            if now.hour > 15 or (now.hour == 15 and now.minute > 30):
                print(f"[{now.strftime('%H:%M:%S')} UTC] Golden Window Closed. No valid momentum today.", end='\r')
                time.sleep(60)
                continue
            # =======================================================

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
                    
                    # --- THE SEMANTIC TAPE GENERATOR ---
                    current_semantic_tape = build_semantic_tape(current_day_data, latest_time)
                    payload['recent_tape'] = current_semantic_tape
                    payload['mfe_points'] = "0"
                    payload['mae_points'] = "0"
                    payload['timestamp'] = str(latest_time)
                    
                    # --- RAG RETRIEVAL (Query ChromaDB) ---
                    payload['historical_context'] = "No historical data available."
                    try:
                        db_path = os.path.join(os.getcwd(), "data", "rag_db")
                        if os.path.exists(db_path):
                            rag_client = chromadb.PersistentClient(path=db_path)
                            rag_collection = rag_client.get_or_create_collection(name="us30_setups")
                            
                            if rag_collection.count() > 0:
                                print(f"{Color.CYAN}🧠 Querying RAG Memory Bank for similar live setups...{Color.RESET}")
                                results = rag_collection.query(
                                    query_texts=[current_semantic_tape],
                                    n_results=3 
                                )
                                
                                hist_text = ""
                                if results['documents'] and len(results['documents'][0]) > 0:
                                    for idx, doc in enumerate(results['documents'][0]):
                                        meta = results['metadatas'][0][idx]
                                        hist_text += f"--- SIMILAR MATCH #{idx+1} ---\n"
                                        hist_text += f"TAPE:\n{doc}\n"
                                        hist_text += f"ACTUAL OUTCOME: {meta['classification']} (PnL: {meta['pnl']} pts)\n\n"
                                    payload['historical_context'] = hist_text
                    except Exception as e:
                        print(f"{Color.RED}⚠️ RAG Retrieval skipped or failed: {e}{Color.RESET}")
                    # ------------------------------------------
                    
                    print(f"{Color.CYAN}Calling AI for RAG-powered tape reading...{Color.RESET}")
                    ai_analysis = analyze_setup_with_ollama(payload)
                    
                    dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                    sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                    tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                    
                    if dir_match and dir_match.group(1).upper() in ['LONG', 'SHORT'] and sl_match and tp_match:
                        direction = dir_match.group(1).upper()
                        
                        # --- WIDENED BOUNDS ---
                        risk = 150.0
                        reward = 250.0
                        
                        if direction == 'LONG':
                            sl = raw_entry - risk
                            tp = raw_entry + reward
                        else:
                            sl = raw_entry + risk
                            tp = raw_entry - reward
                            
                        print(f"\n{Color.YELLOW}🔔 EXECUTION PARAMETERS (MANUAL ENTRY) 🔔{Color.RESET}")
                        print(f"Direction:   {Color.GREEN if direction=='LONG' else Color.RED}{direction}{Color.RESET}")
                        print(f"Entry Price: {raw_entry:.2f} (Market Order)")
                        print(f"Stop Loss:   {sl:.2f} (150 points)")
                        print(f"Take Profit: {tp:.2f} (250 points)")
                        print('\a') 
                        
                        setup_logged_today = True 
                        print(f"\n{Color.CYAN}Bot is now locked for the remainder of the day.{Color.RESET}\n")

            time.sleep(60) 

        except Exception as e:
            print(f"\n⚠️ Live Feed Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_live_bot()