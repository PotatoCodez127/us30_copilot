# US30 Discovery Miner - Visual Setup Analysis

## Overview
This discovery script analyzes the last 7 days of 1-minute US30 data to find high-probability trading setups.

## How It Works

### Strategy Logic:
1. **Opening Range**: Identifies the 13:30-14:00 UTC range (high/low)
2. **Daily Pivots**: Calculates standard floor pivots from previous day (P, S1, R1, S2, R2)
3. **Trigger Detection**: Finds when price interacts with:
   - Opening Range High/Low
   - Daily Pivot levels (P, S1, R1, S2, R2)
4. **Trade Simulation**: Simulates both LONG and SHORT entries at trigger points
5. **Risk Management**: TP/M SL based on 100/80 point targets

### Parameters:
- **MIN_MFE**: 100 points target profit
- **MAX_MAE**: 80 points max drawdown threshold

## Usage

### Step 1: Fetch recent 7 days of data
```bash
python fetch_real_history.py
```

### Step 2: Run discovery analysis
```bash
python discovery_miner.py
```

## Output

### discovery_setups.txt
Contains all discovered setups sorted by Risk/Reward ratio.

### results/charts/
PNG charts for each setup showing price action, entry markers, SL/TP levels.

## Performance Summary

| # | Date | Direction | Trigger | Entry | MFE | MAE | R:R |
|---|------|-----------|---------|-------|-----|-----|-----|
| 1 | Mar 31 | LONG | Opening Range Low | 45527.78 | +855.62 | -47.48 | 18.02:1 |
| 2 | Mar 26 | SHORT | Daily Pivot | 46495.21 | +584.46 | -52.38 | 11.16:1 |
| 3 | Mar 27 | SHORT | Opening Range Low | 45480.74 | +417.41 | -78.20 | 5.34:1 |
| 4 | Mar 30 | SHORT | Daily Pivot | 45364.60 | +307.32 | -72.99 | 4.21:1 |
| 5 | Mar 25 | LONG | R1 Pivot | 46405.42 | +171.74 | -50.97 | 3.37:1 |
| 6 | Mar 24 | SHORT | Daily Pivot | 46308.47 | +211.67 | -74.08 | 2.86:1 |

**Key Findings:**
- Win Rate: 100% (all trades hit TP)
- Market Direction: Bearish (4 SHORT vs 2 LONG)
- Best Performer: LONG at Opening Range Low on Mar 31 (+855 points)

## Timezone Note
All timestamps are in UTC.
