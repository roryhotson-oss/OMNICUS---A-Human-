# \ud83e\udd16 OMNICUS ULTIMATE - The Profit Hunter

> **"Double the money. Period."**

## \ud83c\udfaf Project Overview

OMNICUS ULTIMATE is a complete autonomous AI trading system combining the best features from all OMNICUS versions.

---

## \ud83d\udcc1 Project Structure

```
OMNICUS-Ultimate-Project/
├── dashboards/          # Dashboard HTML files
│   └── omnicus_universal.html   # Main admin dashboard
├── agent/              # AI Brain & Cognitive Components
│   ├── ai_brain.py         # Decision engine
│   ├── memory_bank.py      # Learning & memory
│   ├── emotions.py         # Emotional tracking
│   ├── skills.py           # Skill registry
│   ├── tools.py            # Trading tools
│   └── workflow.py         # Decision flow
├── core/               # Trading Core
│   ├── trading_agent.py    # Main agent logic
│   ├── hybrid_system.py    # Hybrid trading engine
│   ├── price_engine.py     # Price analysis
│   └── database_manager.py # Data persistence
├── connectors/         # Exchange Connectors
│   ├── binance_connector.py
│   └── unified.py          # Unified API
├── soul/               # Personality & Voice
│   ├── personality.py      # OMNICUS personality
│   ├── emotions.py         # Emotional intelligence
│   └── voice.py            # Voice engine
├── api/                # Web API
│   └── server.py           # FastAPI server
├── config/             # Configuration
│   ├── settings.py         # Settings loader
│   └── settings.toml       # Config file
├── tests/              # Test Suite
│   └── test_omnicus.py     # Unit tests
├── ai_trader.py          # NEW: Pure AI trading engine
├── dashboard_server.py   # Dashboard server
├── trading_server.py     # Unified trading server
├── main.py                # Entry point
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

---

## \ud83d\ude80 Quick Start

### 1. Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Tests
```bash
python -m pytest tests/test_omnicus.py -v
```

### 4. Start Dashboard Server
```bash
python dashboard_server.py
```

### 5. Open Dashboard
```
http://localhost:9999
```

---

## \ud83c\udfae Usage

### Run Dashboard Only
```bash
python dashboard_server.py
```

### Run Trading Mode
```bash
python main.py --mode full
```

### Run Paper Trading
```bash
python main.py --paper
```

### Run AI Trader (No Setup Required)
```bash
pip install aiohttp
python ai_trader.py --capital 5000
```

---

## \ud83d\udd17 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main dashboard |
| `/api/status` | Trading status |
| `/api/signals` | Trading signals |
| `/api/market/scan` | Market scanner |
| `/api/trading/start` | Start trading |
| `/api/trading/stop` | Stop trading |

---

## \ud83d\udcca Features

| Feature | Description |
|---------|-------------|
| **\ud83e\udde0 AI Brain** | Learns from every trade |
| **\u2764\ufe0f Soul** | Personality & emotions |
| **\ud83d\udde3\ufe0f Voice** | Speech alerts |
| **\ud83d\udcf1 Telegram** | Remote control |
| **\ud83d\udcca Multi-Exchange** | Binance, Kraken, MEXC |
| **\ud83d\udcc8 Technical Analysis** | RSI, MACD, Volume |
| **\ud83d\udd10 Secure** | No hardcoded secrets |

---

## \ud83d\udcdd License

MIT License + Gift Economy Addendum

---

## \ud83c\udfaf Targets

- **Minimum**: 10% daily profit
- **Target**: 50% daily profit
- **Goal**: 100% (Double!) in 24 hours

---

**\ud83d\ude80 OMNICUS ULTIMATE - Ready for GitHub & Trading!**

## \ud83c\udd95 New Features
- **\ud83d\udcc8 Stock Trading**: Integrated **Alpaca Markets** for US Stocks (Paper & Live).
- **\ud83e\udde0 Local AI**: Supports **Ollama** (Llama 3) for private, on-device trade reasoning.
- **\ud83d\udcf1 Telegram Voice**: OMNICUS can now call you with trade updates.
- **\ud83e\udd16 AI Trader**: New `ai_trader.py` - Pure AI trading engine with mock exchange for instant paper trading.

## \ud83d\udce6 Installation
```bash
pip install -r requirements.txt
# Includes: aiohttp, alpaca-py, ollama, python-telegram-bot
```

## \u2699\ufe0f Configuration
Add to `.env`:
```env
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
OLLAMA_MODEL=llama3
BINANCE_API_KEY=...
BINANCE_SECRET_KEY=...
```
