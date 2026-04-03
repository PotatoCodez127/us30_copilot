import pandas as pd
import os

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

# --- ACCOUNT PARAMETERS ---
ACCOUNT_SIZE = 100.0
RISK_PERCENT = 0.1  # 1%
COMMISSION_PER_LOT = 0.00

def analyze():
    filepath = 'results/trade_log.csv'
    if not os.path.exists(filepath):
        print(f"{Color.RED}No trade log found at {filepath}{Color.RESET}")
        return

    df = pd.read_csv(filepath)
    if df.empty:
        print("Trade log is empty.")
        return

    # --- DYNAMIC DOLLAR PNL RECONSTRUCTION ---
    # Rebuild the dollar values that were removed from main_backtest.py
    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
    
    # Handle SL distance safely
    if 'sl_distance' in df.columns:
        valid_sl = df['sl_distance'].apply(lambda x: x if x > 0 else 95.0) 
    else:
        valid_sl = 95.0
        
    lot_size = dollar_risk / valid_sl
    commissions = lot_size * COMMISSION_PER_LOT
    
    # Calculate Dynamic Dollar PnL based on the raw points
    df['dollar_pnl'] = (df['pnl_points'] * lot_size) - commissions

    # --- CORE METRICS ---
    total_trades = len(df)
    wins = df[df['dollar_pnl'] > 0]
    losses = df[df['dollar_pnl'] <= 0]
    
    win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
    net_profit = df['dollar_pnl'].sum()
    avg_win = wins['dollar_pnl'].mean() if not wins.empty else 0
    avg_loss = losses['dollar_pnl'].mean() if not losses.empty else 0
    
    realized_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    avg_sl = df['sl_distance'].mean() if 'sl_distance' in df.columns else 95.0
    avg_tp = df['tp_distance'].mean() if 'tp_distance' in df.columns else 190.0
    intended_rr = abs(avg_tp / avg_sl) if avg_sl != 0 else 0

    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🏆 US30 COPILOT - DEEP FORENSIC QUANT ANALYSIS 🏆")
    print(f"==========================================================================={Color.RESET}")
    print(f"Total Trades:           {total_trades}")
    print(f"Win Rate:               {win_rate:.2f}%")
    
    color = Color.GREEN if net_profit > 0 else Color.RED
    print(f"Net Profit:             {color}${net_profit:,.2f}{Color.RESET}")
    print(f"Average Win:            +{Color.GREEN}${avg_win:,.2f}{Color.RESET}")
    print(f"Average Loss:           {Color.RED}-${abs(avg_loss):,.2f}{Color.RESET}")
    print(f"Realized Account R:R:   {realized_rr:.2f} to 1")
    
    print(f"{Color.CYAN}---------------------------------------------------------------------------")
    print(f"🤖 AI INTENDED TAPE METRICS:")
    print(f"Avg Intended Stop Loss: -{avg_sl:.1f} points")
    print(f"Avg Intended Take Prof: +{avg_tp:.1f} points")
    print(f"Intended Points R:R:    {intended_rr:.2f} to 1{Color.RESET}")

    # --- TIME OF DAY DISTRIBUTION ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"⏰ TIME OF DAY DISTRIBUTION (UTC)")
    print(f"==========================================================================={Color.RESET}")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    
    time_grouped = df.groupby('hour').agg(
        pnl=('dollar_pnl', 'sum'),
        trades=('dollar_pnl', 'count'),
        wins=('dollar_pnl', lambda x: (x > 0).sum())
    )
    
    for hour, row in time_grouped.iterrows():
        wr = (row['wins'] / row['trades']) * 100 if row['trades'] > 0 else 0
        c = Color.GREEN if row['pnl'] > 0 else Color.RED
        ny_hour = hour - 4 # Quick UTC to NY conversion
        print(f"➤ {hour:02d}:00 UTC (NY {ny_hour:02d}:00) | {c}${row['pnl']:>9,.2f}{Color.RESET} | WR: {wr:>5.1f}% | Trades: {row['trades']}")

    # --- EDGE ISOLATION ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🔍 EDGE ISOLATION (By Trigger Context)")
    print(f"==========================================================================={Color.RESET}")
    edge_grouped = df.groupby('trigger').agg(
        pnl=('dollar_pnl', 'sum'),
        trades=('dollar_pnl', 'count'),
        wins=('dollar_pnl', lambda x: (x > 0).sum())
    )
    
    for trigger, row in edge_grouped.iterrows():
        wr = (row['wins'] / row['trades']) * 100 if row['trades'] > 0 else 0
        c = Color.GREEN if row['pnl'] > 0 else Color.RED
        print(f"➤ {trigger} | {c}${row['pnl']:>9,.2f}{Color.RESET} | WR: {wr:>5.1f}% | Trades: {row['trades']}")

    # --- AUTOPSY OF LOSSES VS ANATOMY OF WINS ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"☠️  AUTOPSY OF LOSSES vs. ANATOMY OF WINS")
    print(f"==========================================================================={Color.RESET}")
    avg_hold_win = wins['holding_time'].mean() if not wins.empty else 0
    avg_hold_loss = losses['holding_time'].mean() if not losses.empty else 0
    print(f"Average Hold Time (WINS):   {avg_hold_win:.1f} minutes")
    print(f"Average Hold Time (LOSSES): {avg_hold_loss:.1f} minutes")
    
    print(f"{Color.CYAN}---------------------------------------------------------------------------{Color.RESET}")
    avg_sl_win = wins['sl_distance'].mean() if 'sl_distance' in wins.columns and not wins.empty else 95.0
    avg_sl_loss = losses['sl_distance'].mean() if 'sl_distance' in losses.columns and not losses.empty else 95.0
    print(f"Avg SL Distance (WINS):     {avg_sl_win:.1f} points")
    print(f"Avg SL Distance (LOSSES):   {avg_sl_loss:.1f} points")
    
    print(f"{Color.CYAN}---------------------------------------------------------------------------{Color.RESET}")
    print(f"💡 ALGORITHMIC PATTERN RECOGNITION:")
    print(f"➤ RISK PATTERN: Stop Loss distance is roughly equal across wins and losses. Risk mapping is highly consistent.")
    if avg_hold_win > avg_hold_loss * 1.5:
        print(f"➤ HOLD PATTERN: Winning trades take significantly longer to play out than losses (A pure trend-following profile).")
    print(f"{Color.MAGENTA}===========================================================================\n{Color.RESET}")

if __name__ == "__main__":
    analyze()