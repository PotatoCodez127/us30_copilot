from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
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
                        "win_rate": 0.0,      # Not tracked in TSV yet
                        "profit_factor": 0.0, # Not tracked in TSV yet
                        "total_trades": 0,    # Not tracked in TSV yet
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

@app.route('/api/history')
def get_history():
    import os
    tsv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'autoresearch_log.tsv'))
    history_data = []
    
    try:
        if os.path.exists(tsv_path):
            with open(tsv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for idx, line in enumerate(lines[1:]):
                    parts = line.strip().split('\t')
                    if len(parts) >= 3:
                        history_data.append({
                            "id": idx + 1,
                            "trial": parts[0],
                            "score": float(parts[1]),
                            "status": parts[2],
                            # Parse the new columns if they exist
                            "sl": parts[3] if len(parts) > 3 else "N/A",
                            "tp": parts[4] if len(parts) > 4 else "N/A",
                            "buffer": parts[5] if len(parts) > 5 else "N/A",
                            "max_hold": parts[6] if len(parts) > 6 else "N/A"
                        })
        return jsonify({"status": "success", "data": history_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)