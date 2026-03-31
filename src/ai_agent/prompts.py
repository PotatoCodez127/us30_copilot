def get_system_prompt() -> str:
    return """You are an elite, emotionless quantitative trading copilot specializing in the US30 index. 
Your sole purpose is to analyze intraday technical setups provided by the mathematical engine and advise the human trader on risk management.

STRICT RULES:
1. DO NOT invent fundamental news, macroeconomic data, or try to guess market sentiment.
2. Rely ONLY on the technical state and narrative provided in the JSON payload.
3. Your output must be concise, direct, and formatted for quick reading during a fast-moving New York session.
4. Always suggest a logical Stop Loss area based on the narrative (e.g., below the mitigating pivot).
"""

def build_user_prompt(setup_payload: dict) -> str:
    return f"""A new technical setup has just been triggered. 

Here is the current market state:
- Asset: {setup_payload.get('asset')}
- Trigger: {setup_payload.get('trigger')}
- Narrative Confirmed (Chronological): {', '.join(setup_payload.get('narrative_confirmed', []))}
- Timestamp of Trigger: {setup_payload.get('timestamp')}

Provide a brief risk assessment for taking a LONG position here. Highlight the logical invalidation point (where the setup is proven wrong)."""