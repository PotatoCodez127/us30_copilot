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
    
    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
    valid_sl = df['sl_distance'].apply(lambda x: x if x > 0 else 75.0) if 'sl_distance' in df.columns else 75.0
    lot_size = dollar_risk / valid_sl
    
    df['dollar_pnl'] = (df['pnl_points'] * lot_size) - (lot_size * COMMISSION_PER_LOT)
    df['cumulative_pnl'] = df['dollar_pnl'].cumsum()
    df['equity'] = ACCOUNT_SIZE + df['cumulative_pnl']
    df['peak_equity'] = df['equity'].cummax()
    df['drawdown_pct'] = ((df['peak_equity'] - df['equity']) / df['peak_equity']) * 100

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
    # ☠️ NEW: DEEP AUTOPSY OF LOSING TRADES
    # =================================================================================
    print(f"\n{Color.RED}===========================================================================")
    print(f"☠️ DEEP AUTOPSY: PROFILING THE LOSING TRADES")
    print(f"==========================================================================={Color.RESET}")
    
    if losses.empty:
        print("No hard losses found to autopsy!")
        return

    # 1. Add Timing Features
    losses = losses.copy()
    losses['day_of_week'] = losses['timestamp'].dt.day_name()
    losses['time_window'] = losses['timestamp'].dt.strftime('%H:%M')

    # 2. Analyze by Day of the Week
    print(f"\n{Color.YELLOW}➤ LOSSES BY DAY OF THE WEEK (Are certain days toxic?){Color.RESET}")
    day_counts = losses['day_of_week'].value_counts()
    total_losses = len(losses)
    
    # Compare against total trades taken on those days to find the true "Loss Rate" per day
    df['day_of_week'] = df['timestamp'].dt.day_name()
    total_by_day = df['day_of_week'].value_counts()
    
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        if day in day_counts:
            l_count = day_counts[day]
            t_count = total_by_day.get(day, 0)
            fail_rate = (l_count / t_count) * 100 if t_count > 0 else 0
            print(f"  {day:<10} | {l_count:>2} Hard Stops | Failed {fail_rate:>5.1f}% of setups taken this day")
        else:
            print(f"  {day:<10} |  0 Hard Stops")

    # 3. Analyze by Micro-Timing (Specific 15-min windows)
    print(f"\n{Color.YELLOW}➤ LOSSES BY MICRO-TIMING (When are the traps sprung?){Color.RESET}")
    # Group by HH:MM to see if the losses cluster at 15:00 vs 15:45
    time_counts = losses['time_window'].value_counts().head(5) # Top 5 deadliest minutes
    for t_window, count in time_counts.items():
        print(f"  {t_window} UTC  | {count:>2} Hard Stops")

    # 4. Analyze by Direction
    print(f"\n{Color.YELLOW}➤ LOSSES BY DIRECTION{Color.RESET}")
    direction_counts = losses['outcome'].str.extract(r'\[(.*?)\]', expand=False).value_counts()
    for dir_val, count in direction_counts.items():
        print(f"  {dir_val:<10} | {count:>2} Hard Stops")

    print(f"\n{Color.RED}===========================================================================\n{Color.RESET}")

if __name__ == "__main__":
    analyze()