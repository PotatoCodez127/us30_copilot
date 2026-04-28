import time
from datetime import datetime
from src.data_feed.historical import fetch_rolling_6_months
from autoresearch import run_loop

def continuous_training_loop():
    print("=" * 60)
    print("🌀 INITIALIZING CONTINUOUS ROLLING WINDOW RESEARCHER 🌀")
    print("=" * 60)

    while True:
        try:
            # 1. Shift the window and download the last 6 months of data
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Updating 6-Month Data Window...")
            fetch_rolling_6_months(symbol="DIA")
            
            # 2. Run the Autoresearcher for a set number of mutations
            # We run 10 AI mutations against the new data before checking the date again
            mutations_per_cycle = 10
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🧠 Beginning AI Mutation Cycle ({mutations_per_cycle} attempts)...")
            
            for i in range(mutations_per_cycle):
                print(f"\n--- Mutation {i+1}/{mutations_per_cycle} ---")
                run_loop() # This calls your existing AI loop in autoresearch.py
                
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 💤 Cycle complete. Resting before next window shift...")
            
            # 3. Sleep for a few hours before shifting the window again
            # E.g., Sleep for 12 hours (43200 seconds)
            time.sleep(43200)

        except Exception as e:
            print(f"🚨 Critical Error in Rolling Loop: {e}")
            time.sleep(60) # Wait a minute and try again

if __name__ == "__main__":
    continuous_training_loop()