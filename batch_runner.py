import os
import subprocess
import sys
import datetime
import re
import time

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

def run_batch():
    output_dir = "batch_results"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"{Color.CYAN}🚀 Starting Monte Carlo Batch Engine...{Color.RESET}")
    print(f"Press CTRL+C at any time to stop manually.\n")
    
    # --- THE FIX: Force Windows to understand emojis in the background ---
    custom_env = os.environ.copy()
    custom_env["PYTHONIOENCODING"] = "utf-8"
    # ---------------------------------------------------------------------
    
    run_count = 1
    
    try:
        while True:
            print(f"{Color.YELLOW}--- Executing Run #{run_count} ---{Color.RESET}")
            
            # 1. Run the Backtester (Forced UTF-8)
            print("Running main_backtest.py (Mining the tape...)")
            subprocess.run(
                [sys.executable, "main_backtest.py"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                encoding="utf-8", 
                env=custom_env
            )
            
            # 2. Run the Analyzer (Forced UTF-8)
            print("Running analyze_results.py (Generating report...)")
            analyzer_process = subprocess.run(
                [sys.executable, "analyze_results.py"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                encoding="utf-8", 
                env=custom_env
            )
            output = analyzer_process.stdout
            
            # 3. Save to a unique text file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_dir}/run_{run_count}_{timestamp}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"✅ Saved results to {filename}")
            
            # 4. The API Exhaustion Kill-Switch
            trades_match = re.search(r'Total Trades Taken:\s+(\d+)', output)
            if trades_match:
                trades = int(trades_match.group(1))
                if trades < 5:  
                    print(f"\n{Color.RED}🚨 CRITICAL: Only {trades} trades taken. API keys are likely exhausted or rate-limited.{Color.RESET}")
                    print(f"{Color.CYAN}Stopping batch engine. Run aggregate_results.py to see your averages!{Color.RESET}")
                    break
            else:
                print(f"\n{Color.RED}⚠️ Could not read trade count. Stopping batch.{Color.RESET}")
                print(f"{Color.YELLOW}Open the {filename} file to see the exact Python error!{Color.RESET}")
                break
                
            run_count += 1
            time.sleep(2) 
            
    except KeyboardInterrupt:
        print(f"\n{Color.MAGENTA}Batch engine stopped manually by user.{Color.RESET}")

if __name__ == "__main__":
    run_batch()