from src.ai_agent.ollama_client import analyze_setup_with_ollama

# A fake payload imitating our State Machine's output
dummy_setup = {
    "asset": "US30",
    "trigger": "15m Close Above Asian High",
    "narrative_confirmed": ["Low Swept", "High Tested", "Pivot Bounced at 39000"],
    "timestamp": "2023-10-11 14:59:00+00:00"
}

print("Initiating comms with Ollama...")
response = analyze_setup_with_ollama(dummy_setup)

print("\n" + "="*50)
print("🤖 AI COPILOT RESPONSE:")
print("="*50)
print(response)
print("="*50)