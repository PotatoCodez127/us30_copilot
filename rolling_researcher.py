import time
from datetime import datetime
from src.data_feed.historical import fetch_rolling_6_months
from autoresearch import run_loop

def continuous_training_loop():
    print("=" * 60)
    print("🌀 INITIALIZING CONTINUOUS ROLLING WINDOW RESEARCHER 🌀")
    print("=" * 60)

    # Number of AI mutations to attempt before moving the time window forward again
    MUTATIONS_PER_CYCLE = 5 

    while True:
        try:
            # 1. Shift the window and download the last 6 months of DIA data
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Updating 6-Month Data Window...")
            fetch_rolling_6_months(symbol="DIA")
            
            # 2. Run the Autoresearcher loop
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🧠 Beginning AI Mutation Cycle ({MUTATIONS_PER_CYCLE} attempts)...")
            
            for i in range(MUTATIONS_PER_CYCLE):
                print(f"\n--- Mutation {i+1}/{MUTATIONS_PER_CYCLE} ---")
                run_loop() # Triggers the deepseek/ministral evaluation loop
                
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 💤 Cycle complete. Resting before next window shift...")
            
            # 3. Sleep for 12 hours (43200 seconds) so the bot trains on fresh data twice a day
            time.sleep(43200)

        except Exception as e:
            print(f"🚨 Critical Error in Rolling Loop: {e}")
            time.sleep(60) # Wait a minute and try again

if __name__ == "__main__":
    continuous_training_loop()