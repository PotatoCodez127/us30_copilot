# US30 Copilot - Project Memory

## Project Overview
An automated quantitative trading assistant for US30 (Dow Jones) combining technical analysis with AI risk assessment.

## Completed Tasks

### Data Sources
* yfinance: Fetches 5 days of 1-minute NY session data (13:30-20:00 UTC)
* MetaTrader5: Fetches 10+ days of 1-minute 24-hour data (00:00-24:00 UTC)
* MT5 includes Asian session (00:00-04:00 UTC) for proper analysis

### Core Scripts
* main_backtest.py: Backtests with MT5 data (5 days), uses State Machine + AI
* main_live.py: Live trading bot using yfinance (5 days)
* discovery_miner.py: Mirrors main_backtest.py logic, optimized for bulk analysis
* All scripts use AI (Ollama Cloud) for risk assessment

### Technical Analysis
* Asian Range: 00:00-04:00 UTC high/low (or fallback to entire day)
* Daily Pivots: P, S1, S2, R1, R2 from previous day
* State Machine: Low Sweep -> High Test -> Pivot Bounce -> Setup Trigger
* Narrative tracking: 4 condition sequence leading to trade signal

### AI Integration
* Ollama Cloud: qwen3-coder:480b-cloud model
* Risk assessment per setup
* Logged to Supabase database

### Visual Charts
* 200 candles centered on entry
* Full OHLC candlesticks with wicks
* Entry marker at exact close price
* SL (red dashed) and TP (green dashed) lines
* Charts in results/charts/

## Data Flow
1. Fetch 1-minute data (MT5 = 24h, yfinance = NY only)
2. Calculate Asian Range (00:00-04:00 UTC)
3. Calculate yesterday's Pivots
4. Run State Machine on NY session (13:30-20:00 UTC)
5. Trigger setup when narrative complete
6. Send to AI for risk assessment
7. Log to Supabase

## Running
```bash
python main_backtest.py       # Backtest (uses MT5)
python discovery_miner.py     # Bulk analysis (uses MT5)  
python main_live.py           # Live trading (uses yfinance)
python fetch_mt5_data.py      # Fetch MT5 data
```

## Notes
* Discovery requires 24-hour data for Asian Session analysis
* main_live/main_backtest work with either source
* MT5 provides superior data depth (10+ days vs 5)
