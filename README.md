# OMNICUS ULTIMATE - The Profit Hunter

> "Double the money. Period."

## Project Overview

OMNICUS ULTIMATE is a complete autonomous AI trading system combining the best features from all OMNICUS versions.

---

## Project Structure

- dashboards/
  - omnicus_universal.html
- agent/
  - ai_brain.py
  - memory_bank.py
  - emotions.py
  - skills.py
  - tools.py
  - workflow.py
- core/
  - trading_agent.py
  - hybrid_system.py
  - price_engine.py
  - database_manager.py
- connectors/
  - binance_connector.py
  - unified.py
- soul/
  - personality.py
  - emotions.py
  - voice.py
- api/
  - server.py
- config/
  - settings.py
  - settings.toml
- tests/
  - test_omnicus.py
- ai_trader.py
- dashboard_server.py
- trading_server.py
- main.py
- requirements.txt
- .env.example

---

## Quick Start

1. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run Tests
```bash
python -m pytest tests/test_omnicus.py -v
```

4. Start Dashboard Server
```bash
python dashboard_server.py
```

5. Open Dashboard
```
http://localhost:9999
```

---

## Usage

Run Dashboard Only
```bash
python dashboard_server.py
```

Run Trading Mode
```bash
python main.py --mode full
```

Run Paper Trading
```bash
python main.py --paper
```

Run AI Trader (No Setup Required)
```bash
pip install aiohttp
python ai_trader.py --capital 5000
```

---

## API Endpoints

- `/` - Main dashboard
- `/api/status` - Trading status
- `/api/signals` - Trading signals
- `/api/market/scan` - Market scanner
- `/api/trading/start` - Start trading
- `/api/trading/stop` - Stop trading

---

## Features

- AI Brain - Learns from every trade
- Soul - Personality & emotions
- Voice - Speech alerts
- Telegram - Remote control
- Multi-Exchange - Binance, Kraken, MEXC
- Technical Analysis - RSI, MACD, Volume
- Secure - No hardcoded secrets

---

## License

MIT License + Gift Economy Addendum

---

## Targets

- Minimum: 10% daily profit
- Target: 50% daily profit
- Goal: 100% (Double!) in 24 hours

---

## New Features

- Stock Trading: Integrated Alpaca Markets for US Stocks (Paper & Live)
- Local AI: Supports Ollama (Llama 3) for private, on-device trade reasoning
- Telegram Voice: OMNICUS can now call you with trade updates
- AI Trader: New ai_trader.py - Pure AI trading engine with mock exchange for instant paper trading

---

## Installation

```bash
pip install -r requirements.txt
```

Includes: aiohttp, alpaca-py, ollama, python-telegram-bot

---

## Configuration

Add to .env:
```
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
OLLAMA_MODEL=llama3
BINANCE_API_KEY=...
BINANCE_SECRET_KEY=...
```
