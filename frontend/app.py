from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Path to your research log
LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'autoresearch_log.tsv')

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    """API endpoint to get the latest research metrics."""
    try:
        # Read the latest line from your autoresearch log
        df = pd.read_csv(LOG_PATH, sep='\t')
        if not df.empty:
            latest = df.iloc[-1]
            return jsonify({
                "status": "success",
                "win_rate": float(latest.get('Win Rate [%]', 0)),
                "net_profit": float(latest.get('Net Profit [$]', 0)),
                "total_trades": int(latest.get('Total Trades', 0)),
                "profit_factor": float(latest.get('Profit Factor', 0))
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
    return jsonify({"status": "empty"})

@app.route('/api/equity')
def get_equity():
    """Mock API endpoint for the equity curve. 
    You can hook this up to your plot_equity.py logic or a CSV export."""
    # Simulating equity data for the chart
    data = {
        "labels": ["10:00", "10:15", "10:30", "10:45", "11:00", "11:15"],
        "equity": [10000, 10050, 10020, 10150, 10100, 10250]
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)