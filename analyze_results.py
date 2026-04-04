import pandas as pd
import os

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

# --- ACCOUNT PARAMETERS ---
# You can scale these to match a Prop Firm challenge (e.g., 100000.0 and 0.01 for 1% risk)
ACCOUNT_SIZE = 100
RISK_PERCENT = 0.1  # 1% Risk per trade
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

    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # --- DYNAMIC DOLLAR PNL RECONSTRUCTION ---
    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
    
    if 'sl_distance' in df.columns:
        valid_sl = df['sl_distance'].apply(lambda x: x if x > 0 else 75.0) 
    else:
        valid_sl = 75.0
        
    lot_size = dollar_risk / valid_sl
    commissions = lot_size * COMMISSION_PER_LOT
    
    df['dollar_pnl'] = (df['pnl_points'] * lot_size) - commissions

    # --- EQUITY CURVE & DRAWDOWN MATH ---
    df['cumulative_pnl'] = df['dollar_pnl'].cumsum()
    df['equity'] = ACCOUNT_SIZE + df['cumulative_pnl']
    df['peak_equity'] = df['equity'].cummax()
    
    # Calculate Drawdown
    df['drawdown_dollars'] = df['peak_equity'] - df['equity']
    df['drawdown_pct'] = (df['drawdown_dollars'] / df['peak_equity']) * 100
    
    max_dd_pct = df['drawdown_pct'].max()
    max_dd_dollars = df['drawdown_dollars'].max()
    total_return_pct = (df['cumulative_pnl'].iloc[-1] / ACCOUNT_SIZE) * 100 if not df.empty else 0

    # --- CORE METRICS: SEPARATING WINS, LOSSES, AND SCRATCHES ---
    if 'outcome' in df.columns:
        is_be = df['outcome'].str.contains('Break-Even', na=False, case=False)
        is_time_eject = df['outcome'].str.contains('Time Ejection', na=False, case=False)
        
        wins = df[(df['dollar_pnl'] > 0) & ~is_be & ~is_time_eject]
        losses = df[(df['dollar_pnl'] < 0) & ~is_be & ~is_time_eject]
        scratches = df[is_be | is_time_eject]
    else:
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
    
    start_date = df['timestamp'].min().strftime('%Y-%m-%d')
    end_date = df['timestamp'].max().strftime('%Y-%m-%d')

    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🏆 US30 COPILOT - INSTITUTIONAL QUANT ANALYSIS 🏆")
    print(f"==========================================================================={Color.RESET}")
    print(f"Date Range:             {Color.CYAN}{start_date} to {end_date}{Color.RESET}")
    print(f"Total Trades Taken:     {total_trades}")
    print(f"True Win Rate:          {Color.GREEN}{win_rate:.2f}%{Color.RESET} (Runners)")
    print(f"Scratch/BE Rate:        {Color.YELLOW}{scratch_rate:.2f}%{Color.RESET} (Shield Activations)")
    print(f"Hard Loss Rate:         {Color.RED}{loss_rate:.2f}%{Color.RESET} (Stopped Out)")
    
    print(f"{Color.CYAN}---------------------------------------------------------------------------")
    print(f"🏦 ACCOUNT METRICS (Starting Bal: ${ACCOUNT_SIZE:,.2f} | Risk/Trade: {RISK_PERCENT*100:.1f}%)")
    print(f"---------------------------------------------------------------------------{Color.RESET}")
    
    color = Color.GREEN if net_profit > 0 else Color.RED
    print(f"Net Profit:             {color}${net_profit:,.2f}{Color.RESET}")
    print(f"Total Account Return:   {color}{total_return_pct:+.2f}%{Color.RESET}")
    print(f"Max Drawdown:           {Color.RED}-{max_dd_pct:.2f}%{Color.RESET} (${max_dd_dollars:,.2f})")
    
    print(f"Average True Win:       +{Color.GREEN}${avg_win:,.2f}{Color.RESET}")
    print(f"Average True Loss:      {Color.RED}-${abs(avg_loss):,.2f}{Color.RESET}")
    print(f"Realized Account R:R:   {realized_rr:.2f} to 1")

    # --- MONTHLY BREAKDOWN ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"📅 MONTHLY PERFORMANCE BREAKDOWN")
    print(f"==========================================================================={Color.RESET}")
    df['year_month'] = df['timestamp'].dt.strftime('%Y-%m')
    
    # Calculate starting equity for each month to find monthly % return
    monthly_grouped = []
    current_eq = ACCOUNT_SIZE
    
    for month, group in df.groupby('year_month'):
        m_pnl = group['dollar_pnl'].sum()
        m_trades = len(group)
        m_wins = len(group[(group['dollar_pnl'] > 0) & ~group['outcome'].str.contains('Break-Even|Time Ejection', na=False, case=False)])
        m_wr = (m_wins / m_trades) * 100 if m_trades > 0 else 0
        m_pct_return = (m_pnl / current_eq) * 100
        
        monthly_grouped.append({
            'month': month, 'pnl': m_pnl, 'pct': m_pct_return, 'trades': m_trades, 'wr': m_wr
        })
        current_eq += m_pnl # Update equity for the next month's baseline
        
    for m in monthly_grouped:
        c = Color.GREEN if m['pnl'] > 0 else Color.RED
        print(f"➤ {m['month']} | PnL: {c}${m['pnl']:>8,.2f} ({m['pct']:>+6.2f}%){Color.RESET} | WR: {m['wr']:>5.1f}% | Trades: {m['trades']}")

    # --- OUTCOME EXIT DISTRIBUTION ---
    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🛡️  TRADE EXIT DISTRIBUTION")
    print(f"==========================================================================={Color.RESET}")
    if 'outcome' in df.columns:
        df['clean_outcome'] = df['outcome'].str.extract(r'\] (.*?) at', expand=False).fillna('Unknown')
        exit_grouped = df.groupby('clean_outcome').agg(
            trades=('dollar_pnl', 'count'),
            avg_pnl=('dollar_pnl', 'mean')
        ).sort_values(by='trades', ascending=False)
        
        for exit_type, row in exit_grouped.iterrows():
            c = Color.GREEN if row['avg_pnl'] > 0 else (Color.RED if row['avg_pnl'] < -5 else Color.YELLOW)
            pct = (row['trades'] / total_trades) * 100
            print(f"➤ {exit_type:<25} | {pct:>5.1f}% | Avg PnL: {c}${row['avg_pnl']:>6,.2f}{Color.RESET}")

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

    print(f"{Color.MAGENTA}===========================================================================\n{Color.RESET}")

if __name__ == "__main__":
    analyze()