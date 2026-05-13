from flask import Flask, render_template, jsonify
import os
import glob
import re

app = Flask(__name__)

def clean_ansi(text):
    """Removes terminal color codes from the text file."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def get_batch_results_dir():
    """Bulletproof directory finder that hunts for batch_results and creates it if missing."""
    current_file_dir = os.path.dirname(os.path.abspath(__file__)) # Likely frontend/
    parent_dir = os.path.dirname(current_file_dir) # Likely us30_copilot/
    
    # Places to look depending on how the app was launched
    paths_to_try = [
        os.path.join(parent_dir, 'batch_results'), # Normal structure
        os.path.join(current_file_dir, 'batch_results'), # If app.py is in the root
        os.path.join(os.getcwd(), 'batch_results') # Absolute fallback
    ]
    
    for path in paths_to_try:
        if os.path.exists(path) and os.path.isdir(path):
            return path
            
    # If it genuinely doesn't exist, create it safely to prevent crashes
    target_path = paths_to_try[0]
    try:
        os.makedirs(target_path, exist_ok=True)
        print(f"[*] Auto-created missing directory: {target_path}")
    except Exception as e:
        print(f"[!] Could not create directory: {e}")
        
    return target_path

# Resolve the directory once when the app starts
BATCH_RESULTS_DIR = get_batch_results_dir()

@app.route('/')
def index():
    return render_template('index.html')

def get_latest_txt_file():
    if not os.path.exists(BATCH_RESULTS_DIR):
        return None
    list_of_files = glob.glob(f"{BATCH_RESULTS_DIR}/*.txt")
    if not list_of_files:
        return None
    # Get the newest file based on creation time
    return max(list_of_files, key=os.path.getctime)

@app.route('/api/metrics')
def get_metrics():
    latest_file = get_latest_txt_file()
    if not latest_file:
        return jsonify({"status": "error", "message": "Waiting for backtest to log to batch_results/"})

    try:
        with open(latest_file, 'r', encoding='utf-8') as file:
            content = clean_ansi(file.read())
            
            # Extract Metrics using regex
            net_profit_match = re.search(r'Net Profit:\s+\$?([-+]?\d*\.\d+|\d+)', content)
            win_rate_match = re.search(r'True Win Rate:\s+([-+]?\d*\.\d+|\d+)%', content)
            trades_match = re.search(r'Total Trades Taken:\s+(\d+)', content)
            
            net_profit = float(net_profit_match.group(1)) if net_profit_match else 0.0
            win_rate = float(win_rate_match.group(1)) if win_rate_match else 0.0
            total_trades = int(trades_match.group(1)) if trades_match else 0
            
            filename = os.path.basename(latest_file)
            trial_match = re.search(r'run_(\d+)_', filename)
            trial_num = trial_match.group(1) if trial_match else "Unknown"

            return jsonify({
                "status": "success",
                "net_profit": net_profit,
                "win_rate": win_rate,
                "profit_factor": 0.0, # (Profit Factor is not currently explicitly logged in your txt)
                "total_trades": total_trades,
                "trial": trial_num,
                "status_msg": "Parsing Successful"
            })
    except Exception as e:
        print(f"Metrics Parsing Error: {e}")
        return jsonify({"status": "error", "message": "Corrupted or incomplete log file"})

@app.route('/api/equity')
def get_equity():
    latest_file = get_latest_txt_file()
    if not latest_file:
         return jsonify({"labels": ["Waiting..."], "equity": [10000]})
         
    try:
        with open(latest_file, 'r', encoding='utf-8') as file:
            content = clean_ansi(file.read())
            
            net_profit_match = re.search(r'Net Profit:\s+\$?([-+]?\d*\.\d+|\d+)', content)
            net_profit = float(net_profit_match.group(1)) if net_profit_match else 0.0
            
            starting_balance = 10000.0
            ending_balance = starting_balance + net_profit

            return jsonify({
                "labels": ["Start", "End"],
                "equity": [starting_balance, ending_balance]
            })
    except Exception as e:
        return jsonify({"labels": ["Error"], "equity": [10000]})

if __name__ == '__main__':
    # Using 0.0.0.0 makes the server accessible across your local network if needed
    app.run(host='0.0.0.0', debug=True, port=5000)