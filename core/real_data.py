"""
OMNICUS Real Data Module
========================
Fetches REAL market data from Binance API.
NO SIMULATION - ALL REAL DATA.
"""

import asyncio
import aiohttp
import logging
import numpy as np
import pandas as pd
import os
import hmac
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    """Real market data snapshot"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume_24h: float
    high_24h: float
    low_24h: float
    change_24h: float
    change_pct_24h: float
    timestamp: datetime
    
    # Technical indicators (calculated from real data)
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    ema_9: float
    ema_21: float
    ema_50: float
    bb_upper: float
    bb_lower: float
    atr: float
    
    # Derived signals
    trend: str
    signal: str
    confidence: float


class BinanceRealData:
    """
    Fetches REAL data from Binance API
    No simulation - all live data
    """
    
    BASE_URL = "https://api.binance.com"
    
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
        
        if self.testnet:
            self.BASE_URL = "https://testnet.binance.vision"
            
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers["X-MBX-APIKEY"] = self.api_key
            self._session = aiohttp.ClientSession(headers=headers)
        return self._session
        
    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
            
    async def _request(self, endpoint: str, params: dict = None) -> dict:
        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if resp.status != 200:
                    logger.error(f"API Error: {data}")
                return data
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}
            
    async def get_ticker(self, symbol: str) -> dict:
        """Get 24hr ticker data"""
        symbol = symbol.upper().replace("/", "")
        return await self._request("/api/v3/ticker/24hr", {"symbol": symbol})
        
    async def get_klines(self, symbol: str, interval: str = "1h", limit: int = 200) -> List:
        """Get candlestick data"""
        symbol = symbol.upper().replace("/", "")
        data = await self._request("/api/v3/klines", {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        })
        return data if isinstance(data, list) else []


class TechnicalAnalysis:
    """
    Calculate REAL technical indicators from price data
    """
    
    @staticmethod
    def rsi(closes: List[float], period: int = 14) -> float:
        """Calculate RSI from real prices"""
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
        
    @staticmethod
    def macd(closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD from real prices"""
        if len(closes) < slow + signal:
            return 0.0, 0.0, 0.0
            
        s = pd.Series(closes)
        ema_fast = s.ewm(span=fast, adjust=False).mean()
        ema_slow = s.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return (
            round(float(macd_line.iloc[-1]), 4),
            round(float(signal_line.iloc[-1]), 4),
            round(float(histogram.iloc[-1]), 4)
        )
        
    @staticmethod
    def ema(closes: List[float], period: int) -> float:
        """Calculate EMA from real prices"""
        if len(closes) < period:
            return closes[-1] if closes else 0.0
        s = pd.Series(closes)
        return round(float(s.ewm(span=period, adjust=False).mean().iloc[-1]), 4)
        
    @staticmethod
    def bollinger(closes: List[float], period: int = 20, std_dev: float = 2.0) -> tuple:
        """Calculate Bollinger Bands from real prices"""
        if len(closes) < period:
            last = closes[-1] if closes else 0
            return last, last, last
            
        s = pd.Series(closes)
        middle = s.rolling(window=period).mean()
        std = s.rolling(window=period).std()
        
        upper = middle + std * std_dev
        lower = middle - std * std_dev
        
        return (
            round(float(upper.iloc[-1]), 4),
            round(float(middle.iloc[-1]), 4),
            round(float(lower.iloc[-1]), 4)
        )
        
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
        """Calculate ATR from real prices"""
        if len(closes) < period + 1:
            return 0.0
            
        highs = np.array(highs[1:])
        lows = np.array(lows[1:])
        closes_prev = np.array(closes[:-1])
        
        tr1 = highs - lows
        tr2 = np.abs(highs - closes_prev)
        tr3 = np.abs(lows - closes_prev)
        
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        return round(float(np.mean(tr[-period:])), 4)


