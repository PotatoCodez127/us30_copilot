import pandas as pd

def calculate_asian_range(df: pd.DataFrame, start_time: str = '00:00', end_time: str = '04:00') -> dict:
    """
    Calculates the highest high and lowest low during the defined Asian session.
    Falls back to entire day's range if no Asian session data found.
    """
    if df.empty:
        raise ValueError("The provided DataFrame is empty.")
        
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("The DataFrame index must be a DatetimeIndex.")
        
    session_data = df.between_time(start_time, end_time)
    
    if session_data.empty:
        print(f"[INFO] No Asian session data found. Using entire day's range as fallback.")
        asia_high = df['high'].max()
        asia_low = df['low'].min()
        return {
            "asia_high": float(asia_high),
            "asia_low": float(asia_low)
        }
        
    asia_high = session_data['high'].max()
    asia_low = session_data['low'].min()
    
    return {
        "asia_high": float(asia_high),
        "asia_low": float(asia_low)
    }
