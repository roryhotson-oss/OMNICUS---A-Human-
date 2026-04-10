"""
OMNICUS Binance Connector
=========================
Real-time market data and trading via Binance API.
Supports both REST API and WebSocket streaming.
"""

import asyncio
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp
import websockets


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class Ticker:
    """Market ticker data"""
    symbol: str
    last_price: float
    bid_price: float
    ask_price: float
    high_24h: float
    low_24h: float
    volume_24h: float
    price_change_24h: float
    price_change_percent_24h: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Kline:
    """Candlestick/Kline data"""
    symbol: str
    interval: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: datetime
    quote_volume: float
    trades: int


@dataclass
class Order:
    """Order data"""
    order_id: int
    symbol: str
    side: OrderSide
    type: OrderType
    status: OrderStatus
    price: float
    quantity: float
    filled_quantity: float
    timestamp: datetime


class BinanceConnector:
    """
    Binance API Connector for OMNICUS
    
    Supports:
    - REST API for orders and account data
    - WebSocket for real-time market streaming
    - Testnet for paper trading
    - Signed requests for private endpoints
    """
    
    # API endpoints
    MAINNET_REST = "https://api.binance.com"
    MAINNET_WS = "wss://stream.binance.com:9443/ws"
    TESTNET_REST = "https://testnet.binance.vision"
    TESTNET_WS = "wss://testnet.binance.vision/ws"
    
    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        testnet: bool = True,
        use_proxy: bool = False,
        proxy_url: str = None
    ):
        """
        Initialize Binance connector
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet for paper trading
            use_proxy: Use proxy for requests
            proxy_url: Proxy URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        
        # Set endpoints
        self.rest_url = self.TESTNET_REST if testnet else self.MAINNET_REST
        self.ws_url = self.TESTNET_WS if testnet else self.MAINNET_WS
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        
        # Callbacks for WebSocket data
        self._callbacks: Dict[str, Callable] = {}
        
        # Cache
        self._tickers: Dict[str, Ticker] = {}
        self._klines: Dict[str, List[Kline]] = {}
    
    async def connect(self):
        """Initialize connection"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
    
    async def disconnect(self):
        """Close connections"""
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        signed: bool = False
    ) -> Dict:
        """
        Make REST API request
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request
            
        Returns:
            Response data
        """
        await self.connect()
        
        url = f"{self.rest_url}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        params = params or {}
        
        if signed:
            if not self.api_key or not self.api_secret:
                raise ValueError("API key and secret required for signed requests")
            
            # Add timestamp
            params["timestamp"] = int(time.time() * 1000)
            
            # Create signature
            query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            signature = hmac.new(
                self.api_secret.encode(),
                query_string.encode(),
                hashlib.sha256
            ).hexdigest()
            params["signature"] = signature
        
        try:
            if method == "GET":
                async with self._session.get(url, params=params, headers=headers) as resp:
                    return await resp.json()
            elif method == "POST":
                async with self._session.post(url, data=params, headers=headers) as resp:
                    return await resp.json()
            elif method == "DELETE":
                async with self._session.delete(url, params=params, headers=headers) as resp:
                    return await resp.json()
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================
    # Public Endpoints (No Authentication)
    # ========================================
    
    async def get_exchange_info(self) -> Dict:
        """Get exchange information"""
        return await self._request("GET", "/api/v3/exchangeInfo")
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Get 24hr ticker price change statistics
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            
        Returns:
            Ticker data
        """
        data = await self._request("GET", "/api/v3/ticker/24hr", {"symbol": symbol})
        
        if "error" in data:
            raise Exception(data["error"])
        
        ticker = Ticker(
            symbol=symbol,
            last_price=float(data["lastPrice"]),
            bid_price=float(data["bidPrice"]),
            ask_price=float(data["askPrice"]),
            high_24h=float(data["highPrice"]),
            low_24h=float(data["lowPrice"]),
            volume_24h=float(data["volume"]),
            price_change_24h=float(data["priceChange"]),
            price_change_percent_24h=float(data["priceChangePercent"])
        )
        
        self._tickers[symbol] = ticker
        return ticker
    
    async def get_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        data = await self._request("GET", "/api/v3/ticker/price", {"symbol": symbol})
        
        if "error" in data:
            raise Exception(data["error"])
        
        return float(data["price"])
    
    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100
    ) -> List[Kline]:
        """
        Get candlestick/kline data
        
        Args:
            symbol: Trading pair
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of klines
            
        Returns:
            List of klines
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        data = await self._request("GET", "/api/v3/klines", params)
        
        if "error" in data:
            raise Exception(data["error"])
        
        klines = []
        for k in data:
            klines.append(Kline(
                symbol=symbol,
                interval=interval,
                open_time=datetime.fromtimestamp(k[0] / 1000),
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5]),
                close_time=datetime.fromtimestamp(k[6] / 1000),
                quote_volume=float(k[7]),
                trades=k[8]
            ))
        
        self._klines[f"{symbol}_{interval}"] = klines
        return klines
    
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book depth"""
        return await self._request("GET", "/api/v3/depth", {
            "symbol": symbol,
            "limit": limit
        })
    
    # ========================================
    # Private Endpoints (Authentication Required)
    # ========================================
    
    async def get_account(self) -> Dict:
        """Get account information"""
        return await self._request("GET", "/api/v3/account", signed=True)
    
    async def get_balances(self) -> Dict[str, float]:
        """Get all non-zero balances"""
        account = await self.get_account()
        
        if "error" in account:
            raise Exception(account["error"])
        
        balances = {}
        for b in account.get("balances", []):
            free = float(b["free"])
            locked = float(b["locked"])
            if free > 0 or locked > 0:
                balances[b["asset"]] = {
                    "free": free,
                    "locked": locked,
                    "total": free + locked
                }
        
        return balances
    
    async def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = None,
        stop_price: float = None,
        time_in_force: str = "GTC"
    ) -> Order:
        """
        Create a new order
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            order_type: Order type
            quantity: Order quantity
            price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            
        Returns:
            Order data
        """
        params = {
            "symbol": symbol,
            "side": side.value,
            "type": order_type.value,
            "quantity": quantity,
            "timeInForce": time_in_force
        }
        
        if price:
            params["price"] = price
        
        if stop_price:
            params["stopPrice"] = stop_price
        
        data = await self._request("POST", "/api/v3/order", params, signed=True)
        
        if "error" in data:
            raise Exception(data["error"])
        
        return Order(
            order_id=data["orderId"],
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            type=OrderType(data["type"]),
            status=OrderStatus(data["status"]),
            price=float(data["price"]),
            quantity=float(data["origQty"]),
            filled_quantity=float(data["executedQty"]),
            timestamp=datetime.fromtimestamp(data["transactTime"] / 1000)
        )
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an order"""
        return await self._request("DELETE", "/api/v3/order", {
            "symbol": symbol,
            "orderId": order_id
        }, signed=True)
    
    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders"""
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return await self._request("GET", "/api/v3/openOrders", params, signed=True)
    
    async def get_my_trades(self, symbol: str, limit: int = 50) -> List[Dict]:
        """Get trade history"""
        return await self._request("GET", "/api/v3/myTrades", {
            "symbol": symbol,
            "limit": limit
        }, signed=True)
    
    # ========================================
    # WebSocket Streaming
    # ========================================
    
    async def subscribe_ticker(self, symbol: str, callback: Callable):
        """Subscribe to ticker updates"""
        stream = f"{symbol.lower()}@ticker"
        await self._subscribe(stream, callback)
    
    async def subscribe_klines(
        self,
        symbol: str,
        interval: str,
        callback: Callable
    ):
        """Subscribe to kline updates"""
        stream = f"{symbol.lower()}@kline_{interval}"
        await self._subscribe(stream, callback)
    
    async def subscribe_depth(self, symbol: str, callback: Callable):
        """Subscribe to order book updates"""
        stream = f"{symbol.lower()}@depth"
        await self._subscribe(stream, callback)
    
    async def _subscribe(self, stream: str, callback: Callable):
        """Subscribe to a WebSocket stream"""
        self._callbacks[stream] = callback
        
        if self._ws is None:
            await self._connect_ws()
        
        # Subscribe to stream
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [stream],
            "id": int(time.time() * 1000)
        }
        
        await self._ws.send(json.dumps(subscribe_msg))
    
    async def _connect_ws(self):
        """Connect to WebSocket"""
        self._ws = await websockets.connect(self.ws_url)
        asyncio.create_task(self._ws_handler())
    
    async def _ws_handler(self):
        """Handle WebSocket messages"""
        try:
            async for message in self._ws:
                data = json.loads(message)
                
                # Find callback for this stream
                stream = data.get("stream", "")
                if stream in self._callbacks:
                    await self._callbacks[stream](data)
        except Exception as e:
            print(f"WebSocket error: {e}")
            self._ws = None
    
    # ========================================
    # Convenience Methods
    # ========================================
    
    async def market_buy(self, symbol: str, quantity: float) -> Order:
        """Execute market buy order"""
        return await self.create_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
    
    async def market_sell(self, symbol: str, quantity: float) -> Order:
        """Execute market sell order"""
        return await self.create_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity
        )
    
    async def limit_buy(
        self,
        symbol: str,
        quantity: float,
        price: float
    ) -> Order:
        """Execute limit buy order"""
        return await self.create_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
    
    async def limit_sell(
        self,
        symbol: str,
        quantity: float,
        price: float
    ) -> Order:
        """Execute limit sell order"""
        return await self.create_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price
        )
    
    async def set_stop_loss(
        self,
        symbol: str,
        quantity: float,
        stop_price: float,
        limit_price: float = None
    ) -> Order:
        """Set stop loss order"""
        order_type = OrderType.STOP_LOSS_LIMIT if limit_price else OrderType.STOP_LOSS
        
        return await self.create_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=order_type,
            quantity=quantity,
            price=limit_price,
            stop_price=stop_price
        )


# ========================================
# Example Usage
# ========================================

async def main():
    """Example usage of Binance connector"""
    
    # Initialize connector (testnet for paper trading)
    connector = BinanceConnector(testnet=True)
    
    try:
        # Get ticker
        ticker = await connector.get_ticker("BTCUSDT")
        print(f"BTC/USDT: ${ticker.last_price:.2f}")
        print(f"24h Change: {ticker.price_change_percent_24h:.2f}%")
        
        # Get klines
        klines = await connector.get_klines("BTCUSDT", "1h", 24)
        print(f"\nLast 24 hours:")
        for k in klines[-5:]:
            print(f"  {k.open_time}: O:{k.open} H:{k.high} L:{k.low} C:{k.close}")
        
        # Calculate simple moving average
        closes = [k.close for k in klines]
        sma = sum(closes) / len(closes)
        print(f"\nSMA(24): ${sma:.2f}")
        
    finally:
        await connector.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
