import pandas as pd
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.asian_range import calculate_asian_range
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama
from src.database.supabase_client import log_setup_to_db

def run_full_backtest(csv_filepath: str):
    print(f"Loading historical data from {csv_filepath}...")
    try:
        df = load_and_prep_data(csv_filepath)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {csv_filepath}.")
        return

    unique_dates = pd.Series(df.index.date).unique()
    print(f"Data loaded successfully. Found {len(unique_dates)} trading days.")
    print("-" * 50)
    
    total_setups = []

    for i in range(1, len(unique_dates)):
        prev_date_str = str(unique_dates[i-1])
        current_date_str = str(unique_dates[i])
        
        # 1. Calculate Daily Pivots
        prev_day_data = df.loc[prev_date_str]
        if prev_day_data.empty: continue
            
        try:
            pivots = calculate_daily_pivots(
                prev_day_data['high'].max(), 
                prev_day_data['low'].min(), 
                prev_day_data['close'].iloc[-1]
            )
        except ValueError: continue

        # 2. Calculate Asian Range
        current_day_data = df.loc[current_date_str]
        try:
            asia_range = calculate_asian_range(current_day_data)
        except ValueError: continue

        # 3. Run the NY Session Simulation
        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots, asia_range)
        
        if daily_setups:
            for setup in daily_setups:
                print(f"\n🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}")
                print(f"Narrative: {setup['narrative_confirmed']}")
                
                # 4. Hand off to the AI Agent
                ai_analysis = analyze_setup_with_ollama(setup)
                setup['ai_risk_analysis'] = ai_analysis
                print("\n🤖 AI Risk Assessment received.")
                
                # 5. Log everything to Supabase
                log_setup_to_db(setup)
                
                total_setups.append(setup)

    print("\n" + "-" * 50)
    print(f"🏁 Integration Complete. Processed {len(total_setups)} total setups over {len(unique_dates)} days.")

if __name__ == "__main__":
    DATA_FILE = "data/historical_us30_1m.csv"
    run_full_backtest(DATA_FILE)