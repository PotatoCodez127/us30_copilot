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
    import os
    # Point directly to the new source of truth
    tsv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'autoresearch_log.tsv'))
    
    try:
        if os.path.exists(tsv_path):
            with open(tsv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 1: # Ensure there is data beyond the header
                    # Grab the very last run
                    last_line = lines[-1].strip().split('\t')
                    latest_score = float(last_line[1])
                    total_runs = len(lines) - 1
                    
                    return jsonify({
                        "status": "success",
                        "net_profit": latest_score,
                        "win_rate": 0.0,      # Currently not tracked in TSV
                        "profit_factor": 0.0, # Currently not tracked in TSV
                        "total_trades": 0,    # Currently not tracked in TSV
                        "trial": str(total_runs),
                        "status_msg": "Rolling Research Active"
                    })
    except Exception as e:
        print(f"🔍 DEBUG: CRASH in get_metrics -> {e}")
        return jsonify({"status": "error", "message": f"Parsing Error: {str(e)}"})

    # Fallback if TSV is empty or missing
    return jsonify({
        "status": "success", "net_profit": 0.0, "win_rate": 0.0, 
        "profit_factor": 0.0, "total_trades": 0, "trial": "N/A", 
        "status_msg": "Waiting for data..."
    })

@app.route('/api/equity')
def get_equity():
    import os
    tsv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'autoresearch_log.tsv'))
    
    try:
        if os.path.exists(tsv_path):
            with open(tsv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1].strip().split('\t')
                    latest_score = float(last_line[1])
                    
                    return jsonify({
                        "labels": ["Start", "End"],
                        "equity": [10000.0, 10000.0 + latest_score]
                    })
    except:
        pass
        
    return jsonify({"labels": ["Waiting for data..."], "equity": [10000.0, 10000.0]})

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