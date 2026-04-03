class US30SessionTracker:
    def __init__(self, or_high: float, or_low: float, daily_pivots: dict):
        """
        Initializes the tracker with the Opening Range (first 30 mins of NY) 
        and the Daily Pivots.
        """
        self.or_high = or_high
        self.or_low = or_low
        self.pivots = daily_pivots

    def update_state(self, candle_5m: dict, current_1m: dict) -> dict | None:
        """
        Evaluates the current 5m candle. Checks for confirmed CLOSES above/below 
        the Opening Range to filter out split-second liquidity sweeps.
        """
        high = candle_5m['high']
        low = candle_5m['low']
        close = candle_5m['close']
        
        interacted_level = None
        close_status = "Unknown"

        # 1. Did we CLOSE beyond the Opening Range? (Filtering Fakeouts)
        if close > self.or_high:
            interacted_level = "Opening Range High"
            close_status = "Closed ABOVE Level (Confirmed 5m Breakout)"
        elif close < self.or_low:
            interacted_level = "Opening Range Low"
            close_status = "Closed BELOW Level (Confirmed 5m Breakdown)"
            
        # 2. Did we touch a Daily Pivot? (Kept as touch for pivots)
        elif low <= self.pivots['P'] <= high:
            interacted_level = "Daily Central Pivot"
            close_status = f"Touched at {close}"
        elif low <= self.pivots['S1'] <= high:
            interacted_level = "S1 Pivot"
            close_status = f"Touched at {close}"
        elif low <= self.pivots['R1'] <= high:
            interacted_level = "R1 Pivot"
            close_status = f"Touched at {close}"

        # 3. If a level was confirmed, build the payload for the AI
        if interacted_level:
            return {
                "asset": "US30",
                "trigger": f"5m Confirmed Close: {interacted_level}" if "Opening" in interacted_level else f"5m Touch: {interacted_level}",
                "narrative_confirmed": [
                    f"Price interacted with {interacted_level}",
                    f"Candle resolved as: {close_status}"
                ],
                "context": {
                    "or_high": round(self.or_high, 2),
                    "or_low": round(self.or_low, 2),
                    "close_price": round(close, 2)
                }
            }
            
        return None