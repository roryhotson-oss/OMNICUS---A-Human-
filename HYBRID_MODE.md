# 🔀 OMNICUS HYBRID TRADING MODE

> **"Learn on paper. Hunt with real money when ready."**

## Overview

Hybrid mode is the **smart way** to run OMNICUS:

- **Paper trades by default** — Learn, test strategies, build confidence without risk
- **Real trades when confident** — When OMNICUS hits 85%+ confidence AND completes learning phase, real money kicks in
- **Automatic calibration** — Tracks if confidence matches actual performance
- **Daily limits** — Protects capital with loss limits and profit targets

---

## 🎯 How It Works

### Phase 1: Paper Learning (First 50 Trades)

```
📝 Every trade is paper (simulated)
📊 Tracks: win rate, P/L, confidence calibration
🧠 OMNICUS learns from every outcome
📈 Builds memory, skills, emotional resilience
```

**Goal:** Complete 50 paper trades to prove the system works.

### Phase 2: Hybrid Mode (After 50 Paper Trades)

```
📝 Paper trades continue (always learning)
💰 Real trades execute when:
   • Confidence ≥ 85%
   • Daily loss limit not hit
   • Minimum capital available
   • Signal quality is exceptional
```

**Goal:** Make real money only on highest-conviction setups.

---

## ⚙️ Configuration

Edit `.env` to customize:

```bash
# Trading Mode
TRADING_MODE=hybrid

# Hybrid Settings
HYBRID_CONFIDENCE_THRESHOLD=0.85        # Real trades need 85%+ confidence
HYBRID_MAX_REAL_POSITION_PERCENT=2.0    # Max 2% of capital per real trade
HYBRID_PAPER_LEARNING_TRADES=50         # Paper trades before real trading

# Daily Limits (Real Trading)
HYBRID_DAILY_LOSS_LIMIT=500.00          # Stop real trading if down $500/day
HYBRID_DAILY_PROFIT_TARGET=1000.00      # Celebrate when up $1000/day
HYBRID_MIN_CAPITAL_FOR_REAL=1000.00     # Minimum capital to allow real trades
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd /home/master/Documents/OMNICUS-Ultimate-Project
cp .env.example .env
# Edit .env with your API keys (even for hybrid, you need them ready)
```

### 2. Run in Hybrid Mode

```bash
./run_omnicus.sh hybrid
```

Or use the launcher options:

```bash
./run_omnicus.sh dashboard    # Just the UI
./run_omnicus.sh paper        # Paper only
./run_omnicus.sh live         # Real money only (risky!)
./run_omnicus.sh hybrid       # Smart hybrid mode ⭐
./run_omnicus.sh test         # Run tests
./run_omnicus.sh status       # Check current state
```

---

## 📊 Dashboard Features

The Universal Dashboard shows:

- **Mode Indicator** — 📚 LEARN | 🎮 PAPER | 💰 REAL
- **Dual Capital Tracking** — Paper capital + Real capital
- **P/L Charts** — Separate tracking for paper vs real
- **Trade Feed** — Color-coded: 📝 paper trades, 💰 real trades
- **Learning Progress** — "37/50 paper trades completed"
- **Confidence Meter** — Shows current AI confidence level

---

## 🧠 Intelligence Features

### Confidence Calibration

OMNICUS tracks whether its confidence matches reality:

| Confidence Range | Expected Win Rate | Actual Win Rate | Status |
|-----------------|-------------------|-----------------|--------|
| High (80%+)     | 70%+              | ???             | 📊 Calibrating |
| Medium (60-80%) | 55-70%            | ???             | 📊 Calibrating |
| Low (<60%)      | <55%              | ???             | 📊 Calibrating |

**If high-confidence trades keep losing:** OMNICUS reduces confidence automatically.

### Emotional Learning

- **Wins** → Confidence boosts, happiness increases
- **Losses** → Stress increases, may trigger caution
- **Consecutive losses** → May pause trading, reduce risk
- **Big wins** → Milestone celebrations, motivation boost

### Memory Bank

Every trade (paper or real) gets logged:

- **Victory Memories** — Big wins to celebrate and learn from
- **Mistake Memories** — Losses with lessons attached
- **Trauma Memories** — Losses >$1000 (never forget)
- **Pattern Recognition** — Recurring market conditions

