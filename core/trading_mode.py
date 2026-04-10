#!/usr/bin/env python3
"""
Trading Mode Enums
Defines different trading modes for the AI system
"""

from enum import Enum


class TradingMode(Enum):
    """Trading modes for the system"""
    SIMULATION = "simulation"
    PAPER_API = "paper_api"
    TESTNET = "testnet"
    MAINNET = "mainnet"


class ExchangeType(Enum):
    """Exchange types"""
    CRYPTO = "crypto"
    PREDICTION = "prediction"
    TOKEN_SCANNER = "token_scanner"


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Order sides"""
    BUY = "buy"
    SELL = "sell"


class PositionSide(Enum):
    """Position sides"""
    LONG = "long"
    SHORT = "short"


class SignalSource(Enum):
    """Signal sources for trading decisions"""
    AI_ANALYSIS = "ai_analysis"
    AXIOM_SCANNER = "axiom_scanner"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"


class RiskLevel(Enum):
    """Risk levels for trading"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"
