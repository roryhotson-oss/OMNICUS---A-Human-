# \ud83e\udd16 OMNICUS ULTIMATE - The AI Trading System

> **"Double the money. Period."**

## \ud83c\udfaf Project Overview

OMNICUS ULTIMATE is a **complete autonomous AI trading system** that combines cutting-edge AI decision-making with real-time market analysis. The system features a **pure AI-driven trading engine** (`ai_trader.py`) that works out of the box with **no API keys required** for paper trading, plus a full-featured **admin dashboard** for monitoring and control.

---

## \ud83d\udcc1 Project Structure

```
OMNICUS---A-Human-/
\u251c\u2500\u2500 \ud83d\udcca dashboards/          # Dashboard HTML files
\u2502   \u2514\u2500\u2500 omnicus_universal.html   # Main admin dashboard
\u2502
\u251c\u2500\u2500 \ud83e\udde0 agent/              # AI Brain & Cognitive Components
\u2502   \u251c\u2500\u2500 ai_brain.py         # Decision engine
\u2502   \u251c\u2500\u2500 memory_bank.py      # Learning & memory
\u2502   \u251c\u2500\u2500 emotions.py         # Emotional tracking
\u2502   \u251c\u2500\u2500 skills.py           # Skill registry
\u2502   \u251c\u2500\u2500 tools.py            # Trading tools
\u2502   \u2514\u2500\u2500 workflow.py         # Decision flow
\u2502
\u251c\u2500\u2500 \u2699\ufe0f core/               # Trading Core
\u2502   \u251c\u2500\u2500 trading_agent.py    # Main agent logic
\u2502   \u251c\u2500\u2500 hybrid_system.py    # Hybrid trading engine
\u2502   \u251c\u2500\u2500 price_engine.py     # Price analysis
\u2502   \u2514\u2500\u2500 database_manager.py # Data persistence
\u2502
\u251c\u2500\u2500 \ud83d\udd0c connectors/         # Exchange Connectors
\u2502   \u251c\u2500\u2500 binance_connector.py  # Binance connector
\u2502   \u2514\u2500\u2500 unified.py          # Unified API
\u2502
\u251c\u2500\u2500 \u2764\ufe0f soul/               # Personality & Voice
\u2502   \u251c\u2500\u2500 personality.py      # OMNICUS personality
\u2502   \u251c\u2500\u2500 emotions.py         # Emotional intelligence
\u2502   \u2514\u2500\u2500 voice.py            # Voice engine
\u2502
\u251c\u2500\u2500 \ud83c\udf10 api/                # Web API
\u2502   \u2514\u2500\u2500 server.py           # FastAPI server
\u2502
\u251c\u2500\u2500 \u2699\ufe0f config/             # Configuration
\u2502   \u251c\u2500\u2500 settings.py         # Settings loader
\u2502   \u2514\u2500\u2500 settings.toml       # Config file
\u2502
\u251c\u2500\u2500 \ud83e\uddea tests/              # Test Suite
\u2502   \u2514\u2500\u2500 test_omnicus.py     # Unit tests
\u2502
\u251c\u2500\u2500 ai_trader.py          # NEW: Pure AI trading engine
\u251c\u2500\u2500 dashboard_server.py   # Dashboard server
\u251c\u2500\u2500 trading_server.py     # Unified trading server
\u251c\u2500\u2500 main.py                # Entry point
\u251c\u2500\u2500 requirements.txt       # Dependencies
\u251c\u2500\u2500 setup.py               # Setup script
\u2514\u2500\u2500 .env.example           # Environment template
```

---

## \ud83d\ude80 Quick Start

### Option 1: AI Trader (No Setup, Instant Use)
The fastest way to get started - **no API keys, no configuration, just run it:**

```bash
# Install the only required dependency
pip install aiohttp

# Run the AI trader with $5000 starting capital
python ai_trader.py --capital 5000

# Or with custom settings
python ai_trader.py --capital 10000 --symbols BTC ETH SOL --risk 0.02
```

**What this does:**
- Launches a **MockExchange** that generates realistic market data
- The **AITradingEngine** analyzes signals using RSI, MACD, Bollinger Bands, Sentiment, and Momentum
- Trades are executed automatically based on AI confidence scores
- All trading is **paper trading** (simulated) - 100% safe

