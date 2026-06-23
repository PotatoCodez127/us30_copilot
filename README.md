# 📉 US30 Copilot: Institutional RAG-Driven Sniper Engine

An institutional-grade quantitative backtesting and live execution framework engineered for the Dow Jones Industrial Average (US30 / DIA). The engine combines structural price-action state machines (Asian Range sweeps & Floor Pivots) with localized RAG pattern memory (ChromaDB) and LLM risk filters (Ollama) to exploit institutional inefficiencies during high-volatility market windows.

## 🧠 Core Algorithmic Architecture

### 1. The Multi-Timeframe State Machine
The core routing logic relies on a disciplined, structural state machine that monitors market development across precise hourly horizons:
- **The Accumulation Anchor:** Dynamically maps out structural high and low levels established during the 00:00–04:00 UTC Asian Range session.
- **The Baseline Filter:** Calculates classical Floor Pivot matrices based on the prior day's high, low, and closing parameters to establish market direction biases.
- **The Sniper Activation Window:** Activates a high-probability trade tracking scanner exclusively inside the 15:00 to 15:30 UTC New York session open window. It monitors for aggressive liquidity sweeps outside the opening range and blocks trades if execution prices conflict with central pivot locations (eliminating high-risk retail breakout traps).

### 2. Semantic Tape Generation & Vector RAG Memory
Instead of relying solely on traditional mathematical indicator overlays, this framework introduces an innovative cognitive pattern recognition pipeline:
- **Semantic Translation:** Translates raw, noisy numerical OHLC matrices into an explicitly structured, human-readable textual narrative stream tracking direction, momentum shifts, candle shapes, and volatility profiles.
- **ChromaDB Vector Matching:** During the sniper execution window, the live tape narrative is vectorized and issued as a query against a local persistent `ChromaDB` index. It retrieves the top 3 most semantically identical historical trading tapes along with their actual financial outcomes.
- **Cognitive Augmentation:** This historical performance profile is appended to the current market payload, feeding the execution engine deep contextual awareness ("Did this exact tape structure result in a valid breakout or a chopping trap in the past?").

### 3. Asynchronous AI Risk Filter
Before any market execution order is triggered, the complete multi-layered payload—combining state-machine indicators, central pivots, raw price arrays, and historical vector match feedback—is passed to an edge-deployed **Ollama LLM Agent**. The AI agent runs a structured risk-reward analysis and must return an explicit `DIRECTION: LONG` or `SHORT` token along with dynamic target boundaries to unlock execution parameters.

### 4. Cloud Telemetry & Research Dashboard
Live trade data, performance evaluations, and state changes are synced to a cloud-based **Supabase** persistence database layer. High-speed analytics are pulled from this database and displayed on an active web interface dashboard written in Flask, allowing developers to monitor equity curves, hit-rates, and live optimization logs.

## 🛠️ Tech Stack
- **Quantitative Engine:** Python, Pandas, NumPy, YFinance
- **AI & Context Processing:** Ollama, ChromaDB, LiteLLM, LlamaIndex
- **Cloud Telemetry & UI:** Supabase, Flask, Matplotlib
- **Quality Infrastructure:** Pytest, Black, Ruff, Docker

## 🧹 Code Quality & Standards
Development pipelines adhere strictly to centralized constraints managed within the root `pyproject.toml` file:
- **Black:** Enforces rigid visual compliance with standard 100-character line lengths across mathematical scripts.
- **Ruff:** Governs static compilation syntax health, strips unused package bloat, and maintains explicit First-Party Isort import sorting constraints.

To format and check your modules locally:
```bash
python -m black .
python -m ruff check .
```

## ⚙️ Deployment & Execution Guide
1. Local Environment Setup
- Clone the repository and install the production dependency sheets:
```bash
git clone [https://github.com/PotatoCodez127/us30-copilot.git](https://github.com/PotatoCodez127/us30-copilot.git)
cd us30-copilot
pip install -r requirements.txt
```
- Configure environment credentials inside a root .env file:
```bash
SUPABASE_URL=your_supabase_project_endpoint
SUPABASE_KEY=your_secure_supabase_api_key
```
- Confirm core mathematical indicator and risk model health by running the unit test suite:
```bash
python -m pytest
```

2. Operational Entrypoints
- Run Historical Research Simulations:
```bash
python main_backtest.py
```
- Launch 24/7 Live Monitoring Client:
```bash
python main_live.py
```
- Boot the Flask Analytics Web Interface:
```bash
python frontend/app.py
```

3. Containerized Isolation (Docker)
The system includes an optimized deployment blueprint to guarantee location-agnostic execution. The container image automatically forces internal system time tracking to strict UTC, ensuring session boundaries remain safe from local clock drift.

Build the lightweight deployment image:
```bash
docker build -t us30-copilot-engine .
```
- Fire up the execution daemon background process:
```bash
docker run -d --name us30-live-instance --env-file .env us30-copilot-engine
```

## 🤖 Continuous Integration (CI/CD)
Automated validation checks are handled through GitHub Actions (.github/workflows/ci.yml). Every codebase push or incoming pull request triggers an isolated cloud environment that runs package compiling, formatting alignment checks, static syntax audits, and executes the mathematical indicator unit test suite to guarantee 100% engine stability before merge authorization.