import pandas as pd
import os

# Load the historical data
df = pd.read_csv("data/historical_us30_1m.csv")
df['datetime'] = pd.to_datetime(df['datetime'], utc=True)
df.set_index('datetime', inplace=True)

# Read discovery results
with open("discovery_setups.txt", "r") as f:
    content = f.read()
    
print(content)

# Show some sample data
print("\n=== Sample of Data Structure ===")
print(f"Total rows in CSV: {len(df)}")
print(f"Date range: {df.index.min()} to {df.index.max()}")
print(f"\nColumns: {list(df.columns)}")

# Show one sample candle
print(f"\nSample candle (2026-03-31 14:45):")
sample = df.loc['2026-03-31 14:45:00']
print(f"  Open: {sample['open']:.2f}")
print(f"  High: {sample['high']:.2f}")
print(f"  Low: {sample['low']:.2f}")
print(f"  Close: {sample['close']:.2f}")
print(f"  Volume: {sample['volume']}")
