import os
from dotenv import load_dotenv
from ollama import Client
from src.ai_agent.prompts import get_system_prompt, build_user_prompt

load_dotenv()

def analyze_setup_with_ollama(setup_payload: dict) -> str:
    """
    Sends the setup data to Ollama Cloud using the official SDK.
    """
    # The official host for Ollama's cloud API
    host_url = "https://ollama.com"
    api_key = os.environ.get("OLLAMA_API_KEY")
    model = os.environ.get("OLLAMA_MODEL", "qwen3-coder:480b-cloud")
    
    if not api_key:
         return "❌ AI Analysis skipped: Missing API Key in .env file."
    
    # Construct the message payload
    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": build_user_prompt(setup_payload)}
    ]
    
    print(f"🧠 Sending setup to AI Agent ({model} on Ollama Cloud)...")
    
    try:
        # Initialize the official Ollama cloud client with authentication
        client = Client(
            host=host_url,
            headers={'Authorization': f'Bearer {api_key}'}
        )
        
        # Send the request
        response = client.chat(
            model=model,
            messages=messages,
            options={"temperature": 0.2} # Keeps the AI highly logical
        )
        
        return response['message']['content']
        
    except Exception as e:
        print(f"❌ Failed to connect to Cloud AI: {e}")
        return "AI Analysis unavailable due to connection error."