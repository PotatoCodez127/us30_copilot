import pandas as pd
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
        
        # 1. Calculate Daily Pivots
        prev_day_data = df.loc[prev_date_str]
        current_day_data = df.loc[current_date_str]
        if prev_day_data.empty or current_day_data.empty: continue
            
        try:
            pivots = calculate_daily_pivots(
                prev_day_data['high'].max(), 
                prev_day_data['low'].min(), 
                prev_day_data['close'].iloc[-1]
            )
        except ValueError: continue

        # 2. Run NY Session Simulator
        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots)
        
        # 3. Process setups
        if daily_setups:
            for setup in daily_setups:
                print(f"{Color.GREEN}🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}{Color.RESET}")
                print(f"Trigger: {setup['trigger']}")
                
                # Send to AI
                print(f"{Color.CYAN}🧠 Sending setup to AI Agent...{Color.RESET}")
                ai_analysis = analyze_setup_with_ollama(setup)
                setup['ai_risk_analysis'] = ai_analysis
                
                # Print AI Analysis in Yellow/Magenta to stand out
                print(f"\n{Color.MAGENTA}" + "="*50)
                print(f"🤖 LIVE AI DESK ANALYSIS:")
                print("="*50 + f"{Color.YELLOW}")
                print(ai_analysis)
                print(f"{Color.MAGENTA}" + "="*50 + f"{Color.RESET}\n")
                
                # Log to DB
                try:
                    log_setup_to_db(setup)
                    print(f"{Color.GREEN}✅ Successfully logged to Supabase.{Color.RESET}")
                except Exception as e:
                    print(f"{Color.RED}❌ Failed to log setup: {e}{Color.RESET}")
                    
                print("-" * 50)
                all_logged_setups.append(setup)
                total_setups += 1

    print(f"\n{Color.CYAN}🏁 Backtest Complete. Processed {total_setups} total setups over {len(unique_dates)} days.{Color.RESET}")

    # Write to text file
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
                f.write(f"PROFIT (MFE): {trade.get('mfe_points', 'N/A')}\n")
                f.write(f"DRAWDOWN (MAE): {trade.get('mae_points', 'N/A')}\n\n")
                f.write("--- AI RISK ASSESSMENT ---\n")
                f.write(f"{trade.get('ai_risk_analysis', 'No analysis provided.')}\n")
                f.write("-" * 60 + "\n\n")
        
        print(f"{Color.GREEN}✅ Done! You can now open {output_filename} to review your trades.{Color.RESET}")

if __name__ == "__main__":
    DATA_FILE = "data/historical_us30_1m.csv"
    run_master_backtest(DATA_FILE)