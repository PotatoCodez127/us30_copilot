# ==========================================
# 🤖 AUTORESEARCHER SANDBOX
# Only edit variables in this file.
# ==========================================

# --- FEATURE FLAGS ---
# Should the bot take trades based on Opening Range Breakouts?
ENABLE_OR_CHECKS = True

# Should the bot take trades based on Pivot Point bounces/touches?
ENABLE_PIVOT_CHECKS = True

# --- THRESHOLDS ---
# How many points beyond the OR High/Low must the 15m candle close to be valid?
BREAKOUT_BUFFER_POINTS = 0.0 

# --- RISK MANAGEMENT ---
# The hard Stop Loss in US30 index points
SL_RISK_POINTS = 150.0

# The hard Take Profit in US30 index points
TP_REWARD_POINTS = 250.0

# Maximum time in minutes to hold a trade before forcing an exit
MAX_HOLDING_MINUTES = 180