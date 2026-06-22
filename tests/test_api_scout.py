import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Suppress pandas display limits so we can see all columns
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)


def test_api_payload():
    load_dotenv()
    api_key = os.getenv("MASSIVE_API_KEY")

    if not api_key:
        print("⚠️ No MASSIVE_API_KEY found in .env file.")
        return

    print("🚀 Initiating connection to API...")

    # NOTE: You will need to replace this URL with the exact endpoint provided by Massive's docs
    # Example format: "https://api.massive.com/v1/historical/candles"
    endpoint_url = "https://api.massive.com/v2/aggs/ticker/DIA/range/1/minute/2025-04-28/2026-04-28"

    # Parameters (Notice we removed the api_key from here!)
    params = {"adjusted": "true", "sort": "asc", "limit": 50000}

    # 🔒 THE PROPER AUTHENTICATION METHOD
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        # Fire the request with the secure headers
        response = requests.get(endpoint_url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        # Massive/Polygon returns the actual candle array inside the 'results' key
        raw_candles = data.get("results", [])

        if not raw_candles:
            print("⚠️ API authenticated, but returned an empty dataset.")
            return

        # Drop it straight into a Pandas DataFrame
        df = pd.DataFrame(raw_candles)

        print("\n✅ CONNECTION SUCCESSFUL!")
        print("=" * 50)
        print(f"📊 Total Candles Retrieved: {len(df)}")
        print(f"🏷️  Exact Column Names:       {list(df.columns)}")
        print("=" * 50)

        print("\n👀 Preview of First 5 Rows:")
        print(df.head())

        print("\n👀 Preview of Last 5 Rows:")
        print(df.tail())

        # Optional: Save a quick CSV dump to inspect it in Excel/VSCode
        df.to_csv("results/api_scout_dump.csv", index=False)
        print("\n💾 Full payload saved to 'results/api_scout_dump.csv'")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ API REQUEST FAILED: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"🔍 Server Reply: {e.response.text}")


if __name__ == "__main__":
    test_api_payload()
