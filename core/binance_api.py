#!/usr/bin/env python3
"""
Binance API Integration
Complete Binance exchange integration for trading system
"""

import asyncio
import aiohttp
import hashlib
import hmac
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)


class BinanceAPI:
    """
    Binance API client for spot and futures trading.
    Supports:
    - Account management
    - Market data
    - Order management
    - WebSocket streaming
    """
    
    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        base_url: str = "https://api.binance.com",
        testnet: bool = True,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.testnet = testnet
        self.timeout = timeout
        
        # Adjust URL for testnet
        if testnet:
            self.base_url = "https://testnet.binance.vision"
        
        self.session = None
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms between requests
        
        logger.info(f"Binance API initialized (testnet: {testnet})")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for API requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    async def _rate_limit(self):
        """Apply rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        signed: bool = False,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            signed: Whether request requires signature
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary
        """
        await self._rate_limit()
        
        if params is None:
            params = {}
        
        if data is None:
            data = {}
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        # Add API key if available
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        # Add signature for signed requests
        if signed:
            if not self.api_key or not self.api_secret:
                raise ValueError("API keys required for signed requests")
            
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 5000
            params["signature"] = self._generate_signature(params)
        
        session = await self._get_session()
        
        try:
            async with session.request(
                method=method,
                url=url,
                params=params if method == "GET" else None,
                json=data if method in ["POST", "PUT"] else None,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("msg", str(response_data))
                    raise Exception(f"API Error {response.status}: {error_msg}")
                
                return response_data
                
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
    
    # MARKET DATA METHODS
    
    async def get_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            
        Returns:
            Price information
        """
        try:
            result = await self._request(
                "GET",
                "/api/v3/ticker/price",
                params={"symbol": symbol.upper()}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    async def get_24hr_stats(self, symbol: str) -> Dict[str, Any]:
        """
        Get 24-hour price statistics.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            24-hour statistics
        """
        try:
            result = await self._request(
                "GET",
                "/api/v3/ticker/24hr",
                params={"symbol": symbol.upper()}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get 24hr stats for {symbol}: {e}")
            raise
    
    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book for a symbol.
        
        Args:
            symbol: Trading symbol
            limit: Number of orders to return
            
        Returns:
            Order book data
        """
        try:
            result = await self._request(
                "GET",
                "/api/v3/depth",
                params={"symbol": symbol.upper(), "limit": limit}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get orderbook for {symbol}: {e}")
            raise
    
    async def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List[Any]]:
        """
        Get candlestick/kline data.
        
        Args:
            symbol: Trading symbol
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
            limit: Number of klines to return
            start_time: Start time (timestamp)
            end_time: End time (timestamp)
            
        Returns:
            List of kline data
        """
        try:
            params = {
                "symbol": symbol.upper(),
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
            
            result = await self._request("GET", "/api/v3/klines", params=params)
            return result
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise
    
    # ACCOUNT METHODS
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Account information including balances and permissions
        """
        try:
            result = await self._request("GET", "/api/v3/account", signed=True)
            return result
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    async def get_balances(self) -> List[Dict[str, Any]]:
        """
        Get account balances.
        
        Returns:
            List of account balances
        """
        try:
            account = await self.get_account_info()
            
            # Filter and format balances
            balances = []
            for balance in account.get("balances", []):
                free = float(balance["free"])
                locked = float(balance["locked"])
                
                if free > 0 or locked > 0:
                    balances.append({
                        "asset": balance["asset"],
                        "free": free,
                        "locked": locked,
                        "total": free + locked
                    })
            
            return balances
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            raise
    
    # ORDER METHODS
    
    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        stop_price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            symbol: Trading symbol
            side: Order side (BUY/SELL)
            order_type: Order type (MARKET/LIMIT/STOP_LOSS_LIMIT)
            quantity: Order quantity
            price: Order price (required for limit orders)
            time_in_force: Time in force
            stop_price: Stop price (for stop orders)
            **kwargs: Additional order parameters
            
        Returns:
            Order information
        """
        try:
            params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": order_type.upper(),
                "quantity": quantity,
                "timeInForce": time_in_force
            }
            
            if price is not None:
                params["price"] = price
            
            if stop_price is not None:
                params["stopPrice"] = stop_price
            
            # Add additional parameters
            params.update(kwargs)
            
            result = await self._request("POST", "/api/v3/order", signed=True, data=params)
            return result
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise
    
    async def buy_market(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market buy order.
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to buy
            
        Returns:
            Order information
        """
        return await self.create_order(symbol, "BUY", "MARKET", quantity)
    
    async def buy_limit(self, symbol: str, quantity: float, price: float) -> Dict[str, Any]:
        """
        Place a limit buy order.
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to buy
            price: Limit price
            
        Returns:
            Order information
        """
        return await self.create_order(symbol, "BUY", "LIMIT", quantity, price)
    
    async def sell_market(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """
        Place a market sell order.
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to sell
            
        Returns:
            Order information
        """
        return await self.create_order(symbol, "SELL", "MARKET", quantity)
    
    async def sell_limit(self, symbol: str, quantity: float, price: float) -> Dict[str, Any]:
        """
        Place a limit sell order.
        
        Args:
            symbol: Trading symbol
            quantity: Quantity to sell
            price: Limit price
            
        Returns:
            Order information
        """
        return await self.create_order(symbol, "SELL", "LIMIT", quantity, price)
    
    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            params = {
                "symbol": symbol.upper(),
                "orderId": order_id
            }
            
            result = await self._request("DELETE", "/api/v3/order", signed=True, data=params)
            return result
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise
    
    async def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """
        Get order information.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID
            
        Returns:
            Order information
        """
        try:
            params = {
                "symbol": symbol.upper(),
                "orderId": order_id
            }
            
            result = await self._request("GET", "/api/v3/order", signed=True, params=params)
            return result
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            raise
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.
        
        Args:
            symbol: Optional symbol to filter orders
            
        Returns:
            List of open orders
        """
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol.upper()
            
            result = await self._request("GET", "/api/v3/openOrders", signed=True, params=params)
            return result
        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise
    
    async def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 500,
        from_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get account order history.
        
        Args:
            symbol: Optional symbol to filter orders
            limit: Number of orders to return
            from_id: Order ID to start from
            
        Returns:
            List of historical orders
        """
        try:
            params = {"limit": limit}
            
            if symbol:
                params["symbol"] = symbol.upper()
            if from_id:
                params["fromId"] = from_id
            
            result = await self._request("GET", "/api/v3/allOrders", signed=True, params=params)
            return result
        except Exception as e:
            logger.error(f"Failed to get order history: {e}")
            raise
    
    # EXCHANGE INFO
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information and trading rules.
        
        Returns:
            Exchange information
        """
        try:
            result = await self._request("GET", "/api/v3/exchangeInfo")
            return result
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get symbol information.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Symbol information or None if not found
        """
        try:
            exchange_info = await self.get_exchange_info()
            
            for sym_info in exchange_info.get("symbols", []):
                if sym_info["symbol"] == symbol.upper():
                    return sym_info
            
            return None
        except Exception as e:
            logger.error(f"Failed to get symbol info for {symbol}: {e}")
            return None
    
    # UTILITY METHODS
    
    async def test_connectivity(self) -> bool:
        """
        Test API connectivity.
        
        Returns:
            True if connection is successful
        """
        try:
            await self._request("GET", "/api/v3/ping")
            return True
        except Exception as e:
            logger.error(f"Connectivity test failed: {e}")
            return False
    
    async def get_server_time(self) -> int:
        """
        Get server time.
        
        Returns:
            Server timestamp
        """
        try:
            result = await self._request("GET", "/api/v3/time")
            return result["serverTime"]
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            raise
    
    def format_quantity(self, quantity: float, symbol: str) -> float:
        """
        Format quantity according to symbol rules.
        
        Args:
            quantity: Raw quantity
            symbol: Trading symbol
            
        Returns:
            Formatted quantity
        """
        # This would get symbol info and format accordingly
        # For now, return the raw value
        return quantity
    
    def format_price(self, price: float, symbol: str) -> float:
        """
        Format price according to symbol rules.
        
        Args:
            price: Raw price
            symbol: Trading symbol
            
        Returns:
            Formatted price
        """
        # This would get symbol info and format accordingly
        # For now, return the raw value
        return price
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Binance API session closed")
