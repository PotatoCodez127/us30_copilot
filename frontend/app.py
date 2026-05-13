from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, 'autoresearch_log.tsv')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    try:
        if not os.path.exists(LOG_PATH):
            return jsonify({"status": "error", "message": "File not found"})

        df = pd.read_csv(LOG_PATH, sep='\t')
        
        if not df.empty:
            latest = df.iloc[-1]
            best_score = df['score'].max() # Find the best score out of all trials
            
            return jsonify({
                "status": "success",
                "trial_number": len(df), # <--- FIX: We just count the number of rows now!
                "latest_score": float(latest.get('score', 0)),
                "best_score": float(best_score),
                "trial_status": str(latest.get('status', 'Unknown'))
            })
    except Exception as e:
        print(f"Error in metrics route: {e}") # This will print errors to your terminal if it fails again
        return jsonify({"status": "error", "message": str(e)})
    
    return jsonify({"status": "empty"})

@app.route('/api/equity')
def get_equity():
    # Still mock data until we find your trade log file
    data = {
        "labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
        "equity": [10000, 10050, 10100, 10080, 10200] 
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)