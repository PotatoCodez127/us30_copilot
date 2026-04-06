import pandas as pd
from datetime import datetime
import re

from src.math_engine.pivots import calculate_daily_pivots
from src.strategy.state_machine import US30SessionTracker
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

SLIPPAGE_POINTS = 1.5 

def run_replay_test(target_date: str):
    print(f"{Color.CYAN}⏪ INITIALIZING LIVE REPLAY ENGINE for {target_date}{Color.RESET}")
    
    df = pd.read_csv("data/historical_us30_1m.csv")
    df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
    df.set_index('datetime', inplace=True)
    
    unique_dates = pd.Series(df.index.date).unique()
    date_objs = [str(d) for d in unique_dates]
    
    if target_date not in date_objs:
        print(f"Date {target_date} not found in CSV.")
        return
        
    day_idx = date_objs.index(target_date)
    prev_day_str = date_objs[day_idx - 1]
    
    prev_day_data = df.loc[prev_day_str]
    current_day_data = df.loc[target_date]
    
    pivots = calculate_daily_pivots(prev_day_data['high'].max(), prev_day_data['low'].min(), prev_day_data['close'].iloc[-1])
    
    opening_range = current_day_data.loc[f"{target_date} 13:30:00":f"{target_date} 14:00:00"]
    or_high = opening_range['high'].max()
    or_low = opening_range['low'].min()
    
    print(f"Opening Range: High {or_high:.2f} | Low {or_low:.2f} | Daily Pivot: {pivots['P']:.2f}")
    
    tracker = US30SessionTracker(or_high=or_high, or_low=or_low, daily_pivots=pivots)
    sniper_window = current_day_data.loc[f"{target_date} 15:00:00":f"{target_date} 17:59:00"]
    setup_logged = False
    
    for i in range(len(sniper_window)):
        if setup_logged:
            break 
            
        current_time = sniper_window.index[i]
        candle_1m = sniper_window.iloc[i].to_dict()
        
        floor_5m = current_time.floor('5min')
        current_5m_window = sniper_window.loc[floor_5m:current_time]
        
        candle_5m = {
            'open': current_5m_window['open'].iloc[0],
            'high': current_5m_window['high'].max(),
            'low': current_5m_window['low'].min(),
            'close': current_5m_window['close'].iloc[-1],
        }
        
        payload = tracker.update_state(candle_5m, candle_1m)
        
        if payload:
            raw_entry = payload['context']['close_price']
            central_pivot = pivots['P']
            
            is_bull_trap = 'Opening Range Low' in payload['trigger'] and raw_entry > central_pivot
            is_bear_trap = 'Opening Range High' in payload['trigger'] and raw_entry < central_pivot
            
            if not is_bull_trap and not is_bear_trap:
                print(f"\n{Color.GREEN}🎯 LIVE LOGIC TRIGGERED EXACTLY AT: {current_time}{Color.RESET}")
                print(f"Trigger: {payload['trigger']}")
                
                tape_start = current_time - pd.Timedelta(minutes=15)
                recent_tape = current_day_data.loc[tape_start:current_time]
                tape_str = "\n".join([
                    f"{idx.strftime('%H:%M')} | O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f}" 
                    for idx, row in recent_tape.iterrows()
                ])
                payload['recent_tape'] = tape_str
                payload['mfe_points'] = "0"
                payload['mae_points'] = "0"
                payload['timestamp'] = str(current_time)
                
                ai_analysis = analyze_setup_with_ollama(payload)
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                if dir_match and dir_match.group(1).upper() in ['LONG', 'SHORT'] and sl_match and tp_match: 
                    direction = dir_match.group(1).upper()
                    print(f"Action: {direction} @ {raw_entry:.2f}")
                    setup_logged = True
                    
                    print(f"\n{Color.CYAN}Fast-forwarding to calculate trade outcome...{Color.RESET}")
                    risk_in_points = 75.0
                    tp_distance = 125.0
                    
                    future_data = current_day_data.loc[current_time : f"{target_date} 20:00:00+00:00"]
                    outcome = "Closed at End of Day 🌇"
                    pnl_points = 0.0
                    
                    if direction == 'LONG':
                        entry_price = raw_entry + SLIPPAGE_POINTS
                        sl = entry_price - risk_in_points
                        tp = entry_price + tp_distance
                        be_hit = False
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            
                            # 1. HARD TAKE PROFIT (Broker priority)
                            if high >= tp:
                                outcome, pnl_points = "Hit Hard Take Profit 🎯", tp - entry_price
                                break
                            
                            # 2. Break-Even Shield Update
                            if not be_hit and high >= (entry_price + risk_in_points):
                                be_hit = True
                                sl = max(sl, entry_price + 5.0)
                            
                            # 3. HARD STOP LOSS (Broker priority)
                            if low <= sl:
                                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                                pnl_points = (sl - SLIPPAGE_POINTS) - entry_price
                                break
                            
                            # 4. TIME EJECTION: 90 mins (Manual priority)
                            mins_held = (idx - current_time).total_seconds() / 60.0
                            if mins_held >= 90:
                                if current_close < entry_price:
                                    outcome, pnl_points = "Time Ejection ⏳", (current_close - SLIPPAGE_POINTS) - entry_price
                                    break
                                
                    elif direction == 'SHORT':
                        entry_price = raw_entry - SLIPPAGE_POINTS
                        sl = entry_price + risk_in_points
                        tp = entry_price - tp_distance
                        be_hit = False
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            
                            # 1. HARD TAKE PROFIT (Broker priority)
                            if low <= tp:
                                outcome, pnl_points = "Hit Hard Take Profit 🎯", entry_price - tp
                                break
                            
                            # 2. Break-Even Shield Update
                            if not be_hit and low <= (entry_price - risk_in_points):
                                be_hit = True
                                sl = min(sl, entry_price - 5.0)
                            
                            # 3. HARD STOP LOSS (Broker priority)
                            if high >= sl:
                                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                                pnl_points = entry_price - (sl + SLIPPAGE_POINTS)
                                break
                            
                            # 4. TIME EJECTION: 90 mins (Manual priority)
                            mins_held = (idx - current_time).total_seconds() / 60.0
                            if mins_held >= 90:
                                if current_close > entry_price:
                                    outcome, pnl_points = "Time Ejection ⏳", entry_price - (current_close + SLIPPAGE_POINTS)
                                    break

                    color = Color.GREEN if pnl_points > 0 else Color.RED
                    print(f"{color}▶ REPLAY OUTCOME: {outcome} | PnL: {round(pnl_points, 2)} pts{Color.RESET}\n")

if __name__ == "__main__":
    run_replay_test("2026-01-29") # You can test that exact date!