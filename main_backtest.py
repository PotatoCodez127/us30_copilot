import pandas as pd
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama
from src.database.supabase_client import log_setup_to_db

def run_master_backtest(csv_filepath: str):
    print(f"🚀 Initializing Opening Range Backtest Engine on {csv_filepath}...")
    df = load_and_prep_data(csv_filepath)
    unique_dates = pd.Series(df.index.date).unique()
    
    print(f"📊 Found {len(unique_dates)} trading days. Beginning quantitative scan...\n")
    print("-" * 60)
    
    total_setups = 0

    for i in range(1, len(unique_dates)):
        prev_date_str = str(unique_dates[i-1])
        current_date_str = str(unique_dates[i])
        
        # 1. Calculate Daily Pivots from yesterday
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

        # 2. Run the NY Session Simulator (This isolates the Opening Range and checks the State Machine)
        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots)
        
        # 3. Process any found setups
        if daily_setups:
            for setup in daily_setups:
                print(f"🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}")
                print(f"Trigger: {setup['trigger']}")
                
                # Send to AI
                print("🧠 Sending setup to AI Agent...")
                ai_analysis = analyze_setup_with_ollama(setup)
                setup['ai_risk_analysis'] = ai_analysis
                
                # Log to DB
                try:
                    log_setup_to_db(setup)
                    print("✅ Successfully logged to Supabase.")
                except Exception as e:
                    print(f"❌ Failed to log setup: {e}")
                    
                print("-" * 50)
                total_setups += 1

    print(f"🏁 Backtest Complete. Processed {total_setups} total setups over {len(unique_dates)} days.")

if __name__ == "__main__":
    DATA_FILE = "data/historical_us30_1m.csv"
    run_master_backtest(DATA_FILE)