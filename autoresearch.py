import os
import time
import sys
import subprocess
import re
import shutil
import requests
from dotenv import load_dotenv
import networkx as nx

RESEARCH_MEMORY = []

def build_research_graph():
    """Builds a NetworkX graph of past runs to find profitable parameter ranges."""
    if len(RESEARCH_MEMORY) < 3:
        return "[GraphRAG Context] Graph is still gathering nodes. Make radical guesses to map the space."
        
    G = nx.Graph()
    G.add_node("WINNING_SCORE", type="outcome")
    G.add_node("LOSING_SCORE", type="outcome")
    
    for run in RESEARCH_MEMORY:
        score = run.get('score', 0)
        outcome = "WINNING_SCORE" if score > 0 else "LOSING_SCORE"
        
        # Create categorical Nodes for the parameters by "bucketing" them
        sl = run.get('sl', 0)
        tp = run.get('tp', 0)
        buf = run.get('buffer', 0)
        
        sl_node = f"SL_Range_{int(sl//50)*50}_to_{int(sl//50)*50+50}"
        tp_node = f"TP_Range_{int(tp//50)*50}_to_{int(tp//50)*50+50}"
        buf_node = f"Buffer_Range_{int(buf//5)*5}_to_{int(buf//5)*5+5}"
        
        # Draw edges between the parameter buckets and the final outcome
        for node in [sl_node, tp_node, buf_node]:
            G.add_node(node, type="parameter")
            if G.has_edge(node, outcome):
                G[node][outcome]['weight'] += 1
            else:
                G.add_edge(node, outcome, weight=1)
                
    # Traverse graph to find what works and what fails
    insights = []
    for node, attr in G.nodes(data=True):
        if attr.get('type') == 'parameter':
            wins = G[node].get("WINNING_SCORE", {}).get("weight", 0)
            losses = G[node].get("LOSING_SCORE", {}).get("weight", 0)
            
            # If a node strongly leans one way, extract that insight
            if wins > losses:
                insights.append(f"🟢 Path Detected: '{node}' heavily connects to WINNING configurations ({wins} Wins vs {losses} Losses).")
            elif losses > wins: 
                insights.append(f"🔴 Danger Node: '{node}' heavily connects to LOSING configurations ({losses} Losses vs {wins} Wins). AVOID.")

    if not insights:
        return "[GraphRAG Context] Graph built, but no dominant paths yet. Keep exploring."
        
    return "[GraphRAG Context] Based on the topological graph of your past runs:\n" + "\n".join(insights)

# Load variables from the .env file
load_dotenv()

# Paths
CONFIG_FILE = "src/strategy/us30_ai_config.py"
BEST_CONFIG_FILE = "src/strategy/us30_ai_config_best.py"
RESULTS_FILE = "autoresearch_log.tsv"
EVAL_CMD = [sys.executable, "-X", "utf8", "-u", "auto_eval.py"]

# ==========================================
# 🔑 CLOUD API KEY & CONFIG MANAGEMENT
# ==========================================
# Fetch raw strings, strip literal quotes, and split keys
raw_keys = os.environ.get("OLLAMA_API_KEYS", "").replace('"', '').replace("'", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "deepseek-v4-flash").replace('"', '').replace("'", "")

print(f"🔧 Loaded {len(API_KEYS)} API keys from .env")
print(f"🤖 Target Model: {OLLAMA_MODEL}")

# Track which key is currently active
CURRENT_KEY_IDX = 0

# Ensure we have a backup of the baseline
if not os.path.exists(BEST_CONFIG_FILE):
    shutil.copy(CONFIG_FILE, BEST_CONFIG_FILE)

def get_best_score():
    if not os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            f.write("trial\tscore\tstatus\n")
        return 0.0
    
    best = 0.0
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]
        for line in lines:
            parts = line.strip().split("\t")
            if len(parts) >= 3 and parts[2] == "keep":
                score = float(parts[1])
                if score > best: best = score
    return best

