import os
import subprocess
import sys
import datetime
import re
import time

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

def run_batch():
    # --- 1. Session Naming ---
    session_name = input(f"{Color.CYAN}Enter a name for this test session (e.g., test_3, baseline): {Color.RESET}").strip()
    if not session_name:
        session_name = "default_run"
        
    # --- 2. Dynamic Run Target ---
    try:
        runs_input = input(f"{Color.CYAN}How many times should we run the backtest? (Default: 20): {Color.RESET}").strip()
        max_runs = int(runs_input) if runs_input else 20
    except ValueError:
        max_runs = 20
        
    output_dir = f"batch_results/{session_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"{Color.CYAN}🚀 Starting Monte Carlo Batch Engine for [{session_name}] | Target: {max_runs} Runs...{Color.RESET}")
    print(f"Press CTRL+C at any time to stop manually.\n")
    
    custom_env = os.environ.copy()
    custom_env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        # --- 3. The Controlled Loop ---
        for run_count in range(1, max_runs + 1):
            print(f"{Color.YELLOW}--- Executing Run #{run_count} of {max_runs} ---{Color.RESET}")
            
            print("Running main_backtest.py (Mining the tape...)")
            subprocess.run(
                [sys.executable, "main_backtest.py"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                encoding="utf-8", 
                env=custom_env
            )
            
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
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_dir}/run_{run_count}_{timestamp}.txt"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"✅ Saved results to {filename}")
            
            trades_match = re.search(r'Total Trades Taken:\s+(\d+)', output)
            if trades_match:
                trades = int(trades_match.group(1))
                if trades < 5:  
                    print(f"\n{Color.RED}🚨 CRITICAL: Only {trades} trades taken. API keys are likely exhausted or rate-limited.{Color.RESET}")
                    print(f"{Color.CYAN}Stopping batch engine.{Color.RESET}")
                    break
            else:
                print(f"\n{Color.RED}⚠️ Could not read trade count. Stopping batch.{Color.RESET}")
                print(f"{Color.YELLOW}Open the {filename} file to see the exact Python error!{Color.RESET}")
                break
                
            if run_count < max_runs:
                time.sleep(2) 
                
        print(f"\n{Color.GREEN}🎉 Batch run complete! {max_runs} runs executed successfully.{Color.RESET}")
        print(f"{Color.CYAN}Run aggregate_results.py to see your averages!{Color.RESET}")
            
    except KeyboardInterrupt:
        print(f"\n{Color.MAGENTA}Batch engine stopped manually by user.{Color.RESET}")

if __name__ == "__main__":
    run_batch()