def calculate_daily_pivots(high: float, low: float, close: float) -> dict:
    """
    Calculates the standard Daily Floor Pivots (S2, S1, P, R1, R2).
    
    Args:
        high (float): Previous day's high price.
        low (float): Previous day's low price.
        close (float): Previous day's closing price.
        
    Returns:
        dict: A dictionary containing the calculated pivot levels.
    """
    # Input validation
    if high <= 0 or low <= 0 or close <= 0:
        raise ValueError("Price values must be greater than zero.")
        
    if high < low:
        raise ValueError("High price cannot be lower than the low price.")
        
    # Standard Floor Pivot Formulas
    pivot = (high + low + close) / 3
    
    r1 = (pivot * 2) - low
    s1 = (pivot * 2) - high
    
    range_val = high - low
    
    r2 = pivot + range_val
    s2 = pivot - range_val
    
    return {
        "S2": round(s2, 2),
        "S1": round(s1, 2),
        "P":  round(pivot, 2),
        "R1": round(r1, 2),
        "R2": round(r2, 2)
    }