"""
OMNICUS Core Module
===================
Core trading components integrated from user's original code.
"""

from .trading_mode import (
    TradingMode, RiskLevel, SignalSource,
    ExchangeType, OrderType, OrderSide, PositionSide
)
from .trading_agent import AITradingAgent, TradeSignal, Position

# Try to import optional modules
try:
    from .hybrid_system import HybridTradingSystem
except ImportError:
    HybridTradingSystem = None

try:
    from .database_manager import DatabaseManager
except ImportError:
    DatabaseManager = None

try:
    from .ai_decision_engine import AIDecisionEngine
except ImportError:
    AIDecisionEngine = None

try:
    from .binance_api import BinanceAPI
except ImportError:
    BinanceAPI = None

try:
    from .axiom_monitor import AxiomMonitor
except ImportError:
    AxiomMonitor = None

try:
    from .price_engine import PriceEngine
except ImportError:
    PriceEngine = None

__all__ = [
    # Enums
    "TradingMode",
    "RiskLevel", 
    "SignalSource",
    "ExchangeType",
    "OrderType",
    "OrderSide",
    "PositionSide",
    # Core classes
    "AITradingAgent",
    "TradeSignal",
    "Position",
    # Optional imports
    "HybridTradingSystem",
    "DatabaseManager",
    "AIDecisionEngine",
    "BinanceAPI",
    "AxiomMonitor",
    "PriceEngine",
]
