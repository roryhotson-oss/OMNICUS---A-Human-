"""
OMNICUS Base Connector
======================
Abstract base class for all exchange connectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class OrderResult:
    """Result of an order execution"""
    success: bool
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[OrderSide] = None
    quantity: Optional[float] = None
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    fee: float = 0.0
    fee_currency: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value if self.side else None,
            "quantity": self.quantity,
            "price": self.price,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "fee": self.fee,
            "fee_currency": self.fee_currency
        }


@dataclass
class Position:
    """Trading position"""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime = field(default_factory=datetime.now)
    
    def update_price(self, current_price: float):
        """Update position with current price"""
        self.current_price = current_price
        
        if self.side == OrderSide.BUY:
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
            self.unrealized_pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:  # SELL/SHORT
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
            self.unrealized_pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100


@dataclass
class MarketData:
    """Market data for a symbol"""
    symbol: str
    price: float
    bid: float = 0.0
    ask: float = 0.0
    volume_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    change_24h: float = 0.0
    change_pct_24h: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "volume_24h": self.volume_24h,
            "high_24h": self.high_24h,
            "low_24h": self.low_24h,
            "change_24h": self.change_24h,
            "change_pct_24h": self.change_pct_24h,
            "timestamp": self.timestamp.isoformat()
        }


class BaseConnector(ABC):
    """
    Abstract base class for all exchange connectors.
    
    All exchange connectors must implement these methods for
    unified trading across multiple platforms.
    """
    
    def __init__(self, name: str, api_key: str = "", api_secret: str = "", **kwargs):
        self.name = name
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_connected = False
        self.session = None
        self._callbacks: Dict[str, List[Callable]] = {}
        
        logger.info(f"Initializing {name} connector")
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the exchange"""
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str = None) -> Dict[str, float]:
        """Get account balance(s)"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get current market data for a symbol"""
        pass
    
    @abstractmethod
    async def get_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        **kwargs
    ) -> OrderResult:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, symbol: str, order_id: str) -> OrderResult:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order(self, symbol: str, order_id: str) -> OrderResult:
        """Get order status"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResult]:
        """Get all open orders"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100
    ) -> List[Dict]:
        """Get candlestick data"""
        pass
    
    # ==================== CONVENIENCE METHODS ====================
    
    async def buy_market(self, symbol: str, quantity: float) -> OrderResult:
        """Place a market buy order"""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
    
    async def sell_market(self, symbol: str, quantity: float) -> OrderResult:
        """Place a market sell order"""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
    
    async def buy_limit(
        self,
        symbol: str,
        quantity: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> OrderResult:
        """Place a limit buy order with optional SL/TP"""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
    
    async def sell_limit(self, symbol: str, quantity: float, price: float) -> OrderResult:
        """Place a limit sell order"""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
    
    # ==================== CALLBACK SYSTEM ====================
    
    def on(self, event: str, callback: Callable):
        """Register a callback for an event"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    async def _emit(self, event: str, data: Any):
        """Emit an event to all registered callbacks"""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Callback error for {event}: {e}")
    
    # ==================== UTILITY METHODS ====================
    
    @staticmethod
    def format_quantity(quantity: float, precision: int = 8) -> float:
        """Format quantity to precision"""
        return round(quantity, precision)
    
    @staticmethod
    def format_price(price: float, precision: int = 8) -> float:
        """Format price to precision"""
        return round(price, precision)
    
    def is_configured(self) -> bool:
        """Check if the connector has valid credentials"""
        return bool(self.api_key and self.api_secret)
