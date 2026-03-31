class US30SessionTracker:
    def __init__(self, asia_high: float, asia_low: float, daily_pivots: list):
        """
        Initializes the session tracker with the static levels for the day.
        """
        self.asia_high = asia_high
        self.asia_low = asia_low
        self.pivots = daily_pivots
        
        # Narrative State Memory
        self.low_swept = False
        self.high_tested_once = False
        self.liquidity_grabbed = False
        
        # Final Trigger
        self.setup_ready = False

    def update_state(self, current_candle_15m: dict, current_candle_1m: dict):
        """
        Evaluates the current market state and updates the narrative sequence.
        Returns a JSON-ready dictionary for the AI agent if the setup is triggered.
        """
        
        # Condition 1: Downside Magnet Cleared (Asia Low Swept)
        if not self.low_swept:
            if current_candle_1m['low'] < self.asia_low:
                self.low_swept = True

        # Condition 2: Asia High Tested (Fake-out)
        # Price breaks the high, but the 15m candle fails to close above it
        if self.low_swept and not self.high_tested_once:
            if current_candle_1m['high'] > self.asia_high and current_candle_15m['close'] <= self.asia_high:
                self.high_tested_once = True

        # Condition 3: Pivot Bounce (Liquidity Grab)
        # Price wicks below a daily pivot and closes above it
        if self.high_tested_once and not self.liquidity_grabbed:
            for pivot in self.pivots:
                if current_candle_1m['low'] <= pivot and current_candle_1m['close'] > pivot:
                    self.liquidity_grabbed = True
                    break  # Stop checking pivots once one is bounced

        # Condition 4: The Final Trigger (15m close above Asia High)
        if self.liquidity_grabbed and not self.setup_ready:
            if current_candle_15m['close'] > self.asia_high:
                self.setup_ready = True
                
                # Package the state for the AI Agent
                return {
                    "asset": "US30",
                    "trigger": "15m Close Above Asian High",
                    "narrative_confirmed": ["Low Swept", "High Tested", "Pivot Bounced"]
                }
                
        return None