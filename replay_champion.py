# replay_champion.py
import os
import shutil
import subprocess


def run_champion_backtest():
    print("🏆 Preparing to run backtest with the Champion Configuration...")

    best_config = "src/strategy/us30_ai_config_best.py"
    active_config = "src/strategy/us30_ai_config.py"

    if not os.path.exists(best_config):
        print("❌ No champion config found. Let the autoresearcher run first!")
        return

    # Overwrite the active config with the champion
    shutil.copy(best_config, active_config)
    print("✅ Champion configuration loaded into active slot.")

    print("📈 Launching visual backtest...\n" + "-" * 40)

    # Trigger your main visual backtester
    # (Using main_backtest.py since your project memory says it generates visual charts)
    try:
        subprocess.run(["python", "-u", "main_backtest.py"])
    except KeyboardInterrupt:
        print("\n🛑 Backtest stopped.")


if __name__ == "__main__":
    run_champion_backtest()
