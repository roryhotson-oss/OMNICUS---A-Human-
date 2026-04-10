#!/usr/bin/env python3
"""
OMNICUS Real-Time Market Scanner
=================================
Fetches REAL data from Binance API - NO SIMULATION
"""

import requests
import numpy as np
from datetime import datetime

def calculate_rsi(closes, period=14):
    """Calculate RSI from real price data"""
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

def calculate_ema(closes, period):
    """Calculate EMA"""
    if len(closes) < period:
        return closes[-1] if closes else 0.0
    
    multiplier = 2 / (period + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def scan_market():
    """Scan market with REAL Binance data"""
    symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
        "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
        "MATICUSDT", "DOTUSDT", "LINKUSDT", "ATOMUSDT",
        "ARBUSDT", "OPUSDT", "INJUSDT", "FETUSDT"
    ]
    
    results = []
    
    for symbol in symbols:
        try:
            # Get ticker data
            ticker_resp = requests.get(
                f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}",
                timeout=5
            )
            ticker = ticker_resp.json()
            
            # Get klines for technical analysis
            klines_resp = requests.get(
                f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=50",
                timeout=5
            )
            klines = klines_resp.json()
            
            closes = [float(k[4]) for k in klines]
            
            price = float(ticker['lastPrice'])
            change_pct = float(ticker['priceChangePercent'])
            
            # Calculate indicators
            rsi = calculate_rsi(closes)
            ema9 = calculate_ema(closes, 9)
            ema21 = calculate_ema(closes, 21)
            ema50 = calculate_ema(closes, 50)
            
            # Determine trend
            if ema9 > ema21 > ema50:
                trend = "BULLISH"
            elif ema9 < ema21 < ema50:
                trend = "BEARISH"
            else:
                trend = "NEUTRAL"
            
            # Generate signal
            score = 0.5
            if rsi < 30:
                score += 0.25
            elif rsi > 70:
                score -= 0.25
            
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
            
            results.append({
                'symbol': symbol.replace('USDT', '/USDT'),
                'price': price,
                'change_pct': round(change_pct, 2),
                'rsi': rsi,
                'trend': trend,
                'signal': signal,
                'confidence': confidence
            })
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    # Sort by signal priority
    priority = {"BUY": 0, "SELL": 1, "HOLD": 2}
    results.sort(key=lambda x: (priority.get(x['signal'], 2), -x['confidence']))
    
    return results

def main():
    print("\n" + "=" * 80)
    print("🤖 OMNICUS REAL-TIME MARKET SCANNER")
    print("📡 Data Source: BINANCE LIVE API - NO SIMULATION")
    print("=" * 80)
    print()
    
    results = scan_market()
    
    print(f"{'Symbol':<12} | {'Price':>14} | {'24h %':>8} | {'RSI':>6} | {'Trend':<10} | Signal")
    print("-" * 80)
    
    for r in results:
        emoji = '🟢' if r['signal'] == 'BUY' else '🔴' if r['signal'] == 'SELL' else '🟡'
        print(f"{r['symbol']:<12} | ${r['price']:>12,.4f} | {r['change_pct']:>+7.2f}% | {r['rsi']:>6.1f} | {r['trend']:<10} | {emoji} {r['signal']} ({r['confidence']:.0%})")
    
    buy_count = len([r for r in results if r['signal'] == 'BUY'])
    sell_count = len([r for r in results if r['signal'] == 'SELL'])
    
    print()
    print("=" * 80)
    print(f"📊 SUMMARY: {buy_count} BUY signals | {sell_count} SELL signals | {len(results) - buy_count - sell_count} HOLD")
    print(f"⏰ Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ ALL DATA IS REAL FROM BINANCE API - NO SIMULATION")
    print("=" * 80)
    print()

if __name__ == "__main__":
    main()
