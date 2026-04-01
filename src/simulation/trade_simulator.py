import pandas as pd

def simulate_trade_entry(entry_price, future_data, direction, min_rr=1.0):
    if future_data.empty:
        return None
    
    best_sl = None
    best_tp = None
    best_rr = min_rr
    
    for i in range(len(future_data)):
        row = future_data.iloc[i]
        current_price = row['close']
        
        if direction == "LONG":
            max_profit = row['high'] - entry_price
        else:
            max_profit = entry_price - row['low']
        
        if max_profit > 0:
            required_sl_distance = max_profit / min_rr
            
            if direction == "LONG":
                simulated_sl = current_price - required_sl_distance
                simulated_tp = current_price + max_profit
                simulated_rr = max_profit / (current_price - simulated_sl) if (current_price - simulated_sl) != 0 else 0
                
                if simulated_rr >= min_rr and simulated_rr > best_rr:
                    best_rr = simulated_rr
                    best_sl = simulated_sl
                    best_tp = simulated_tp
            else:
                simulated_sl = current_price + required_sl_distance
                simulated_tp = current_price - max_profit
                simulated_rr = max_profit / (simulated_sl - current_price) if (simulated_sl - current_price) != 0 else 0
                
                if simulated_rr >= min_rr and simulated_rr > best_rr:
                    best_rr = simulated_rr
                    best_sl = simulated_sl
                    best_tp = simulated_tp
    
    if best_sl is None:
        if direction == "LONG":
            best_sl = entry_price - 80
            best_tp = entry_price + 100
        else:
            best_sl = entry_price + 80
            best_tp = entry_price - 100
        best_rr = 1.0
    
    final_profit = abs(best_tp - entry_price)
    final_loss = abs(best_sl - entry_price)
    final_rr = final_profit / final_loss if final_loss != 0 else 0
    if final_rr < min_rr:
        if direction == "LONG":
            best_tp = entry_price + (final_loss * min_rr)
        else:
            best_tp = entry_price - (final_loss * min_rr)
    
    if direction == "LONG":
        final_mfe = best_tp - entry_price
        final_mae = entry_price - best_sl
    else:
        final_mfe = entry_price - best_tp
        final_mae = best_sl - entry_price
    
    return {
        "entry": entry_price,
        "direction": direction,
        "final_sl": round(best_sl, 2),
        "final_tp": round(best_tp, 2),
        "final_mfe": round(final_mfe, 2),
        "final_mae": round(final_mae, 2),
        "final_rr": round(final_rr, 2)
    }