### Option 2: Full System with Dashboard
For the complete experience with admin dashboard and real exchange connectivity:

```bash
# 1. Clone the repository
git clone https://github.com/roryhotson-oss/OMNICUS---A-Human-.git
cd OMNICUS---A-Human-

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (optional for paper trading)
cp .env.example .env
# Edit .env with your API keys for live trading

# 5. Run tests to verify installation
python -m pytest tests/test_omnicus.py -v

# 6. Start the dashboard
python dashboard_server.py

# 7. Open your browser to:
# http://localhost:9999
```

---

## \ud83c\udfae Usage Commands

### AI Trader (Recommended for Beginners)
```bash
# Basic usage - starts with $1000 capital
python ai_trader.py

# Custom capital amount
python ai_trader.py --capital 5000

# Trade specific symbols only
python ai_trader.py --symbols BTC ETH SOL

# Adjust risk per trade (default: 0.02 = 2%)
python ai_trader.py --risk 0.01

# Enable verbose logging
python ai_trader.py --verbose

# Run for specific duration (minutes)
python ai_trader.py --duration 60
```

### Dashboard Server
```bash
# Start dashboard only (port 9999)
python dashboard_server.py

# Start trading server (includes dashboard)
python trading_server.py
```

### Main Trading System
```bash
# Run in paper trading mode (safe)
python main.py --paper

# Run in full trading mode
python main.py --mode full

# Run with custom configuration
python main.py --config config/settings.toml
```

---

## \ud83d\udd17 API Endpoints

The dashboard server provides these REST API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard HTML |
| GET | `/api/status` | Get trading status, capital, profit |
| GET | `/api/signals` | Get current trading signals |
| GET | `/api/trades` | Get trade history (last 50) |
| GET | `/api/market/scan` | Scan market for opportunities |
| POST | `/api/start` | Start trading (JSON: `{mode, capital}`) |
| POST | `/api/stop` | Stop trading |
| POST | `/api/connect-wallet` | Connect wallet |
| POST | `/api/chat` | Chat with OMNICUS |
| WS | `/ws/updates` | WebSocket for real-time updates |

### Example API Usage:
```bash
# Get current status
curl http://localhost:9999/api/status

# Start trading with $5000
curl -X POST http://localhost:9999/api/start \
  -H "Content-Type: application/json" \
  -d '{"mode": "paper", "capital": 5000}'

# Stop trading
curl -X POST http://localhost:9999/api/stop
```

---

## \ud83d\udcca Features

### Core Trading Features
| Feature | Description |
|---------|-------------|
| **\ud83e\udde0 AI Trading Engine** | `ai_trader.py` - Pure AI-driven decisions with multi-factor analysis |
| **\ud83d\udcc8 Multi-Factor Analysis** | RSI, MACD, Bollinger Bands, Sentiment, Momentum |
| **\ud83d\udca1 Learning AI** | Adapts confidence based on win/loss history |
| **\ud83d\udd10 Paper Trading** | Safe simulation with MockExchange |
| **\u26a1\ufe0f Live Trading** | Connect to Binance, Kraken, MEXC (with API keys) |
| **\ud83d\udcc8 Technical Indicators** | 15+ indicators for signal generation |

### Dashboard & Admin Features
| Feature | Description |
|---------|-------------|
| **\ud83d\udda5 Real-time Dashboard** | Beautiful HTML dashboard at `http://localhost:9999` |
| **\ud83d\udcc0 WebSocket Updates** | Real-time streaming of trades and signals |
| **\ud83d\udcc3 Trading Controls** | Start/Stop trading via API or dashboard |
| **\ud83d\udcb0 Trade History** | View last 50 trades with P&L |
| **\ud83d\udcca Market Scanner** | Find opportunities across markets |
| **\ud83d\udcac Chat Interface** | Communicate with OMNICUS via API |

### AI & Personality Features
| Feature | Description |
|---------|-------------|
| **\u2764\ufe0f Soul System** | OMNICUS has personality and emotions |
| **\ud83d\udde3\ufe0f Voice Synthesis** | Text-to-speech alerts (optional) |
| **\ud83d\udcac Natural Language** | Understands trading commands |
| **\ud83e\udde0 Memory Bank** | Learns from every trade |

