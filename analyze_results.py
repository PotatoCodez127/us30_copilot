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
    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
    
    # Handle SL distance safely with new 75-point baseline
    if 'sl_distance' in df.columns:
        valid_sl = df['sl_distance'].apply(lambda x: x if x > 0 else 75.0) 
    else:
        valid_sl = 75.0
        
    lot_size = dollar_risk / valid_sl
    commissions = lot_size * COMMISSION_PER_LOT
    
    # Calculate Dynamic Dollar PnL based on the raw points
    df['dollar_pnl'] = (df['pnl_points'] * lot_size) - commissions

    # --- CORE METRICS: SEPARATING WINS, LOSSES, AND SCRATCHES ---
    if 'outcome' in df.columns:
        is_be = df['outcome'].str.contains('Break-Even', na=False, case=False)
        is_time_eject = df['outcome'].str.contains('Time Ejection', na=False, case=False)
        
        # Pure runners
        wins = df[(df['dollar_pnl'] > 0) & ~is_be & ~is_time_eject]
        # Pure full losses
        losses = df[(df['dollar_pnl'] < 0) & ~is_be & ~is_time_eject]
        # Scratches (Break-Evens and Ejections that hover around 0 PnL)
        scratches = df[is_be | is_time_eject]
    else:
        # Fallback if outcome text is missing
        wins = df[df['dollar_pnl'] > (dollar_risk * 0.2)] 
        losses = df[df['dollar_pnl'] < -(dollar_risk * 0.2)]
        scratches = df[(df['dollar_pnl'] >= -(dollar_risk * 0.2)) & (df['dollar_pnl'] <= (dollar_risk * 0.2))]

    total_trades = len(df)
    win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
    scratch_rate = (len(scratches) / total_trades) * 100 if total_trades > 0 else 0
    loss_rate = (len(losses) / total_trades) * 100 if total_trades > 0 else 0
    
    net_profit = df['dollar_pnl'].sum()
    avg_win = wins['dollar_pnl'].mean() if not wins.empty else 0
    avg_loss = losses['dollar_pnl'].mean() if not losses.empty else 0
    
    realized_rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    
    avg_sl = df['sl_distance'].mean() if 'sl_distance' in df.columns else 75.0
    avg_tp = df['tp_distance'].mean() if 'tp_distance' in df.columns else 200.0
    intended_rr = abs(avg_tp / avg_sl) if avg_sl != 0 else 0

    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🏆 US30 COPILOT - DEEP FORENSIC QUANT ANALYSIS 🏆")
    print(f"==========================================================================={Color.RESET}")
    print(f"Total Trades:           {total_trades}")
    print(f"True Win Rate:          {Color.GREEN}{win_rate:.2f}%{Color.RESET} (Runners)")
    print(f"Scratch/BE Rate:        {Color.YELLOW}{scratch_rate:.2f}%{Color.RESET} (Shield Activations/Ejections)")
    print(f"Hard Loss Rate:         {Color.RED}{loss_rate:.2f}%{Color.RESET} (Stopped Out)")
    
    color = Color.GREEN if net_profit > 0 else Color.RED
    print(f"\nNet Profit:             {color}${net_profit:,.2f}{Color.RESET}")
    print(f"Average True Win:       +{Color.GREEN}${avg_win:,.2f}{Color.RESET}")
    print(f"Average True Loss:      {Color.RED}-${abs(avg_loss):,.2f}{Color.RESET}")
    print(f"Realized Account R:R:   {realized_rr:.2f} to 1")
    
    print(f"{Color.CYAN}---------------------------------------------------------------------------")
    print(f"🤖 AI INTENDED TAPE METRICS:")
    print(f"Avg Intended Stop Loss: -{avg_sl:.1f} points")
    print(f"Avg Intended Take Prof: +{avg_tp:.1f} points")
    print(f"Intended Points R:R:    {intended_rr:.2f} to 1{Color.RESET}")

    # --- OUTCOME EXIT DISTRIBUTION ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🛡️  TRADE EXIT DISTRIBUTION (Why are we leaving trades?)")
    print(f"==========================================================================={Color.RESET}")
    if 'outcome' in df.columns:
        # Extract everything between "] " and " at" to get the pure string (e.g., "Hit Trailing Stop")
        df['clean_outcome'] = df['outcome'].str.extract(r'\] (.*?) at', expand=False).fillna('Unknown')
        exit_grouped = df.groupby('clean_outcome').agg(
            trades=('dollar_pnl', 'count'),
            avg_pnl=('dollar_pnl', 'mean')
        ).sort_values(by='trades', ascending=False)
        
        for exit_type, row in exit_grouped.iterrows():
            c = Color.GREEN if row['avg_pnl'] > 0 else (Color.RED if row['avg_pnl'] < -5 else Color.YELLOW)
            pct = (row['trades'] / total_trades) * 100
            print(f"➤ {exit_type:<25} | {pct:>5.1f}% | Avg PnL: {c}${row['avg_pnl']:>6,.2f}{Color.RESET}")

    # --- TIME OF DAY DISTRIBUTION ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"⏰ TIME OF DAY DISTRIBUTION (UTC)")
    print(f"==========================================================================={Color.RESET}")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    
    time_grouped = df.groupby('hour').agg(
        pnl=('dollar_pnl', 'sum'),
        trades=('dollar_pnl', 'count'),
        wins=('dollar_pnl', lambda x: (x > 0).sum()) # Note: This includes scratches with slight pos PnL
    )
    
    for hour, row in time_grouped.iterrows():
        wr = (row['wins'] / row['trades']) * 100 if row['trades'] > 0 else 0
        c = Color.GREEN if row['pnl'] > 0 else Color.RED
        ny_hour = hour - 4 # Quick UTC to NY conversion
        print(f"➤ {hour:02d}:00 UTC (NY {ny_hour:02d}:00) | {c}${row['pnl']:>9,.2f}{Color.RESET} | +PnL Rate: {wr:>5.1f}% | Trades: {row['trades']}")

    # --- EDGE ISOLATION ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🔍 EDGE ISOLATION (By Trigger Context)")
    print(f"==========================================================================={Color.RESET}")
    edge_grouped = df.groupby('trigger').agg(
        pnl=('dollar_pnl', 'sum'),
        trades=('dollar_pnl', 'count')
    )
    
    for trigger, row in edge_grouped.iterrows():
        c = Color.GREEN if row['pnl'] > 0 else Color.RED
        print(f"➤ {trigger} | {c}${row['pnl']:>9,.2f}{Color.RESET} | Trades: {row['trades']}")

    # --- AUTOPSY OF LOSSES VS ANATOMY OF WINS ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"☠️  AUTOPSY OF LOSSES vs. ANATOMY OF WINS")
    print(f"==========================================================================={Color.RESET}")
    avg_hold_win = wins['holding_time'].mean() if not wins.empty else 0
    avg_hold_scratch = scratches['holding_time'].mean() if not scratches.empty else 0
    avg_hold_loss = losses['holding_time'].mean() if not losses.empty else 0
    
    print(f"Avg Hold Time (WINS):      {avg_hold_win:.1f} minutes")
    print(f"Avg Hold Time (SCRATCH):   {avg_hold_scratch:.1f} minutes")
    print(f"Avg Hold Time (LOSSES):    {avg_hold_loss:.1f} minutes")
    
    print(f"{Color.CYAN}---------------------------------------------------------------------------{Color.RESET}")
    avg_sl_win = wins['sl_distance'].mean() if 'sl_distance' in wins.columns and not wins.empty else 75.0
    avg_sl_loss = losses['sl_distance'].mean() if 'sl_distance' in losses.columns and not losses.empty else 75.0
    print(f"Avg SL Distance (WINS):     {avg_sl_win:.1f} points")
    print(f"Avg SL Distance (LOSSES):   {avg_sl_loss:.1f} points")
    
    print(f"{Color.CYAN}---------------------------------------------------------------------------{Color.RESET}")
    print(f"💡 ALGORITHMIC PATTERN RECOGNITION:")
    if avg_hold_win > avg_hold_loss * 1.5:
        print(f"➤ HOLD PATTERN: Winning trades take significantly longer to play out than losses (A healthy profile).")
    if scratch_rate > loss_rate:
        print(f"➤ RISK SHIELD: Your Break-Even/Ejection logic is intercepting more trades than your hard stop.")
    print(f"{Color.MAGENTA}===========================================================================\n{Color.RESET}")

if __name__ == "__main__":
    analyze()