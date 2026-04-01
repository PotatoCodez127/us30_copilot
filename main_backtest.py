import pandas as pd
import re
import os
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

# --- ACCOUNT PARAMETERS ---
ACCOUNT_SIZE = 100000.0
RISK_PERCENT = 0.01  # Risk 1% per trade ($1,000)
# --------------------------

def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing Dynamic Risk Breakout Engine ($100k Account)...{Color.RESET}")
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
                print(f"{Color.GREEN}🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}{Color.RESET}")
                ai_analysis = analyze_setup_with_ollama(setup)
                
                entry_price = setup.get('context', {}).get('close_price', 0)
                setup['trade_outcome'] = "Skipped"
                setup['pnl_points'], setup['holding_time_mins'], setup['dollar_pnl'] = 0.0, 0, 0.0
                
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                if dir_match and dir_match.group(1).upper() != 'NONE' and sl_match and tp_match:
                    direction = dir_match.group(1).upper()
                    sl = float(sl_match.group(1).replace(',', ''))
                    tp = float(tp_match.group(1).replace(',', ''))
                    
                    # SANITY CHECKS
                    if direction == 'LONG' and (tp <= entry_price or sl >= entry_price): continue
                    if direction == 'SHORT' and (tp >= entry_price or sl <= entry_price): continue

                    # CALCULATE DYNAMIC LOT SIZE
                    risk_in_points = abs(entry_price - sl)
                    if risk_in_points == 0: continue
                    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
                    lot_size = dollar_risk / risk_in_points # Value per point

                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    outcome, exit_price, exit_time = "Closed Manually", future_data['close'].iloc[-1] if not future_data.empty else entry_price, future_data.index[-1] if not future_data.empty else pd.to_datetime(setup['timestamp'])
                    
                    # PURE FORWARD WALK
                    for idx, candle in future_data.iloc[1:].iterrows():
                        high, low = candle['high'], candle['low']
                        if direction == 'LONG':
                            if low <= sl: outcome, exit_price, exit_time = "Hit Stop Loss 🛑", sl, idx; break
                            elif high >= tp: outcome, exit_price, exit_time = "Hit Take Profit 🎯", tp, idx; break
                        elif direction == 'SHORT':
                            if high >= sl: outcome, exit_price, exit_time = "Hit Stop Loss 🛑", sl, idx; break
                            elif low <= tp: outcome, exit_price, exit_time = "Hit Take Profit 🎯", tp, idx; break
                    
                    pnl_points = exit_price - entry_price if direction == 'LONG' else entry_price - exit_price
                    dollar_pnl = pnl_points * lot_size
                    
                    setup['trade_outcome'] = f"{outcome} at {exit_price:.2f}"
                    setup['pnl_points'] = round(pnl_points, 2)
                    setup['dollar_pnl'] = round(dollar_pnl, 2)
                    setup['holding_time_mins'] = round((exit_time - pd.to_datetime(setup['timestamp'])).total_seconds() / 60.0, 1)
                    
                    color = Color.GREEN if dollar_pnl > 0 else Color.RED
                    print(f"{color}▶ {direction} | {outcome} | Pts: {setup['pnl_points']} | PNL: ${setup['dollar_pnl']}{Color.RESET}")
                    
                    all_logged_setups.append(setup)

    if all_logged_setups:
        os.makedirs('results', exist_ok=True)
        export_df = pd.DataFrame([{
            'timestamp': t['timestamp'],
            'trigger': t['trigger'],
            'outcome': t['trade_outcome'],
            'pnl_points': t['pnl_points'],
            'dollar_pnl': t['dollar_pnl'],
            'holding_time': t['holding_time_mins']
        } for t in all_logged_setups])
        export_df.to_csv('results/trade_log.csv', index=False)

if __name__ == "__main__":
    run_master_backtest("data/historical_us30_1m.csv")