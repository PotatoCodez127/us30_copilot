import os
import time
import sys
import subprocess
import re
import shutil
import requests
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# Paths
CONFIG_FILE = "src/strategy/us30_ai_config.py"
BEST_CONFIG_FILE = "src/strategy/us30_ai_config_best.py"
RESULTS_FILE = "autoresearch_log.tsv"
EVAL_CMD = [sys.executable, "auto_eval.py"]

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

    prompt = f"""You are an elite quantitative researcher optimizing a US30 trading algorithm.
Our current best custom evaluation score is {best_score}. 

You MUST generate a new hypothesis for our strategy configuration to beat this score.
US30 is highly volatile. Consider widening stops or optimizing breakout buffers.

You MUST format your response EXACTLY like this:
THINKING: [Your reasoning]
HYPOTHESIS:
ENABLE_OR_CHECKS = True|False
ENABLE_PIVOT_CHECKS = True|False
BREAKOUT_BUFFER_POINTS = [float between 0.0 and 15.0]
SL_RISK_POINTS = [float between 50.0 and 300.0]
TP_REWARD_POINTS = [float between 100.0 and 500.0]
MAX_HOLDING_MINUTES = [int between 30 and 240]
"""

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
            
            think_match = re.search(r'THINKING:\s*(.*?)(?=HYPOTHESIS:)', content, re.DOTALL)
            hypo_match = re.search(r'HYPOTHESIS:\s*(.*)', content, re.DOTALL)
            
            thinking = think_match.group(1).strip() if think_match else "No reasoning provided."
            hypothesis = hypo_match.group(1).strip() if hypo_match else ""
            
            return thinking, hypothesis

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
    
    thinking, hypothesis = generate_hypothesis(best_score)
    
    if not hypothesis or "SL_RISK_POINTS" not in hypothesis:
        print("⚠️ Malformed output from LLM or API exhausted. Skipping iteration.")
        time.sleep(3)
        return

    print(f"\n🧠 AI Reasoning:\n   > {thinking}")
    print(f"\n💡 Testing Configuration:\n{hypothesis}")

    # Inject the new code into the sandbox
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("# ==========================================\n")
        f.write("# 🤖 AUTORESEARCHER SANDBOX\n")
        f.write("# ==========================================\n\n")
        f.write(hypothesis.replace("```python", "").replace("```", "").strip())

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