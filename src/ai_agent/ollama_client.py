import os
import time
from dotenv import load_dotenv
import litellm
from src.ai_agent.prompts import generate_risk_assessment_prompt

# Suppress verbose litellm output to keep your terminal clean
litellm.suppress_debug_info = True

load_dotenv()

# Parse keys into a Python list
keys_str = os.environ.get("OLLAMA_API_KEYS", "").replace('"', '').replace("'", "")
API_KEYS = [k.strip() for k in keys_str.split(",") if k.strip()]
CURRENT_KEY_INDEX = 0

def analyze_setup_with_ollama(setup_payload: dict, max_retries=3) -> str:
    global CURRENT_KEY_INDEX
    
    if not API_KEYS:
        return "AI Analysis skipped: No OLLAMA_API_KEYS found in .env file."
        
    prompt_text = generate_risk_assessment_prompt(setup_payload)
    messages = [{"role": "user", "content": prompt_text}]
    
    # Grab settings from .env
    raw_model = os.environ.get("OLLAMA_MODEL", "deepseek-v3.2:cloud").replace('"', '').replace("'", "")
    base_url = os.environ.get("OLLAMA_BASE_URL", "https://ollama.com").replace('"', '').replace("'", "")
    
    # LiteLLM handles the /api/chat path automatically, so we just want the base domain
    if base_url.endswith("/api/chat"):
        base_url = base_url.replace("/api/chat", "")
        
    # Add the litellm provider prefix just like in your crypto app's yaml config
    if not raw_model.startswith("ollama_chat/") and "ollama" in base_url.lower():
        model = f"ollama_chat/{raw_model}"
    else:
        model = raw_model
    
    # Attempt to send the payload, rotating keys if an error occurs
    for attempt in range(max_retries):
        current_key = API_KEYS[CURRENT_KEY_INDEX]
        try:
            print(f"    [SENDING] Analyzing live tape with Key #{CURRENT_KEY_INDEX + 1}...")
            
            # Using LiteLLM directly matching your Crypto App architecture
            response = litellm.completion(
                model=model,
                messages=messages,
                api_base=base_url,
                api_key=current_key,
                temperature=0.0,
                timeout=180
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"    [WARNING] Key #{CURRENT_KEY_INDEX + 1} failed: {e}")
            # Switch to the next key in the list
            CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS)
            print(f"    [INFO] Rotating to Key #{CURRENT_KEY_INDEX + 1}...")
            time.sleep(2) # Give the connection a brief moment to reset
            
    return "AI Analysis failed. All keys exhausted or network down."