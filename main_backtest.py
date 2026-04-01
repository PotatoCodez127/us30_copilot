import pandas as pd
import re
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama
from src.database.supabase_client import log_setup_to_db

# --- TERMINAL COLORS ---
class Color:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
# -----------------------

def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing Opening Range Backtest Engine on {csv_filepath}...{Color.RESET}")
    df = load_and_prep_data(csv_filepath)
    unique_dates = pd.Series(df.index.date).unique()
    
    print(f"{Color.CYAN}📊 Found {len(unique_dates)} trading days. Beginning quantitative scan...{Color.RESET}\n")
    print("-" * 60)
    
    total_setups = 0
    all_logged_setups = []

    for i in range(1, len(unique_dates)):
        prev_date_str = str(unique_dates[i-1])
        current_date_str = str(unique_dates[i])
        
        prev_day_data = df.loc[prev_date_str]
        current_day_data = df.loc[current_date_str]
        if prev_day_data.empty or current_day_data.empty: continue
            
        try:
            pivots = calculate_daily_pivots(
                prev_day_data['high'].max(), prev_day_data['low'].min(), prev_day_data['close'].iloc[-1]
            )
        except ValueError: continue

        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots)
        
        if daily_setups:
            for setup in daily_setups:
                print(f"{Color.GREEN}🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}{Color.RESET}")
                print(f"Trigger: {setup['trigger']}")
                
                print(f"{Color.CYAN}🧠 Sending tape to AI Agent...{Color.RESET}")
                ai_analysis = analyze_setup_with_ollama(setup)
                setup['ai_risk_analysis'] = ai_analysis
                
                print(f"\n{Color.MAGENTA}" + "="*50)
                print(f"🤖 LIVE AI DESK ANALYSIS:")
                print("="*50 + f"{Color.YELLOW}")
                print(ai_analysis)
                print(f"{Color.MAGENTA}" + "="*50 + f"{Color.RESET}\n")
                
                # --- NEW: TRADE SIMULATION ENGINE ---
                entry_price = setup.get('context', {}).get('close_price', 0)
                setup['trade_outcome'] = "Parse Failed / No Trade"
                setup['pnl'] = 0.0
                
                # Extract AI Execution Data using Regex
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                if dir_match and sl_match and tp_match and entry_price > 0:
                    direction = dir_match.group(1).upper()
                    sl = float(sl_match.group(1).replace(',', ''))
                    tp = float(tp_match.group(1).replace(',', ''))
                    
                    # Grab the rest of the day's candles
                    # Grab the rest of the day's candles (Ensuring timezone-aware matching)
                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    
                    outcome = "Closed Manually (End of Session)"
                    exit_price = future_data['close'].iloc[-1] if not future_data.empty else entry_price
                    
                    # Walk forward minute-by-minute
                    for idx, candle in future_data.iloc[1:].iterrows():
                        high, low = candle['high'], candle['low']
                        
                        if direction == 'LONG':
                            if low <= sl:
                                outcome = "Hit Stop Loss 🛑"
                                exit_price = sl
                                break
                            elif high >= tp:
                                outcome = "Hit Take Profit 🎯"
                                exit_price = tp
                                break
                        elif direction == 'SHORT':
                            if high >= sl:
                                outcome = "Hit Stop Loss 🛑"
                                exit_price = sl
                                break
                            elif low <= tp:
                                outcome = "Hit Take Profit 🎯"
                                exit_price = tp
                                break
                    
                    # Calculate P/L
                    pnl = exit_price - entry_price if direction == 'LONG' else entry_price - exit_price
                    setup['trade_outcome'] = f"{outcome} at {exit_price:.2f}"
                    setup['pnl'] = round(pnl, 2)
                    
                    # Print outcome to terminal
                    color = Color.GREEN if pnl > 0 else Color.RED
                    print(f"{color}▶ TRADE OUTCOME: {direction} | {outcome} | PNL: {setup['pnl']} points{Color.RESET}")
                else:
                    print(f"{Color.RED}▶ TRADE OUTCOME: AI did not provide strict execution format.{Color.RESET}")
                # ------------------------------------

                try:
                    log_setup_to_db(setup)
                    print(f"{Color.GREEN}✅ Successfully logged to Supabase.{Color.RESET}")
                except Exception as e:
                    print(f"{Color.RED}❌ Failed to log setup: {e}{Color.RESET}")
                    
                print("-" * 50)
                all_logged_setups.append(setup)
                total_setups += 1

    print(f"\n{Color.CYAN}🏁 Backtest Complete. Processed {total_setups} total setups.{Color.RESET}")

    # Write to text file with Outcomes
    output_filename = "backtest_results.txt"
    if all_logged_setups:
        print(f"{Color.CYAN}💾 Saving detailed results to {output_filename}...{Color.RESET}")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("🏆 US30 COPILOT - QUANTITATIVE BACKTEST RESULTS\n")
            f.write("=" * 60 + "\n\n")
            
            for i, trade in enumerate(all_logged_setups):
                f.write(f"TRADE #{i+1} | {trade.get('timestamp', 'Unknown Time')}\n")
                f.write(f"TRIGGER: {trade.get('trigger', 'Unknown')}\n")
                f.write(f"ENTRY PRICE: {trade.get('context', {}).get('close_price', 'N/A')}\n")
                f.write(f"OUTCOME: {trade.get('trade_outcome', 'Unknown')}\n")
                f.write(f"PNL: {trade.get('pnl', '0.0')} points\n\n")
                f.write("--- AI RISK ASSESSMENT ---\n")
                f.write(f"{trade.get('ai_risk_analysis', 'No analysis provided.')}\n")
                f.write("-" * 60 + "\n\n")

if __name__ == "__main__":
    DATA_FILE = "data/historical_us30_1m.csv"
    run_master_backtest(DATA_FILE)