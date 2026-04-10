#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗ ███╗   ███╗██╗   ██╗██╗  ██╗                           ║
║  ██╔═══██╗████╗ ████║██║   ██║╚██╗██╔╝                           ║
║  ██║   ██║██╔████╔██║██║   ██║ ╚███╔╝                            ║
║  ██║   ██║██║╚██╔╝██║██║   ██║ ██╔██╗                            ║
║  ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗                           ║
║   ╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝                           ║
║                                                                   ║
║                    💰 THE PROFIT HUNTER 💰                       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

OMNICUS Complete System - REAL DATA VERSION
"""

import os
import sys
import json
import time
import random
import threading
import requests
import numpy as np
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================
# OMNICUS PERSONALITY
# ============================================

class OMNICUSPersonality:
    """OMNICUS AI Personality - The Profit Hunter"""
    
    NAME = "OMNICUS"
    MISSION = "Double the capital in 24 hours"
    
    TRAITS = {
        "aggression": 0.8,
        "confidence": 0.9,
        "patience": 0.4,
        "risk_tolerance": 0.85,
        "greed": 0.75,
        "hunger": 1.0
    }
    
    MOODS = {
        "hunting": "🎯 Scanning for opportunities...",
        "excited": "🚀 Found something JUICY!",
        "cautious": "👀 Market looking uncertain...",
        "victorious": "💰 SECURED THE BAG!",
        "hungry": "🤑 Need more profits!"
    }
    
    @staticmethod
    def greet():
        greetings = [
            "Yo boss! OMNICUS is LIVE and HUNGRY! Let's make some MONEY! 🚀",
            "Time to HUNT! Market scanner locked and loaded! 💰",
            "OMNICUS online! Watching EVERY market! Let's EAT! 🎯"
        ]
        return random.choice(greetings)
    
    @staticmethod
    def respond_to_buy(symbol, price, rsi):
        return f"🟢 {symbol} is looking JUICY at ${price:,.4f}! RSI at {rsi:.1f} says it's TIME TO LOAD UP! Let's RIDE THIS UP! 💰"
    
    @staticmethod
    def respond_to_sell(symbol, price, rsi):
        return f"🔴 {symbol} looking TOPPY at ${price:,.4f}! RSI {rsi:.1f} says TAKE PROFITS! Secure that BAG! 💸"
    
    @staticmethod
    def get_motivation():
        phrases = [
            "We're gonna DOUBLE that capital! Let's GO! 🚀",
            "Every trade brings us closer to the TARGET! 💰",
            "I can SMELL the profits! Keep hunting! 🎯",
            "The market is our PLAYGROUND! 🏆"
        ]
        return random.choice(phrases)


# ============================================
# REAL MARKET ENGINE
# ============================================

class RealMarketEngine:
    """Fetches REAL data from Binance API"""
    
    BASE_URL = "https://api.binance.com"
    
    WATCH_LIST = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
        "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
        "MATICUSDT", "DOTUSDT", "LINKUSDT", "ATOMUSDT",
        "ARBUSDT", "OPUSDT", "INJUSDT", "FETUSDT"
    ]
    
    @staticmethod
    def get_ticker(symbol):
        try:
            resp = requests.get(f"{RealMarketEngine.BASE_URL}/api/v3/ticker/24hr?symbol={symbol}", timeout=5)
            return resp.json() if resp.status_code == 200 else {}
        except:
            return {}
    
    @staticmethod
    def get_klines(symbol, interval="1h", limit=50):
        try:
            resp = requests.get(f"{RealMarketEngine.BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}", timeout=5)
            return resp.json() if resp.status_code == 200 else []
        except:
            return []
    
    @staticmethod
    def calculate_rsi(closes, period=14):
        if len(closes) < period + 1:
            return 50.0
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        return round(100 - (100 / (1 + avg_gain/avg_loss)), 1)
    
    @staticmethod
    def calculate_ema(closes, period):
        if len(closes) < period:
            return closes[-1] if closes else 0.0
        multiplier = 2 / (period + 1)
        ema = closes[0]
        for price in closes[1:]:
            ema = (price - ema) * multiplier + ema
        return ema
    
    @staticmethod
    def scan_market():
        results = []
        for symbol in RealMarketEngine.WATCH_LIST:
            try:
                ticker = RealMarketEngine.get_ticker(symbol)
                klines = RealMarketEngine.get_klines(symbol)
                
                if not ticker or not klines:
                    continue
                
                closes = [float(k[4]) for k in klines]
                price = float(ticker['lastPrice'])
                change_pct = float(ticker['priceChangePercent'])
                volume = float(ticker['volume'])
                
                rsi = RealMarketEngine.calculate_rsi(closes)
                ema9 = RealMarketEngine.calculate_ema(closes, 9)
                ema21 = RealMarketEngine.calculate_ema(closes, 21)
                ema50 = RealMarketEngine.calculate_ema(closes, 50)
                
                if ema9 > ema21 > ema50:
                    trend = "BULLISH"
                elif ema9 < ema21 < ema50:
                    trend = "BEARISH"
                else:
                    trend = "NEUTRAL"
                
                score = 0.5
                if rsi < 30: score += 0.25
                elif rsi > 70: score -= 0.25
                if trend == "BULLISH": score += 0.15
                elif trend == "BEARISH": score -= 0.15
                
                score = max(0, min(1, score))
                signal = "BUY" if score >= 0.65 else "SELL" if score <= 0.35 else "HOLD"
                confidence = round(abs(score - 0.5) * 2, 2)
                
                results.append({
                    'symbol': symbol.replace('USDT', '/USDT'),
                    'price': price,
                    'change_pct': round(change_pct, 2),
                    'volume': volume,
                    'high_24h': float(ticker.get('highPrice', 0)),
                    'low_24h': float(ticker.get('lowPrice', 0)),
                    'rsi': rsi,
                    'ema9': round(ema9, 4),
                    'ema21': round(ema21, 4),
                    'ema50': round(ema50, 4),
                    'trend': trend,
                    'signal': signal,
                    'confidence': confidence
                })
            except:
                pass
        
        priority = {"BUY": 0, "SELL": 1, "HOLD": 2}
        results.sort(key=lambda x: (priority.get(x['signal'], 2), -x['confidence']))
        return results


# ============================================
# CACHED DATA & BACKGROUND SCANNER
# ============================================

CACHED = {
    'market_data': [],
    'last_scan': None,
    'capital': 10000.0,
    'profit': 0.0,
    'positions': {},
    'trades': [],
    'auto_trading': False
}

def background_scanner():
    global CACHED
    while True:
        try:
            CACHED['market_data'] = RealMarketEngine.scan_market()
            CACHED['last_scan'] = datetime.now().isoformat()
        except Exception as e:
            print(f"Scan error: {e}")
        time.sleep(30)

# Start scanner thread
scanner_thread = threading.Thread(target=background_scanner, daemon=True)
scanner_thread.start()


# ============================================
# FLASK APP
# ============================================

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboards", "omnicus_ultimate.html")
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path)
    return "<h1>🤖 OMNICUS</h1><p><a href='/api/market/scan'>Market Scan</a></p>"

@app.route("/api/status")
def api_status():
    return jsonify({
        "status": "online",
        "name": "OMNICUS Trading System",
        "data_source": "BINANCE_REAL",
        "version": "2.0.0",
        "capital": CACHED['capital'],
        "profit": CACHED['profit'],
        "auto_trading": CACHED['auto_trading'],
        "last_scan": CACHED['last_scan'],
        "symbols_count": len(CACHED['market_data']),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/market/scan")
def api_market_scan():
    return jsonify({
        "success": True,
        "data_source": "BINANCE_REAL",
        "count": len(CACHED['market_data']),
        "data": CACHED['market_data'],
        "last_scan": CACHED['last_scan'],
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/market/<symbol>")
def api_market_symbol(symbol):
    symbol = symbol.upper().replace("-", "") + "USDT"
    ticker = RealMarketEngine.get_ticker(symbol)
    klines = RealMarketEngine.get_klines(symbol)
    
    if not ticker or not klines:
        return jsonify({"success": False, "error": "Symbol not found"})
    
    closes = [float(k[4]) for k in klines]
    return jsonify({
        "success": True,
        "data_source": "BINANCE_REAL",
        "symbol": symbol.replace("USDT", "/USDT"),
        "price": float(ticker['lastPrice']),
        "change_pct": float(ticker['priceChangePercent']),
        "rsi": RealMarketEngine.calculate_rsi(closes)
    })

@app.route("/api/signals")
def api_signals():
    signals = [r for r in CACHED['market_data'] if r['signal'] in ['BUY', 'SELL']]
    return jsonify({
        "success": True,
        "data_source": "BINANCE_REAL",
        "count": len(signals),
        "signals": signals
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json or {}
    msg = data.get("message", "").lower()
    
    market = CACHED['market_data']
    
    if not msg:
        return jsonify({"response": "Say something! I'm here to help you make MONEY!", "timestamp": datetime.now().isoformat()})
    
    # Greeting
    if any(w in msg for w in ["hello", "hi", "hey", "yo"]):
        return jsonify({"response": OMNICUSPersonality.greet(), "timestamp": datetime.now().isoformat()})
    
    # Status check
    elif any(w in msg for w in ["status", "how are", "how you", "what's up"]):
        btc = next((r for r in market if 'BTC' in r['symbol']), {})
        buy_count = len([r for r in market if r['signal'] == 'BUY'])
        return jsonify({
            "response": f"Yo boss! I'm HUNTING! 🎯\n\n📊 Watching {len(market)} pairs with REAL Binance data\n💰 BTC at ${btc.get('price', 0):,.2f}\n🟢 {buy_count} BUY signals detected\n{OMNICUSPersonality.get_motivation()}",
            "timestamp": datetime.now().isoformat()
        })
    
    # Buy signals
    elif any(w in msg for w in ["buy", "long", "opportunity"]):
        buy_signals = [r for r in market if r['signal'] == 'BUY']
        if buy_signals:
            top = buy_signals[0]
            return jsonify({
                "response": OMNICUSPersonality.respond_to_buy(top['symbol'], top['price'], top['rsi']),
                "timestamp": datetime.now().isoformat()
            })
        return jsonify({"response": "No strong BUY signals right now. Market is consolidating. Stay READY! 🎯", "timestamp": datetime.now().isoformat()})
    
    # Sell signals
    elif any(w in msg for w in ["sell", "short", "dump"]):
        sell_signals = [r for r in market if r['signal'] == 'SELL']
        if sell_signals:
            top = sell_signals[0]
            return jsonify({
                "response": OMNICUSPersonality.respond_to_sell(top['symbol'], top['price'], top['rsi']),
                "timestamp": datetime.now().isoformat()
            })
        return jsonify({"response": "No strong SELL signals. Market might be bullish. Keep watching! 👀", "timestamp": datetime.now().isoformat()})
    
    # Signals summary
    elif "signal" in msg:
        buy_count = len([r for r in market if r['signal'] == 'BUY'])
        sell_count = len([r for r in market if r['signal'] == 'SELL'])
        top_buy = next((r for r in market if r['signal'] == 'BUY'), None)
        
        response = f"📊 SIGNAL SUMMARY:\n\n🟢 BUY: {buy_count} signals\n🔴 SELL: {sell_count} signals\n🟡 HOLD: {len(market) - buy_count - sell_count} pairs\n\n"
        if top_buy:
            response += f"🔥 TOP BUY: {top_buy['symbol']} at ${top_buy['price']:,.4f} (RSI: {top_buy['rsi']:.1f})"
        
        return jsonify({"response": response, "timestamp": datetime.now().isoformat()})
    
    # Scan request
    elif "scan" in msg:
        buy_count = len([r for r in market if r['signal'] == 'BUY'])
        sell_count = len([r for r in market if r['signal'] == 'SELL'])
        return jsonify({
            "response": f"📡 Market scan complete!\n\n📊 Analyzed {len(market)} pairs\n🟢 {buy_count} BUY signals\n🔴 {sell_count} SELL signals\n\n{OMNICUSPersonality.get_motivation()}",
            "timestamp": datetime.now().isoformat()
        })
    
    # Capital/Profit
    elif any(w in msg for w in ["capital", "profit", "money", "balance"]):
        return jsonify({
            "response": f"💰 ACCOUNT STATUS:\n\n💵 Capital: ${CACHED['capital']:,.2f}\n📈 Profit: ${CACHED['profit']:,.2f}\n🎯 Mission: {OMNICUSPersonality.MISSION}\n\n{OMNICUSPersonality.get_motivation()}",
            "timestamp": datetime.now().isoformat()
        })
    
    # Help
    elif "help" in msg:
        return jsonify({
            "response": """🤖 I'm OMNICUS - The Profit Hunter!

