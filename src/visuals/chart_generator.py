import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def plot_setup_chart(df_15m, entry_time, entry_price, stop_loss, take_profit, 
                     levels_dict, direction, save_path=None, show_plot=False):
    entry_dt = pd.to_datetime(entry_time)
    # Remove timezone for comparison
    if entry_dt.tzinfo:
        entry_dt_no_tz = entry_dt.replace(tzinfo=None)
    else:
        entry_dt_no_tz = entry_dt
    
    # Find entry position in the dataframe
    entry_idx_loc = None
    for i, dt in enumerate(df_15m.index):
        dt_check = pd.to_datetime(dt)
        if dt_check.tzinfo:
            dt_check = dt_check.replace(tzinfo=None)
        if dt_check == entry_dt_no_tz:
            entry_idx_loc = i
            break
    
    # If not found, use middle of data as fallback
    entry_pos = entry_idx_loc if entry_idx_loc is not None else len(df_15m) // 2
    
    # Center the chart around the entry candle with 200 candles total
    start_idx = max(0, entry_pos - 99)
    end_idx = min(len(df_15m), entry_pos + 101)
    
    chart_data = df_15m.iloc[start_idx:end_idx].copy()
    
    if chart_data.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 5), facecolor='white')
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Get the exact close price from the entry candle (using absolute indices)
    entry_candle = df_15m.iloc[entry_pos]
    actual_entry_price = entry_candle['close']
    
    # Plot actual candlesticks with wicks and bodies
    x_positions = range(len(chart_data))
    width = 0.6
    
    for i in x_positions:
        row = chart_data.iloc[i]
        open_price = row['open']
        high_price = row['high']
        low_price = row['low']
        close_price = row['close']
        
        # Determine color: green for bullish (close >= open), red for bearish
        if close_price >= open_price:
            color = '#00b894'  # Green
        else:
            color = '#d63031'  # Red
        
        # Draw wick (high to low)
        ax.plot([i, i], [low_price, high_price], color=color, linewidth=1)
        
        # Draw body (open to close)
        body_height = abs(close_price - open_price)
        if body_height > 0:
            bottom = min(open_price, close_price)
            ax.add_patch(patches.Rectangle((i - width/2, bottom), width, body_height, 
                                           facecolor=color, edgecolor=color))
    
    # Entry mark - position relative to chart_data, price from actual candle
    entry_idx = entry_pos - start_idx
    
    if entry_idx >= 0 and entry_idx < len(chart_data):
        if direction == "LONG":
            ax.scatter(entry_idx, actual_entry_price, color='cyan', s=150, marker='^', zorder=10)
            ax.text(entry_idx, actual_entry_price + 2, 'ENTRY', color='cyan', fontsize=9, 
                   fontweight='bold', ha='center')
        else:
            ax.scatter(entry_idx, actual_entry_price, color='red', s=150, marker='v', zorder=10)
            ax.text(entry_idx, actual_entry_price - 2, 'ENTRY', color='red', fontsize=9, 
                   fontweight='bold', ha='center')
    
    # SL and TP lines
    ax.axhline(y=stop_loss, color='darkred', linestyle='--', linewidth=1.5, label='Stop Loss')
    ax.axhline(y=take_profit, color='darkgreen', linestyle='--', linewidth=1.5, label='Take Profit')
    
    # Format x-axis as time (show all labels for better visibility)
    step = max(1, len(chart_data) // 10)
    ax.set_xticks(x_positions[::step])
    ax.set_xticklabels([chart_data.index[i].strftime('%H:%M') for i in x_positions[::step]], rotation=45)
    
    # Title and labels
    title_prefix = "LONG" if direction == "LONG" else "SHORT"
    ax.set_title(f'{title_prefix} Setup | {entry_dt.strftime("%Y-%m-%d %H:%M")} UTC', fontsize=12, fontweight='bold')
    ax.set_ylabel('Price', fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return save_path
    
    if show_plot:
        plt.show()
    else:
        plt.close(fig)
    
    return save_path
