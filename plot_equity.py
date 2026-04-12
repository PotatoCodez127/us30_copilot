import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

class Color:
    GREEN, CYAN, YELLOW, RED, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[0m'

def generate_equity_curve():
    print(f"{Color.CYAN}📊 Generating Equity Curve...{Color.RESET}")
    
    file_path = 'results/trade_log.csv'
    if not os.path.exists(file_path):
        print(f"{Color.RED}No trade_log.csv found in results/. Run a backtest first!{Color.RESET}")
        return

    df = pd.read_csv(file_path)
    if df.empty:
        print(f"{Color.YELLOW}Trade log is empty. No trades to plot.{Color.RESET}")
        return

    # 1. Chronological Ordering
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    # 2. Calculate Cumulative PnL
    df['cumulative_pnl'] = df['pnl_points'].cumsum()

    # 3. Add a Ground-Zero Starting Point
    start_time = df['timestamp'].iloc[0] - pd.Timedelta(days=1)
    start_row = pd.DataFrame([{'timestamp': start_time, 'cumulative_pnl': 0.0}])
    plot_df = pd.concat([start_row, df[['timestamp', 'cumulative_pnl']]], ignore_index=True)

    # 4. Institutional Dark Mode Plotting
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot the main trajectory line
    ax.plot(plot_df['timestamp'], plot_df['cumulative_pnl'], color='#00ffcc', linewidth=2.5, marker='o', markersize=4)
    
    # Add green/red shading for profit vs drawdown territories
    ax.fill_between(plot_df['timestamp'], plot_df['cumulative_pnl'], 0, where=(plot_df['cumulative_pnl'] >= 0), color='#00ffcc', alpha=0.15)
    ax.fill_between(plot_df['timestamp'], plot_df['cumulative_pnl'], 0, where=(plot_df['cumulative_pnl'] < 0), color='#ff3333', alpha=0.15)

    # 5. Formatting
    ax.axhline(0, color='white', linewidth=1, linestyle='--')
    ax.set_title('US30 Copilot - RAG Strategy Equity Curve', fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Cumulative Net Profit (Points)', fontsize=12)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d, %Y'))
    plt.xticks(rotation=45)
    plt.grid(color='#333333', linestyle='-', linewidth=0.5)
    plt.tight_layout()

    # 6. Save and Display
    save_path = 'results/equity_curve.png'
    plt.savefig(save_path, dpi=300)
    print(f"{Color.GREEN}✅ Equity curve saved successfully to {save_path}{Color.RESET}")
    
    # Open the window natively on Mac
    plt.show()

if __name__ == "__main__":
    generate_equity_curve()