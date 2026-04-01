import pandas as pd
import os

def analyze_trade_data():
    csv_path = 'results/trade_log.csv'
    if not os.path.exists(csv_path):
        print("❌ No trade_log.csv found. Run main_backtest.py first.")
        return

    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("⚠️ Log is empty.")
        return

    total_trades = len(df)
    winning_trades = df[df['pnl'] > 0]
    losing_trades = df[df['pnl'] < 0]
    breakeven_trades = df[df['pnl'] == 0]

    winrate = (len(winning_trades) / total_trades) * 100
    total_pnl = df['pnl'].sum()
    avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
    avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
    biggest_loss = losing_trades['pnl'].min() if not losing_trades.empty else 0
    smallest_win = winning_trades['pnl'].min() if not winning_trades.empty else 0
    avg_hold = df['holding_time'].mean()
    
    realized_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    print("=" * 60)
    print("🏆 US30 COPILOT - ADVANCED QUANTITATIVE STATS 🏆")
    print("=" * 60)
    print(f"Total Trades:      {total_trades}")
    print(f"Win Rate:          {winrate:.2f}% ({len(winning_trades)}W / {len(breakeven_trades)}BE / {len(losing_trades)}L)")
    print(f"Total P/L:         {total_pnl:.2f} points")
    print(f"Average Win:       +{avg_win:.2f} points")
    print(f"Average Loss:      {avg_loss:.2f} points")
    print(f"Biggest Loss:      {biggest_loss:.2f} points")
    print(f"Smallest Win:      +{smallest_win:.2f} points")
    print(f"Realized R:R:      {realized_rr:.2f} to 1")
    print(f"Avg Holding Time:  {avg_hold:.1f} minutes")
    print("=" * 60)
    
    print("\n🔍 LEVEL STRICTNESS (EDGE ISOLATION) 🔍")
    print("-" * 60)
    
    # Group the stats by the specific level touched (e.g., OR Low, R1 Pivot)
    trigger_stats = df.groupby('trigger').agg(
        Total_Trades=('pnl', 'count'),
        Total_PNL=('pnl', 'sum'),
        Wins=('pnl', lambda x: (x > 0).sum())
    )
    
    trigger_stats['Win_Rate_%'] = (trigger_stats['Wins'] / trigger_stats['Total_Trades'] * 100).round(2)
    trigger_stats = trigger_stats.sort_values(by='Total_PNL', ascending=False)
    
    for trigger, row in trigger_stats.iterrows():
        pnl = row['Total_PNL']
        color = '\033[92m' if pnl > 0 else '\033[91m'
        print(f"➤ {trigger.ljust(30)} | {color}{pnl:>8.2f} pts\033[0m | {row['Win_Rate_%']}% WR ({row['Total_Trades']} trades)")
    print("-" * 60)

if __name__ == "__main__":
    analyze_trade_data()