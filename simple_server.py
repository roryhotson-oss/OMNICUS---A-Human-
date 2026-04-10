#!/usr/bin/env python3
"""
OMNICUS Dashboard Server - REAL DATA (Synchronous)
===================================================
Simple Flask server with REAL Binance data - no async issues.
"""

import os
import json
import logging
import requests
import numpy as np
from datetime import datetime
from flask import Flask, jsonify, send_file
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OMNICUS")

app = Flask(__name__)
CORS(app)

# ============================================
# REAL BINANCE DATA - SYNCHRONOUS
# ============================================

class RealBinanceData:
    """Fetches REAL data from Binance public API"""
    
    BASE_URL = "https://api.binance.com"
    
    def get_ticker(self, symbol: str) -> dict:
        """Get 24hr ticker - REAL data"""
        symbol = symbol.upper().replace("/", "")
        url = f"{self.BASE_URL}/api/v3/ticker/24hr?symbol={symbol}"
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> list:
        """Get candlestick data - REAL data"""
        symbol = symbol.upper().replace("/", "")
        url = f"{self.BASE_URL}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return []
        except:
            return []
    
    def calculate_rsi(self, closes: list, period: int = 14) -> float:
        """Calculate RSI from real price data"""
        if len(closes) < period + 1:
            return 50.0
        
        closes = np.array(closes)
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)
    
    def calculate_ema(self, closes: list, period: int) -> float:
        """Calculate EMA from real prices"""
        if len(closes) < period:
            return closes[-1] if closes else 0.0
        
        multiplier = 2 / (period + 1)
        ema = closes[0]
        for price in closes[1:]:
            ema = (price - ema) * multiplier + ema
        return round(ema, 4)
    
    def get_snapshot(self, symbol: str) -> dict:
        """Get complete market snapshot with REAL indicators"""
        try:
            # Fetch both ticker and klines
            ticker = self.get_ticker(symbol)
            klines = self.get_klines(symbol)
            
            if "error" in ticker or not klines:
                return {"symbol": symbol, "error": ticker.get("error", "No data")}
            
            # Extract OHLCV
            closes = [float(k[4]) for k in klines]
            
            price = float(ticker.get("lastPrice", 0))
            change_pct = float(ticker.get("priceChangePercent", 0))
            volume = float(ticker.get("volume", 0))
            
            # Calculate REAL technical indicators
            rsi = self.calculate_rsi(closes)
            ema9 = self.calculate_ema(closes, 9)
            ema21 = self.calculate_ema(closes, 21)
            ema50 = self.calculate_ema(closes, 50)
            
            # Determine trend
            if ema9 > ema21 > ema50:
                trend = "BULLISH"
            elif ema9 < ema21 < ema50:
                trend = "BEARISH"
            else:
                trend = "NEUTRAL"
            
            # Generate signal based on REAL analysis
            score = 0.5
            if rsi < 30:
                score += 0.25  # Oversold - buy signal
            elif rsi > 70:
                score -= 0.25  # Overbought - sell signal
            
            if trend == "BULLISH":
                score += 0.15
            elif trend == "BEARISH":
                score -= 0.15
            
            score = max(0, min(1, score))
            
            if score >= 0.65:
                signal = "BUY"
            elif score <= 0.35:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            confidence = round(abs(score - 0.5) * 2, 2)
            
            return {
                "symbol": symbol,
                "price": price,
                "change_pct": round(change_pct, 2),
                "volume": volume,
                "high_24h": float(ticker.get("highPrice", 0)),
                "low_24h": float(ticker.get("lowPrice", 0)),
                "rsi": rsi,
                "ema9": ema9,
                "ema21": ema21,
                "ema50": ema50,
                "trend": trend,
                "signal": signal,
                "confidence": confidence,
                "data_source": "BINANCE_REAL",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}


# Global instance
binance = RealBinanceData()

# Default watchlist
WATCH_LIST = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT",
    "XRP/USDT", "ADA/USDT", "DOGE/USDT"
]

# ============================================
# FLASK ROUTES
# ============================================

