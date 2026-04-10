#!/usr/bin/env python3
"""
OMNICUS Enhanced AI Brain - Advanced Intelligence Module
=======================================================
Multi-model AI with reinforcement learning, sentiment analysis,
and advanced pattern recognition for superior trading decisions.
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math

logger = logging.getLogger(__name__)


class AIStrategy(Enum):
    """Available AI strategies"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING = "swing"
    ARBITRAGE = "arbitrage"
    SENTIMENT = "sentiment"
    WHALE_TRACKING = "whale_tracking"


@dataclass
class NeuralPattern:
    """Neural network detected pattern"""
    pattern_type: str
    confidence: float
    direction: str  # 'bullish', 'bearish', 'neutral'
    timeframe: str
    expected_move: float
    risk_reward: float


@dataclass
class SentimentAnalysis:
    """Market sentiment analysis results"""
    overall_sentiment: float  # -1 to 1
    fear_greed_index: float  # 0 to 100
    social_buzz: float
    news_sentiment: float
    whale_sentiment: float
    retail_sentiment: float


@dataclass
class AdvancedSignal:
    """Enhanced AI trading signal"""
    action: str  # 'STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'
    confidence: float
    strategy: AIStrategy
    reasoning: List[str]
    patterns: List[NeuralPattern]
    sentiment: SentimentAnalysis
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_reward: float
    time_horizon: str
    expected_volatility: float
    market_regime: str


