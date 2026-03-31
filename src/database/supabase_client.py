import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load the keys from the .env file
load_dotenv()

def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("⚠️ Warning: Missing Supabase credentials in .env file. Database logging skipped.")
        return None
        
    return create_client(url, key)

def log_setup_to_db(setup_payload: dict):
    """
    Takes the JSON payload from the State Machine + AI and inserts it into Supabase.
    """
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    # Map the Python dictionary to our PostgreSQL columns
    db_row = {
        "setup_timestamp": setup_payload['timestamp'],
        "asset": setup_payload.get('asset', 'US30'),
        "trigger_reason": setup_payload['trigger'],
        "narrative_confirmed": setup_payload['narrative_confirmed'],
        "mfe_points": setup_payload.get('mfe_points'),  # <--- NEW
        "mae_points": setup_payload.get('mae_points'),  # <--- NEW
        "ai_risk_analysis": setup_payload.get('ai_risk_analysis', '')
    }
    
    try:
        # Insert the row into the us30_setups table
        response = supabase.table("us30_setups").insert(db_row).execute()
        print(f"💾 Setup successfully logged to Supabase! (ID: {response.data[0]['id']})")
        return response.data[0]
    except Exception as e:
        print(f"❌ Failed to log setup to Supabase: {e}")
        return None