---

## 🛡️ Safety Features

| Feature | Purpose |
|---------|---------|
| **50-trade learning phase** | Prove the system before risking real money |
| **85% confidence threshold** | Only trade real money on highest-conviction signals |
| **2% max position** | Never overexpose on a single trade |
| **$500 daily loss limit** | Stop trading before a bad day becomes catastrophic |
| **Paper trading always on** | Continuous learning, strategy testing |
| **Confidence calibration** | Prevents overconfidence after lucky streaks |

---

## 📈 Performance Tracking

### Paper Trading Stats

- Total trades
- Win rate
- Total P/L
- Average win/loss
- Best trade
- Worst trade

### Real Trading Stats

- Total trades
- Win rate
- Total P/L
- Daily P/L
- Sharpe ratio (eventually)
- Max drawdown

### Calibration Metrics

- High-confidence win rate
- Medium-confidence win rate
- Low-confidence win rate
- Confidence vs reality gap

---

## 🎮 Example Flow

```
[OMNICUS scans markets]
→ Sees BTC setup with 72% confidence
→ "Confidence 72% below 85% threshold"
→ Executes PAPER trade only
→ Trade wins +$150
→ Logs victory memory, updates skills

[Later...]

→ Sees ETH setup with 89% confidence
→ "Confidence 89% exceeds threshold!"
→ Checks: 50+ paper trades done? ✅
→ Checks: Daily loss limit hit? ❌
→ Checks: Capital available? ✅
→ Executes REAL trade
→ Trade wins +$340
→ 💰 REAL PROFIT! Celebration!
→ Logs milestone if daily target hit
```

---

## 🔧 API Integration

### Required API Keys (in `.env`)

Even in hybrid mode, have these ready:

```bash
# Binance (Primary)
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
BINANCE_TESTNET=true  # Start with testnet!

# Alpaca (Stocks)
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_PAPER_TRADING=true

# Polymarket (Optional)
POLYMARKET_API_KEY=your_key_here
```

**Recommendation:** Start with `BINANCE_TESTNET=true` even for "real" hybrid trades. Graduate to live keys after 100+ successful paper trades.

---

## 📝 Command Reference

```bash
# Start hybrid mode
./run_omnicus.sh hybrid

# Check status
./run_omnicus.sh status

# View logs
./run_omnicus.sh logs

# Run tests
./run_omnicus.sh test

# Reset (clear logs/cache)
./run_omnicus.sh reset

# Dashboard only
./run_omnicus.sh dashboard 5000
```

---

## 🎯 Success Metrics

### Graduation Criteria (Ready for More Real Trades)

- ✅ 50+ paper trades completed
- ✅ Paper win rate > 55%
- ✅ Paper P/L positive
- ✅ Confidence calibration shows high-confidence trades outperform
- ✅ No trauma memories (losses > $1000)
- ✅ Emotional state stable (no panic, no overconfidence)

### When to Increase Real Position Limit

Current: 2% max per trade

Increase to 3% when:
- 100+ real trades executed
- Real win rate > 60%
- Real P/L consistently positive
- No daily loss limit hits in 30 days

---

## 🧪 Testing

Before running hybrid mode:

```bash
# Run test suite
./run_omnicus.sh test

# Or with pytest
source venv/bin/activate
python -m pytest tests/test_omnicus.py -v
```

---

## 🚨 Warnings

> ⚠️ **Real money trading involves risk.** Hybrid mode reduces risk but doesn't eliminate it.

> ⚠️ **Start with testnet.** Even in "real" mode, use Binance testnet until you have 100+ successful trades.

> ⚠️ **Never trade money you can't afford to lose.** OMNICUS is learning. Losses will happen.

> ⚠️ **Monitor daily.** Check the dashboard, review trades, adjust settings as needed.

---

## 📞 Support

- **Dashboard:** http://localhost:5000
- **Logs:** `tail -f logs/omnicus.log`
- **Telegram:** Configure bot token for remote alerts
- **Voice Calls:** Configure Twilio for trade alerts

---

**"Double the money. Period."**

🤖 OMNICUS ULTIMATE — The Profit Hunter
