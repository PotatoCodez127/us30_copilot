import os
import traceback
import pandas as pd
from main_backtest import run_master_backtest

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def evaluate():
    print("⏳ Running Backtest Engine...")
    
    # 1. Run the backtest (Outputs to results/trade_log.csv)
    try:
        run_master_backtest("data/historical_us30_1m.csv")
    except Exception as e:
        print(f"❌ FATAL: Backtest crashed with exception: {e}")
        traceback.print_exc()
        print("FINAL_RESULT:0.0")
        return

    # 2. Read the results
    log_path = 'results/trade_log.csv'
    if not os.path.exists(log_path):
        print("❌ GUARDRAIL: No trades were taken. 'trade_log.csv' was not generated.")
        print("FINAL_RESULT:0.0")
        return

    df = pd.read_csv(log_path)
    trade_count = len(df)
    
    # 3. Guardrails: Penalize strategies that don't trade enough
    if trade_count < 10:
        print(f"❌ GUARDRAIL: Not enough trades to be statistically significant ({trade_count} trades < 10 required).")
        print("FINAL_RESULT:0.0")
        return

    # 4. Calculate the Custom Metric
    total_pnl = df['pnl_points'].sum()
    win_rate = len(df[df['pnl_points'] > 0]) / trade_count if trade_count > 0 else 0
    
    cumulative = df['pnl_points'].cumsum()
    running_max = cumulative.cummax()
    drawdowns = running_max - cumulative
    max_drawdown = drawdowns.max()
    
    if max_drawdown <= 0: 
        max_drawdown = 1.0 

    if total_pnl <= 0:
        score = total_pnl # Negative score for losing strategies
        print("📉 Strategy is unprofitable. Returning raw PnL as score.")
    else:
        # The US30 Calmar-Variant Score
        score = (total_pnl / max_drawdown) * (win_rate * 100)

    print(f"\n=== 📊 PERFORMANCE SUMMARY ===")
    print(f"Total Trades: {trade_count}")
    print(f"Total PnL:    {total_pnl:.2f} pts")
    print(f"Max Drawdown: {max_drawdown:.2f} pts")
    print(f"Win Rate:     {win_rate*100:.1f}%")
    print(f"Scbore Math:   ({total_pnl:.2f} / {max_drawdown:.2f}) * {win_rate*100:.1f}")
    print(f"==============================")
    print(f"FINAL_RESULT:{score:.4f}")

if __name__ == "__main__":
    evaluate()