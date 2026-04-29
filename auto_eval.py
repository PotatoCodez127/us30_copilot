import os
import traceback
import pandas as pd
from main_backtest import run_master_backtest

def evaluate():
    print("[RUNNING] Backtest Engine...")
    print("[DEBUG] Step 1: Entering evaluate() function...")
    
    # 1. Run the backtest (Outputs to results/trade_log.csv)
    print("[DEBUG] Step 2: Attempting to call run_master_backtest()...")
    try:
        run_master_backtest("data/rolling_train.csv")
        print("[DEBUG] Step 3: run_master_backtest() completed successfully.")
    except Exception as e:
        print(f"[DEBUG] Step 3 FAILED: Exception caught during backtest: {e}")
        print(f"[FATAL] Backtest crashed with exception: {e}")
        traceback.print_exc()
        print("FINAL_RESULT:0.0")
        return

    # 2. Read the results
    log_path = 'results/trade_log.csv'
    print(f"[DEBUG] Step 4: Checking for existence of trade log at {log_path}...")
    if not os.path.exists(log_path):
        print(f"[DEBUG] Step 4 FAILED: {log_path} does not exist.")
        print("[GUARDRAIL] No trades were taken. 'trade_log.csv' was not generated.")
        print("FINAL_RESULT:0.0")
        return
    
    print("[DEBUG] Step 5: Loading trade log into pandas DataFrame...")
    df = pd.read_csv(log_path)
    trade_count = len(df)
    print(f"[DEBUG] Step 5 Complete: Loaded {trade_count} trades.")
    
    # 3. Guardrails: Penalize strategies that don't trade enough
    print("[DEBUG] Step 6: Checking trade count guardrail (minimum 10)...")
    if trade_count < 10:
        print(f"[DEBUG] Step 6 FAILED: Only {trade_count} trades found.")
        print(f"[GUARDRAIL] Not enough trades to be statistically significant ({trade_count} trades < 10 required).")
        print("FINAL_RESULT:0.0")
        return
    print("[DEBUG] Step 6 Complete: Guardrail passed.")

    # 4. Calculate the Custom Metric
    print("[DEBUG] Step 7: Calculating metrics (PnL, Win Rate)...")
    total_pnl = df['pnl_points'].sum()
    win_rate = len(df[df['pnl_points'] > 0]) / trade_count if trade_count > 0 else 0
    
    print("[DEBUG] Step 8: Calculating max drawdown...")
    cumulative = df['pnl_points'].cumsum()
    running_max = cumulative.cummax()
    drawdowns = running_max - cumulative
    max_drawdown = drawdowns.max()
    
    if max_drawdown <= 0: 
        print("[DEBUG] Step 8.1: Max drawdown was <= 0, defaulting to 1.0.")
        max_drawdown = 1.0 

    print(f"[DEBUG] Step 9: Finalizing score. Total PnL: {total_pnl}, Max DD: {max_drawdown}")
    if total_pnl <= 0:
        score = total_pnl # Negative score for losing strategies
        print("[DEBUG] Step 9.1: Strategy is unprofitable.")
        print("[BAD] Strategy is unprofitable. Returning raw PnL as score.")
    else:
        # The US30 Calmar-Variant Score
        score = (total_pnl / max_drawdown) * (win_rate * 100)
        print(f"[DEBUG] Step 9.2: Strategy is profitable. Calculated score: {score}")

    print("[DEBUG] Step 10: Printing Performance Summary...")
    print(f"\n=== [PERFORMANCE SUMMARY] ===")
    print(f"Total Trades: {trade_count}")
    print(f"Total PnL:    {total_pnl:.2f} pts")
    print(f"Max Drawdown: {max_drawdown:.2f} pts")
    print(f"Win Rate:     {win_rate*100:.1f}%")
    print(f"Score Math:   ({total_pnl:.2f} / {max_drawdown:.2f}) * {win_rate*100:.1f}")
    print(f"==============================")
    print(f"FINAL_RESULT:{score:.4f}")
    print("[DEBUG] Step 11: auto_eval.py execution finished completely.")

if __name__ == "__main__":
    evaluate()