📝 COMMANDS:
• 'status' - Current market status
• 'signals' - Trading signal summary
• 'buy' - Show BUY opportunities
• 'sell' - Show SELL warnings
• 'scan' - Fresh market scan
• 'capital' - Account balance
• 'help' - This message

📡 All data is REAL from Binance API!
🎯 Mission: Double the capital!

Let's make some MONEY! 💰""",
            "timestamp": datetime.now().isoformat()
        })
    
    # Default response
    else:
        return jsonify({
            "response": f"I'm watching {len(market)} pairs with REAL Binance data! 💰\n\nType 'help' for commands, or ask about 'signals', 'buy', 'sell', or 'status'!\n\n{OMNICUSPersonality.get_motivation()}",
            "timestamp": datetime.now().isoformat()
        })

@app.route("/api/trade", methods=["POST"])
def api_trade():
    data = request.json or {}
    symbol = data.get("symbol", "")
    action = data.get("action", "").upper()
    quantity = float(data.get("quantity", 0))
    
    if action not in ["BUY", "SELL"]:
        return jsonify({"success": False, "error": "Invalid action. Use BUY or SELL"})
    
    symbol_binance = symbol.replace("/", "").replace("-", "") + "USDT"
    ticker = RealMarketEngine.get_ticker(symbol_binance)
    
    if not ticker:
        return jsonify({"success": False, "error": "Symbol not found"})
    
    price = float(ticker['lastPrice'])
    total = price * quantity
    
    if action == "BUY":
        if total > CACHED['capital']:
            return jsonify({"success": False, "error": f"Insufficient capital. Need ${total:,.2f}, have ${CACHED['capital']:,.2f}"})
        CACHED['capital'] -= total
        CACHED['positions'][symbol] = CACHED['positions'].get(symbol, 0) + quantity
    else:
        if symbol not in CACHED['positions'] or CACHED['positions'][symbol] < quantity:
            return jsonify({"success": False, "error": "Insufficient position"})
        CACHED['capital'] += total
        CACHED['positions'][symbol] -= quantity
    
    trade = {
        "symbol": symbol,
        "action": action,
        "price": price,
        "quantity": quantity,
        "total": total,
        "timestamp": datetime.now().isoformat()
    }
    CACHED['trades'].append(trade)
    CACHED['profit'] = CACHED['capital'] - 10000.0
    
    return jsonify({
        "success": True,
        "message": f"✅ {action} {quantity} {symbol} at ${price:,.4f}",
        "trade": trade,
        "capital": CACHED['capital'],
        "profit": CACHED['profit']
    })

