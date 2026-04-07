import os
import time
from dotenv import load_dotenv
from ollama import Client
from src.ai_agent.prompts import generate_risk_assessment_prompt

load_dotenv()

# Parse keys into a Python list
keys_str = os.environ.get("OLLAMA_API_KEYS", "")
API_KEYS = [k.strip() for k in keys_str.split(",") if k.strip()]
CURRENT_KEY_INDEX = 0

def analyze_setup_with_ollama(setup_payload: dict, max_retries=3) -> str:
    global CURRENT_KEY_INDEX
    
    if not API_KEYS:
        return "AI Analysis skipped: No OLLAMA_API_KEYS found in .env file."
        
    prompt_text = generate_risk_assessment_prompt(setup_payload)
    messages = [{"role": "user", "content": prompt_text}]
    model = os.environ.get("OLLAMA_MODEL", "qwen3-coder:480b-cloud")
    host_url = "https://ollama.com"
    
    # Attempt to send the payload, rotating keys if an error occurs
    for attempt in range(max_retries):
        current_key = API_KEYS[CURRENT_KEY_INDEX]
        try:
            client = Client(host=host_url, headers={'Authorization': f'Bearer {current_key}'})
            print(f"    [SENDING] Analyzing live tape with Key #{CURRENT_KEY_INDEX + 1}...")
            
            response = client.chat(
                model=model,
                messages=messages,
                options={"temperature": 0.0} # Low temperature for strict quantitative logic
            )
            return response['message']['content']
            
        except Exception as e:
            print(f"    [WARNING] Key #{CURRENT_KEY_INDEX + 1} failed or rate-limited: {e}")
            # Switch to the next key in the list
            CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
            print(f"    [INFO] Rotating to Key #{CURRENT_KEY_INDEX + 1}...")
            time.sleep(2) # Give the connection a brief moment to reset
            
    return "AI Analysis failed. All keys exhausted or network down."