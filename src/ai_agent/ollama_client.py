import os
import requests
import json
from dotenv import load_dotenv
from src.ai_agent.prompts import get_system_prompt, build_user_prompt

load_dotenv()

def analyze_setup_with_ollama(setup_payload: dict) -> str:
    """
    Sends the setup data to the cloud Ollama instance and returns the AI's risk assessment.
    """
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    
    endpoint = f"{base_url}/api/chat"
    
    # Construct the message payload expected by Ollama
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": build_user_prompt(setup_payload)}
    ]
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False # We want the full response at once, not streamed token-by-token
    }
    
    print(f"🧠 Sending setup to AI Agent ({model} at {base_url})...")
    
    try:
        response = requests.post(endpoint, json=payload, timeout=30)
        response.raise_for_status() # Raise an exception for bad status codes
        
        response_data = response.json()
        ai_message = response_data.get("message", {}).get("content", "")
        
        return ai_message
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        return "AI Analysis unavailable due to connection error."