@app.route("/")
def index():
    """Serve the main dashboard"""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboards", "omnicus_ultimate.html")
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OMNICUS - REAL DATA Dashboard</title>
        <style>
            body {{
                background: linear-gradient(135deg, #0a0a0f, #1a1a2e);
                color: #00ff88;
                font-family: 'Courier New', monospace;
                padding: 20px;
            }}
            h1 {{ text-shadow: 0 0 20px rgba(0,255,136,0.5); }}
            a {{ color: #3a86ff; }}
            .live {{ animation: blink 1s infinite; }}
            @keyframes blink {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.3; }}
            }}
        </style>
    </head>
    <body>
        <h1>🤖 OMNICUS Trading Dashboard</h1>
        <p class="live">● LIVE DATA from Binance</p>
        <p><a href="/api/market/scan">📊 Scan Markets</a></p>
        <p><a href="/api/signals">🔥 Trading Signals</a></p>
        <p><a href="/api/status">📡 API Status</a></p>
    </body>
    </html>
    """

@app.route("/api/status")
def api_status():
    """API status"""
    return jsonify({
        "status": "online",
        "name": "OMNICUS Trading System",
        "data_source": "BINANCE_REAL",
        "version": "2.0.0",
        "symbols_supported": len(WATCH_LIST),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/market/scan")
def api_market_scan():
    """Scan all markets - REAL DATA from Binance"""
    results = []
    for symbol in WATCH_LIST:
        snapshot = binance.get_snapshot(symbol)
        if "error" not in snapshot:
            results.append(snapshot)
    
    # Sort by signal priority
    priority = {"BUY": 0, "SELL": 1, "HOLD": 2}
    results.sort(key=lambda x: (priority.get(x.get("signal", "HOLD"), 2), -x.get("confidence", 0)))
    
    return jsonify({
        "success": True,
        "data_source": "BINANCE_REAL",
        "count": len(results),
        "data": results,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/market/<symbol>")
def api_market_symbol(symbol):
    """Get single symbol data - REAL DATA"""
    symbol = symbol.upper().replace("-", "/")
    result = binance.get_snapshot(symbol)
    
    return jsonify({
        "success": "error" not in result,
        "data_source": "BINANCE_REAL",
        "data": result
    })

@app.route("/api/signals")
def api_signals():
    """Get current trading signals"""
    results = []
    for symbol in WATCH_LIST:
        snapshot = binance.get_snapshot(symbol)
        if "error" not in snapshot and snapshot.get("signal") in ["BUY", "SELL"]:
            results.append(snapshot)
    
    results.sort(key=lambda x: -x.get("confidence", 0))
    
    return jsonify({
        "success": True,
        "data_source": "BINANCE_REAL",
        "count": len(results),
        "signals": results
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Simple chat endpoint"""
    from flask import request
    msg = request.json.get("message", "").lower()
    
    if "status" in msg or "how are" in msg:
        snapshot = binance.get_snapshot("BTC/USDT")
        btc_price = snapshot.get("price", 0)
        return jsonify({
            "response": f"I'm alive and scanning! BTC is at ${btc_price:,.2f}. All data is REAL from Binance.",
            "timestamp": datetime.now().isoformat()
        })
    
    elif "signal" in msg or "buy" in msg:
        results = []
        for symbol in WATCH_LIST:
            snapshot = binance.get_snapshot(symbol)
            if "error" not in snapshot and snapshot.get("signal") == "BUY":
                results.append(snapshot)
        
        if results:
            top = results[0]
            return jsonify({
                "response": f"Top BUY signal: {top['symbol']} at ${top['price']:,.2f}. RSI: {top['rsi']:.1f}, Trend: {top['trend']}, Confidence: {top['confidence']:.0%}",
                "timestamp": datetime.now().isoformat()
            })
        return jsonify({
            "response": "No strong BUY signals at the moment. Market seems neutral.",
            "timestamp": datetime.now().isoformat()
        })
    
    elif "help" in msg:
        return jsonify({
            "response": "I'm OMNICUS, your AI trading assistant using REAL data from Binance.\n\nCommands:\n- 'status' - Current market status\n- 'signals' - Show trading signals\n- 'help' - This message\n\nAll data is LIVE from Binance API!",
            "timestamp": datetime.now().isoformat()
        })
    
    else:
        return jsonify({
            "response": f"I'm watching {len(WATCH_LIST)} trading pairs with REAL Binance data. Ask me about 'signals' or 'status'!",
            "timestamp": datetime.now().isoformat()
        })


if __name__ == "__main__":
    print("""
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
║   🌐 Dashboard: http://localhost:8080                            ║
║   📊 API: http://localhost:8080/api/market/scan                  ║
║   📡 Data Source: BINANCE REAL API                               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
