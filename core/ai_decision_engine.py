#!/usr/bin/env python3
"""
AI Decision Engine - Intelligence Module
Advanced AI for trading decisions with multi-factor analysis
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import random

from trading_agent import TradeSignal
from trading_mode import SignalSource, RiskLevel

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MarketIndicators:
    """Technical and fundamental market indicators"""
    rsi: float = 50.0
    macd: float = 0.0
    bollinger_position: float = 0.5
    volume_ratio: float = 1.0
    price_momentum: float = 0.0
    volatility: float = 0.02
    sentiment_score: float = 0.5
    whale_activity: float = 0.0
    support_resistance: float = 0.5


@dataclass
class AISignal:
    """AI-generated trading signal"""
    action: str
    confidence: float
    reasoning: str
    indicators: MarketIndicators
    risk_level: RiskLevel
    expected_return: float
    time_horizon: str
    factors: Dict[str, float]


class AIDecisionEngine:
    """
    Advanced AI decision engine for trading.
    Uses multiple analysis methods:
    - Technical analysis
    - Sentiment analysis  
    - Pattern recognition
    - Risk assessment
    - Machine learning models
    """
    
    def __init__(self):
        self.current_confidence = 0.7
        self.last_analysis_time = datetime.now()
        self.learning_enabled = True
        self.models_initialized = False
        
        # Analysis weights (adjustable)
        self.analysis_weights = {
            'technical': 0.30,
            'sentiment': 0.20,
            'momentum': 0.20,
            'volume': 0.15,
            'whale_activity': 0.10,
            'risk_assessment': 0.05
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            RiskLevel.CONSERVATIVE: 0.85,
            RiskLevel.MODERATE: 0.75,
            RiskLevel.AGGRESSIVE: 0.65,
            RiskLevel.EXTREME: 0.55
        }
        
        self._initialize_models()
        logger.info("AI Decision Engine initialized")
    
    async def evaluate_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        Evaluate an incoming trading signal using AI analysis.
        
        Args:
            signal: TradeSignal to evaluate
            
        Returns:
            Dictionary with decision and reasoning
        """
        logger.info(f"Evaluating signal: {signal.action} {signal.symbol} ({signal.confidence:.2f})")
        
        # Get market data and indicators
        indicators = await self._analyze_market(signal.symbol)
        
        # Multi-factor analysis
        technical_score = self._analyze_technical_indicators(indicators)
        sentiment_score = self._analyze_sentiment(signal.symbol)
        momentum_score = self._analyze_momentum(indicators)
        volume_score = self._analyze_volume(indicators)
        whale_score = self._analyze_whale_activity(signal.symbol)
        risk_score = self._assess_risk(signal, indicators)
        
        # Calculate weighted confidence
        weighted_confidence = (
            technical_score * self.analysis_weights['technical'] +
            sentiment_score * self.analysis_weights['sentiment'] +
            momentum_score * self.analysis_weights['momentum'] +
            volume_score * self.analysis_weights['volume'] +
            whale_score * self.analysis_weights['whale_activity'] +
            risk_score * self.analysis_weights['risk_assessment']
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(indicators, weighted_confidence)
        
        # Make decision
        min_confidence = self.confidence_thresholds[risk_level]
        
        if weighted_confidence >= min_confidence:
            decision = {
                'action': 'execute',
                'confidence': weighted_confidence,
                'risk_level': risk_level.value,
                'reasoning': self._generate_reasoning(
                    technical_score, sentiment_score, momentum_score,
                    volume_score, whale_score, risk_score
                ),
                'indicators': indicators.__dict__,
                'recommendations': self._generate_recommendations(
                    signal, indicators, risk_level
                )
            }
        else:
            decision = {
                'action': 'reject',
                'confidence': weighted_confidence,
                'risk_level': risk_level.value,
                'reasoning': f"Confidence {weighted_confidence:.2f} below threshold {min_confidence:.2f} for {risk_level.value} risk"
            }
        
        self.last_analysis_time = datetime.now()
        self.current_confidence = weighted_confidence
        
        logger.info(f"AI Decision: {decision['action']} (confidence: {weighted_confidence:.2f})")
        
        return decision
    
    async def generate_signal(self, symbol: str, market_data: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        Generate a proactive trading signal using AI analysis.
        
        Args:
            symbol: Trading symbol
            market_data: Current market data
            
        Returns:
            TradeSignal if opportunity detected, None otherwise
        """
        # Analyze market
        indicators = await self._analyze_market(symbol, market_data)
        
        # Look for trading opportunities
        opportunity = await self._identify_opportunity(symbol, indicators)
        
        if opportunity:
            signal = TradeSignal(
                source=SignalSource.AI_ANALYSIS.value,
                exchange="binance",  # Default exchange
                action=opportunity['action'],
                symbol=symbol,
                confidence=opportunity['confidence'],
                size_usd=opportunity['size_usd'],
                entry_price=opportunity.get('entry_price'),
                stop_loss_pct=opportunity.get('stop_loss_pct'),
                take_profit_pct=opportunity.get('take_profit_pct'),
                reason=opportunity['reasoning'],
                timestamp=datetime.now()
            )
            
            logger.info(f"Generated AI signal: {signal.action} {signal.symbol} ({signal.confidence:.2f})")
            return signal
        
        return None
    
    async def _analyze_market(self, symbol: str, market_data: Optional[Dict[str, Any]] = None) -> MarketIndicators:
        """
        Analyze market and calculate technical indicators.
        
        Args:
            symbol: Trading symbol
            market_data: Optional market data
            
        Returns:
            MarketIndicators with calculated values
        """
        # Generate mock indicators for now
        # In production, this would use real market data
        
        indicators = MarketIndicators(
            rsi=50 + random.uniform(-20, 20),
            macd=random.uniform(-2, 2),
            bollinger_position=random.uniform(0, 1),
            volume_ratio=random.uniform(0.5, 2.0),
            price_momentum=random.uniform(-0.1, 0.1),
            volatility=random.uniform(0.01, 0.05),
            sentiment_score=random.uniform(0, 1),
            whale_activity=random.uniform(0, 1),
            support_resistance=random.uniform(0, 1)
        )
        
        return indicators
    
    def _analyze_technical_indicators(self, indicators: MarketIndicators) -> float:
        """Analyze technical indicators and return score (0-1)"""
        score = 0.5  # Base score
        
        # RSI analysis
        if indicators.rsi < 30:  # Oversold
            score += 0.2
        elif indicators.rsi > 70:  # Overbought
            score -= 0.2
        
        # MACD analysis
        if indicators.macd > 0:
            score += 0.1
        else:
            score -= 0.1
        
        # Bollinger Bands
        if indicators.bollinger_position < 0.2:  # Near lower band
            score += 0.15
        elif indicators.bollinger_position > 0.8:  # Near upper band
            score -= 0.15
        
        return max(0, min(1, score))
    
    def _analyze_sentiment(self, symbol: str) -> float:
        """Analyze market sentiment and return score (0-1)"""
        # Mock sentiment analysis
        # In production, this would analyze social media, news, etc.
        base_score = 0.5
        sentiment_factor = random.uniform(-0.3, 0.3)
        
        return max(0, min(1, base_score + sentiment_factor))
    
    def _analyze_momentum(self, indicators: MarketIndicators) -> float:
        """Analyze price momentum and return score (0-1)"""
        momentum_score = 0.5
        
        # Price momentum
        if indicators.price_momentum > 0.05:
            momentum_score += 0.3
        elif indicators.price_momentum < -0.05:
            momentum_score -= 0.3
        
        return max(0, min(1, momentum_score))
    
    def _analyze_volume(self, indicators: MarketIndicators) -> float:
        """Analyze volume patterns and return score (0-1)"""
        volume_score = 0.5
        
        # Volume ratio
        if indicators.volume_ratio > 1.5:  # High volume
            volume_score += 0.25
        elif indicators.volume_ratio < 0.5:  # Low volume
            volume_score -= 0.15
        
        return max(0, min(1, volume_score))
    
    def _analyze_whale_activity(self, symbol: str) -> float:
        """Analyze whale activity and return score (0-1)"""
        # Mock whale activity analysis
        # In production, this would track large transactions
        whale_score = 0.5
        whale_factor = random.uniform(-0.2, 0.2)
        
        return max(0, min(1, whale_score + whale_factor))
    
    def _assess_risk(self, signal: TradeSignal, indicators: MarketIndicators) -> float:
        """Assess risk level and return score (0-1)"""
        risk_score = 0.7  # Base risk score
        
        # Volatility adjustment
        if indicators.volatility > 0.04:  # High volatility
            risk_score -= 0.2
        elif indicators.volatility < 0.01:  # Low volatility
            risk_score += 0.1
        
        # Signal confidence adjustment
        if signal.confidence > 0.9:
            risk_score += 0.1
        elif signal.confidence < 0.7:
            risk_score -= 0.1
        
        return max(0, min(1, risk_score))
    
    def _determine_risk_level(self, indicators: MarketIndicators, confidence: float) -> RiskLevel:
        """Determine risk level based on analysis"""
        if confidence >= 0.85 and indicators.volatility < 0.02:
            return RiskLevel.CONSERVATIVE
        elif confidence >= 0.75 and indicators.volatility < 0.03:
            return RiskLevel.MODERATE
        elif confidence >= 0.65:
            return RiskLevel.AGGRESSIVE
        else:
            return RiskLevel.EXTREME
    
    def _generate_reasoning(self, *scores) -> str:
        """Generate reasoning for the decision"""
        technical, sentiment, momentum, volume, whale, risk = scores
        
        reasoning_parts = []
        
        if technical > 0.7:
            reasoning_parts.append("Strong technical indicators")
        elif technical < 0.3:
            reasoning_parts.append("Weak technical signals")
        
        if sentiment > 0.7:
            reasoning_parts.append("Positive market sentiment")
        elif sentiment < 0.3:
            reasoning_parts.append("Negative market sentiment")
        
        if momentum > 0.7:
            reasoning_parts.append("Strong price momentum")
        
        if volume > 0.7:
            reasoning_parts.append("High volume support")
        
        if risk < 0.5:
            reasoning_parts.append("Moderate risk profile")
        
        return "; ".join(reasoning_parts) if reasoning_parts else "Mixed signals"
    
    def _generate_recommendations(self, signal: TradeSignal, indicators: MarketIndicators, risk_level: RiskLevel) -> List[str]:
        """Generate trading recommendations"""
        recommendations = []
        
        # Position size recommendations
        if risk_level == RiskLevel.CONSERVATIVE:
            recommendations.append("Use smaller position size")
        elif risk_level == RiskLevel.AGGRESSIVE:
            recommendations.append("Can use larger position size")
        
        # Stop loss recommendations
        if indicators.volatility > 0.03:
            recommendations.append("Use wider stop loss due to high volatility")
        
        # Entry timing
        if indicators.rsi < 30:
            recommendations.append("Consider waiting for RSI bounce")
        elif indicators.rsi > 70:
            recommendations.append("Be cautious of overbought conditions")
        
        return recommendations
    
    async def _identify_opportunity(self, symbol: str, indicators: MarketIndicators) -> Optional[Dict[str, Any]]:
        """Identify trading opportunities"""
        # Look for bullish conditions
        if (indicators.rsi < 35 and 
            indicators.macd > -1 and 
            indicators.volume_ratio > 1.2):
            
            return {
                'action': 'buy',
                'confidence': 0.8,
                'size_usd': 2000,
                'entry_price': None,
                'stop_loss_pct': 3.0,
                'take_profit_pct': 8.0,
                'reasoning': "Oversold conditions with positive MACD and high volume"
            }
        
        # Look for bearish conditions
        elif (indicators.rsi > 65 and 
              indicators.macd < 1 and 
              indicators.volume_ratio > 1.2):
            
            return {
                'action': 'sell',
                'confidence': 0.75,
                'size_usd': 1500,
                'entry_price': None,
                'stop_loss_pct': 2.5,
                'take_profit_pct': 6.0,
                'reasoning': "Overbought conditions with negative MACD divergence"
            }
        
        return None
    
    def _initialize_models(self):
        """Initialize machine learning models"""
        try:
            # Placeholder for ML model initialization
            # In production, this would load pre-trained models
            self.models_initialized = True
            logger.info("AI models initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            self.models_initialized = False
    
    def update_weights(self, performance_data: Dict[str, Any]):
        """Update analysis weights based on performance"""
        if not self.learning_enabled:
            return
        
        # Simple adaptive weight adjustment
        # In production, this would use more sophisticated learning
        
        win_rate = performance_data.get('win_rate', 0.5)
        
        if win_rate > 0.6:  # Good performance
            # Increase weights of successful factors
            self.analysis_weights['technical'] *= 1.05
            self.analysis_weights['sentiment'] *= 1.05
        elif win_rate < 0.4:  # Poor performance
            # Decrease weights and redistribute
            self.analysis_weights['technical'] *= 0.95
            self.analysis_weights['sentiment'] *= 0.95
            
            # Increase risk assessment weight
            self.analysis_weights['risk_assessment'] *= 1.1
        
        # Normalize weights
        total_weight = sum(self.analysis_weights.values())
        for key in self.analysis_weights:
            self.analysis_weights[key] /= total_weight
        
        logger.info("AI analysis weights updated based on performance")
