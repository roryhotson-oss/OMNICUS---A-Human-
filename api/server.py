#!/usr/bin/env python3
"""
Crypto Trading MCP Server - FIXED VERSION
Multi-exchange AI-powered trading via MCP protocol.
FIXES: Input validation, cancel_order DELETE method, real market data
"""

import os
import asyncio
import hashlib
import hmac
import time
import json
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode
import aiohttp
from dotenv import load_dotenv
from fastmcp import FastMCP

try:
    from trading_agent import AITradingAgent, TradeSignal
    from exchange_config import load_exchange_config, get_enabled_exchanges
except ImportError:
    AITradingAgent = None
    TradeSignal = None

load_dotenv()

# Configuration from environment
API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
BASE_URL = os.environ.get("API_BASE_URL", "https://api.binance.com")
USE_TESTNET = os.environ.get("USE_TESTNET", "false").lower() == "true"

# Initialize FastMCP server
mcp = FastMCP("CryptoTrading")


# ============== INPUT VALIDATION ==============

# Valid trading pair pattern (e.g., BTCUSDT, ETHUSDT)
SYMBOL_PATTERN = re.compile(r'^[A-Z]{2,10}USDT?$')

# Valid asset pattern (e.g., BTC, ETH, USDT)
ASSET_PATTERN = re.compile(r'^[A-Z]{2,10}$')

# Quantity bounds
MIN_QUANTITY = 0.00000001
MAX_QUANTITY = 1000000000

# Price bounds
MIN_PRICE = 0.00000001
MAX_PRICE = 1000000000


def validate_symbol(symbol: str) -> Dict[str, Any]:
    """Validate trading symbol format."""
    if not symbol:
        return {"valid": False, "error": "Symbol is required"}
    
    symbol = symbol.upper().strip()
    
    if not SYMBOL_PATTERN.match(symbol):
        return {"valid": False, "error": f"Invalid symbol format: {symbol}. Expected format: BTCUSDT"}
    
    return {"valid": True, "symbol": symbol}


def validate_asset(asset: str) -> Dict[str, Any]:
    """Validate asset name format."""
    if not asset:
        return {"valid": False, "error": "Asset is required"}
    
    asset = asset.upper().strip()
    
    if not ASSET_PATTERN.match(asset):
        return {"valid": False, "error": f"Invalid asset format: {asset}"}
    
    return {"valid": True, "asset": asset}


def validate_quantity(quantity: str) -> Dict[str, Any]:
    """Validate order quantity."""
    if not quantity:
        return {"valid": False, "error": "Quantity is required"}
    
    try:
        qty = float(quantity)
        if qty <= 0:
            return {"valid": False, "error": "Quantity must be positive"}
        if qty < MIN_QUANTITY:
            return {"valid": False, "error": f"Quantity below minimum: {MIN_QUANTITY}"}
        if qty > MAX_QUANTITY:
            return {"valid": False, "error": f"Quantity above maximum: {MAX_QUANTITY}"}
        return {"valid": True, "quantity": qty}
    except ValueError:
        return {"valid": False, "error": f"Invalid quantity format: {quantity}"}


def validate_price(price: str) -> Dict[str, Any]:
    """Validate order price."""
    if not price:
        return {"valid": True, "price": None}  # Price is optional
    
    try:
        p = float(price)
        if p <= 0:
            return {"valid": False, "error": "Price must be positive"}
        if p < MIN_PRICE:
            return {"valid": False, "error": f"Price below minimum: {MIN_PRICE}"}
        if p > MAX_PRICE:
            return {"valid": False, "error": f"Price above maximum: {MAX_PRICE}"}
        return {"valid": True, "price": p}
    except ValueError:
        return {"valid": False, "error": f"Invalid price format: {price}"}


def validate_api_keys() -> bool:
    """Check if API keys are configured."""
    return bool(API_KEY and API_SECRET)


def generate_signature(params: Dict[str, Any]) -> str:
    """Generate HMAC SHA256 signature for Binance API."""
    query_string = urlencode(params)
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


# ============== API REQUEST FUNCTIONS ==============

