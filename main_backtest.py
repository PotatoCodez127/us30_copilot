import pandas as pd
import re
import os
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

SLIPPAGE_POINTS = 1.5 

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

# =======================================================
# 🧠 TEST 3: THE SEMANTIC TRANSLATOR
# =======================================================
def build_semantic_tape(current_day_data, trigger_time):
    """Translates raw OHLC numbers into a semantic story for the LLM."""
    tape_start = trigger_time - pd.Timedelta(minutes=15)
    recent_tape = current_day_data.loc[tape_start:trigger_time]

    tape_lines = []
    for idx, row in recent_tape.iterrows():
        time_str = idx.strftime('%H:%M')
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        
        # 1. Math
        point_change = c - o
        total_range = h - l
        body = abs(c - o)
        if total_range == 0: total_range = 0.1
        
        # 2. Direction
        direction = "Bullish" if point_change > 0 else "Bearish" if point_change < 0 else "Neutral"
        
        # 3. Shape Analysis
        if body <= (total_range * 0.25):
            shape = "Indecision/Doji"
        elif body >= (total_range * 0.75):
            shape = "Strong Momentum"
        else:
            shape = "Standard Candle"
            
        # 4. Volatility Context
        vol = "High Volatility" if total_range > 30 else "Low Volatility" if total_range < 10 else "Normal Volatility"
        
        # 5. The Semantic String
        tape_lines.append(f"[{time_str}] {direction} | Net: {point_change:+.1f} pts | {shape} | {vol}")
        
    return "\n".join(tape_lines)
# =======================================================


