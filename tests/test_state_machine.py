import pytest
from src.strategy.state_machine import US30SessionTracker

def test_long_setup_sequence():
    # 1. Initialize the session tracker with static morning levels
    tracker = US30SessionTracker(
        asia_high=39100.0, 
        asia_low=38900.0, 
        daily_pivots=[38800.0, 38850.0, 39000.0, 39150.0, 39200.0]
    )
    
    # 2. Step 1: Sweep the Asia Low (Price dips to 38880)
    candle_1m = {'high': 38950.0, 'low': 38880.0, 'close': 38920.0}
    candle_15m = {'high': 38950.0, 'low': 38880.0, 'close': 38920.0}
    tracker.update_state(candle_15m, candle_1m)
    
    assert tracker.low_swept == True, "Failed to register Asia Low sweep"
    assert tracker.setup_ready == False

    # 3. Step 2: Test the Asia High (Breaks 39100, but 15m closes below at 39080)
    candle_1m = {'high': 39120.0, 'low': 39050.0, 'close': 39080.0}
    candle_15m = {'high': 39120.0, 'low': 39050.0, 'close': 39080.0}
    tracker.update_state(candle_15m, candle_1m)
    
    assert tracker.high_tested_once == True, "Failed to register Asia High test"

    # 4. Step 3: Pivot Bounce (Dips below the 39000 pivot, closes above it)
    candle_1m = {'high': 39050.0, 'low': 38990.0, 'close': 39020.0}
    candle_15m = {'high': 39050.0, 'low': 38990.0, 'close': 39020.0}
    tracker.update_state(candle_15m, candle_1m)
    
    assert tracker.liquidity_grabbed == True, "Failed to register Pivot bounce"

    # 5. Step 4: The Trigger (15m finally closes above the 39100 Asia High)
    candle_1m = {'high': 39150.0, 'low': 39100.0, 'close': 39130.0}
    candle_15m = {'high': 39150.0, 'low': 39100.0, 'close': 39130.0}
    result = tracker.update_state(candle_15m, candle_1m)
    
    assert tracker.setup_ready == True, "Failed to trigger setup_ready"
    assert result is not None, "Did not return the AI payload"
    assert result['trigger'] == "15m Close Above Asian High"
    
    print("✅ test_long_setup_sequence passed successfully.")