class RealMarketEngine:
    """
    Main engine for fetching REAL market data
    """
    
    def __init__(self):
        self.binance = BinanceRealData()
        self.ta = TechnicalAnalysis()
        
    async def initialize(self):
        await self.binance._get_session()
        logger.info("Real Market Engine initialized - LIVE DATA ONLY")
        
    async def close(self):
        await self.binance.close()
        
    async def get_snapshot(self, symbol: str) -> MarketSnapshot:
        """
        Get complete real market snapshot with indicators
        """
        # Fetch real data
        ticker = await self.binance.get_ticker(symbol)
        klines = await self.binance.get_klines(symbol, "1h", 200)
        
        if "error" in ticker or not klines:
            logger.error(f"Failed to get data for {symbol}")
            return self._empty_snapshot(symbol)
            
        # Parse OHLCV
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        
        price = float(ticker.get("lastPrice", closes[-1]))
        
        # Calculate REAL indicators
        rsi = self.ta.rsi(closes)
        macd_val, macd_sig, macd_hist = self.ta.macd(closes)
        ema9 = self.ta.ema(closes, 9)
        ema21 = self.ta.ema(closes, 21)
        ema50 = self.ta.ema(closes, 50)
        bb_upper, bb_mid, bb_lower = self.ta.bollinger(closes)
        atr = self.ta.atr(highs, lows, closes)
        
        # Determine trend and signal
        trend = "bullish" if ema9 > ema21 > ema50 else "bearish" if ema9 < ema21 < ema50 else "neutral"
        
        # Calculate signal
        score = 0.5
        if rsi < 30: score += 0.2
        elif rsi > 70: score -= 0.2
        if macd_val > macd_sig: score += 0.15
        else: score -= 0.1
        if trend == "bullish": score += 0.1
        elif trend == "bearish": score -= 0.1
        
        score = max(0, min(1, score))
        
        if score >= 0.65: signal = "BUY"
        elif score <= 0.35: signal = "SELL"
        else: signal = "HOLD"
        
        confidence = round(abs(score - 0.5) * 2, 2)
        
        return MarketSnapshot(
            symbol=symbol,
            price=price,
            bid=float(ticker.get("bidPrice", price)),
            ask=float(ticker.get("askPrice", price)),
            volume_24h=float(ticker.get("volume", 0)),
            high_24h=float(ticker.get("highPrice", 0)),
            low_24h=float(ticker.get("lowPrice", 0)),
            change_24h=float(ticker.get("priceChange", 0)),
            change_pct_24h=float(ticker.get("priceChangePercent", 0)),
            timestamp=datetime.now(),
            rsi=rsi,
            macd=macd_val,
            macd_signal=macd_sig,
            macd_histogram=macd_hist,
            ema_9=ema9,
            ema_21=ema21,
            ema_50=ema50,
            bb_upper=bb_upper,
            bb_lower=bb_lower,
            atr=atr,
            trend=trend,
            signal=signal,
            confidence=confidence
        )
        
    def _empty_snapshot(self, symbol: str) -> MarketSnapshot:
        return MarketSnapshot(
            symbol=symbol, price=0, bid=0, ask=0,
            volume_24h=0, high_24h=0, low_24h=0,
            change_24h=0, change_pct_24h=0,
            timestamp=datetime.now(),
            rsi=50, macd=0, macd_signal=0, macd_histogram=0,
            ema_9=0, ema_21=0, ema_50=0,
            bb_upper=0, bb_lower=0, atr=0,
            trend="unknown", signal="HOLD", confidence=0
        )
        
    async def scan_all(self, symbols: List[str] = None) -> List[MarketSnapshot]:
        """Scan multiple symbols"""
        if symbols is None:
            symbols = [
                "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT",
                "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT",
                "MATIC/USDT", "DOT/USDT", "LINK/USDT", "ATOM/USDT"
            ]
            
        results = []
        for s in symbols:
            try:
                snapshot = await self.get_snapshot(s)
                results.append(snapshot)
                await asyncio.sleep(0.1)  # Rate limit
            except Exception as e:
                logger.error(f"Error scanning {s}: {e}")
                
        # Sort by signal priority
        priority = {"BUY": 0, "SELL": 1, "HOLD": 2}
        results.sort(key=lambda x: (priority.get(x.signal, 2), -x.confidence))
        
        return results


# Global instance
real_market = RealMarketEngine()
