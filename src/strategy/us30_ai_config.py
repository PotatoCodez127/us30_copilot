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
# (e.g., US30 is volatile, maybe a 5.0 point buffer reduces fake-outs)
BREAKOUT_BUFFER_POINTS = 0.0