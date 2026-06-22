# tests/test_state_machine_ai.py

import unittest
from unittest.mock import patch

from src.strategy.state_machine import US30SessionTracker


class TestStateMachineAiSandbox(unittest.TestCase):
    def setUp(self):
        # Standard US30 environment setup
        self.or_high = 39050.0
        self.or_low = 39000.0
        self.pivots = {"P": 39025.0, "S1": 38950.0, "R1": 39100.0}

        self.tracker = US30SessionTracker(self.or_high, self.or_low, self.pivots)

        # A candle that breaks the OR High by exactly 2 points
        self.breakout_candle = {"high": 39060.0, "low": 39040.0, "close": 39052.0}

        # A candle that touches the Central Pivot
        self.pivot_candle = {"high": 39030.0, "low": 39020.0, "close": 39028.0}

    @patch("src.strategy.state_machine.BREAKOUT_BUFFER_POINTS", 0.0)
    @patch("src.strategy.state_machine.ENABLE_OR_CHECKS", True)
    @patch("src.strategy.state_machine.ENABLE_PIVOT_CHECKS", True)
    def test_default_behavior(self):
        """Test the baseline logic with no AI tweaks."""
        result = self.tracker.update_state(self.breakout_candle, {})
        self.assertIsNotNone(result)
        self.assertIn("Opening Range High", result["trigger"])

    @patch("src.strategy.state_machine.BREAKOUT_BUFFER_POINTS", 5.0)
    @patch("src.strategy.state_machine.ENABLE_OR_CHECKS", True)
    def test_ai_buffer_rejection(self):
        """Test if the AI applying a 5-point buffer correctly rejects a weak 2-point breakout."""
        # The candle closes at 39052. OR High is 39050. Buffer is 5.
        # It needs to close > 39055. This should return None.
        result = self.tracker.update_state(self.breakout_candle, {})
        self.assertIsNone(result, "State machine failed to respect the AI's Breakout Buffer.")

    @patch("src.strategy.state_machine.ENABLE_PIVOT_CHECKS", False)
    def test_ai_disabling_pivots(self):
        """Test if the AI turning off the PIVOT feature flag successfully bypasses pivot logic."""
        # The candle clearly touches the pivot point
        result = self.tracker.update_state(self.pivot_candle, {})

        # Because the AI set ENABLE_PIVOT_CHECKS to False, it should ignore the touch
        self.assertIsNone(
            result, "State machine triggered a pivot trade even though AI disabled them."
        )

    @patch("src.strategy.state_machine.ENABLE_OR_CHECKS", False)
    def test_ai_disabling_or_breakouts(self):
        """Test if the AI turning off Opening Range checks bypasses them."""
        result = self.tracker.update_state(self.breakout_candle, {})
        self.assertIsNone(
            result, "State machine triggered an OR trade even though AI disabled them."
        )


if __name__ == "__main__":
    unittest.main()