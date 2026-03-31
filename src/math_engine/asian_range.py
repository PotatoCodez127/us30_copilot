import pandas as pd

def calculate_asian_range(df: pd.DataFrame, start_time: str = '00:00', end_time: str = '04:00') -> dict:
    """
    Calculates the highest high and lowest low during the defined Asian session.
    
    Args:
        df (pd.DataFrame): OHLCV dataframe with a timezone-aware DatetimeIndex.
        start_time (str): Session start time in 'HH:MM' format (UTC).
        end_time (str): Session end time in 'HH:MM' format (UTC).
        
    Returns:
        dict: A dictionary containing 'asia_high' and 'asia_low'.
    """
    if df.empty:
        raise ValueError("The provided DataFrame is empty.")
        
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("The DataFrame index must be a DatetimeIndex.")
        
    # Extract just the rows that fall within the specified time window
    # Note: between_time is inclusive by default
    session_data = df.between_time(start_time, end_time)
    
    if session_data.empty:
        raise ValueError(f"No data found between {start_time} and {end_time}.")
        
    # Calculate the absolute max high and min low
    asia_high = session_data['high'].max()
    asia_low = session_data['low'].min()
    
    return {
        "asia_high": float(asia_high),
        "asia_low": float(asia_low)
    }