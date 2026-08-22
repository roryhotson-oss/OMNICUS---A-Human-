"""
OMNICUS Binance Connector
=========================
Integration with Binance exchange for crypto trading.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from functools import wraps

from .base import (
    BaseConnector, OrderResult, OrderSide, OrderType, 
    OrderStatus, Position, MarketData
)

logger = logging.getLogger(__name__)


# Rate limiting configuration
BINANCE_RATE_LIMIT = 1200  # requests per minute
BINANCE_BURST_LIMIT = 10  # requests per second burst

_request_data = {'count': 0, 'last_time': 0.0}
_rate_lock = None


def rate_limited(max_per_minute: int = BINANCE_RATE_LIMIT, max_per_second: int = BINANCE_BURST_LIMIT):
    """Decorator for rate limiting API calls."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            global _request_data, _rate_lock
            
            if _rate_lock is None:
                _rate_lock = asyncio.Lock()
            
            async with _rate_lock:
                current_time = time.time()
                
                # Reset counter if minute has passed
                if current_time - _request_data['last_time'] > 60:
                    _request_data['count'] = 0
                    _request_data['last_time'] = current_time
                
                # Check rate limits
                if _request_data['count'] >= max_per_minute:
                    wait_time = 60 - (current_time - _request_data['last_time'])
                    logger.warning(f"Rate limit reached. Waiting {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time + 0.1)
                    _request_data['count'] = 0
                    _request_data['last_time'] = time.time()
                
                # Check burst limit
                if _request_data['count'] >= max_per_second:
                    await asyncio.sleep(0.1)
                
                _request_data['count'] += 1
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class BinanceConnector(BaseConnector):
    """
    Binance exchange connector for crypto trading.
    Supports spot and futures trading with testnet option.
    """
    
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = True,
        **kwargs
    ):
        super().__init__(
            name="Binance",
            api_key=api_key,
            api_secret=api_secret,
            **kwargs
        )
        self.testnet = testnet
        self.base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        self.ws_url = "wss://testnet.binance.vision/ws" if testnet else "wss://stream.binance.com/ws"
        
        self._session = None
        self._ws = None
        self._last_prices: Dict[str, float] = {}
        
    async def connect(self) -> bool:
        """Connect to Binance API"""
        try:
            import aiohttp
            
            self._session = aiohttp.ClientSession()
            
            # Test connectivity
            async with self._session.get(f"{self.base_url}/api/v3/ping") as resp:
                if resp.status == 200:
                    self.is_connected = True
                    logger.info(f"✅ Connected to Binance ({'testnet' if self.testnet else 'mainnet'})")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            
        self.is_connected = False
        return False
    
    async def disconnect(self) -> None:
        """Disconnect from Binance"""
        if self._session:
            await self._session.close()
            self._session = None
        
        self.is_connected = False
        logger.info("Disconnected from Binance")
    
    @rate_limited()
    async def _request(
        self,
        method: str,
        endpoint: str,
        signed: bool = False,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to Binance API with rate limiting"""
        import aiohttp
        import hashlib
        import hmac
        import time
        from urllib.parse import urlencode
        
        if params is None:
            params = {}
        if data is None:
            data = {}
            
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        if signed:
            if not self.api_key or not self.api_secret:
                raise ValueError("API credentials required for signed requests")
            
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            
            query_string = urlencode(params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params["signature"] = signature
        
        try:
            async with self._session.request(
                method=method,
                url=url,
                params=params if method == "GET" else None,
                json=data if method in ["POST", "PUT", "DELETE"] else None,
                headers=headers
            ) as resp:
                result = await resp.json()
                
                if resp.status != 200:
                    raise Exception(f"API Error {resp.status}: {result.get('msg', result)}")
                
                return result
                
        except Exception as e:
            logger.error(f"Binance API request failed: {e}")
            raise
    
    async def get_balance(self, asset: str = None) -> Dict[str, float]:
        """Get account balance"""
        if not self.is_connected:
            await self.connect()
        
        try:
            account = await self._request("GET", "/api/v3/account", signed=True)
            
            balances = {}
            for bal in account.get("balances", []):
                free = float(bal["free"])
                locked = float(bal["locked"])
                
                if free > 0 or locked > 0:
                    total = free + locked
                    if asset is None or bal["asset"] == asset:
                        balances[bal["asset"]] = {
                            "free": free,
                            "locked": locked,
                            "total": total
                        }
            
            if asset:
                return balances.get(asset, {"free": 0, "locked": 0, "total": 0})
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
    
    async def get_market_data(self, symbol: str) -> MarketData:
        """Get market data for symbol"""
        if not self.is_connected:
            await self.connect()
        
        try:
            ticker = await self._request(
                "GET",
                "/api/v3/ticker/24hr",
                params={"symbol": symbol.upper()}
            )
            
            return MarketData(
                symbol=symbol.upper(),
                price=float(ticker.get("lastPrice", 0)),
                bid=float(ticker.get("bidPrice", 0)),
                ask=float(ticker.get("askPrice", 0)),
                volume_24h=float(ticker.get("volume", 0)),
                high_24h=float(ticker.get("highPrice", 0)),
                low_24h=float(ticker.get("lowPrice", 0)),
                change_24h=float(ticker.get("priceChange", 0)),
                change_pct_24h=float(ticker.get("priceChangePercent", 0)),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return MarketData(symbol=symbol.upper(), price=0)
    
    async def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            ticker = await self._request(
                "GET",
                "/api/v3/ticker/price",
                params={"symbol": symbol.upper()}
            )
            
            price = float(ticker.get("price", 0))
            self._last_prices[symbol.upper()] = price
            return price
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return self._last_prices.get(symbol.upper(), 0)
    
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
        """Place an order on Binance"""
        if not self.is_connected:
            await self.connect()
        
        try:
            params = {
                "symbol": symbol.upper(),
                "side": side.value.upper(),
                "type": order_type.value.upper(),
                "quantity": quantity
            }
            
            # Add price for limit orders
            if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
                if price is None:
                    raise ValueError("Price required for limit orders")
                params["price"] = price
                params["timeInForce"] = "GTC"
            
            # Add stop price for stop orders
            if order_type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT]:
                if stop_price is None:
                    raise ValueError("Stop price required for stop orders")
                params["stopPrice"] = stop_price
            
            # Add optional parameters
            if "time_in_force" in kwargs:
                params["timeInForce"] = kwargs["time_in_force"]
            if "stop_loss" in kwargs:
                params["stopLoss"] = kwargs["stop_loss"]
            if "take_profit" in kwargs:
                params["takeProfit"] = kwargs["take_profit"]
            
            result = await self._request("POST", "/api/v3/order", signed=True, data=params)
            
            return OrderResult(
                success=True,
                order_id=str(result.get("orderId")),
                symbol=symbol,
                side=side,
                quantity=float(result.get("executedQty", quantity)),
                price=float(result.get("price", price or 0)),
                status=OrderStatus.OPEN,
                message=f"Order placed successfully",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                status=OrderStatus.REJECTED,
                message=str(e)
            )
    
    async def cancel_order(self, symbol: str, order_id: str) -> OrderResult:
        """Cancel an order"""
        if not self.is_connected:
            await self.connect()
        
        try:
            result = await self._request(
                "DELETE",
                "/api/v3/order",
                signed=True,
                data={"symbol": symbol.upper(), "orderId": int(order_id)}
            )
            
            return OrderResult(
                success=True,
                order_id=order_id,
                symbol=symbol,
                status=OrderStatus.CANCELLED,
                message="Order cancelled successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            return OrderResult(
                success=False,
                order_id=order_id,
                symbol=symbol,
                status=OrderStatus.REJECTED,
                message=str(e)
            )
    
    async def get_order(self, symbol: str, order_id: str) -> OrderResult:
        """Get order status"""
        if not self.is_connected:
            await self.connect()
        
        try:
            result = await self._request(
                "GET",
                "/api/v3/order",
                signed=True,
                params={"symbol": symbol.upper(), "orderId": int(order_id)}
            )
            
            status_map = {
                "NEW": OrderStatus.OPEN,
                "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
                "FILLED": OrderStatus.FILLED,
                "CANCELED": OrderStatus.CANCELLED,
                "REJECTED": OrderStatus.REJECTED,
                "EXPIRED": OrderStatus.CANCELLED
            }
            
            return OrderResult(
                success=True,
                order_id=order_id,
                symbol=symbol,
                side=OrderSide.BUY if result.get("side") == "BUY" else OrderSide.SELL,
                quantity=float(result.get("origQty", 0)),
                price=float(result.get("price", 0)),
                status=status_map.get(result.get("status"), OrderStatus.PENDING),
                message=result.get("status", "")
            )
            
        except Exception as e:
            logger.error(f"Failed to get order: {e}")
            return OrderResult(
                success=False,
                order_id=order_id,
                symbol=symbol,
                status=OrderStatus.REJECTED,
                message=str(e)
            )
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[OrderResult]:
        """Get all open orders"""
        if not self.is_connected:
            await self.connect()
        
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol.upper()
            
            orders = await self._request(
                "GET",
                "/api/v3/openOrders",
                signed=True,
                params=params
            )
            
            results = []
            for order in orders:
                results.append(OrderResult(
                    success=True,
                    order_id=str(order.get("orderId")),
                    symbol=order.get("symbol"),
                    side=OrderSide.BUY if order.get("side") == "BUY" else OrderSide.SELL,
                    quantity=float(order.get("origQty", 0)),
                    price=float(order.get("price", 0)),
                    status=OrderStatus.OPEN,
                    message=order.get("type", "")
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []
    
    async def get_positions(self) -> List[Position]:
        """Get open positions (for spot, this returns holdings)"""
        balances = await self.get_balance()
        positions = []
        
        for asset, data in balances.items():
            if data["total"] > 0 and asset not in ["USDT", "USDC", "BUSD", "USD"]:
                # Try to get current price
                try:
                    price = await self.get_price(f"{asset}USDT")
                    if price > 0:
                        positions.append(Position(
                            symbol=f"{asset}USDT",
                            side=OrderSide.BUY,
                            quantity=data["total"],
                            entry_price=price,  # Would need trade history for actual entry
                            current_price=price
                        ))
                except:
                    pass
        
        return positions
    
    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100
    ) -> List[Dict]:
        """Get candlestick data"""
        if not self.is_connected:
            await self.connect()
        
        try:
            result = await self._request(
                "GET",
                "/api/v3/klines",
                params={
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "limit": limit
                }
            )
            
            candles = []
            for k in result:
                candles.append({
                    "timestamp": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                })
            
            return candles
            
        except Exception as e:
            logger.error(f"Failed to get klines: {e}")
            return []
    
    async def get_exchange_info(self) -> Dict:
        """Get exchange information"""
        try:
            return await self._request("GET", "/api/v3/exchangeInfo")
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            return {}