def generate_hypothesis(best_score):
    global CURRENT_KEY_IDX
    
    if not API_KEYS:
        print("⚠️ ERROR: No API keys were loaded. Check that your file is named exactly '.env' and not '.env.txt'.")
        return "", ""
    
    # Grab the champion config
    champion_config = "No previous configuration found."
    if os.path.exists(BEST_CONFIG_FILE):
        with open(BEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            champion_config = "".join([line for line in lines if "=" in line]).strip()

    # --- NEW: Get Graph Insights ---
    graph_context = build_research_graph()
    # -------------------------------

    prompt = f"""You are an elite quantitative researcher optimizing a US30 trading algorithm.
                Our current best custom evaluation score is {best_score}. 

                Here are the parameters of the CURRENT CHAMPION that achieved this score:
                {champion_config}

                =========================================
                🕸️ KNOWLEDGE GRAPH TRAVERSAL
                =========================================
                {graph_context}

                You MUST generate a new hypothesis for our strategy configuration to beat this score. 
                DO NOT just repeat the same reasoning. Use the GraphRAG context above to navigate away from Danger Nodes and towards Winning Paths.

                CRITICAL RULES:
                1. You MUST write all code and reasoning strictly in English. Do NOT output any Chinese characters.
                2. Only output raw floating point numbers or integers for the variables. Do not include units.

                You MUST format your response EXACTLY like this:
                ..."""

    print(f"🤔 AI ({OLLAMA_MODEL}) is thinking of a new hypothesis...")
    
    max_attempts = len(API_KEYS)
    attempts = 0
    
    while attempts < max_attempts:
        active_key = API_KEYS[CURRENT_KEY_IDX]
        
        try:
            # We use the generate endpoint with the model from your .env
            response = requests.post(
                'https://ollama.com/api/generate', 
                headers={"Authorization": f"Bearer {active_key}"},
                json={
                    "model": OLLAMA_MODEL, 
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.8
                },
                timeout=180 # Extended timeout for larger cloud models
            )
            
            # --- NEW: VERBOSE ERROR LOGGING ---
            if response.status_code != 200:
                print(f"\n❌ Key {CURRENT_KEY_IDX + 1} Rejected (Status: {response.status_code})")
                
                # Attempt to parse the exact error message from the server
                try:
                    error_details = response.json()
                    print(f"🔍 Server JSON Reply: {error_details}")
                except Exception:
                    # If it's not JSON (like a Cloudflare HTML block), print the raw text
                    print(f"🔍 Server RAW Reply: {response.text[:800]}...")
                
                if response.status_code in [401, 403, 429]:
                    print("🔄 Rolling over to next key...\n")
                    CURRENT_KEY_IDX = (CURRENT_KEY_IDX + 1) % len(API_KEYS)
                    attempts += 1
                    time.sleep(2)
                    continue
                else:
                    # For 500 Server Errors, crash out
                    response.raise_for_status() 
            # ----------------------------------
            
            content = response.json().get('response', '')
            
            # More forgiving regex to catch the thinking block
            think_match = re.search(r'THINKING:\s*(.*?)(?=(HYPOTHESIS:|```|\n\nENABLE_OR_CHECKS|\*\*NEW PARAMETERS))', content, re.DOTALL | re.IGNORECASE)
            thinking = think_match.group(1).strip() if think_match else "No explicit THINKING block found. Using parameter mapping."
            
            # Return the full raw content to the extractor
            return thinking, content

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network/API Error with Key {CURRENT_KEY_IDX + 1}: {e}")
            print("🔄 Rolling over to next key...\n")
            CURRENT_KEY_IDX = (CURRENT_KEY_IDX + 1) % len(API_KEYS)
            attempts += 1
            time.sleep(2)
            
    print("🚨 FATAL: All API keys have been exhausted or failed.")
    return "", ""

def run_loop():
    best_score = get_best_score()
    print(f"\n" + "="*50)
    print(f"🚀 STARTING AUTORESEARCH LOOP | Target to beat: {best_score:.4f}")
    print("="*50)
    
    thinking, raw_output = generate_hypothesis(best_score)
    
    if not raw_output or "SL_RISK_POINTS" not in raw_output:
        print("⚠️ Malformed output from LLM or API exhausted. Skipping iteration.")
        time.sleep(3)
        return

    print(f"\n🧠 AI Reasoning:\n   > {thinking}")

    # ==========================================
    # 🛡️ THE BULLETPROOF EXTRACTOR
    # ==========================================
    def extract_val(pattern, text, default):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else default

    or_checks = extract_val(r'ENABLE_OR_CHECKS\s*=\s*(True|False)', raw_output, None)
    pivot_checks = extract_val(r'ENABLE_PIVOT_CHECKS\s*=\s*(True|False)', raw_output, None)
    buffer_pts = extract_val(r'BREAKOUT_BUFFER_POINTS\s*=\s*([0-9.]+)', raw_output, None)
    sl_pts = extract_val(r'SL_RISK_POINTS\s*=\s*([0-9.]+)', raw_output, None)
    tp_pts = extract_val(r'TP_REWARD_POINTS\s*=\s*([0-9.]+)', raw_output, None)
    max_hold = extract_val(r'MAX_HOLDING_MINUTES\s*=\s*([0-9]+)', raw_output, None)

    if not all([or_checks, pivot_checks, buffer_pts, sl_pts, tp_pts, max_hold]):
        print(f"⚠️ LLM missed core variables. Skipping iteration.")
        time.sleep(2)
        return

    # Explicitly rebuild the Python string. This ignores ALL hallucinated text, arrows, and fake variables.
    new_code = "# ==========================================\n"
    new_code += "# 🤖 AUTORESEARCHER SANDBOX (BULLETPROOF)\n"
    new_code += "# ==========================================\n\n"
    new_code += f"ENABLE_OR_CHECKS = {or_checks}\n"
    new_code += f"ENABLE_PIVOT_CHECKS = {pivot_checks}\n"
    new_code += f"BREAKOUT_BUFFER_POINTS = {buffer_pts}\n"
    new_code += f"SL_RISK_POINTS = {sl_pts}\n"
    new_code += f"TP_REWARD_POINTS = {tp_pts}\n"
    new_code += f"MAX_HOLDING_MINUTES = {max_hold}\n"

    print(f"\n💡 Testing Configuration:\n{new_code.strip()}")

    # --- NEW: PRE-FLIGHT SYNTAX CHECK ---
    try:
        # This checks if the code is valid Python without actually running it
        compile(new_code, '<string>', 'exec')
    except SyntaxError as e:
        print(f"⚠️ AI generated invalid Python syntax ({e}). Discarding hypothesis.")
        time.sleep(2)
        return
    # ------------------------------------

    # If syntax is valid, inject the new code into the sandbox
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(new_code)

    # Run Evaluator
    print(f"\n📈 Running Walk-Forward Judge...")
    print("-" * 40)
    print("⚖️ REAL-TIME JUDGE LOGS:")
    
    # Popen allows us to read the output line-by-line as it happens
    process = subprocess.Popen(EVAL_CMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
    
    full_output = ""
    for line in iter(process.stdout.readline, ''):
        print(line, end="", flush=True) # Stream directly to the terminal
        full_output += line

    process.stdout.close()
    process.wait()
    print("-" * 40 + "\n")

    match = re.search(r"FINAL_RESULT:([-\d.]+)", full_output)
    score = float(match.group(1)) if match else 0.0

    try:
        # Directly use the cleanly extracted variables from above
        RESEARCH_MEMORY.append({
            'sl': float(sl_pts),
            'tp': float(tp_pts),
            'buffer': float(buffer_pts),
            'score': score
        })

        import json
        with open("results/research_memory.json", "w", encoding="utf-8") as f:
            json.dump(RESEARCH_MEMORY, f, indent=4)

    except Exception as e:
        print(f"[DEBUG] Could not map run to Graph: {e}")
    
    print(f"📊 OOS Score Achieved: {score:.4f}")

    if score > best_score:
        print(f"🏆 NEW HIGH SCORE! ({score:.4f} > {best_score:.4f}). Saving configuration.")
        shutil.copy(CONFIG_FILE, BEST_CONFIG_FILE)
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(f"auto\t{score:.4f}\tkeep\n")
    else:
        print(f"❌ FAILED to beat high score. Reverting configuration to best known.")
        shutil.copy(BEST_CONFIG_FILE, CONFIG_FILE)
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(f"auto\t{score:.4f}\tdiscard\n")

    time.sleep(3)

if __name__ == "__main__":
    while True:
        try:
            run_loop()
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user. Exiting gracefully.")
            break
        except Exception as e:
            print(f"\n⚠️ Unexpected Error: {e}")
            time.sleep(10)