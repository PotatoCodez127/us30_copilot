# tests/test_risk_management_ai.py

import unittest
from unittest.mock import patch

import pandas as pd

from main_backtest import simulate_trade


class TestRiskManagementAiSandbox(unittest.TestCase):
    def setUp(self):
        # Create a fake trigger time
        self.trigger_time = pd.Timestamp("2024-01-01 10:00:00")
        self.raw_entry = 39000.0

        # Create a sequence of 1-minute candles representing a 100-point drawdown,
        # followed by a massive 300-point rally.
        times = pd.date_range(start="2024-01-01 10:00:00", periods=4, freq="1min")
        self.future_data = pd.DataFrame(
            {
                "high": [39000, 38950, 39300, 39400],
                "low": [39000, 38900, 38920, 39300],  # The drawdown to 38900 happens here
                "close": [39000, 38920, 39250, 39350],
            },
            index=times,
        )

    @patch("main_backtest.SL_RISK_POINTS", 150.0)
    @patch("main_backtest.TP_REWARD_POINTS", 250.0)
    @patch("main_backtest.SLIPPAGE_POINTS", 0.0)
    def test_wide_stop_survives_drawdown(self):
        """AI uses a wide 150pt stop. It should survive the 100pt drawdown and hit Take Profit."""
        outcome, exit_price, exit_time, pnl = simulate_trade(
            "LONG", self.raw_entry, self.future_data, self.trigger_time
        )
        self.assertIn("Take Profit", outcome)
        self.assertGreater(pnl, 0)

    @patch("main_backtest.SL_RISK_POINTS", 50.0)
    @patch("main_backtest.TP_REWARD_POINTS", 250.0)
    @patch("main_backtest.SLIPPAGE_POINTS", 0.0)
    def test_tight_stop_gets_stopped_out(self):
        """AI tries a tight 50pt stop. It should hit the hard stop during the drawdown."""
        outcome, exit_price, exit_time, pnl = simulate_trade(
            "LONG", self.raw_entry, self.future_data, self.trigger_time
        )
        self.assertIn("Hard Stop", outcome)
        self.assertLess(pnl, 0)

    @patch("main_backtest.MAX_HOLDING_MINUTES", 1)
    @patch("main_backtest.SL_RISK_POINTS", 200.0)  # Fortified to survive minute-1 drawdown drop
    @patch("main_backtest.SLIPPAGE_POINTS", 0.0)
    def test_ai_time_ejection(self):
        """AI forces the bot to exit after exactly 1 minute of drawdown."""
        outcome, exit_price, exit_time, pnl = simulate_trade(
            "LONG", self.raw_entry, self.future_data, self.trigger_time
        )
        self.assertIn("Time Ejection", outcome)


if __name__ == "__main__":
    unittest.main()