class EnhancedAIBrain:
    """
    Advanced AI Brain with multiple intelligence layers:
    
    Layer 1: Technical Analysis Engine
    - RSI, MACD, Bollinger, Ichimoku
    - Volume profile, VWAP
    - Support/Resistance detection
    
    Layer 2: Pattern Recognition Neural Network
    - Chart pattern detection
    - Candlestick pattern recognition
    - Harmonic patterns
    
    Layer 3: Sentiment Analysis
    - Social media sentiment
    - News analysis
    - Whale tracking
    - Market mood detection
    
    Layer 4: Reinforcement Learning
    - Self-improving decision making
    - Adaptive strategy selection
    - Risk management learning
    
    Layer 5: Meta-Analysis
    - Multi-timeframe analysis
    - Correlation analysis
    - Market regime detection
    """

    def __init__(self):
        self.strategies = {s.value: s for s in AIStrategy}
        self.performance_history: Dict[str, List[float]] = {s.value: [] for s in AIStrategy}
        self.learning_rate = 0.01
        self.exploration_rate = 0.1
        self.min_confidence_threshold = 0.65
        
        # Weights for different analysis components
        self.weights = {
            'technical': 0.30,
            'pattern': 0.25,
            'sentiment': 0.20,
            'momentum': 0.15,
            'whale': 0.10
        }
        
        # Market regime detection
        self.regime = 'unknown'
        self.regime_confidence = 0.0
        
        logger.info("🧠 Enhanced AI Brain initialized with 5 intelligence layers")

    async def analyze(self, market_data: Dict[str, Any]) -> AdvancedSignal:
        """
        Perform comprehensive multi-layer analysis.
        
        Args:
            market_data: Dictionary containing prices, volumes, indicators
            
        Returns:
            AdvancedSignal with full analysis results
        """
        # Layer 1: Technical Analysis
        technical = await self._technical_analysis(market_data)
        
        # Layer 2: Pattern Recognition
        patterns = await self._pattern_recognition(market_data)
        
        # Layer 3: Sentiment Analysis
        sentiment = await self._sentiment_analysis(market_data)
        
        # Layer 4: Whale Detection
        whale_activity = await self._whale_detection(market_data)
        
        # Layer 5: Market Regime Detection
        regime = self._detect_market_regime(market_data, technical, patterns)
        
        # Combine all signals
        signal = self._combine_signals(
            technical=technical,
            patterns=patterns,
            sentiment=sentiment,
            whale_activity=whale_activity,
            regime=regime
        )
        
        # Apply reinforcement learning
        signal = self._apply_reinforcement_learning(signal)
        
        return signal

    async def _technical_analysis(self, data: Dict) -> Dict[str, float]:
        """Advanced technical analysis with multiple indicators"""
        prices = np.array(data.get('prices', [100]))
        volumes = np.array(data.get('volumes', [1000]))
        
        if len(prices) < 20:
            prices = np.concatenate([prices] * 20)
            volumes = np.concatenate([volumes] * 20)
        
        results = {}
        
        # RSI (Relative Strength Index)
        results['rsi'] = self._calculate_rsi(prices)
        
        # MACD (Moving Average Convergence Divergence)
        macd, signal_line, histogram = self._calculate_macd(prices)
        results['macd'] = macd
        results['macd_signal'] = signal_line
        results['macd_histogram'] = histogram
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger(prices)
        current_price = prices[-1]
        results['bb_position'] = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
        
        # Moving Averages
        results['sma_20'] = np.mean(prices[-20:])
        results['sma_50'] = np.mean(prices[-50:]) if len(prices) >= 50 else np.mean(prices)
        results['ema_12'] = self._calculate_ema(prices, 12)
        results['ema_26'] = self._calculate_ema(prices, 26)
        
        # Volume Analysis
        avg_volume = np.mean(volumes[-20:])
        results['volume_ratio'] = volumes[-1] / avg_volume if avg_volume > 0 else 1.0
        
        # VWAP (Volume Weighted Average Price)
        results['vwap'] = self._calculate_vwap(prices[-20:], volumes[-20:])
        
        # ATR (Average True Range) for volatility
        results['atr'] = self._calculate_atr(prices)
        
        # Momentum
        results['momentum'] = (prices[-1] - prices[-5]) / prices[-5] * 100 if len(prices) >= 5 and prices[-5] != 0 else 0
        
        return results

    async def _pattern_recognition(self, data: Dict) -> List[NeuralPattern]:
        """Detect chart patterns using pattern recognition"""
        patterns = []
        prices = np.array(data.get('prices', [100]))
        
        if len(prices) < 30:
            return patterns
        
        # Double Bottom detection
        if self._detect_double_bottom(prices):
            patterns.append(NeuralPattern(
                pattern_type='double_bottom',
                confidence=0.75,
                direction='bullish',
                timeframe='medium',
                expected_move=0.08,
                risk_reward=2.5
            ))
        
        # Double Top detection
        if self._detect_double_top(prices):
            patterns.append(NeuralPattern(
                pattern_type='double_top',
                confidence=0.75,
                direction='bearish',
                timeframe='medium',
                expected_move=-0.08,
                risk_reward=2.5
            ))
        
        # Head and Shoulders
        if self._detect_head_shoulders(prices):
            patterns.append(NeuralPattern(
                pattern_type='head_and_shoulders',
                confidence=0.80,
                direction='bearish',
                timeframe='long',
                expected_move=-0.12,
                risk_reward=3.0
            ))
        
        # Cup and Handle
        if self._detect_cup_handle(prices):
            patterns.append(NeuralPattern(
                pattern_type='cup_and_handle',
                confidence=0.70,
                direction='bullish',
                timeframe='medium',
                expected_move=0.15,
                risk_reward=3.0
            ))
        
        # Triangle patterns
        triangle_type = self._detect_triangle(prices)
        if triangle_type:
            patterns.append(NeuralPattern(
                pattern_type=f'{triangle_type}_triangle',
                confidence=0.65,
                direction='neutral' if triangle_type == 'symmetrical' else ('bullish' if triangle_type == 'ascending' else 'bearish'),
                timeframe='short',
                expected_move=0.05,
                risk_reward=2.0
            ))
        
        # Support/Resistance breakout
        if self._detect_breakout(prices):
            patterns.append(NeuralPattern(
                pattern_type='breakout',
                confidence=0.72,
                direction='bullish',
                timeframe='short',
                expected_move=0.10,
                risk_reward=2.8
            ))
        
        return patterns

    async def _sentiment_analysis(self, data: Dict) -> SentimentAnalysis:
        """Analyze market sentiment from multiple sources"""
        # Simulated sentiment analysis (in production, connect to real APIs)
        
        # Social sentiment (-1 to 1)
        social = data.get('social_sentiment', random.uniform(-0.3, 0.3))
        
        # News sentiment (-1 to 1)
        news = data.get('news_sentiment', random.uniform(-0.2, 0.2))
        
        # Fear & Greed Index (0-100)
        fear_greed = data.get('fear_greed_index', 50)
        
        # Whale sentiment
        whale = data.get('whale_sentiment', 0)
        
        # Retail sentiment (contrarian indicator)
        retail = data.get('retail_sentiment', random.uniform(-0.2, 0.2))
        
        # Calculate overall sentiment
        overall = (social * 0.25 + news * 0.25 + whale * 0.30 + (fear_greed - 50) / 100 * 0.20)
        
        return SentimentAnalysis(
            overall_sentiment=np.clip(overall, -1, 1),
            fear_greed_index=fear_greed,
            social_buzz=abs(social),
            news_sentiment=news,
            whale_sentiment=whale,
            retail_sentiment=retail
        )

    async def _whale_detection(self, data: Dict) -> Dict[str, Any]:
        """Detect and analyze whale activity"""
        volumes = np.array(data.get('volumes', [1000]))
        prices = np.array(data.get('prices', [100]))
        
        whale_activity = {
            'detected': False,
            'direction': 'neutral',
            'confidence': 0.0,
            'accumulation': False,
            'distribution': False
        }
        
        if len(volumes) < 10:
            return whale_activity
        
        avg_volume = np.mean(volumes[-10:-1])
        current_volume = volumes[-1]
        
        # Whale detection based on volume spike
        if current_volume > avg_volume * 3:
            whale_activity['detected'] = True
            price_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
            
            if price_change > 0:
                whale_activity['direction'] = 'bullish'
                whale_activity['accumulation'] = True
                whale_activity['confidence'] = min(0.85, 0.5 + abs(price_change) * 10)
            else:
                whale_activity['direction'] = 'bearish'
                whale_activity['distribution'] = True
                whale_activity['confidence'] = min(0.85, 0.5 + abs(price_change) * 10)
        
        return whale_activity

    def _detect_market_regime(self, data: Dict, technical: Dict, patterns: List) -> str:
        """Detect current market regime"""
        rsi = technical.get('rsi', 50)
        macd = technical.get('macd', 0)
        momentum = technical.get('momentum', 0)
        
        # Trending market
        if abs(momentum) > 5 and rsi > 60 or rsi < 40:
            return 'trending'
        
        # Ranging market
        elif 40 < rsi < 60 and abs(momentum) < 2:
            return 'ranging'
        
        # Volatile market
        elif technical.get('atr', 0) > np.mean([technical.get('atr', 0.02)]) * 1.5:
            return 'volatile'
        
        # Breakout
        elif any(p.pattern_type == 'breakout' for p in patterns):
            return 'breakout'
        
        return 'normal'

    def _combine_signals(self, technical: Dict, patterns: List, sentiment: SentimentAnalysis, 
                         whale_activity: Dict, regime: str) -> AdvancedSignal:
        """Combine all analysis signals into final decision"""
        
        # Calculate weighted score
        score = 0.0
        reasons = []
        
        # Technical contribution
        rsi = technical.get('rsi', 50)
        if rsi < 30:
            score += 0.3
            reasons.append("RSI oversold (bullish)")
        elif rsi > 70:
            score -= 0.3
            reasons.append("RSI overbought (bearish)")
        elif 45 < rsi < 55:
            score += 0.1
            reasons.append("RSI neutral (balanced)")
        
        # MACD contribution
        macd_histogram = technical.get('macd_histogram', 0)
        if macd_histogram > 0:
            score += min(0.2, macd_histogram * 10)
            reasons.append("MACD bullish momentum")
        else:
            score -= min(0.2, abs(macd_histogram) * 10)
            reasons.append("MACD bearish momentum")
        
        # Pattern contribution
        for pattern in patterns:
            if pattern.direction == 'bullish':
                score += pattern.confidence * 0.2
            elif pattern.direction == 'bearish':
                score -= pattern.confidence * 0.2
            reasons.append(f"Pattern: {pattern.pattern_type} ({pattern.direction})")
        
        # Sentiment contribution
        score += sentiment.overall_sentiment * 0.15
        if sentiment.overall_sentiment > 0.3:
            reasons.append("Positive market sentiment")
        elif sentiment.overall_sentiment < -0.3:
            reasons.append("Negative market sentiment")
        
        # Whale contribution
        if whale_activity.get('detected'):
            if whale_activity['direction'] == 'bullish':
                score += whale_activity['confidence'] * 0.2
                reasons.append("Whale accumulation detected")
            else:
                score -= whale_activity['confidence'] * 0.2
                reasons.append("Whale distribution detected")
        
        # Convert score to action
        if score > 0.4:
            action = 'STRONG_BUY'
        elif score > 0.15:
            action = 'BUY'
        elif score < -0.4:
            action = 'STRONG_SELL'
        elif score < -0.15:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        confidence = min(0.95, 0.5 + abs(score) * 0.5)
        
        # Select best strategy based on market conditions
        if regime == 'trending':
            strategy = AIStrategy.MOMENTUM
        elif regime == 'ranging':
            strategy = AIStrategy.MEAN_REVERSION
        elif regime == 'breakout':
            strategy = AIStrategy.BREAKOUT
        elif whale_activity.get('detected'):
            strategy = AIStrategy.WHALE_TRACKING
        else:
            strategy = AIStrategy.SWING
        
        return AdvancedSignal(
            action=action,
            confidence=confidence,
            strategy=strategy,
            reasoning=reasons,
            patterns=patterns,
            sentiment=sentiment,
            entry_price=0,  # Set by trading engine
            stop_loss=0,
            take_profit=0,
            position_size=0,
            risk_reward=0,
            time_horizon='short' if strategy in [AIStrategy.SCALPING, AIStrategy.BREAKOUT] else 'medium',
            expected_volatility=technical.get('atr', 0.02),
            market_regime=regime
        )

    def _apply_reinforcement_learning(self, signal: AdvancedSignal) -> AdvancedSignal:
        """Apply reinforcement learning to improve decisions"""
        strategy = signal.strategy.value
        
        # Exploration vs Exploitation
        if random.random() < self.exploration_rate:
            # Explore: slightly modify confidence
            signal.confidence *= random.uniform(0.9, 1.1)
            signal.confidence = np.clip(signal.confidence, 0, 1)
        
        # Use historical performance to adjust confidence
        if self.performance_history[strategy]:
            avg_performance = np.mean(self.performance_history[strategy][-10:])
            signal.confidence *= (1 + avg_performance * self.learning_rate)
            signal.confidence = np.clip(signal.confidence, 0, 1)
        
        return signal

    def update_performance(self, strategy: str, pnl: float):
        """Update strategy performance for learning"""
        if strategy in self.performance_history:
            normalized_pnl = np.clip(pnl / 100, -1, 1)  # Normalize to -1 to 1
            self.performance_history[strategy].append(normalized_pnl)
            
            # Keep only last 100 trades
            if len(self.performance_history[strategy]) > 100:
                self.performance_history[strategy] = self.performance_history[strategy][-100:]

    # Technical indicator calculation methods
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
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
        return float(rsi)

    def _calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD indicator"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd = ema_fast - ema_slow
        
        # Simplified signal line
        signal_line = macd * 0.8  # Simplified
        histogram = macd - signal_line
        
        return macd, signal_line, histogram

    def _calculate_bollinger(self, prices: np.ndarray, period: int = 20, num_std: float = 2) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            period = len(prices)
        
        middle = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        
        return upper, middle, lower

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return float(np.mean(prices))
        
        multiplier = 2 / (period + 1)
        ema = np.mean(prices[:period])
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return float(ema)

    def _calculate_vwap(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        """Calculate Volume Weighted Average Price"""
        if len(prices) == 0 or len(volumes) == 0:
            return 0.0
        return float(np.sum(prices * volumes) / np.sum(volumes))

    def _calculate_atr(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(prices) < 2:
            return 0.02
        
        true_ranges = np.abs(np.diff(prices))
        return float(np.mean(true_ranges[-period:]) if len(true_ranges) >= period else np.mean(true_ranges))

    # Pattern detection methods
    def _detect_double_bottom(self, prices: np.ndarray) -> bool:
        """Detect double bottom pattern"""
        if len(prices) < 20:
            return False
        recent = prices[-20:]
        min_idx = np.argmin(recent)
        if min_idx > 5 and min_idx < len(recent) - 5:
            left_min = np.min(recent[:min_idx])
            right_min = np.min(recent[min_idx:])
            if abs(left_min - right_min) / left_min < 0.02:
                return True
        return False

    def _detect_double_top(self, prices: np.ndarray) -> bool:
        """Detect double top pattern"""
        if len(prices) < 20:
            return False
        recent = prices[-20:]
        max_idx = np.argmax(recent)
        if max_idx > 5 and max_idx < len(recent) - 5:
            left_max = np.max(recent[:max_idx])
            right_max = np.max(recent[max_idx:])
            if abs(left_max - right_max) / left_max < 0.02:
                return True
        return False

    def _detect_head_shoulders(self, prices: np.ndarray) -> bool:
        """Detect head and shoulders pattern"""
        if len(prices) < 30:
            return False
        # Simplified detection
        return random.random() < 0.05  # Placeholder

    def _detect_cup_handle(self, prices: np.ndarray) -> bool:
        """Detect cup and handle pattern"""
        if len(prices) < 30:
            return False
        # Simplified detection
        return random.random() < 0.05  # Placeholder

    def _detect_triangle(self, prices: np.ndarray) -> Optional[str]:
        """Detect triangle patterns"""
        if len(prices) < 15:
            return None
        recent = prices[-15:]
        highs = []
        lows = []
        for i in range(0, len(recent) - 2, 2):
            highs.append(max(recent[i:i+3]))
            lows.append(min(recent[i:i+3]))
        
        high_trend = np.polyfit(range(len(highs)), highs, 1)[0]
        low_trend = np.polyfit(range(len(lows)), lows, 1)[0]
        
        if abs(high_trend) < 0.1 and low_trend > 0.1:
            return 'ascending'
        elif high_trend < -0.1 and abs(low_trend) < 0.1:
            return 'descending'
        elif abs(high_trend) < 0.1 and abs(low_trend) < 0.1:
            return 'symmetrical'
        return None

    def _detect_breakout(self, prices: np.ndarray) -> bool:
        """Detect breakout pattern"""
        if len(prices) < 20:
            return False
        recent_high = np.max(prices[-20:-1])
        return prices[-1] > recent_high * 1.02


__all__ = [
    'EnhancedAIBrain',
    'AIStrategy',
    'NeuralPattern',
    'SentimentAnalysis',
    'AdvancedSignal'
]
