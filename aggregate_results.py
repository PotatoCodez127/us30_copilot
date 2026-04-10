import os
import re
import glob

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

def aggregate():
    session_name = input(f"{Color.CYAN}Enter the name of the test session to aggregate (e.g., test_3): {Color.RESET}").strip()
    if not session_name:
        session_name = "default_run"
        
    output_dir = f"batch_results/{session_name}"
    
    if not os.path.exists(output_dir):
        print(f"{Color.RED}No folder found at {output_dir}. Run batch_runner.py first!{Color.RESET}")
        return
        
    files = glob.glob(f"{output_dir}/*.txt")
    if not files:
        print(f"{Color.RED}No text files found in {output_dir}.{Color.RESET}")
        return
        
    total_runs = 0
    metrics = {'trades': [], 'profit': [], 'drawdown': [], 'win_rate': [], 'loss_rate': []}
    
    print(f"{Color.CYAN}📊 Aggregating data from {len(files)} Monte Carlo runs...{Color.RESET}\n")
    
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            trades_m = re.search(r'Total Trades Taken:\s+(\d+)', content)
            profit_m = re.search(r'Net Profit:\s+\$([\d,\.-]+)', content)
            dd_m = re.search(r'Max Drawdown:\s+-([\d\.]+)%', content)
            wr_m = re.search(r'True Win Rate:\s+([\d\.]+)%', content)
            lr_m = re.search(r'Hard Loss Rate:\s+([\d\.]+)%', content)
            
            if trades_m and profit_m and dd_m and wr_m and lr_m:
                metrics['trades'].append(int(trades_m.group(1)))
                metrics['profit'].append(float(profit_m.group(1).replace(',', '')))
                metrics['drawdown'].append(float(dd_m.group(1)))
                metrics['win_rate'].append(float(wr_m.group(1)))
                metrics['loss_rate'].append(float(lr_m.group(1)))
                total_runs += 1

    if total_runs == 0:
        print("No valid metrics found in files.")
        return
        
    avg_trades = sum(metrics['trades']) / total_runs
    avg_profit = sum(metrics['profit']) / total_runs
    avg_dd = sum(metrics['drawdown']) / total_runs
    avg_wr = sum(metrics['win_rate']) / total_runs
    avg_lr = sum(metrics['loss_rate']) / total_runs
    
    print(f"{Color.MAGENTA}===========================================================================")
    print(f"🧠 MONTE CARLO AGGREGATION RESULTS ({total_runs} SUCCESSFUL RUNS) 🧠")
    print(f"==========================================================================={Color.RESET}")
    print(f"Average Trades Taken:   {avg_trades:.1f}")
    
    c_prof = Color.GREEN if avg_profit > 0 else Color.RED
    print(f"Average Net Profit:     {c_prof}${avg_profit:,.2f}{Color.RESET}")
    print(f"Average Max Drawdown:   {Color.RED}-{avg_dd:.2f}%{Color.RESET}")
    print(f"Average True Win Rate:  {Color.GREEN}{avg_wr:.2f}%{Color.RESET}")
    print(f"Average Hard Loss Rate: {Color.RED}{avg_lr:.2f}%{Color.RESET}")
    print(f"{Color.MAGENTA}===========================================================================\n{Color.RESET}")

if __name__ == "__main__":
    aggregate()