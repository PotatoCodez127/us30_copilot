import pandas as pd
import re
import os
from src.data_feed.historical import load_and_prep_data, simulate_ny_session
from src.math_engine.pivots import calculate_daily_pivots
from src.ai_agent.ollama_client import analyze_setup_with_ollama

class Color:
    GREEN, CYAN, YELLOW, RED, MAGENTA, WHITE, RESET = '\033[92m', '\033[96m', '\033[93m', '\033[91m', '\033[95m', '\033[97m', '\033[0m'

# --- REALISTIC ACCOUNT & FRICTION PARAMETERS ---
ACCOUNT_SIZE = 100000.0
RISK_PERCENT = 0.01  # Risk 1% per trade ($1,000)
COMMISSION_PER_LOT = 5.00 
SLIPPAGE_POINTS = 1.5 
# -----------------------------------------------

# --- INSTITUTIONAL LIQUIDITY LEVELS (TradingView HTF Grid) ---
def generate_tradingview_levels():
    """
    Dynamically generates the Q4 and EQ support/resistance levels 
    to perfectly match the TradingView 'US30 HTF Trade Levels' indicator.
    """
    q4_start = 48362
    eq_start = 48555
    spacing = 385
    levels_count = 14
    
    levels = []
    # Generate the 15 up and 15 down lines just like the Pine Script
    for i in range(-levels_count, levels_count + 1):
        levels.append(q4_start + (i * spacing)) # Q4 Base Levels
        levels.append(eq_start + (i * spacing)) # EQ 50% Levels
        
    return sorted(levels)

# Initialize the synchronized grid
Q4_LEVELS = generate_tradingview_levels()

def is_too_close_to_support(entry_price: float, levels: list, minimum_clearance: float = 50.0) -> bool:
    """
    Checks if the short entry is too close to a major psychological support level.
    Returns True if we are shorting into a brick wall.
    """
    for level in levels:
        # If the level is below our entry price, and the distance is less than our minimum clearance
        if entry_price > level and (entry_price - level) < minimum_clearance:
            return True
    return False