def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing 11 AM Sniper Engine (Golden Window Edition)...{Color.RESET}")
    
    # --- DESTROY GHOST FILES ---
    if os.path.exists('results/trade_log.csv'):
        os.remove('results/trade_log.csv')
    
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
        trade_taken_today = False 
        
        if daily_setups:
            for setup in daily_setups:
                if trade_taken_today:
                    continue 

                trigger_time = pd.to_datetime(setup['timestamp'])
                raw_entry = setup.get('context', {}).get('close_price', 0)
                
                # =======================================================
                # 🛡️ THE QUANTITATIVE FILTERS (Hard-Coded Edge)
                # =======================================================
                # 1. Filter out the Mid-Week Chop
                if trigger_time.day_name() == 'Wednesday':
                    continue 
                
                # 2. The Golden Window: Only trade between 15:00 and 15:30 UTC
                if trigger_time.hour != 15 or trigger_time.minute > 30:
                    continue 
                # =======================================================
                
                central_pivot = pivots['P']
                if 'Opening Range Low' in setup['trigger'] and raw_entry > central_pivot:
                    continue 
                if 'Opening Range High' in setup['trigger'] and raw_entry < central_pivot:
                    continue 
                
                # print(f"{Color.YELLOW}🔍 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']} | Level: {setup['trigger']}{Color.RESET}")
                
                # --- OVERWRITE RAW TAPE WITH SEMANTIC TAPE ---
                setup['recent_tape'] = build_semantic_tape(current_day_data, trigger_time)
                # ---------------------------------------------
                
                ai_analysis = analyze_setup_with_ollama(setup)
                
                # 👇 ADD THESE 3 LINES TO READ THE AI'S MIND 👇
                print(f"\n{Color.CYAN}--- AI RAW THOUGHT PROCESS ---{Color.RESET}")
                print(ai_analysis)
                print(f"{Color.CYAN}------------------------------\n{Color.RESET}")

                setup['trade_outcome'] = "Skipped"
                setup['pnl_points'], setup['holding_time_mins'] = 0.0, 0
                setup['sl_distance'], setup['tp_distance'] = 0.0, 0.0
                
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                if dir_match and dir_match.group(1).upper() in ['LONG', 'SHORT'] and sl_match and tp_match: 
                    direction = dir_match.group(1).upper()
                    
                    risk_in_points = 75.0
                    setup['sl_distance'] = risk_in_points
                    setup['tp_distance'] = 125.0 

                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    trigger_idx = future_data.index[0] if not future_data.empty else trigger_time
                    outcome = "Closed at End of Day 🌇"
                    
                    pnl_points = 0.0
                    
                    if direction == 'LONG':
                        entry_price = raw_entry + SLIPPAGE_POINTS
                        sl = entry_price - risk_in_points 
                        tp = entry_price + 125.0 
                        exit_price = future_data['close'].iloc[-1] if not future_data.empty else entry_price
                        exit_time = future_data.index[-1] if not future_data.empty else trigger_idx

                        be_hit = False
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            
                            if high >= tp:
                                outcome, exit_price, exit_time = "Hit Hard Take Profit 🎯", tp, idx
                                break
                                
                            if not be_hit and high >= (entry_price + risk_in_points):
                                be_hit = True
                                sl = max(sl, entry_price + 5.0)
                            
                            if low <= sl:
                                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                                exit_price, exit_time = sl - SLIPPAGE_POINTS, idx
                                break
                            
                            mins_held = (idx - trigger_time).total_seconds() / 60.0
                            if mins_held >= 90:
                                if current_close < entry_price: 
                                    outcome, exit_price, exit_time = "Time Ejection ⏳", current_close - SLIPPAGE_POINTS, idx
                                    break
                                
                        pnl_points = exit_price - entry_price

                    elif direction == 'SHORT':
                        entry_price = raw_entry - SLIPPAGE_POINTS
                        sl = entry_price + risk_in_points 
                        tp = entry_price - 125.0 
                        exit_price = future_data['close'].iloc[-1] if not future_data.empty else entry_price
                        exit_time = future_data.index[-1] if not future_data.empty else trigger_idx

                        be_hit = False
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            
                            if low <= tp:
                                outcome, exit_price, exit_time = "Hit Hard Take Profit 🎯", tp, idx
                                break
                                
                            if not be_hit and low <= (entry_price - risk_in_points):
                                be_hit = True
                                sl = min(sl, entry_price - 5.0)
                            
                            if high >= sl:
                                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                                exit_price, exit_time = sl + SLIPPAGE_POINTS, idx
                                break
                            
                            mins_held = (idx - trigger_time).total_seconds() / 60.0
                            if mins_held >= 90:
                                if current_close > entry_price: 
                                    outcome, exit_price, exit_time = "Time Ejection ⏳", current_close + SLIPPAGE_POINTS, idx
                                    break
                                
                        pnl_points = entry_price - exit_price 

                    setup['trade_outcome'] = f"[{direction}] {outcome} at {exit_price:.2f}"
                    setup['pnl_points'] = round(pnl_points, 2)
                    setup['holding_time_mins'] = round((exit_time - trigger_time).total_seconds() / 60.0, 1)
                    
                    color = Color.GREEN if pnl_points > 0 else Color.RED
                    print(f"{color}▶ EXECUTED {direction}: {outcome} | PnL: {setup['pnl_points']} pts{Color.RESET}")
                    
                    all_logged_setups.append(setup)
                    trade_taken_today = True 

    if all_logged_setups:
        import json # Ensure json is imported at the top of your file
        
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
        
        # =======================================================
        # 🧠 RAG HARVESTER: Saving Semantic Tapes for the AI
        # =======================================================
        memory_data = []
        for t in all_logged_setups:
            # Only save the extreme winners and losers for the AI to learn from
            if t['pnl_points'] >= 100.0 or t['pnl_points'] <= -50.0:
                classification = "VALID BREAKOUT" if t['pnl_points'] > 0 else "TRAP / CHOP"
                memory_data.append({
                    'id': str(t['timestamp']).replace(' ', '_'),
                    'tape': t['recent_tape'],
                    'classification': classification,
                    'pnl': t['pnl_points']
                })
                
        # Append to a master memory bank
        memory_file = 'results/master_memory_bank.json'
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                existing_memory = json.load(f)
            existing_memory.extend(memory_data)
        else:
            existing_memory = memory_data
            
        with open(memory_file, 'w') as f:
            json.dump(existing_memory, f, indent=4)
        # =======================================================

if __name__ == "__main__":
    run_master_backtest("data/historical_us30_1m.csv")