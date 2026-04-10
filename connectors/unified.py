"""
OMNICUS Unified Exchange Manager
================================
Coordinates multiple exchanges with a single interface.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

from .base import BaseConnector, OrderResult, OrderSide, OrderType, Position, MarketData
from .binance_connector import BinanceConnector

logger = logging.getLogger(__name__)


@dataclass
class ExchangeStats:
    """Statistics for an exchange"""
    name: str
    is_connected: bool = False
    total_trades: int = 0
    total_volume_usd: float = 0.0
    total_pnl: float = 0.0
    last_trade_time: Optional[datetime] = None


class UnifiedExchangeManager:
    """
    Unified manager for all exchange connections.
    
    Provides a single interface to trade across multiple exchanges:
    - Binance (Crypto)
    - Kraken (Crypto)
    - MEXC (Crypto)
    - Polymarket (Predictions)
    - Alpaca (Stocks)
    """
    
    def __init__(self, config=None):
        self.config = config
        self.exchanges: Dict[str, BaseConnector] = {}
        self.stats: Dict[str, ExchangeStats] = {}
        self._market_data_cache: Dict[str, MarketData] = {}
        
        logger.info("🔄 Unified Exchange Manager initialized")
    
    async def add_exchange(self, name: str, connector: BaseConnector) -> bool:
        """Add an exchange connector"""
        try:
            connected = await connector.connect()
            
            self.exchanges[name] = connector
            self.stats[name] = ExchangeStats(
                name=name,
                is_connected=connected
            )
            
            if connected:
                logger.info(f"✅ {name.upper()} exchange connected")
            else:
                logger.warning(f"⚠️  {name.upper()} connection failed")
            
            return connected
            
        except Exception as e:
            logger.error(f"Failed to add exchange {name}: {e}")
            return False
    
    async def connect_all(self, credentials: Dict[str, Dict[str, str]]) -> Dict[str, bool]:
        """Connect to all configured exchanges"""
        results = {}
        
        # Binance
        if "binance" in credentials:
            creds = credentials["binance"]
            connector = BinanceConnector(
                api_key=creds.get("api_key", ""),
                api_secret=creds.get("api_secret", ""),
                testnet=creds.get("testnet", "true").lower() == "true"
            )
            results["binance"] = await self.add_exchange("binance", connector)
        
        # TODO: Add other exchanges as connectors are implemented
        # Kraken, MEXC, Polymarket, Alpaca
        
        return results
    
    async def disconnect_all(self) -> None:
        """Disconnect from all exchanges"""
        for name, connector in self.exchanges.items():
            try:
                await connector.disconnect()
                self.stats[name].is_connected = False
            except Exception as e:
                logger.error(f"Error disconnecting {name}: {e}")
        
        logger.info("All exchanges disconnected")
    
    # ==================== UNIFIED METHODS ====================
    
    async def get_best_price(self, symbol: str) -> Dict[str, float]:
        """Get best price across all exchanges"""
        prices = {}
        
        for name, connector in self.exchanges.items():
            if connector.is_connected:
                try:
                    price = await connector.get_price(symbol)
                    if price > 0:
                        prices[name] = price
                except Exception as e:
                    logger.debug(f"Could not get {symbol} price from {name}: {e}")
        
        return prices
    
    async def get_all_balances(self) -> Dict[str, Dict[str, float]]:
        """Get balances from all exchanges"""
        balances = {}
        
        for name, connector in self.exchanges.items():
            if connector.is_connected:
                try:
                    balance = await connector.get_balance()
                    if balance:
                        balances[name] = balance
                except Exception as e:
                    logger.error(f"Could not get balance from {name}: {e}")
        
        return balances
    
    async def place_order(
        self,
        exchange: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> OrderResult:
        """Place an order on a specific exchange"""
        if exchange not in self.exchanges:
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                status="rejected",
                message=f"Exchange {exchange} not connected"
            )
        
        connector = self.exchanges[exchange]
        
        result = await connector.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            **kwargs
        )
        
        # Update stats
        if result.success:
            self.stats[exchange].total_trades += 1
            self.stats[exchange].total_volume_usd += (price or 0) * quantity
            self.stats[exchange].last_trade_time = datetime.now()
        
        return result
    
    async def smart_route_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET
    ) -> OrderResult:
        """
        Smart order routing - find best exchange for the order.
        
        Currently uses simple price comparison.
        TODO: Add liquidity, fees, slippage considerations.
        """
        # Get prices from all exchanges
        prices = await self.get_best_price(symbol)
        
        if not prices:
            return OrderResult(
                success=False,
                symbol=symbol,
                side=side,
                quantity=quantity,
                status="rejected",
                message="No exchanges have this symbol"
            )
        
        # Find best exchange
        if side == OrderSide.BUY:
            # Buy at lowest price
            best_exchange = min(prices, key=prices.get)
        else:
            # Sell at highest price
            best_exchange = max(prices, key=prices.get)
        
        return await self.place_order(
            exchange=best_exchange,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=prices[best_exchange]
        )
    
    async def get_all_positions(self) -> List[Dict]:
        """Get positions from all exchanges"""
        all_positions = []
        
        for name, connector in self.exchanges.items():
            if connector.is_connected:
                try:
                    positions = await connector.get_positions()
                    for pos in positions:
                        pos_dict = {
                            "exchange": name,
                            "symbol": pos.symbol,
                            "side": pos.side.value,
                            "quantity": pos.quantity,
                            "entry_price": pos.entry_price,
                            "current_price": pos.current_price,
                            "unrealized_pnl": pos.unrealized_pnl,
                            "unrealized_pnl_pct": pos.unrealized_pnl_pct
                        }
                        all_positions.append(pos_dict)
                except Exception as e:
                    logger.error(f"Could not get positions from {name}: {e}")
        
        return all_positions
    
    async def close_all_positions(self) -> List[OrderResult]:
        """Close all positions across all exchanges"""
        results = []
        
        positions = await self.get_all_positions()
        
        for pos in positions:
            try:
                result = await self.place_order(
                    exchange=pos["exchange"],
                    symbol=pos["symbol"],
                    side=OrderSide.SELL if pos["side"] == "buy" else OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=pos["quantity"]
                )
                results.append(result)
            except Exception as e:
                results.append(OrderResult(
                    success=False,
                    symbol=pos["symbol"],
                    message=f"Failed to close: {e}"
                ))
        
        return results
    
    # ==================== MARKET SCANNING ====================
    
    async def scan_opportunities(
        self,
        symbols: List[str],
        min_confidence: float = 0.7
    ) -> List[Dict]:
        """Scan markets for trading opportunities"""
        opportunities = []
        
        for symbol in symbols:
            for name, connector in self.exchanges.items():
                if connector.is_connected:
                    try:
                        market_data = await connector.get_market_data(symbol)
                        
                        # Simple opportunity detection
                        # TODO: Integrate with AI brain for better signals
                        if market_data.change_pct_24h < -5:
                            # Potential dip buy
                            opportunities.append({
                                "symbol": symbol,
                                "exchange": name,
                                "type": "dip_buy",
                                "confidence": 0.75,
                                "price": market_data.price,
                                "change_24h": market_data.change_pct_24h
                            })
                        elif market_data.change_pct_24h > 10:
                            # Potential momentum trade
                            opportunities.append({
                                "symbol": symbol,
                                "exchange": name,
                                "type": "momentum",
                                "confidence": 0.70,
                                "price": market_data.price,
                                "change_24h": market_data.change_pct_24h
                            })
                            
                    except Exception as e:
                        logger.debug(f"Could not scan {symbol} on {name}: {e}")
        
        return [o for o in opportunities if o["confidence"] >= min_confidence]
    
    # ==================== STATUS ====================
    
    def get_status(self) -> Dict:
        """Get manager status"""
        return {
            "exchanges": {
                name: {
                    "connected": stat.is_connected,
                    "trades": stat.total_trades,
                    "volume_usd": stat.total_volume_usd,
                    "pnl": stat.total_pnl,
                    "last_trade": stat.last_trade_time.isoformat() if stat.last_trade_time else None
                }
                for name, stat in self.stats.items()
            },
            "total_exchanges": len(self.exchanges),
            "connected_exchanges": sum(1 for s in self.stats.values() if s.is_connected)
        }