def run_master_backtest(csv_filepath: str):
    print(f"{Color.CYAN}🚀 Initializing Final Production Engine (God Mode)...{Color.RESET}")
    df = load_and_prep_data(csv_filepath)
    unique_dates = pd.Series(df.index.date).unique()
    all_logged_setups = []

    for i in range(1, len(unique_dates)):
        current_date_str = str(unique_dates[i])
        prev_day_data, current_day_data = df.loc[str(unique_dates[i-1])], df.loc[current_date_str]
        
        if prev_day_data.empty or current_day_data.empty: continue
        try: 
            pivots = calculate_daily_pivots(prev_day_data['high'].max(), prev_day_data['low'].min(), prev_day_data['close'].iloc[-1])
        except ValueError: 
            continue

        daily_setups = simulate_ny_session(current_day_data, current_date_str, pivots)
        
        # --- 1. SESSION LOCKOUT FLAG ---
        trade_taken_today = False 
        
        if daily_setups:
            for setup in daily_setups:
                
                # --- 2. ENFORCE THE LOCKOUT ---
                if trade_taken_today:
                    continue

                trigger_time = pd.to_datetime(setup['timestamp'])
                
                # 1. STRICT FORENSIC FILTERS
                if trigger_time.hour != 14: continue # 10 AM NY hour only
                if 'Pivot' in setup['trigger']: continue # No pivot noise
                
                # --- ASYMMETRIC FILTER: THE AMPUTATION ---
                if 'Opening Range High' in setup['trigger']: continue # Kill topside breakouts
                
                # --- NEW Q4 PROXIMITY FILTER ---
                # Check if our entry price is too close to a Q4 level (e.g., within 50 points)
                base_entry = setup.get('context', {}).get('close_price', 0)
                if is_too_close_to_support(base_entry, Q4_LEVELS, minimum_clearance=50.0):
                    print(f"{Color.YELLOW}⏭️ SKIPPED: Selling into Q4 Support at {base_entry}{Color.RESET}")
                    continue
                
                print(f"{Color.GREEN}🟢 SETUP TRIGGERED: {current_date_str} at {setup['timestamp']}{Color.RESET}")
                ai_analysis = analyze_setup_with_ollama(setup)
                
                setup['trade_outcome'] = "Skipped"
                setup['pnl_points'], setup['holding_time_mins'], setup['dollar_pnl'] = 0.0, 0, 0.0
                setup['sl_distance'], setup['tp_distance'] = 0.0, 0.0
                
                dir_match = re.search(r'DIRECTION:\s*(LONG|SHORT|NONE)', ai_analysis, re.IGNORECASE)
                sl_match = re.search(r'SL:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                tp_match = re.search(r'TP:\s*[\$]?([\d,]+\.?\d*)', ai_analysis)
                
                # 2. OMNI-DIRECTIONAL EXECUTION
                if dir_match and dir_match.group(1).upper() in ['LONG', 'SHORT'] and sl_match and tp_match: 
                    direction = dir_match.group(1).upper()
                    
                    # --- STANDARDIZED RISK ---
                    risk_in_points = 95.0
                    dollar_risk = ACCOUNT_SIZE * RISK_PERCENT
                    lot_size = dollar_risk / risk_in_points
                    total_commission = lot_size * COMMISSION_PER_LOT

                    setup['sl_distance'] = risk_in_points
                    setup['tp_distance'] = 190.0

                    future_data = current_day_data.loc[setup['timestamp'] : f"{current_date_str} 20:00:00+00:00"]
                    trigger_idx = future_data.index[0] if not future_data.empty else trigger_time
                    outcome = "Closed at End of Day 🌇"
                    
                    pnl_points = 0.0
                    
                    # ==========================================
                    # LONG EXECUTION LOGIC (Kept for robustness)
                    # ==========================================
                    if direction == 'LONG':
                        entry_price = base_entry + SLIPPAGE_POINTS
                        sl = entry_price - risk_in_points 
                        tp = entry_price + 190.0
                        exit_price = future_data['close'].iloc[-1] if not future_data.empty else entry_price
                        exit_time = future_data.index[-1] if not future_data.empty else trigger_idx

                        tp_hit = False
                        highest_seen = entry_price
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            highest_seen = max(highest_seen, high)
                            
                            # Time Ejection
                            if (idx - trigger_time).total_seconds() / 60.0 >= 45 and not tp_hit:
                                if current_close < (entry_price + 10.0):
                                    outcome, exit_price, exit_time = "Time Ejection ⏳", current_close - SLIPPAGE_POINTS, idx
                                    break

                            # Trailing Stop
                            if not tp_hit and high >= tp:
                                tp_hit, sl = True, entry_price + 5.0 # BE + 5
                            if tp_hit:
                                sl = max(sl, highest_seen - 50.0)
                            
                            # Hard Stop
                            if low <= sl:
                                outcome, exit_price, exit_time = ("Hit Trailing Stop 🏃‍♂️💨" if tp_hit else "Hit Hard Stop 🛑"), sl - SLIPPAGE_POINTS, idx
                                break
                                
                        pnl_points = exit_price - entry_price

                    # ==========================================
                    # SHORT EXECUTION LOGIC (The Alpha)
                    # ==========================================
                    elif direction == 'SHORT':
                        entry_price = base_entry - SLIPPAGE_POINTS
                        sl = entry_price + risk_in_points 
                        tp = entry_price - 190.0
                        exit_price = future_data['close'].iloc[-1] if not future_data.empty else entry_price
                        exit_time = future_data.index[-1] if not future_data.empty else trigger_idx

                        tp_hit = False
                        lowest_seen = entry_price
                        
                        for idx, candle in future_data.iloc[1:].iterrows():
                            high, low, current_close = candle['high'], candle['low'], candle['close']
                            lowest_seen = min(lowest_seen, low)
                            
                            # Time Ejection
                            if (idx - trigger_time).total_seconds() / 60.0 >= 45 and not tp_hit:
                                if current_close > (entry_price - 10.0): # Price hasn't dropped
                                    outcome, exit_price, exit_time = "Time Ejection ⏳", current_close + SLIPPAGE_POINTS, idx
                                    break

                            # Trailing Stop
                            if not tp_hit and low <= tp:
                                tp_hit, sl = True, entry_price - 5.0 # BE + 5
                            if tp_hit:
                                sl = min(sl, lowest_seen + 50.0) # Trail down
                            
                            # Hard Stop
                            if high >= sl:
                                outcome, exit_price, exit_time = ("Hit Trailing Stop 🏃‍♂️💨" if tp_hit else "Hit Hard Stop 🛑"), sl + SLIPPAGE_POINTS, idx
                                break
                                
                        pnl_points = entry_price - exit_price # Inverse calculation for shorts

                    # --- FINAL MATH & LOGGING ---
                    dollar_pnl = (pnl_points * lot_size) - total_commission
                    setup['trade_outcome'] = f"[{direction}] {outcome} at {exit_price:.2f}"
                    setup['pnl_points'] = round(pnl_points, 2)
                    setup['dollar_pnl'] = round(dollar_pnl, 2)
                    setup['holding_time_mins'] = round((exit_time - trigger_time).total_seconds() / 60.0, 1)
                    
                    color = Color.GREEN if dollar_pnl > 0 else Color.RED
                    print(f"{color}▶ EXECUTED {direction}: {outcome} | Pts: {setup['pnl_points']} | PNL: ${setup['dollar_pnl']}{Color.RESET}")
                    
                    all_logged_setups.append(setup)
                    
                    # --- TRIGGER THE LOCKOUT ---
                    trade_taken_today = True 

    if all_logged_setups:
        os.makedirs('results', exist_ok=True)
        export_df = pd.DataFrame([{
            'timestamp': t['timestamp'],
            'trigger': t['trigger'],
            'outcome': t['trade_outcome'],
            'pnl_points': t['pnl_points'],
            'dollar_pnl': t['dollar_pnl'],
            'holding_time': t['holding_time_mins'],
            'sl_distance': t.get('sl_distance', 0),
            'tp_distance': t.get('tp_distance', 0)
        } for t in all_logged_setups])
        export_df.to_csv('results/trade_log.csv', index=False)

if __name__ == "__main__":
    run_master_backtest("data/historical_us30_1m.csv")