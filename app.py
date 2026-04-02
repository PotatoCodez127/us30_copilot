import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="US30 Quant Engine", layout="wide", page_icon="📈")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    if not os.path.exists('results/trade_log.csv'):
        return pd.DataFrame()
    df = pd.read_csv('results/trade_log.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour_utc'] = df['timestamp'].dt.hour
    return df

df = load_data()

# --- SIDEBAR CONTROLS ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python-logo-notext.svg/1869px-Python-logo-notext.svg.png", width=50)
st.sidebar.title("Engine Parameters")
st.sidebar.markdown("Filter the backtest results dynamically.")

if not df.empty:
    # Filters
    min_pnl = st.sidebar.slider("Minimum PNL ($)", int(df['dollar_pnl'].min()), int(df['dollar_pnl'].max()), int(df['dollar_pnl'].min()))
    selected_hours = st.sidebar.multiselect("Trading Hours (UTC)", sorted(df['hour_utc'].unique()), default=sorted(df['hour_utc'].unique()))
    
    # Apply Filters
    filtered_df = df[(df['dollar_pnl'] >= min_pnl) & (df['hour_utc'].isin(selected_hours))].copy()
    
    # --- CALCULATE METRICS ---
    total_trades = len(filtered_df)
    wins = len(filtered_df[filtered_df['dollar_pnl'] > 0])
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    total_pnl = filtered_df['dollar_pnl'].sum()
    
    # --- UI LAYOUT ---
    st.title("🏆 US30 Copilot - Institutional Dashboard")
    st.markdown("### Strategy Performance & Forensic Analysis")
    
    # Top KPI Row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Executions", total_trades)
    col2.metric("Win Rate", f"{win_rate:.2f}%")
    col3.metric("Net Profit", f"${total_pnl:,.2f}", delta=f"${total_pnl:,.2f}")
    col4.metric("Avg Hold Time", f"{filtered_df['holding_time'].mean():.1f} min" if total_trades > 0 else "0 min")

    # Equity Curve Chart
    st.markdown("---")
    st.subheader("📈 Cumulative Equity Curve")
    if total_trades > 0:
        filtered_df = filtered_df.sort_values('timestamp')
        filtered_df['Cumulative_PNL'] = filtered_df['dollar_pnl'].cumsum() + 100000 # Assume 100k start
        
        st.line_chart(filtered_df.set_index('timestamp')['Cumulative_PNL'], use_container_width=True)
    else:
        st.warning("No trades match the current filters.")

    # Data Table
    st.markdown("---")
    st.subheader("🤖 Forensic Execution Log")
    display_df = filtered_df[['timestamp', 'trigger', 'outcome', 'pnl_points', 'dollar_pnl', 'sl_distance', 'holding_time']].copy()
    display_df.columns = ['Date', 'Trigger', 'Outcome', 'Points', 'Net Profit ($)', 'Risk (Pts)', 'Hold (Min)']
    st.dataframe(display_df.style.map(lambda x: 'color: green' if isinstance(x, (int, float)) and x > 0 else ('color: red' if isinstance(x, (int, float)) and x < 0 else ''), subset=['Net Profit ($)', 'Points']), use_container_width=True)

else:
    st.error("No trade data found! Please run `main_backtest.py` first to generate the log.")