@app.route("/api/positions")
def api_positions():
    return jsonify({
        "success": True,
        "capital": CACHED['capital'],
        "profit": CACHED['profit'],
        "positions": CACHED['positions'],
        "trades_count": len(CACHED['trades'])
    })

@app.route("/api/auto/<state>", methods=["POST"])
def api_auto_trading(state):
    CACHED['auto_trading'] = state.lower() == "on"
    return jsonify({
        "success": True,
        "auto_trading": CACHED['auto_trading'],
        "message": f"Auto trading {'ENABLED' if CACHED['auto_trading'] else 'DISABLED'}"
    })


# ============================================
# MAIN
# ============================================

def main():
    print("\n" + "="*70)
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                                                                   ║")
    print("║   ██████╗ ███╗   ███╗██╗   ██╗██╗  ██╗                           ║")
    print("║  ██╔═══██╗████╗ ████║██║   ██║╚██╗██╔╝                           ║")
    print("║  ██║   ██║██╔████╔██║██║   ██║ ╚███╔╝                            ║")
    print("║  ██║   ██║██║╚██╔╝██║██║   ██║ ██╔██╗                            ║")
    print("║  ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗                           ║")
    print("║   ╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝                           ║")
    print("║                                                                   ║")
    print("║                    💰 THE PROFIT HUNTER 💰                       ║")
    print("║                                                                   ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print("="*70)
    print()
    print("📡 Data Source: BINANCE REAL API (NO SIMULATION)")
    print("🎯 Mission: Double the capital in 24 hours")
    print()
    print("🌐 DASHBOARD:    http://localhost:8080")
    print("📊 MARKET SCAN:  http://localhost:8080/api/market/scan")
    print("💬 CHAT API:     POST http://localhost:8080/api/chat")
    print("📈 SIGNALS:      http://localhost:8080/api/signals")
    print()
    print("="*70)
    print()
    print("⏳ Initial market scan in progress...")
    print()
    
    # Wait for first scan
    time.sleep(5)
    
    if CACHED['market_data']:
        print("✅ Market data loaded!")
        buy_count = len([r for r in CACHED['market_data'] if r['signal'] == 'BUY'])
        print(f"📊 {len(CACHED['market_data'])} pairs scanned | {buy_count} BUY signals")
        print()
    
    print("="*70)
    print("🚀 OMNICUS IS LIVE! Press Ctrl+C to stop")
    print("="*70)
    print()
    
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)


if __name__ == "__main__":
    main()
