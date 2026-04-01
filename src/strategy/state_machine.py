class US30SessionTracker:
    def __init__(self, or_high: float, or_low: float, daily_pivots: dict):
        """
        Initializes the tracker with the Opening Range (first 30 mins of NY) 
        and the Daily Pivots.
        """
        self.or_high = or_high
        self.or_low = or_low
        self.pivots = daily_pivots

    def update_state(self, candle_15m: dict, current_1m: dict) -> dict | None:
        """
        Evaluates the current 15m candle. If it touches a key Opening Range 
        level or Daily Pivot, it triggers a setup payload for the AI.
        """
        high = candle_15m['high']
        low = candle_15m['low']
        close = candle_15m['close']
        
        interacted_level = None

        # 1. Did we touch the Opening Range?
        if low <= self.or_high <= high:
            interacted_level = "Opening Range High"
        elif low <= self.or_low <= high:
            interacted_level = "Opening Range Low"
            
        # 2. Did we touch a Daily Pivot?
        elif low <= self.pivots['P'] <= high:
            interacted_level = "Daily Central Pivot"
        elif low <= self.pivots['S1'] <= high:
            interacted_level = "S1 Pivot"
        elif low <= self.pivots['R1'] <= high:
            interacted_level = "R1 Pivot"

        # 3. If a level was touched, build the payload for the AI
        if interacted_level:
            
            # Basic logic to help the AI: Did we close above or below the level we touched?
            close_status = "Unknown"
            if interacted_level == "Opening Range High":
                close_status = "Closed ABOVE Level (Breakout)" if close > self.or_high else "Closed BELOW Level (Rejection)"
            elif interacted_level == "Opening Range Low":
                close_status = "Closed BELOW Level (Breakdown)" if close < self.or_low else "Closed ABOVE Level (Rejection/Bounce)"

            return {
                "asset": "US30",
                "trigger": f"15m Touch: {interacted_level}",
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