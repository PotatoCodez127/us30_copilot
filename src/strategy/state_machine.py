from typing import Optional

class US30SessionTracker:
    def __init__(self, or_high: float, or_low: float, daily_pivots: dict):
        self.or_high = or_high
        self.or_low = or_low
        self.pivots = daily_pivots

    # --- THE FIX: Using Optional[dict] instead of dict | None ---
    def update_state(self, candle_15m: dict, current_1m: dict) -> Optional[dict]:
        high = candle_15m['high']
        low = candle_15m['low']
        close = candle_15m['close']
        
        interacted_level = None
        close_status = "Unknown"

        if close > self.or_high:
            interacted_level = "Opening Range High"
            close_status = "Closed ABOVE Level (Confirmed 15m Breakout)"
        elif close < self.or_low:
            interacted_level = "Opening Range Low"
            close_status = "Closed BELOW Level (Confirmed 15m Breakdown)"
            
        elif low <= self.pivots['P'] <= high:
            interacted_level = "Daily Central Pivot"
            close_status = f"Touched at {close}"
        elif low <= self.pivots['S1'] <= high:
            interacted_level = "S1 Pivot"
            close_status = f"Touched at {close}"
        elif low <= self.pivots['R1'] <= high:
            interacted_level = "R1 Pivot"
            close_status = f"Touched at {close}"

        if interacted_level:
            return {
                "asset": "US30",
                "trigger": f"15m Confirmed Close: {interacted_level}" if "Opening" in interacted_level else f"15m Touch: {interacted_level}",
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