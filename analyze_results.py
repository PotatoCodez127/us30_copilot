import pandas as pd
import os

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

def analyze_trade_data():
    csv_path = 'results/trade_log.csv'
    if not os.path.exists(csv_path):
        print(f"{Color.RED}❌ No trade_log.csv found. Run main_backtest.py first.{Color.RESET}")
        return
        
    df = pd.read_csv(csv_path)
    if df.empty: return

    # Parse timestamps to extract the exact Time of Day
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour_utc'] = df['timestamp'].dt.hour
    
    # Base splits
    total_trades = len(df)
    winning_trades = df[df['dollar_pnl'] > 0]
    losing_trades = df[df['dollar_pnl'] <= 0]

    winrate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    total_dollar_pnl = df['dollar_pnl'].sum()
    avg_win = winning_trades['dollar_pnl'].mean() if not winning_trades.empty else 0
    avg_loss = losing_trades['dollar_pnl'].mean() if not losing_trades.empty else 0
    realized_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    # AI Intended Risk vs Reward (In Points)
    avg_sl_pts = df['sl_distance'].mean() if 'sl_distance' in df.columns else 0
    avg_tp_pts = df['tp_distance'].mean() if 'tp_distance' in df.columns else 0
    intended_rr = (avg_tp_pts / avg_sl_pts) if avg_sl_pts > 0 else 0

    print("=" * 75)
    print(f"🏆 {Color.WHITE}US30 COPILOT - DEEP FORENSIC QUANT ANALYSIS{Color.RESET} 🏆")
    print("=" * 75)
    print(f"Total Trades:           {total_trades}")
    print(f"Win Rate:               {winrate:.2f}%")
    
    pnl_color = Color.GREEN if total_dollar_pnl > 0 else Color.RED
    print(f"Net Profit:             {pnl_color}${total_dollar_pnl:,.2f}{Color.RESET}")
    print(f"Average Win:            {Color.GREEN}+${avg_win:,.2f}{Color.RESET}")
    print(f"Average Loss:           {Color.RED}-${abs(avg_loss):,.2f}{Color.RESET}")
    print(f"Realized Account R:R:   {realized_rr:.2f} to 1")
    
    print("-" * 75)
    print(f"🤖 {Color.CYAN}AI INTENDED TAPE METRICS:{Color.RESET}")
    print(f"Avg Intended Stop Loss: -{avg_sl_pts:.1f} points")
    print(f"Avg Intended Take Prof: +{avg_tp_pts:.1f} points")
    print(f"Intended Points R:R:    {intended_rr:.2f} to 1")
    
    print("\n" + "=" * 75)
    print(f"⏰ {Color.YELLOW}TIME OF DAY DISTRIBUTION (UTC){Color.RESET}")
    print("=" * 75)
    # Group by Hour to see when the market is toxic
    time_stats = df.groupby('hour_utc').agg(
        Trades=('dollar_pnl', 'count'),
        Net_PNL=('dollar_pnl', 'sum'),
        Win_Rate=('dollar_pnl', lambda x: (x > 0).mean() * 100)
    ).sort_index()
    
    for hour, row in time_stats.iterrows():
        # US30 opens at 13:30 UTC. 14:00 UTC is 10:00 AM NY time (EST)
        est_hour = hour - 4 if hour >= 4 else hour + 20 
        pnl_col = Color.GREEN if row['Net_PNL'] > 0 else Color.RED
        print(f"➤ {hour:02d}:00 UTC (NY {est_hour:02d}:00) | {pnl_col}${row['Net_PNL']:>9,.2f}{Color.RESET} | WR: {row['Win_Rate']:>5.1f}% | Trades: {row['Trades']}")

    print("\n" + "=" * 75)
    print(f"🔍 {Color.MAGENTA}EDGE ISOLATION (By Trigger Context){Color.RESET}")
    print("=" * 75)
    trigger_stats = df.groupby('trigger').agg(
        Trades=('dollar_pnl', 'count'),
        Net_PNL=('dollar_pnl', 'sum'),
        Win_Rate=('dollar_pnl', lambda x: (x > 0).mean() * 100)
    ).sort_values(by='Net_PNL', ascending=False)
    
    for trigger, row in trigger_stats.iterrows():
        pnl_col = Color.GREEN if row['Net_PNL'] > 0 else Color.RED
        print(f"➤ {trigger.ljust(30)} | {pnl_col}${row['Net_PNL']:>9,.2f}{Color.RESET} | WR: {row['Win_Rate']:>5.1f}% | Trades: {row['Trades']}")

    print("\n" + "=" * 75)
    print(f"☠️  {Color.RED}AUTOPSY OF LOSSES vs. ANATOMY OF WINS{Color.RESET}")
    print("=" * 75)
    
    win_hold = winning_trades['holding_time'].mean() if not winning_trades.empty else 0
    loss_hold = losing_trades['holding_time'].mean() if not losing_trades.empty else 0
    
    win_sl_dist = winning_trades['sl_distance'].mean() if not winning_trades.empty else 0
    loss_sl_dist = losing_trades['sl_distance'].mean() if not losing_trades.empty else 0

    print(f"Average Hold Time (WINS):   {Color.GREEN}{win_hold:.1f} minutes{Color.RESET}")
    print(f"Average Hold Time (LOSSES): {Color.RED}{loss_hold:.1f} minutes{Color.RESET}")
    print("-" * 75)
    print(f"Avg SL Distance (WINS):     {Color.GREEN}{win_sl_dist:.1f} points{Color.RESET}")
    print(f"Avg SL Distance (LOSSES):   {Color.RED}{loss_sl_dist:.1f} points{Color.RESET}")
    print("-" * 75)
    
    # Automated Pattern Recognition
    print(f"💡 {Color.CYAN}ALGORITHMIC PATTERN RECOGNITION:{Color.RESET}")
    
    if loss_sl_dist > win_sl_dist * 1.25:
        print(f"{Color.YELLOW}➤ RISK PATTERN:{Color.RESET} Losing trades happen when the AI sets excessively WIDE stops.")
        print("  SUGGESTION: Lower your 'Hard Cap' in main_backtest.py to tighten the structural bounds.")
    elif loss_sl_dist < win_sl_dist * 0.75:
        print(f"{Color.YELLOW}➤ RISK PATTERN:{Color.RESET} Losing trades happen when the AI sets excessively TIGHT stops.")
        print("  SUGGESTION: The AI is getting chopped out by standard US30 volatility. Give it more breathing room.")
    else:
        print(f"{Color.GREEN}➤ RISK PATTERN:{Color.RESET} Stop Loss distance is roughly equal across wins and losses. Risk mapping is highly consistent.")

    if win_hold > loss_hold * 2:
        print(f"{Color.YELLOW}➤ HOLD PATTERN:{Color.RESET} Winning trades take significantly longer to play out than losses (A pure trend-following profile).")
    elif loss_hold > win_hold * 1.5:
        print(f"{Color.YELLOW}➤ HOLD PATTERN:{Color.RESET} You are holding losing trades longer than winning trades (Bleeding out in chop).")
        print("  SUGGESTION: Consider a time-based exit (e.g., if trade doesn't hit TP in 30 minutes, close it manually).")
        
    print("=" * 75 + "\n")

if __name__ == "__main__":
    analyze_trade_data()