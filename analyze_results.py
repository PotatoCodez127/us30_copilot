import pandas as pd
import os

def analyze_trade_data():
    csv_path = 'results/trade_log.csv'
    if not os.path.exists(csv_path): return
    df = pd.read_csv(csv_path)
    if df.empty: return

    total_trades = len(df)
    winning_trades = df[df['dollar_pnl'] > 0]
    losing_trades = df[df['dollar_pnl'] <= 0]

    winrate = (len(winning_trades) / total_trades) * 100
    total_dollar_pnl = df['dollar_pnl'].sum()
    avg_win = winning_trades['dollar_pnl'].mean() if not winning_trades.empty else 0
    avg_loss = losing_trades['dollar_pnl'].mean() if not losing_trades.empty else 0
    realized_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    print("=" * 60)
    print("🏆 US30 COPILOT - FUNDED ACCOUNT SIMULATION ($100k) 🏆")
    print("=" * 60)
    print(f"Total Trades:      {total_trades}")
    print(f"Win Rate:          {winrate:.2f}%")
    print(f"Net Profit:        ${total_dollar_pnl:,.2f}")
    print(f"Average Win:       +${avg_win:,.2f}")
    print(f"Average Loss:      -${abs(avg_loss):,.2f}")
    print(f"Realized R:R:      {realized_rr:.2f} to 1")
    print("=" * 60)

if __name__ == "__main__":
    analyze_trade_data()