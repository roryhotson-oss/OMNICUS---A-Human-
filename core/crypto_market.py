#!/usr/bin/env python3
"""
Crypto Market Handler
Comprehensive cryptocurrency market management and analysis
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass

from exchanges.binance_api import BinanceAPI
from trading_mode import SignalSource, RiskLevel
from trading_agent import TradeSignal

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Market data for a cryptocurrency"""
    symbol: str
    price: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    spread: float = 0.0
    liquidity_score: float = 0.0
    volatility: float = 0.0


@dataclass
class TechnicalIndicators:
    """Technical indicators for market analysis"""
    rsi: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_lower: float = 0.0
    bollinger_middle: float = 0.0
    ema_20: float = 0.0
    ema_50: float = 0.0
    volume_sma: float = 0.0
    atr: float = 0.0


@dataclass
class MarketAnalysis:
    """Complete market analysis"""
    market_data: MarketData
    technical_indicators: TechnicalIndicators
    trend_direction: str  # 'bullish', 'bearish', 'sideways'
    momentum_strength: float  # 0-1
    support_level: float
    resistance_level: float
    risk_level: RiskLevel
    trading_volume: str  # 'low', 'medium', 'high'
    market_sentiment: str  # 'fear', 'neutral', 'greed'


class CryptoMarketHandler:
    """
    Comprehensive cryptocurrency market handler.
    Manages:
    - Multiple exchange connections
    - Real-time market data
    - Technical analysis
    - Market sentiment analysis
    - Trading opportunities identification
    """
    
    def __init__(self, exchanges: Dict[str, BinanceAPI]):
        self.exchanges = exchanges
        self.market_data_cache: Dict[str, MarketData] = {}
        self.technical_indicators_cache: Dict[str, TechnicalIndicators] = {}
        self.supported_symbols = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT',
            'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'LINKUSDT', 'DOTUSDT'
        ]
        
        # Analysis parameters
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.ema_short = 20
        self.ema_long = 50
        self.bollinger_period = 20
        self.bollinger_std = 2
        
        logger.info(f"Crypto Market Handler initialized with {len(exchanges)} exchanges")
    
    async def get_market_data(self, symbol: str, exchange: str = "binance") -> Optional[MarketData]:
        """
        Get current market data for a symbol.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange to use
            
        Returns:
            MarketData object or None if failed
        """
        try:
            if exchange not in self.exchanges:
                logger.error(f"Exchange {exchange} not available")
                return None
            
            api = self.exchanges[exchange]
            
            # Get current price and 24h stats
            price_data = await api.get_price(symbol)
            stats_data = await api.get_24hr_stats(symbol)
            
            # Get orderbook for spread calculation
            orderbook = await api.get_orderbook(symbol, limit=5)
            
            # Calculate spread
            best_bid = float(orderbook['bids'][0][0]) if orderbook['bids'] else 0
            best_ask = float(orderbook['asks'][0][0]) if orderbook['asks'] else 0
            spread = best_ask - best_bid if best_bid > 0 and best_ask > 0 else 0
            
            # Calculate volatility (simplified)
            high_price = float(stats_data.get('highPrice', 0))
            low_price = float(stats_data.get('lowPrice', 0))
            current_price = float(price_data.get('price', 0))
            volatility = (high_price - low_price) / current_price if current_price > 0 else 0
            
            # Calculate liquidity score (simplified)
            volume_24h = float(stats_data.get('volume', 0))
            liquidity_score = min(1.0, volume_24h / 1000000)  # Normalize to 0-1
            
            market_data = MarketData(
                symbol=symbol,
                price=current_price,
                volume_24h=volume_24h,
                change_24h=float(stats_data.get('priceChangePercent', 0)),
                high_24h=high_price,
                low_24h=low_price,
                timestamp=datetime.now(),
                spread=spread,
                liquidity_score=liquidity_score,
                volatility=volatility
            )
            
            # Cache the data
            self.market_data_cache[symbol] = market_data
            
            return market_data
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return None
    
    async def get_technical_indicators(self, symbol: str, exchange: str = "binance") -> Optional[TechnicalIndicators]:
        """
        Calculate technical indicators for a symbol.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange to use
            
        Returns:
            TechnicalIndicators object or None if failed
        """
        try:
            if exchange not in self.exchanges:
                logger.error(f"Exchange {exchange} not available")
                return None
            
            api = self.exchanges[exchange]
            
            # Get historical price data
            klines = await api.get_klines(symbol, interval="1h", limit=100)
            
            if len(klines) < 50:  # Need enough data for calculations
                logger.warning(f"Insufficient data for {symbol}: {len(klines)} candles")
                return None
            
            # Extract price data
            closes = [float(kline[4]) for kline in klines]  # Close prices
            volumes = [float(kline[5]) for kline in klines]  # Volumes
            highs = [float(kline[2]) for kline in klines]    # High prices
            lows = [float(kline[3]) for kline in klines]     # Low prices
            
            closes_array = np.array(closes)
            volumes_array = np.array(volumes)
            highs_array = np.array(highs)
            lows_array = np.array(lows)
            
            # Calculate RSI
            rsi = self._calculate_rsi(closes_array, self.rsi_period)
            
            # Calculate MACD
            macd, macd_signal, macd_histogram = self._calculate_macd(
                closes_array, self.macd_fast, self.macd_slow, self.macd_signal
            )
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                closes_array, self.bollinger_period, self.bollinger_std
            )
            
            # Calculate EMAs
            ema_20 = self._calculate_ema(closes_array, self.ema_short)
            ema_50 = self._calculate_ema(closes_array, self.ema_long)
            
            # Calculate Volume SMA
            volume_sma = np.mean(volumes_array[-20:])
            
            # Calculate ATR (Average True Range)
            atr = self._calculate_atr(highs_array, lows_array, closes_array, 14)
            
            indicators = TechnicalIndicators(
                rsi=rsi,
                macd=macd,
                macd_signal=macd_signal,
                bollinger_upper=bb_upper,
                bollinger_middle=bb_middle,
                bollinger_lower=bb_lower,
                ema_20=ema_20,
                ema_50=ema_50,
                volume_sma=volume_sma,
                atr=atr
            )
            
            # Cache the indicators
            self.technical_indicators_cache[symbol] = indicators
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators for {symbol}: {e}")
            return None
    
    async def analyze_market(self, symbol: str, exchange: str = "binance") -> Optional[MarketAnalysis]:
        """
        Perform comprehensive market analysis.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange to use
            
        Returns:
            MarketAnalysis object or None if failed
        """
        try:
            # Get market data and technical indicators
            market_data = await self.get_market_data(symbol, exchange)
            indicators = await self.get_technical_indicators(symbol, exchange)
            
            if not market_data or not indicators:
                return None
            
            # Determine trend direction
            trend_direction = self._determine_trend(indicators, market_data)
            
            # Calculate momentum strength
            momentum_strength = self._calculate_momentum_strength(indicators)
            
            # Find support and resistance levels
            support_level, resistance_level = self._find_support_resistance(
                market_data, indicators
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(market_data, indicators)
            
            # Categorize trading volume
            trading_volume = self._categorize_volume(market_data.volume_24h)
            
            # Determine market sentiment
            market_sentiment = self._determine_sentiment(market_data, indicators)
            
            analysis = MarketAnalysis(
                market_data=market_data,
                technical_indicators=indicators,
                trend_direction=trend_direction,
                momentum_strength=momentum_strength,
                support_level=support_level,
                resistance_level=resistance_level,
                risk_level=risk_level,
                trading_volume=trading_volume,
                market_sentiment=market_sentiment
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze market for {symbol}: {e}")
            return None
    
    async def identify_opportunities(self, symbols: Optional[List[str]] = None) -> List[TradeSignal]:
        """
        Identify trading opportunities across multiple symbols.
        
        Args:
            symbols: List of symbols to analyze (default: all supported symbols)
            
        Returns:
            List of trading signals
        """
        if symbols is None:
            symbols = self.supported_symbols
        
        opportunities = []
        
        for symbol in symbols:
            try:
                analysis = await self.analyze_market(symbol)
                
                if not analysis:
                    continue
                
                # Look for specific patterns
                signal = self._check_trading_opportunities(symbol, analysis)
                
                if signal:
                    opportunities.append(signal)
                    logger.info(f"Identified opportunity: {signal.action} {symbol} ({signal.confidence:.2f})")
                    
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                continue
        
        return opportunities
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: np.ndarray, fast: int, slow: int, signal: int) -> Tuple[float, float, float]:
        """Calculate MACD indicator"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd = ema_fast - ema_slow
        
        # For signal line, we'd need to calculate EMA of MACD values
        # Simplified version
        macd_signal = macd * 0.9  # Simplified signal calculation
        macd_histogram = macd - macd_signal
        
        return macd, macd_signal, macd_histogram
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int, std_dev: float) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            current_price = prices[-1] if len(prices) > 0 else 0
            return current_price, current_price, current_price
        
        recent_prices = prices[-period:]
        middle = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return float(prices[-1]) if len(prices) > 0 else 0.0
        
        # Simple EMA calculation
        weights = np.exp(np.linspace(-1, 0, period))
        weights = weights / weights.sum()
        ema = np.dot(prices[-period:], weights)
        
        return float(ema)
    
    def _calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> float:
        """Calculate Average True Range"""
        if len(highs) < period + 1:
            return 0.0
        
        true_ranges = []
        
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        atr = np.mean(true_ranges[-period:])
        return float(atr)
    
    def _determine_trend(self, indicators: TechnicalIndicators, market_data: MarketData) -> str:
        """Determine trend direction"""
        # Multiple trend signals
        signals = []
        
        # EMA trend
        if indicators.ema_20 > indicators.ema_50:
            signals.append('bullish')
        elif indicators.ema_20 < indicators.ema_50:
            signals.append('bearish')
        
        # MACD trend
        if indicators.macd > indicators.macd_signal:
            signals.append('bullish')
        elif indicators.macd < indicators.macd_signal:
            signals.append('bearish')
        
        # Price relative to Bollinger Bands
        if market_data.price > indicators.bollinger_upper:
            signals.append('bullish')
        elif market_data.price < indicators.bollinger_lower:
            signals.append('bearish')
        
        # Determine majority trend
        bullish_count = signals.count('bullish')
        bearish_count = signals.count('bearish')
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        else:
            return 'sideways'
    
    def _calculate_momentum_strength(self, indicators: TechnicalIndicators) -> float:
        """Calculate momentum strength (0-1)"""
        # Combine multiple momentum indicators
        rsi_strength = abs(indicators.rsi - 50) / 50  # 0-1
        macd_strength = min(1.0, abs(indicators.macd) / 10)  # Normalized
        
        return (rsi_strength + macd_strength) / 2
    
    def _find_support_resistance(self, market_data: MarketData, indicators: TechnicalIndicators) -> Tuple[float, float]:
        """Find support and resistance levels"""
        # Use Bollinger Bands as dynamic S/R levels
        support = indicators.bollinger_lower
        resistance = indicators.bollinger_upper
        
        # Adjust based on recent highs/lows
        if market_data.low_24h < support:
            support = market_data.low_24h
        
        if market_data.high_24h > resistance:
            resistance = market_data.high_24h
        
        return support, resistance
    
    def _determine_risk_level(self, market_data: MarketData, indicators: TechnicalIndicators) -> RiskLevel:
        """Determine risk level"""
        risk_score = 0
        
        # Volatility risk
        if market_data.volatility > 0.05:
            risk_score += 2
        elif market_data.volatility > 0.03:
            risk_score += 1
        
        # Volume risk
        if market_data.liquidity_score < 0.3:
            risk_score += 2
        elif market_data.liquidity_score < 0.6:
            risk_score += 1
        
        # Price level risk
        if market_data.price < 10:  # Low price coins
            risk_score += 1
        
        if risk_score >= 4:
            return RiskLevel.EXTREME
        elif risk_score >= 3:
            return RiskLevel.AGGRESSIVE
        elif risk_score >= 1:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.CONSERVATIVE
    
    def _categorize_volume(self, volume: float) -> str:
        """Categorize trading volume"""
        if volume > 10000000:  # > 10M
            return 'high'
        elif volume > 1000000:  # > 1M
            return 'medium'
        else:
            return 'low'
    
    def _determine_sentiment(self, market_data: MarketData, indicators: TechnicalIndicators) -> str:
        """Determine market sentiment"""
        sentiment_score = 0
        
        # Price change sentiment
        if market_data.change_24h > 5:
            sentiment_score += 2
        elif market_data.change_24h < -5:
            sentiment_score -= 2
        
        # RSI sentiment
        if indicators.rsi > 70:
            sentiment_score -= 1  # Greed (overbought)
        elif indicators.rsi < 30:
            sentiment_score += 1  # Fear (oversold)
        
        # MACD sentiment
        if indicators.macd > indicators.macd_signal:
            sentiment_score += 1
        else:
            sentiment_score -= 1
        
        if sentiment_score >= 2:
            return 'greed'
        elif sentiment_score <= -2:
            return 'fear'
        else:
            return 'neutral'
    
    def _check_trading_opportunities(self, symbol: str, analysis: MarketAnalysis) -> Optional[TradeSignal]:
        """Check for specific trading opportunities"""
        opportunities = []
        
        # Oversold bounce opportunity
        if (analysis.technical_indicators.rsi < 30 and
            analysis.market_data.price <= analysis.technical_indicators.bollinger_lower and
            analysis.trading_volume in ['medium', 'high']):
            
            opportunities.append({
                'action': 'buy',
                'confidence': 0.75,
                'reason': 'Oversold conditions with Bollinger Band support',
                'size_usd': 2000,
                'stop_loss_pct': 3.0,
                'take_profit_pct': 8.0
            })
        
        # Breakout opportunity
        elif (analysis.market_data.price > analysis.technical_indicators.bollinger_upper and
              analysis.trend_direction == 'bullish' and
              analysis.momentum_strength > 0.7):
            
            opportunities.append({
                'action': 'buy',
                'confidence': 0.8,
                'reason': 'Bullish breakout with strong momentum',
                'size_usd': 1500,
                'stop_loss_pct': 2.5,
                'take_profit_pct': 10.0
            })
        
        # Overbought reversal
        elif (analysis.technical_indicators.rsi > 70 and
              analysis.market_data.price >= analysis.technical_indicators.bollinger_upper and
              analysis.market_sentiment == 'greed'):
            
            opportunities.append({
                'action': 'sell',
                'confidence': 0.7,
                'reason': 'Overbought conditions - potential reversal',
                'size_usd': 1000,
                'stop_loss_pct': 2.0,
                'take_profit_pct': 6.0
            })
        
        # Return the highest confidence opportunity
        if opportunities:
            best = max(opportunities, key=lambda x: x['confidence'])
            
            return TradeSignal(
                source=SignalSource.TECHNICAL.value,
                exchange="binance",
                action=best['action'],
                symbol=symbol,
                confidence=best['confidence'],
                size_usd=best['size_usd'],
                entry_price=analysis.market_data.price,
                stop_loss_pct=best['stop_loss_pct'],
                take_profit_pct=best['take_profit_pct'],
                reason=best['reason'],
                timestamp=datetime.now()
            )
        
        return None
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Get market overview for all supported symbols.
        
        Returns:
            Market overview dictionary
        """
        overview = {
            'timestamp': datetime.now().isoformat(),
            'markets': {},
            'summary': {
                'total_symbols': len(self.supported_symbols),
                'bullish_markets': 0,
                'bearish_markets': 0,
                'sideways_markets': 0,
                'high_volume_markets': 0,
                'avg_volatility': 0
            }
        }
        
        volatilities = []
        
        for symbol in self.supported_symbols:
            try:
                analysis = await self.analyze_market(symbol)
                
                if not analysis:
                    continue
                
                overview['markets'][symbol] = {
                    'price': analysis.market_data.price,
                    'change_24h': analysis.market_data.change_24h,
                    'volume_24h': analysis.market_data.volume_24h,
                    'trend': analysis.trend_direction,
                    'momentum': analysis.momentum_strength,
                    'sentiment': analysis.market_sentiment,
                    'risk_level': analysis.risk_level.value
                }
                
                # Update summary
                if analysis.trend_direction == 'bullish':
                    overview['summary']['bullish_markets'] += 1
                elif analysis.trend_direction == 'bearish':
                    overview['summary']['bearish_markets'] += 1
                else:
                    overview['summary']['sideways_markets'] += 1
                
                if analysis.trading_volume == 'high':
                    overview['summary']['high_volume_markets'] += 1
                
                volatilities.append(analysis.market_data.volatility)
                
            except Exception as e:
                logger.error(f"Failed to analyze {symbol} for overview: {e}")
                continue
        
        # Calculate average volatility
        if volatilities:
            overview['summary']['avg_volatility'] = np.mean(volatilities)
        
        return overview
    
    def clear_cache(self):
        """Clear cached market data and indicators"""
        self.market_data_cache.clear()
        self.technical_indicators_cache.clear()
        logger.info("Market data cache cleared")
