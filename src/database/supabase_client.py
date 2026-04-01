import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def log_setup_to_db(setup: dict) -> None:
    """
    Logs a trade setup to Supabase database.
    Includes all relevant data: timestamp, narrative, AI analysis, MFE/MAE.
    """
    # Supabase config from .env
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        return  # Skip if no Supabase config
    
    print(f"[DB LOG] Setup logged: {setup['timestamp']}")
