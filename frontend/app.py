from flask import Flask, render_template, jsonify
import os
import re

app = Flask(__name__)

def find_latest_text_file():
    found_files = []
    search_roots = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
        os.getcwd()
    ]
    for root_dir in set(search_roots):
        for root, dirs, files in os.walk(root_dir):
            if 'batch_results' in root:
                for file in files:
                    if file.endswith(".txt"):
                        found_files.append(os.path.join(root, file))
    if not found_files:
        return None
    return max(found_files, key=os.path.getctime)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    print("\n" + "="*50)
    print("🔍 DEBUG: /api/metrics ENDPOINT CALLED")
    
    latest_file = find_latest_text_file()
    
    if not latest_file:
        print("🔍 DEBUG: No text file found by crawler!")
        return jsonify({"status": "success", "net_profit": 0.0, "win_rate": 0.0, "profit_factor": 0.0, "total_trades": 0, "trial": "N/A", "status_msg": "Waiting for backtester..."})

    print(f"🔍 DEBUG: Target File -> {latest_file}")

    try:
        with open(latest_file, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            
            # --- DEBUG BLOCK 1: Raw Content ---
            print("\n--- DEBUG: RAW FILE CONTENT (Last 300 chars) ---")
            print(repr(content[-300:])) # Using repr() to show hidden newline/formatting characters
            print("--------------------------------------------------\n")

            # Scrape the numbers using the forgiving regex
            net_profit_match = re.search(r'Net Profit[^\d-]+([-+]?\d+\.\d+)', content, re.IGNORECASE)
            win_rate_match = re.search(r'Win Rate[^\d-]+(\d+\.\d+)', content, re.IGNORECASE)
            trades_match = re.search(r'Total Trades[^\d]+(\d+)', content, re.IGNORECASE)
            
            # --- DEBUG BLOCK 2: Regex Results ---
            print("🔍 DEBUG: Regex Match Results:")
            print(f"   Net Profit Match Obj: {net_profit_match}")
            print(f"   Win Rate Match Obj:   {win_rate_match}")
            print(f"   Trades Match Obj:     {trades_match}")

            net_profit = float(net_profit_match.group(1)) if net_profit_match else 0.0
            win_rate = float(win_rate_match.group(1)) if win_rate_match else 0.0
            total_trades = int(trades_match.group(1)) if trades_match else 0
            
            filename = os.path.basename(latest_file)
            trial_match = re.search(r'(\d+)', filename)
            trial_num = trial_match.group(1) if trial_match else "Latest"

            print(f"\n🔍 DEBUG: Final Output -> Profit: {net_profit}, Win Rate: {win_rate}, Trades: {total_trades}")
            print("="*50 + "\n")

            return jsonify({
                "status": "success",
                "net_profit": net_profit,
                "win_rate": win_rate,
                "profit_factor": 0.0, 
                "total_trades": total_trades,
                "trial": trial_num,
                "status_msg": "Tracking Live" if total_trades == 0 else "Run Complete"
            })
    except Exception as e:
        print(f"🔍 DEBUG: CRASH in get_metrics -> {e}")
        return jsonify({"status": "error", "message": f"Parsing Error: {str(e)}"})

@app.route('/api/equity')
def get_equity():
    latest_file = find_latest_text_file()
    if not latest_file:
         return jsonify({"labels": ["Waiting for data..."], "equity": [10000]})
         
    try:
        with open(latest_file, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            net_profit_match = re.search(r'Net Profit[^\d-]+([-+]?\d+\.\d+)', content, re.IGNORECASE)
            net_profit = float(net_profit_match.group(1)) if net_profit_match else 0.0
            
            return jsonify({
                "labels": ["Start", "End"],
                "equity": [10000.0, 10000.0 + net_profit]
            })
    except:
        return jsonify({"labels": ["Error"], "equity": [10000]})

@app.route('/api/history')
def get_history():
    """Reads the autoresearch_log.tsv file to populate the history table and chart."""
    import os
    
    # Locate the TSV file in the root directory (one level up from frontend)
    tsv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'autoresearch_log.tsv'))
    history_data = []
    
    try:
        if os.path.exists(tsv_path):
            with open(tsv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Skip the header row
                for idx, line in enumerate(lines[1:]):
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        history_data.append({
                            "id": idx + 1,
                            "trial": parts[0],
                            "score": float(parts[1]),
                            "status": parts[2]
                        })
        return jsonify({"status": "success", "data": history_data})
    except Exception as e:
        print(f"剥 DEBUG: Error reading history -> {e}")
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)