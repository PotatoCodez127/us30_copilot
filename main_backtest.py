import pandas as pd
import re
import os
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

# --- REALISTIC ACCOUNT & FRICTION PARAMETERS ---
ACCOUNT_SIZE = 100000.0
RISK_PERCENT = 0.01  # Risk 1% per trade ($1,000)
COMMISSION_PER_LOT = 5.00 
SLIPPAGE_POINTS = 1.5 
# -----------------------------------------------

def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing Final Production Engine (God Mode)...{Color.RESET}")
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
                trigger_time = pd.to_datetime(setup['timestamp'])
                
                # 1. STRICT FORENSIC FILTERS
                if trigger_time.hour != 14: continue # 10 AM NY hour only
                if 'Pivot' in setup['trigger']: continue # No pivot noise
                
                print(f"{Color.GREEN}🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}{Color.RESET}")
                ai_analysis = analyze_setup_with_ollama(setup)
                
                base_entry = setup.get('context', {}).get('close_price', 0)
                setup['trade_outcome'] = "Skipped"
                setup['pnl_points'], setup['holding_time_mins'], setup['dollar_pnl'] = 0.0, 0, 0.0
                setup['sl_distance'], setup['tp_distance'] = 0.0, 0.0
                
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                # 2. LONG ONLY FILTER
                if dir_match and dir_match.group(1).upper() == 'LONG' and sl_match and tp_match: 
                    direction = dir_match.group(1).upper()
                    sl = float(sl_match.group(1).replace(',', ''))
                    tp = float(tp_match.group(1).replace(',', ''))
                    
                    # Entry Slippage
                    entry_price = base_entry + SLIPPAGE_POINTS
                    
                    if tp <= entry_price or sl >= entry_price: continue
                    
                    risk_in_points = abs(entry_price - sl)
                    
                    # 3. THE "CHOP ZONE" FILTER (Minimum 50pt Stop)
                    if risk_in_points < 50: 
                        print(f"{Color.YELLOW}▶ SKIPPED: AI set stop too tight ({risk_in_points:.1f} pts). Evading chop.{Color.RESET}")
                        continue 
                    
                    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
                    lot_size = dollar_risk / risk_in_points
                    total_commission = lot_size * COMMISSION_PER_LOT

                    setup['sl_distance'] = risk_in_points
                    setup['tp_distance'] = abs(tp - entry_price)

                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    outcome, exit_price, exit_time = "Closed at End of Day", future_data['close'].iloc[-1] if not future_data.empty else entry_price, future_data.index[-1] if not future_data.empty else trigger_time
                    
                    # 4. HOME RUN TRAILING PROTOCOL
                    tp_hit = False
                    highest_seen = entry_price
                    
                    for idx, candle in future_data.iloc[1:].iterrows():
                        high, low = candle['high'], candle['low']
                        highest_seen = max(highest_seen, high)
                        
                        if not tp_hit and high >= tp:
                            tp_hit = True
                            sl = entry_price + 5.0 # Move to Break-Even + 5
                            
                        if tp_hit:
                            sl = max(sl, highest_seen - 50.0) # Trail by 50 pts
                        
                        if low <= sl:
                            outcome = "Hit Trailing Stop 🏃‍♂️💨" if tp_hit else "Hit Hard Stop Loss 🛑"
                            exit_price = sl - SLIPPAGE_POINTS # Exit Slippage
                            exit_time = idx
                            break
                    
                    pnl_points = exit_price - entry_price
                    dollar_pnl = (pnl_points * lot_size) - total_commission
                    
                    setup['trade_outcome'] = f"{outcome} at {exit_price:.2f}"
                    setup['pnl_points'] = round(pnl_points, 2)
                    setup['dollar_pnl'] = round(dollar_pnl, 2)
                    setup['holding_time_mins'] = round((exit_time - trigger_time).total_seconds() / 60.0, 1)
                    
                    color = Color.GREEN if dollar_pnl > 0 else Color.RED
                    print(f"{color}▶ EXECUTED: {outcome} | Pts: {setup['pnl_points']} | PNL: ${setup['dollar_pnl']}{Color.RESET}")
                    
                    all_logged_setups.append(setup)

    if all_logged_setups:
        os.makedirs('results', exist_ok=True)
        export_df = pd.DataFrame([{
            'timestamp': t['timestamp'],
            'trigger': t['trigger'],
            'outcome': t['trade_outcome'],
            'pnl_points': t['pnl_points'],
            'dollar_pnl': t['dollar_pnl'],
            'holding_time': t['holding_time_mins'],
            'sl_distance': t.get('sl_distance', 0),
            'tp_distance': t.get('tp_distance', 0)
        } for t in all_logged_setups])
        export_df.to_csv('results/trade_log.csv', index=False)

if __name__ == "__main__":
    run_master_backtest("data/historical_us30_1m.csv")