### Exchange Support
| Exchange | Status | Type |
|----------|--------|------|
| MockExchange | \u2705 Built-in | Paper trading |
| Binance | \u2705 Supported | Spot & Futures |
| Kraken | \u2705 Supported | Spot |
| MEXC | \u2705 Supported | Spot |
| Alpaca | \u2705 Supported | US Stocks |

---

## \u2699\ufe0f Configuration

### Environment Variables (.env)
```env
# Required for live trading (optional for paper trading)
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key

# Alpaca (US Stocks)
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret

# Ollama (Local AI)
OLLAMA_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading Settings
TRADING_MODE=paper  # paper, live, or learning
INITIAL_CAPITAL=1000
RISK_PER_TRADE=0.02
```

### Config File (config/settings.toml)
```toml
[trading]
mode = "paper"
capital = 1000.0
risk_per_trade = 0.02
symbols = ["BTC", "ETH", "SOL", "ADA", "DOT"]

[ai]
enabled = true
model = "llama3"
confidence_threshold = 0.6

[exchanges]
binance = true
kraken = false
mexc = false
alpaca = false
```

---

## \ud83d\udce6 Dependencies

### Required Dependencies
```bash
pip install aiohttp python-dotenv
```

### Full Installation (All Features)
```bash
pip install -r requirements.txt
```

### Optional Dependencies
| Package | Purpose | Required |
|---------|---------|----------|
| aiohttp | HTTP requests | \u2705 Yes |
| python-dotenv | Environment variables | \u2705 Yes |
| fastapi | Dashboard API | \u2573 No (dashboard only) |
| uvicorn | ASGI server | \u2573 No (dashboard only) |
| python-binance | Binance API | \u2573 No (live trading) |
| ccxt | Multi-exchange | \u2573 No (live trading) |
| pyttsx3 | Text-to-speech | \u2573 No (voice) |
| SpeechRecognition | Voice recognition | \u2573 No (voice) |
| pyaudio | Audio I/O | \u2573 No (voice) |

---

## \ud83c\udfaf Targets

- **\u2705 Achieved**: Working AI trader with paper trading
- **\ud83d\udca1 Learning**: AI improves with each trade
- **\ud83c\udf00 Goal**: 10%+ daily profit (paper trading)
- **\ud83d\udd25 Ultimate Goal**: Fully autonomous profitable trading

---

## \ud83d\udcdd License

MIT License + Gift Economy Addendum

---

## \u2728 Important Notes

1. **Paper Trading First**: Always test with paper trading before using real money
2. **No Hardcoded Secrets**: All API keys are loaded from environment variables
3. **Graceful Degradation**: Missing optional dependencies won't break core functionality
4. **Rate Limiting**: All exchange connectors have built-in rate limiting
5. **Error Handling**: Comprehensive error handling throughout the system

---

## \ud83d\udc80 Troubleshooting

### Common Issues

**"ModuleNotFoundError: aiohttp"**
```bash
pip install aiohttp
```

**Dashboard not loading**
```bash
# Make sure you're running the dashboard server
python dashboard_server.py
# Then open http://localhost:9999
```

**API keys not working**
```bash
# Copy the example and edit
cp .env.example .env
# Edit .env with your actual API keys
```

**Trading not starting**
```bash
# Check the mode
python main.py --paper  # For paper trading
python main.py --mode live  # For live trading (requires API keys)
```

---

## \ud83c\udd95 What's New

### Latest Additions
- **\ud83e\udd16 ai_trader.py**: Pure AI trading engine with MockExchange
  - No external dependencies beyond aiohttp
  - Works instantly with no configuration
  - Multi-factor analysis (RSI, MACD, Bollinger, Sentiment, Momentum)
  - Learning AI that adapts confidence based on performance
  - Paper trading only - 100% safe

- **\ud83d\udda5 Enhanced Dashboard**: Full admin interface at `http://localhost:9999`
  - Real-time WebSocket updates
  - Trading controls (start/stop)
  - Trade history and P&L tracking
  - Chat interface with OMNICUS

- **\u2705 Fixed Issues**:
  - Import path errors resolved
  - Duplicate files removed
  - Rate limiting added to all exchange connectors
  - Configuration validation added
  - Enhanced error handling throughout

---

**\ud83d\ude80 OMNICUS ULTIMATE - Ready for Trading!**

For questions, issues, or contributions, please open a GitHub issue.
