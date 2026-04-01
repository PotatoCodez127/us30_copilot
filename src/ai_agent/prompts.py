def generate_risk_assessment_prompt(setup_payload: dict) -> str:
    return f"""
    You are an elite quantitative day trader sitting at your terminal during the live New York session. 
    You are trading the US30 (Dow Jones) Cash Market. 
    
    You only look at the data provided right now. Do not assume this is historical data. Treat this as happening LIVE at this exact second.
    
    --- KEY LEVELS ESTABLISHED TODAY ---
    Opening Range High: {setup_payload.get('context', {}).get('or_high', 'N/A')}
    Opening Range Low: {setup_payload.get('context', {}).get('or_low', 'N/A')}
    
    --- LIVE TAPE (LAST 15 MINUTES) ---
    This is the minute-by-minute price action leading up to right now:
    {setup_payload.get('recent_tape', 'N/A')}

    --- CURRENT TRIGGER ---
    Event: {setup_payload.get('trigger', 'Unknown')}
    Current Price: {setup_payload.get('context', {}).get('close_price', 'N/A')}
    Narrative: {setup_payload.get('narrative_confirmed', [])}

    --- YOUR TASK ---
    Analyze the live tape above. Look at the highs, lows, and momentum leading into this trigger. Provide your exact trade execution plan formatted strictly in Markdown.

    1. **Tape Reading:** Briefly describe the momentum and candle structure you see in the last 15 minutes of the tape. Are we rejecting a level hard, or consolidating?
    2. **Direction:** State clearly if you are executing a LONG or SHORT right now.
    3. **Stop Loss (Exact Price):** Based on the structure in the live tape, where EXACTLY are you placing your stop loss? (e.g., "Just below the 14:12 wick low at 39,120").
    4. **Take Profit (Exact Price):** Provide a realistic, logical Take Profit target based on a minimum 2:1 Risk/Reward ratio.
    5. **Execution Confidence:** Score from 1 to 10.
    """