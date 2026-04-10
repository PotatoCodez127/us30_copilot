def generate_risk_assessment_prompt(setup_payload: dict) -> str:
    """
    Generates a draconian Chain-of-Thought (CoT) prompt.
    Pre-calculates all math to prevent the LLM from hallucinating its own risk parameters.
    """
    
    entry = setup_payload.get('context', {}).get('close_price', 0)
    sl_long = entry - 75.0
    tp_long = entry + 125.0
    sl_short = entry + 75.0
    tp_short = entry - 125.0
    
    prompt = f"""
You are an elite, cold, and calculating Institutional Quantitative Trading AI.
Your ONLY objective is to analyze the following 15-minute rolling tape of the US30 index and determine if a structural breakout is legitimate or a trap.

=========================================
🚨 SETUP DETECTED 🚨
Trigger Level: {setup_payload.get('trigger', 'Unknown')}
Entry Price: {entry}
Time of Trigger: {setup_payload.get('timestamp', 'Unknown')}
=========================================

📊 ROLLING 15-MINUTE SEMANTIC TAPE:
{setup_payload.get('recent_tape', 'N/A')}
=========================================

CRITICAL INSTRUCTION: You are strictly forbidden from writing conversational paragraphs. You must output EXACTLY the following template. Fill in the brackets. Do not add any other text.

STEP 1 TAPE_ANALYSIS: [Write 1 sentence assessing the semantic tape]
STEP 2 EXHAUSTION_CHECK: [Write 1 sentence checking if volatility is too high or price overextended]
STEP 3 TRAP_CHECK: [Write 1 sentence deciding if this is a clean breakout or fakeout]
STEP 4 EXECUTION:
DIRECTION: [Output exactly LONG, SHORT, or NONE]
SL: [If LONG output {sl_long}. If SHORT output {sl_short}. If NONE output 0]
TP: [If LONG output {tp_long}. If SHORT output {tp_short}. If NONE output 0]
"""
    return prompt