import pandas as pd
import re
import os
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing Institutional Breakout Engine...{Color.RESET}")
    df = load_and_prep_data(csv_filepath)
    unique_dates = pd.Series(df.index.date).unique()
    all_logged_setups = []

    for i in range(1, len(unique_dates)):
        current_date_str = str(unique_dates[i])
        prev_day_data, current_day_data = df.loc[str(unique_dates[i-1])], df.loc[current_date_str]
        
        if prev_day_data.empty or current_day_data.empty: continue
        try: pivots = calculate_daily_pivots(prev_day_data['high'].max(), prev_day_data['low'].min(), prev_day_data['close'].iloc[-1])
        except ValueError: continue

        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots)
        
        if daily_setups:
            for setup in daily_setups:
                # 1. TIME FILTER: "The Morning Drive" (Skip after 12:00 PM NY Time)
                trigger_time = pd.to_datetime(setup['timestamp'])
                if trigger_time.hour >= 16:
                    continue

                print(f"{Color.GREEN}🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}{Color.RESET}")
                ai_analysis = analyze_setup_with_ollama(setup)
                
                entry_price = setup.get('context', {}).get('close_price', 0)
                setup['trade_outcome'] = "Skipped"
                setup['pnl'], setup['holding_time_mins'] = 0.0, 0
                
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                if dir_match and dir_match.group(1).upper() != 'NONE' and sl_match and tp_match:
                    direction = dir_match.group(1).upper()
                    sl = float(sl_match.group(1).replace(',', ''))
                    tp = float(tp_match.group(1).replace(',', ''))
                    
                    # 2. CAP: 85-point Goldilocks Cap
                    if abs(entry_price - sl) > 85:
                        print(f"{Color.RED}▶ TRADE SKIPPED: Risk > 85 points.{Color.RESET}")
                        continue

                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    outcome, exit_price, exit_time = "Closed Manually", future_data['close'].iloc[-1] if not future_data.empty else entry_price, future_data.index[-1] if not future_data.empty else trigger_time
                    
                    # 3. PURE FORWARD WALK (Let the Edge play out)
                    for idx, candle in future_data.iloc[1:].iterrows():
                        high, low = candle['high'], candle['low']
                        
                        if direction == 'LONG':
                            if low <= sl:
                                outcome = "Hit Stop Loss 🛑"
                                exit_price, exit_time = sl, idx
                                break
                            elif high >= tp:
                                outcome = "Hit Take Profit 🎯"
                                exit_price, exit_time = tp, idx
                                break
                                
                        elif direction == 'SHORT':
                            if high >= sl:
                                outcome = "Hit Stop Loss 🛑"
                                exit_price, exit_time = sl, idx
                                break
                            elif low <= tp:
                                outcome = "Hit Take Profit 🎯"
                                exit_price, exit_time = tp, idx
                                break
                    
                    pnl = exit_price - entry_price if direction == 'LONG' else entry_price - exit_price
                    setup['trade_outcome'] = f"{outcome} at {exit_price:.2f}"
                    setup['pnl'] = round(pnl, 2)
                    setup['holding_time_mins'] = round((exit_time - trigger_time).total_seconds() / 60.0, 1)
                    
                    color = Color.GREEN if pnl > 0 else Color.RED
                    print(f"{color}▶ OUTCOME: {direction} | {outcome} | PNL: {setup['pnl']} pts{Color.RESET}")
                    
                    all_logged_setups.append(setup)

    # EXPORT TO CSV
    if all_logged_setups:
        os.makedirs('results', exist_ok=True)
        export_df = pd.DataFrame([{
            'timestamp': t['timestamp'],
            'trigger': t['trigger'],
            'outcome': t['trade_outcome'],
            'pnl': t['pnl'],
            'holding_time': t['holding_time_mins']
        } for t in all_logged_setups])
        export_df.to_csv('results/trade_log.csv', index=False)

if __name__ == "__main__":
    run_master_backtest("data/historical_us30_1m.csv")