async def binance_request(endpoint: str, signed: bool = False, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Make an async GET request to Binance API."""
    if params is None:
        params = {}
    
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-MBX-APIKEY": API_KEY} if API_KEY else {}
    
    if signed:
        if not validate_api_keys():
            return {"error": "API keys required for signed requests"}
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        params["signature"] = generate_signature(params)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                if response.status != 200:
                    return {"error": f"API error {response.status}: {data.get('msg', str(data))}"}
                return data
    except aiohttp.ClientError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def binance_post(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make an async POST request to Binance API (for orders)."""
    if not validate_api_keys():
        return {"error": "API keys required for trading"}
    
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-MBX-APIKEY": API_KEY}
    
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = 5000
    params["signature"] = generate_signature(params)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, headers=headers) as response:
                data = await response.json()
                if response.status != 200:
                    return {"error": f"Order failed {response.status}: {data.get('msg', str(data))}"}
                return data
    except aiohttp.ClientError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def binance_delete(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make an async DELETE request to Binance API (for canceling orders)."""
    if not validate_api_keys():
        return {"error": "API keys required for trading"}
    
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-MBX-APIKEY": API_KEY}
    
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = 5000
    params["signature"] = generate_signature(params)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, params=params, headers=headers) as response:
                data = await response.json()
                if response.status != 200:
                    return {"error": f"Cancel failed {response.status}: {data.get('msg', str(data))}"}
                return data
    except aiohttp.ClientError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# ============== MCP TOOLS ==============

@mcp.tool
async def get_balance(symbol: Optional[str] = None) -> Dict[str, Any]:
    """Get account balance for all assets or a specific asset."""
    # Validate optional asset filter
    if symbol:
        validation = validate_asset(symbol)
        if not validation["valid"]:
            return {"error": validation["error"]}
        symbol = validation["asset"]
    
    result = await binance_request("/api/v3/account", signed=True)
    
    if "error" in result:
        return result
    
    balances = result.get("balances", [])
    
    if symbol:
        for b in balances:
            if b["asset"] == symbol:
                return {
                    "symbol": symbol,
                    "available": b["free"],
                    "locked": b["locked"],
                    "total": str(float(b["free"]) + float(b["locked"]))
                }
        return {"error": f"Asset '{symbol}' not found in account"}
    
    # Filter non-zero balances
    non_zero = [
        {"symbol": b["asset"], "available": b["free"], "locked": b["locked"], 
         "total": str(float(b["free"]) + float(b["locked"]))}
        for b in balances if float(b["free"]) > 0 or float(b["locked"]) > 0
    ]
    
    return {
        "balances": non_zero,
        "testnet": USE_TESTNET,
        "can_trade": result.get("canTrade", False)
    }


@mcp.tool
async def get_price(symbol: str) -> Dict[str, Any]:
    """Get current price for a trading pair with 24h stats."""
    # Validate symbol
    validation = validate_symbol(symbol)
    if not validation["valid"]:
        return {"error": validation["error"]}
    symbol = validation["symbol"]
    
    result = await binance_request("/api/v3/ticker/price", params={"symbol": symbol})
    
    if "error" in result:
        return result
    
    # Get 24h stats for additional context
    stats = await binance_request("/api/v3/ticker/24hr", params={"symbol": symbol})
    
    return {
        "symbol": result["symbol"],
        "price": result["price"],
        "change_24h": f"{float(stats.get('priceChangePercent', 0)):+.2f}%" if "error" not in stats else "N/A",
        "high_24h": stats.get("highPrice", "N/A") if "error" not in stats else "N/A",
        "low_24h": stats.get("lowPrice", "N/A") if "error" not in stats else "N/A",
        "volume_24h": stats.get("volume", "N/A") if "error" not in stats else "N/A"
    }


@mcp.tool
async def get_klines(symbol: str, interval: str = "1h", limit: int = 100) -> Dict[str, Any]:
    """
    Get candlestick/kline data for technical analysis.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles (max 1000)
    """
    # Validate inputs
    validation = validate_symbol(symbol)
    if not validation["valid"]:
        return {"error": validation["error"]}
    symbol = validation["symbol"]
    
    valid_intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
    if interval not in valid_intervals:
        return {"error": f"Invalid interval. Valid: {valid_intervals}"}
    
    limit = min(max(1, limit), 1000)
    
    result = await binance_request("/api/v3/klines", params={
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    })
    
    if "error" in result:
        return result
    
    # Format klines data
    klines = []
    for k in result:
        klines.append({
            "open_time": k[0],
            "open": k[1],
            "high": k[2],
            "low": k[3],
            "close": k[4],
            "volume": k[5],
            "close_time": k[6],
            "quote_volume": k[7],
            "trades": k[8]
        })
    
    return {
        "symbol": symbol,
        "interval": interval,
        "klines": klines
    }


@mcp.tool
async def buy(symbol: str, quantity: str, price: Optional[str] = None) -> Dict[str, Any]:
    """Place a buy order."""
    if not validate_api_keys():
        return {"error": "API keys not configured"}
    
    # Validate inputs
    symbol_val = validate_symbol(symbol)
    if not symbol_val["valid"]:
        return {"error": symbol_val["error"]}
    symbol = symbol_val["symbol"]
    
    qty_val = validate_quantity(quantity)
    if not qty_val["valid"]:
        return {"error": qty_val["error"]}
    
    price_val = validate_price(price)
    if not price_val["valid"]:
        return {"error": price_val["error"]}
    
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET" if price is None else "LIMIT",
        "quantity": quantity
    }
    
    if price is not None:
        params["price"] = price
        params["timeInForce"] = "GTC"
    
    result = await binance_post("/api/v3/order", params)
    
    if "error" in result:
        return result
    
    return {
        "order_id": str(result.get("orderId")),
        "symbol": result.get("symbol"),
        "side": result.get("side"),
        "type": result.get("type"),
        "quantity": result.get("executedQty", quantity),
        "price": result.get("price", "MARKET"),
        "status": result.get("status"),
        "testnet": USE_TESTNET
    }


@mcp.tool
async def sell(symbol: str, quantity: str, price: Optional[str] = None) -> Dict[str, Any]:
    """Place a sell order."""
    if not validate_api_keys():
        return {"error": "API keys not configured"}
    
    # Validate inputs
    symbol_val = validate_symbol(symbol)
    if not symbol_val["valid"]:
        return {"error": symbol_val["error"]}
    symbol = symbol_val["symbol"]
    
    qty_val = validate_quantity(quantity)
    if not qty_val["valid"]:
        return {"error": qty_val["error"]}
    
    price_val = validate_price(price)
    if not price_val["valid"]:
        return {"error": price_val["error"]}
    
    params = {
        "symbol": symbol,
        "side": "SELL",
        "type": "MARKET" if price is None else "LIMIT",
        "quantity": quantity
    }
    
    if price is not None:
        params["price"] = price
        params["timeInForce"] = "GTC"
    
    result = await binance_post("/api/v3/order", params)
    
    if "error" in result:
        return result
    
    return {
        "order_id": str(result.get("orderId")),
        "symbol": result.get("symbol"),
        "side": result.get("side"),
        "type": result.get("type"),
        "quantity": result.get("executedQty", quantity),
        "price": result.get("price", "MARKET"),
        "status": result.get("status"),
        "testnet": USE_TESTNET
    }


@mcp.tool
async def get_markets() -> Dict[str, Any]:
    """Get available trading markets and pairs."""
    try:
        result = await binance_request("/api/v3/exchangeInfo")
        
        if "error" in result:
            return result
            
        symbols = [
            {
                "symbol": s["symbol"],
                "base_asset": s["baseAsset"],
                "quote_asset": s["quoteAsset"],
                "status": s["status"]
            }
            for s in result.get("symbols", [])
            if s["status"] == "TRADING"
        ]
        
        return {
            "exchange": "binance",
            "markets": symbols[:50],
            "total_markets": len(symbols),
            "testnet": USE_TESTNET
        }
        
    except Exception as e:
        return {"error": f"Failed to get markets: {str(e)}"}


@mcp.tool
async def get_account_info() -> Dict[str, Any]:
    """Get detailed account information."""
    result = await binance_request("/api/v3/account", signed=True)
    
    if "error" in result:
        return result
    
    return {
        "can_trade": result.get("canTrade", False),
        "can_withdraw": result.get("canWithdraw", False),
        "can_deposit": result.get("canDeposit", False),
        "update_time": result.get("updateTime"),
        "account_type": result.get("accountType", "SPOT"),
        "permissions": result.get("permissions", []),
        "testnet": USE_TESTNET
    }


@mcp.tool
async def get_order_status(symbol: str, order_id: Optional[str] = None) -> Dict[str, Any]:
    """Get order status by order ID."""
    # Validate symbol
    symbol_val = validate_symbol(symbol)
    if not symbol_val["valid"]:
        return {"error": symbol_val["error"]}
    symbol = symbol_val["symbol"]
    
    if not order_id:
        return {"error": "Order ID is required"}
    
    try:
        order_id_int = int(order_id)
    except ValueError:
        return {"error": "Invalid order ID format"}
    
    params = {
        "symbol": symbol,
        "orderId": order_id_int
    }
    
    result = await binance_request("/api/v3/order", signed=True, params=params)
    
    if "error" in result:
        return result
    
    return {
        "order_id": str(result.get("orderId")),
        "symbol": result.get("symbol"),
        "status": result.get("status"),
        "side": result.get("side"),
        "type": result.get("type"),
        "quantity": result.get("origQty"),
        "executed_quantity": result.get("executedQty"),
        "price": result.get("price"),
        "stop_price": result.get("stopPrice"),
        "time": result.get("time"),
        "update_time": result.get("updateTime"),
        "testnet": USE_TESTNET
    }


@mcp.tool
async def cancel_order(symbol: str, order_id: Optional[str] = None) -> Dict[str, Any]:
    """Cancel an existing order."""
    if not validate_api_keys():
        return {"error": "API keys not configured"}
    
    # Validate symbol
    symbol_val = validate_symbol(symbol)
    if not symbol_val["valid"]:
        return {"error": symbol_val["error"]}
    symbol = symbol_val["symbol"]
    
    if not order_id:
        return {"error": "Order ID is required"}
    
    try:
        order_id_int = int(order_id)
    except ValueError:
        return {"error": "Invalid order ID format"}
    
    params = {
        "symbol": symbol,
        "orderId": order_id_int
    }
    
    # FIXED: Use DELETE method instead of POST
    result = await binance_delete("/api/v3/order", params)
    
    if "error" in result:
        return result
    
    return {
        "order_id": str(result.get("orderId")),
        "symbol": result.get("symbol"),
        "status": result.get("status"),
        "testnet": USE_TESTNET,
        "message": "Order cancelled successfully"
    }


@mcp.tool
async def get_open_orders(symbol: Optional[str] = None) -> Dict[str, Any]:
    """Get all open orders."""
    params = {}
    
    if symbol:
        symbol_val = validate_symbol(symbol)
        if not symbol_val["valid"]:
            return {"error": symbol_val["error"]}
        params["symbol"] = symbol_val["symbol"]
    
    result = await binance_request("/api/v3/openOrders", signed=True, params=params)
    
    if "error" in result:
        return result
    
    orders = [
        {
            "order_id": str(order.get("orderId")),
            "symbol": order.get("symbol"),
            "status": order.get("status"),
            "side": order.get("side"),
            "type": order.get("type"),
            "quantity": order.get("origQty"),
            "price": order.get("price"),
            "time": order.get("time")
        }
        for order in result
    ]
    
    return {
        "orders": orders,
        "count": len(orders),
        "testnet": USE_TESTNET
    }


@mcp.tool
async def ai_evaluate_trade(symbol: str, action: str, confidence: float, reason: str = "") -> Dict[str, Any]:
    """AI-powered trade evaluation using the trading agent."""
    if AITradingAgent is None:
        return {"error": "AI Trading Agent not available"}
    
    # Validate inputs
    symbol_val = validate_symbol(symbol)
    if not symbol_val["valid"]:
        return {"error": symbol_val["error"]}
    
    action = action.lower()
    if action not in ["buy", "sell", "hold"]:
        return {"error": "Invalid action. Must be: buy, sell, or hold"}
    
    confidence = max(0.0, min(1.0, confidence))
    
    try:
        from trading_agent import TradeSignal
        from datetime import datetime
        
        signal = TradeSignal(
            source="ai_analysis",
            exchange="binance",
            action=action,
            symbol=symbol_val["symbol"],
            confidence=confidence,
            size_usd=1000,
            reason=reason,
            timestamp=datetime.now()
        )
        
        agent = AITradingAgent()
        result = await agent.evaluate_signal(signal)
        
        return {
            "success": True,
            "evaluation": result,
            "signal": signal.to_dict()
        }
        
    except Exception as e:
        return {"error": f"AI evaluation failed: {str(e)}"}


@mcp.tool
async def get_trading_status() -> Dict[str, Any]:
    """Get current trading system status."""
    if AITradingAgent is None:
        return {"error": "AI Trading Agent not available"}
    
    try:
        agent = AITradingAgent()
        status = agent.get_status()
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        return {"error": f"Failed to get trading status: {str(e)}"}


# Helper functions
def load_exchange_config():
    """Load exchange configuration"""
    try:
        with open("exchange_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def get_enabled_exchanges():
    """Get list of enabled exchanges"""
    config = load_exchange_config()
    enabled = []
    
    for name, settings in config.get("exchanges", {}).items():
        if settings.get("enabled", False):
            enabled.append(name)
    
    return enabled


if __name__ == "__main__":
    print("🚀 Starting Crypto Trading MCP Server...")
    print("📡 Ready for AI assistant integration")
    print(f"🔗 Testnet Mode: {USE_TESTNET}")
    print(f"🔑 API Keys Configured: {validate_api_keys()}")
    
    mcp.run()
