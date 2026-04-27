import pandas as pd
import re
import os
import json
import chromadb
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama

# 1. NEW IMPORT: Bring in the AI sandbox variables
from src.strategy.us30_ai_config import SL_RISK_POINTS, TP_REWARD_POINTS, MAX_HOLDING_MINUTES

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

SLIPPAGE_POINTS = 1.5 

def simulate_trade(direction: str, raw_entry: float, future_data: pd.DataFrame, trigger_time: pd.Timestamp):
    """Simulates the trade using AI Sandbox parameters."""
    if future_data.empty:
        return "No Future Data", raw_entry, trigger_time, 0.0

    trigger_idx = future_data.index[0]
    outcome = "Closed at End of Day 🌇"
    
    if direction == 'LONG':
        entry_price = raw_entry + SLIPPAGE_POINTS
        sl = entry_price - SL_RISK_POINTS
        tp = entry_price + TP_REWARD_POINTS
        exit_price = future_data['close'].iloc[-1]
        exit_time = future_data.index[-1]
        be_hit = False

        for idx, candle in future_data.iloc[1:].iterrows():
            high, low, current_close = candle['high'], candle['low'], candle['close']
            
            if high >= tp:
                return "Hit Hard Take Profit 🎯", tp, idx, (tp - entry_price)
                
            if not be_hit and high >= (entry_price + SL_RISK_POINTS):
                be_hit = True
                sl = max(sl, entry_price + 5.0)
            
            if low <= sl:
                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                exit_price = sl - SLIPPAGE_POINTS
                return outcome, exit_price, idx, (exit_price - entry_price)
            
            mins_held = (idx - trigger_time).total_seconds() / 60.0
            if mins_held >= MAX_HOLDING_MINUTES:
                if current_close < entry_price: 
                    exit_price = current_close - SLIPPAGE_POINTS
                    return "Time Ejection ⏳", exit_price, idx, (exit_price - entry_price)
                    
        return outcome, exit_price, exit_time, (exit_price - entry_price)

    elif direction == 'SHORT':
        entry_price = raw_entry - SLIPPAGE_POINTS
        sl = entry_price + SL_RISK_POINTS
        tp = entry_price - TP_REWARD_POINTS
        exit_price = future_data['close'].iloc[-1]
        exit_time = future_data.index[-1]
        be_hit = False

        for idx, candle in future_data.iloc[1:].iterrows():
            high, low, current_close = candle['high'], candle['low'], candle['close']
            
            if low <= tp:
                return "Hit Hard Take Profit 🎯", tp, idx, (entry_price - tp)
                
            if not be_hit and low <= (entry_price - SL_RISK_POINTS):
                be_hit = True
                sl = min(sl, entry_price - 5.0)
            
            if high >= sl:
                outcome = "Hit Break-Even 🛡️" if be_hit else "Hit Hard Stop 🛑"
                exit_price = sl + SLIPPAGE_POINTS
                return outcome, exit_price, idx, (entry_price - exit_price)
            
            mins_held = (idx - trigger_time).total_seconds() / 60.0
            if mins_held >= MAX_HOLDING_MINUTES:
                if current_close > entry_price: 
                    exit_price = current_close + SLIPPAGE_POINTS
                    return "Time Ejection ⏳", exit_price, idx, (entry_price - exit_price)
                    
        return outcome, exit_price, exit_time, (entry_price - exit_price)

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

def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing 11 AM Sniper Engine (RAG-Powered Edition)...{Color.RESET}")
    
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
                
                if trigger_time.day_name() == 'Wednesday':
                    continue 
                
                if trigger_time.hour != 15 or trigger_time.minute > 30:
                    continue 
                
                central_pivot = pivots['P']
                if 'Opening Range Low' in setup['trigger'] and raw_entry > central_pivot:
                    continue 
                if 'Opening Range High' in setup['trigger'] and raw_entry < central_pivot:
                    continue 
                
                print(f"{Color.YELLOW}🔍 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']} | Level: {setup['trigger']}{Color.RESET}")
                
                current_semantic_tape = build_semantic_tape(current_day_data, trigger_time)
                setup['recent_tape'] = current_semantic_tape
                
                setup['historical_context'] = "No historical data available."
                try:
                    db_path = os.path.join(os.getcwd(), "data", "rag_db")
                    if os.path.exists(db_path):
                        rag_client = chromadb.PersistentClient(path=db_path)
                        rag_collection = rag_client.get_or_create_collection(name="us30_setups")
                        
                        if rag_collection.count() > 0:
                            print(f"{Color.CYAN}🧠 Querying RAG Memory Bank for similar setups...{Color.RESET}")
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
                                setup['historical_context'] = hist_text
                except Exception as e:
                    print(f"{Color.RED}⚠️ RAG Retrieval skipped or failed: {e}{Color.RESET}")

                ai_analysis = analyze_setup_with_ollama(setup)
                
                setup['trade_outcome'] = "Skipped"
                setup['pnl_points'], setup['holding_time_mins'] = 0.0, 0
                setup['sl_distance'], setup['tp_distance'] = 0.0, 0.0
                
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                if dir_match and dir_match.group(1).upper() in ['LONG', 'SHORT'] and sl_match and tp_match: 
                    direction = dir_match.group(1).upper()
                    
                    setup['sl_distance'] = SL_RISK_POINTS
                    setup['tp_distance'] = TP_REWARD_POINTS 

                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    
                    outcome, exit_price, exit_time, pnl_points = simulate_trade(
                        direction, raw_entry, future_data, trigger_time
                    )

                    setup['trade_outcome'] = f"[{direction}] {outcome} at {exit_price:.2f}"
                    setup['pnl_points'] = round(pnl_points, 2)
                    setup['holding_time_mins'] = round((exit_time - trigger_time).total_seconds() / 60.0, 1)
                    
                    color = Color.GREEN if pnl_points > 0 else Color.RED
                    print(f"{color}▶ EXECUTED {direction}: {outcome} | PnL: {setup['pnl_points']} pts{Color.RESET}")
                    
                    all_logged_setups.append(setup)
                    trade_taken_today = True 

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
        
        try:
            memory_data = []
            for t in all_logged_setups:
                if t['pnl_points'] >= 100.0 or t['pnl_points'] <= -50.0:
                    classification = "VALID BREAKOUT" if t['pnl_points'] > 0 else "TRAP / CHOP"
                    memory_data.append({
                        'id': str(t['timestamp']).replace(' ', '_'),
                        'tape': t['recent_tape'],
                        'classification': classification,
                        'pnl': t['pnl_points']
                    })
                    
            if memory_data:
                memory_file = os.path.join('results', 'master_memory_bank.json')
                existing_memory = []
                
                if os.path.exists(memory_file):
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        try:
                            existing_memory = json.load(f)
                        except Exception:
                            print(f"{Color.YELLOW}⚠️ Warning: memory bank was corrupted/empty. Overwriting with new data.{Color.RESET}")
                            existing_memory = []
                            
                existing_memory.extend(memory_data)
                
                with open(memory_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_memory, f, indent=4)
                    
        except Exception as e:
            print(f"{Color.RED}🚨 Failed to save to JSON memory bank: {e}{Color.RESET}")

if __name__ == "__main__":
    run_master_backtest("data/historical_us30_1m.csv")