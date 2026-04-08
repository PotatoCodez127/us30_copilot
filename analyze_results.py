import pandas as pd
import os

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

# --- ACCOUNT PARAMETERS ---
ACCOUNT_SIZE = 100.0 
RISK_PERCENT = 0.10  # 10% Risk per trade
COMMISSION_PER_LOT = 0.00

def analyze():
    filepath = 'results/trade_log.csv'
    if not os.path.exists(filepath):
        print(f"{Color.RED}No trade log found at {filepath}{Color.RESET}")
        return

    df = pd.read_csv(filepath)
    if df.empty: return

    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    
    # ==========================================
    # PRE-CALCULATE TIMING FEATURES FIRST
    # ==========================================
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['time_window'] = df['timestamp'].dt.strftime('%H:%M')
    total_by_day = df['day_of_week'].value_counts()
    
    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
    valid_sl = df['sl_distance'].apply(lambda x: x if x > 0 else 75.0) if 'sl_distance' in df.columns else 75.0
    lot_size = dollar_risk / valid_sl
    
    df['dollar_pnl'] = (df['pnl_points'] * lot_size) - (lot_size * COMMISSION_PER_LOT)
    df['cumulative_pnl'] = df['dollar_pnl'].cumsum()
    df['equity'] = ACCOUNT_SIZE + df['cumulative_pnl']
    df['peak_equity'] = df['equity'].cummax()
    df['drawdown_pct'] = ((df['peak_equity'] - df['equity']) / df['peak_equity']) * 100

    # ==========================================
    # NOW CATEGORIZE TRADES
    # ==========================================
    is_be = df['outcome'].str.contains('Break-Even', na=False, case=False)
    is_time_eject = df['outcome'].str.contains('Time Ejection', na=False, case=False)
    
    wins = df[(df['dollar_pnl'] > 0) & ~is_be & ~is_time_eject]
    losses = df[(df['dollar_pnl'] < 0) & ~is_be & ~is_time_eject]
    scratches = df[is_be | is_time_eject]

    print(f"\n{Color.MAGENTA}===========================================================================")
    print(f"🏆 US30 COPILOT - INSTITUTIONAL QUANT ANALYSIS 🏆")
    print(f"==========================================================================={Color.RESET}")
    print(f"Total Trades Taken:     {len(df)}")
    print(f"Net Profit:             ${df['dollar_pnl'].sum():,.2f}")
    print(f"Max Drawdown:           -{df['drawdown_pct'].max():.2f}%")
    print(f"True Win Rate:          {(len(wins) / len(df)) * 100:.2f}%")
    print(f"Hard Loss Rate:         {(len(losses) / len(df)) * 100:.2f}%")

    # =================================================================================
    # 🕵️‍♂️ DEEP AUTOPSY: FULL PROFILE (WINS, LOSSES, SCRATCHES)
    # =================================================================================

    profiles = [
        ("☠️ PROFILING THE LOSING TRADES 🛑", losses, Color.RED),
        ("🏆 PROFILING THE WINNING TRADES 🎯", wins, Color.GREEN),
        ("🛡️ PROFILING THE SCRATCH/BE TRADES 🛡️", scratches, Color.YELLOW)
    ]

    for title, subset, color in profiles:
        print(f"\n{color}===========================================================================")
        print(title)
        print(f"==========================================================================={Color.RESET}")
        
        if subset.empty:
            print("  No trades found in this category.")
            continue
            
        # 1. Analyze by Day of the Week
        print(f"\n{Color.CYAN}➤ BY DAY OF THE WEEK{Color.RESET}")
        day_counts = subset['day_of_week'].value_counts()
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            if day in day_counts:
                l_count = day_counts[day]
                t_count = total_by_day.get(day, 0)
                rate = (l_count / t_count) * 100 if t_count > 0 else 0
                print(f"  {day:<10} | {l_count:>2} Trades | {rate:>5.1f}% of total {day} setups")
            else:
                print(f"  {day:<10} |  0 Trades")

        # 2. Analyze by Micro-Timing (Top 5 Minutes)
        print(f"\n{Color.CYAN}➤ BY MICRO-TIMING (Top 5 Minutes){Color.RESET}")
        time_counts = subset['time_window'].value_counts().head(5) 
        for t_window, count in time_counts.items():
            print(f"  {t_window} UTC  | {count:>2} Trades")

        # 3. Analyze by Direction
        print(f"\n{Color.CYAN}➤ BY DIRECTION{Color.RESET}")
        direction_counts = subset['outcome'].str.extract(r'\[(.*?)\]', expand=False).value_counts()
        if not direction_counts.empty:
            for dir_val, count in direction_counts.items():
                print(f"  {dir_val:<10} | {count:>2} Trades")
        else:
            print("  Could not parse direction.")

    print(f"\n{Color.MAGENTA}===========================================================================\n{Color.RESET}")

if __name__ == "__main__":
    analyze()