import pandas as pd
import re
import os
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

# --- MARKET FRICTION ---
SLIPPAGE_POINTS = 1.5 
# -----------------------

def generate_tradingview_levels():
    q4_start = 48362
    eq_start = 48555
    spacing = 385
    levels_count = 14
    
    levels = []
    for i in range(-levels_count, levels_count + 1):
        levels.append(q4_start + (i * spacing))
        levels.append(eq_start + (i * spacing))
        
    return sorted(levels)

Q4_LEVELS = generate_tradingview_levels()

def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing Full Discovery Engine (Unrestricted Raw Data)...{Color.RESET}")
    df = load_and_prep_data(csv_filepath)
    unique_dates = pd.Series(df.index.date).unique()
    all_logged_setups = []

    for i in range(1, len(unique_dates)):
        current_date_str = str(unique_dates[i])
        prev_day_data, current_day_data = df.loc[str(unique_dates[i-1])], df.loc[current_date_str]
        
        if prev_day_data.empty or current_day_data.empty: continue
        try: 
            pivots = calculate_daily_pivots(prev_day_data['high'].max(), prev_day_data['low'].min(), prev_day_data['close'].iloc[-1])
        except ValueError: 
            continue

        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots)
        
        # trade_taken_today = False  <-- LOCKOUT REMOVED
        
        if daily_setups:
            for setup in daily_setups:
                
                # if trade_taken_today: continue <-- LOCKOUT REMOVED

                trigger_time = pd.to_datetime(setup['timestamp'])
                
                # --- ALL FORENSIC FILTERS OFF FOR DISCOVERY ---
                # We are letting the engine take EVERY setup (Pivots, Top/Bottom, All Hours)
                raw_entry = setup.get('context', {}).get('close_price', 0)
                
                print(f"{Color.YELLOW}🔍 DISCOVERY TRIGGERED: {current_date_str} at {setup['timestamp']} | Level: {setup['trigger']}{Color.RESET}")
                
                # --- AI CONFIRMATION ---
                ai_analysis = analyze_setup_with_ollama(setup)
                
                setup['trade_outcome'] = "Skipped"
                setup['pnl_points'], setup['holding_time_mins'] = 0.0, 0
                setup['sl_distance'], setup['tp_distance'] = 0.0, 0.0
                
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                if dir_match and dir_match.group(1).upper() in ['LONG', 'SHORT'] and sl_match and tp_match: 
                    direction = dir_match.group(1).upper()
                    
                    # --- REALISTIC RISK MAPPING KEEPT INTACT ---
                    risk_in_points = 75.0
                    setup['sl_distance'] = risk_in_points
                    setup['tp_distance'] = 125.0 

                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    trigger_idx = future_data.index[0] if not future_data.empty else trigger_time
                    outcome = "Closed at End of Day 🌇"
                    
                    pnl_points = 0.0
                    
                    # ==========================================
                    # LONG EXECUTION LOGIC 
                    # ==========================================
                    if direction == 'LONG':
                        entry_price = raw_entry + SLIPPAGE_POINTS
                        sl = entry_price - risk_in_points 
                        tp = entry_price + 125.0 
                        exit_price = future_data['close'].iloc[-1] if not future_data.empty else entry_price
                        exit_time = future_data.index[-1] if not future_data.empty else trigger_idx

                        tp_hit = False
                        be_hit = False
                        highest_seen = entry_price
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            highest_seen = max(highest_seen, high)
                            
                            # HARD TAKE PROFIT
                            if high >= tp:
                                outcome, exit_price, exit_time = "Hit Hard Take Profit 🎯", tp, idx
                                break
                            
                            # TIME EJECTION: 90 mins
                            mins_held = (idx - trigger_time).total_seconds() / 60.0
                            if mins_held >= 90:
                                if current_close < entry_price: 
                                    outcome, exit_price, exit_time = "Time Ejection ⏳", current_close - SLIPPAGE_POINTS, idx
                                    break
                                    
                            # Break-Even
                            if not be_hit and high >= (entry_price + risk_in_points):
                                be_hit = True
                                sl = max(sl, entry_price + 5.0)
                            
                            # Stop Loss
                            if low <= sl:
                                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                                exit_price, exit_time = sl - SLIPPAGE_POINTS, idx
                                break
                                
                        pnl_points = exit_price - entry_price

                    # ==========================================
                    # SHORT EXECUTION LOGIC 
                    # ==========================================
                    elif direction == 'SHORT':
                        entry_price = raw_entry - SLIPPAGE_POINTS
                        sl = entry_price + risk_in_points 
                        tp = entry_price - 125.0 
                        exit_price = future_data['close'].iloc[-1] if not future_data.empty else entry_price
                        exit_time = future_data.index[-1] if not future_data.empty else trigger_idx

                        tp_hit = False
                        be_hit = False
                        lowest_seen = entry_price
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            lowest_seen = min(lowest_seen, low)
                            
                            # HARD TAKE PROFIT
                            if low <= tp:
                                outcome, exit_price, exit_time = "Hit Hard Take Profit 🎯", tp, idx
                                break
                            
                            # TIME EJECTION: 90 mins
                            mins_held = (idx - trigger_time).total_seconds() / 60.0
                            if mins_held >= 90:
                                if current_close > entry_price: 
                                    outcome, exit_price, exit_time = "Time Ejection ⏳", current_close + SLIPPAGE_POINTS, idx
                                    break

                            # Break-Even
                            if not be_hit and low <= (entry_price - risk_in_points):
                                be_hit = True
                                sl = min(sl, entry_price - 5.0)
                            
                            # Stop Loss
                            if high >= sl:
                                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                                exit_price, exit_time = sl + SLIPPAGE_POINTS, idx
                                break
                                
                        pnl_points = entry_price - exit_price 

                    # --- FINAL MATH & LOGGING ---
                    setup['trade_outcome'] = f"[{direction}] {outcome} at {exit_price:.2f}"
                    setup['pnl_points'] = round(pnl_points, 2)
                    setup['holding_time_mins'] = round((exit_time - trigger_time).total_seconds() / 60.0, 1)
                    
                    color = Color.GREEN if pnl_points > 0 else Color.RED
                    print(f"{color}▶ EXECUTED {direction}: {outcome} | PnL: {setup['pnl_points']} pts{Color.RESET}")
                    
                    all_logged_setups.append(setup)

    if all_logged_setups:
        os.makedirs('results', exist_ok=True)
        export_df = pd.DataFrame([{
            'timestamp': t['timestamp'],
            'trigger': t['trigger'],
            'outcome': t['trade_outcome'],
            'pnl_points': t['pnl_points'],
            'holding_time': t['holding_time_mins'],
            'sl_distance': t.get('sl_distance', 0),
            'tp_distance': t.get('tp_distance', 0)
        } for t in all_logged_setups])
        export_df.to_csv('results/trade_log.csv', index=False)

if __name__ == "__main__":
    run_master_backtest("data/historical_us30_1m.csv")