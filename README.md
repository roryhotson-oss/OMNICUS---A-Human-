# 🤖 OMNICUS ULTIMATE - The Profit Hunter

> **"Double the money. Period."**

## 🎯 Project Overview

OMNICUS ULTIMATE is a complete autonomous AI trading system combining the best features from all OMNICUS versions.

---

## 📁 Project Structure

```
OMNICUS-Ultimate-Project/
├── 📊 dashboards/          # 5 Beautiful Dashboard HTMLs
│   ├── omnicus_ultimate.html    # Main dashboard
│   ├── omnicus_dashboard.html   # Standard view
│   ├── omnicus_full.html        # Full layout
│   ├── omnicus_hungry.html      # Hungry mode
│   └── omnicus_universal.html   # Universal dashboard
│
├── 🧠 agent/              # AI Brain & Cognitive Components
│   ├── ai_brain.py         # Decision engine
│   ├── memory_bank.py      # Learning & memory
│   ├── emotions.py         # Emotional tracking
│   ├── skills.py           # Skill registry
│   ├── tools.py            # Trading tools
│   └── workflow.py         # Decision flow
│
├── ⚙️ core/               # Trading Core
│   ├── trading_agent.py    # Main agent logic
│   ├── hybrid_system.py    # Hybrid trading engine
│   ├── binance_api.py      # Binance integration
│   ├── price_engine.py     # Price analysis
│   ├── ai_decision_engine.py  # AI decisions
│   └── database_manager.py # Data persistence
│
├── 🔌 connectors/         # Exchange Connectors
│   ├── binance.py          # Binance connector
│   ├── binance_connector.py
│   └── unified.py          # Unified API
│
├── ❤️ soul/               # Personality & Voice
│   ├── personality.py      # OMNICUS personality
│   ├── emotions.py         # Emotional intelligence
│   └── voice.py            # Voice engine
│
├── 🌐 api/                # Web API
│   └── server.py           # FastAPI server
│
├── ⚙️ config/             # Configuration
│   ├── settings.py         # Settings loader
│   └── settings.toml       # Config file
│
├── 🧪 tests/              # Test Suite
│   └── test_omnicus.py     # 7 passing tests
│
├── trading_server.py      # Unified trading server
├── main.py                # Entry point
├── requirements.txt       # Dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

---

## 🚀 Quick Start

### 1. Setup Virtual Environment
```bash
cd /home/master/Documents/OMNICUS-Ultimate-Project
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
python trading_server.py
```

### 5. Open Dashboard
```
http://localhost:9999
```

---

## 🎮 Usage

### Run Dashboard Only
```bash
python trading_server.py
```

### Run Trading Mode
```bash
python main.py --mode full
```

### Run Paper Trading
```bash
python main.py --paper
```

---

## 🔗 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main dashboard |
| `/api/status` | Trading status |
| `/api/signals` | Trading signals |
| `/api/market/scan` | Market scanner |
| `/api/trading/start` | Start trading |
| `/api/trading/stop` | Stop trading |

---

## 📊 Features

| Feature | Description |
|---------|-------------|
| **🧠 AI Brain** | Learns from every trade |
| **❤️ Soul** | Personality & emotions |
| **🗣️ Voice** | Speech alerts |
| **📱 Telegram** | Remote control |
| **📊 Multi-Exchange** | Binance, Kraken, MEXC |
| **📈 Technical Analysis** | RSI, MACD, Volume |
| **🔐 Secure** | No hardcoded secrets |

---

## 📝 License

MIT License + Gift Economy Addendum

---

## 🎯 Targets

- **Minimum**: 10% daily profit
- **Target**: 50% daily profit
- **Goal**: 100% (Double!) in 24 hours

---

**🚀 OMNICUS ULTIMATE - Ready for GitHub & Trading!**
