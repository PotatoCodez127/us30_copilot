import os
import requests
from dotenv import load_dotenv
from src.ai_agent.prompts import get_system_prompt, build_user_prompt

load_dotenv()

def analyze_setup_with_ollama(setup_payload: dict) -> str:
    """
    Sends the setup data to the cloud instance and returns the AI's risk assessment.
    Authenticates using a Bearer token (API Key).
    """
    base_url = os.environ.get("OLLAMA_BASE_URL")
    api_key = os.environ.get("OLLAMA_API_KEY")
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    
    if not base_url or not api_key:
         return "❌ AI Analysis skipped: Missing Base URL or API Key in .env file."
    
    # Construct the message payload
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": build_user_prompt(setup_payload)}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2, # Keep this low so the AI is highly logical, not "creative"
        "stream": False 
    }
    
    # Attach your API Key to the request headers securely
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"🧠 Sending setup to AI Agent ({model} in the cloud)...")
    
    try:
        response = requests.post(base_url, json=payload, headers=headers, timeout=15)
        response.raise_for_status() 
        
        response_data = response.json()
        
        # Most cloud APIs return the message tucked inside a 'choices' array
        if "choices" in response_data:
             ai_message = response_data["choices"][0]["message"]["content"]
        else:
             # Fallback for standard Ollama formatting
             ai_message = response_data.get("message", {}).get("content", "")
             
        return ai_message
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Cloud AI: {e}")
        return "AI Analysis unavailable due to connection error."