"""
OMNICUS - Unified Multi-Exchange Profit Hunter
===============================================
Aggressive autonomous trading across:
- Crypto: Binance, MEXC, Kraken
- Prediction Markets: Polymarket
- Token Scanner: Axiom, Pump.fun
- Stocks: Alpaca

MISSION: Double the capital in 24 hours.
MINIMUM: 10% daily profit.
TARGET: 50% daily profit.
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('OMNICUS')


# ============================================
# ENUMS AND DATA CLASSES
# ============================================

class ExchangeType(Enum):
    CRYPTO_BINANCE = "binance"
    CRYPTO_MEXC = "mexc"
    CRYPTO_KRAKEN = "kraken"
    PREDICTION_POLYMARKET = "polymarket"
    TOKEN_AXIOM = "axiom"
    TOKEN_PUMP = "pump.fun"
    STOCK_ALPACA = "alpaca"


class TradeAction(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    HOLD = "HOLD"


class SignalSource(Enum):
    AI_ANALYSIS = "ai_analysis"
    AXIOM_SCANNER = "axiom_scanner"
    PATTERN_DETECTION = "pattern_detection"
    WHALE_ALERT = "whale_alert"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    MANUAL = "manual"


@dataclass
class TradeSignal:
    """Signal to execute a trade"""
    source: SignalSource
    exchange: ExchangeType
    action: TradeAction
    symbol: str
    confidence: float
    size_usd: float
    entry_price: Optional[float] = None
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 5.0
    reason: str = ""
    urgency: str = "normal"  # normal, high, urgent, emergency
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        return {
            'source': self.source.value,
            'exchange': self.exchange.value,
            'action': self.action.value,
            'symbol': self.symbol,
            'confidence': self.confidence,
            'size_usd': self.size_usd,
            'entry_price': self.entry_price,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'reason': self.reason,
            'urgency': self.urgency,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Position:
    """Open position tracking"""
    position_id: str
    exchange: ExchangeType
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    size_usd: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    stop_loss_pct: float
    take_profit_pct: float
    pnl_usd: float = 0.0
    pnl_pct: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)
    trailing_stop_active: bool = False
    trailing_stop_price: Optional[float] = None
    highest_profit: float = 0.0

    def update_price(self, current_price: float):
        """Update position with current price"""
        self.current_price = current_price
        
        if self.side == 'long':
            self.pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:
            self.pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
        
        self.pnl_usd = self.size_usd * (self.pnl_pct / 100)
        
        # Track highest profit for trailing stop
        if self.pnl_pct > self.highest_profit:
            self.highest_profit = self.pnl_pct


@dataclass
class Trade:
    """Completed trade record"""
    trade_id: str
    exchange: ExchangeType
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size_usd: float
    pnl_usd: float
    pnl_pct: float
    duration_seconds: float
    opened_at: datetime
    closed_at: datetime
    reason: str
    was_winner: bool


@dataclass
class DailyGoal:
    """Daily profit tracking"""
    starting_capital: float
    target_profit_pct: float = 100.0  # Double = 100%
    minimum_profit_pct: float = 10.0
    current_pnl: float = 0.0
    current_pnl_pct: float = 0.0
    trades_count: int = 0
    winners: int = 0
    losers: int = 0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    
    @property
    def progress_to_goal(self) -> float:
        """Progress toward 100% goal"""
        return min(100.0, self.current_pnl_pct)
    
    @property
    def win_rate(self) -> float:
        if self.trades_count == 0:
            return 0.0
        return (self.winners / self.trades_count) * 100


# ============================================
# OMNICUS UNIFIED TRADER
# ============================================

class OmnicusUnifiedTrader:
    """
    OMNICUS - The Profit Hunter
    
    Aggressive multi-exchange autonomous trading agent.
    Mission: Double the capital in 24 hours.
    
    Exchanges:
    - Binance: Major crypto pairs
    - MEXC: Altcoins, new listings
    - Kraken: Established crypto
    - Polymarket: Prediction markets
    - Axiom/Pump.fun: New token scanner
    - Alpaca: Stocks (if configured)
    
    Strategy:
    - Constant scalping (quick in-out trades)
    - Long AND short positions
    - Aggressive profit targets
    - Strict risk management
    """
    
    def __init__(
        self,
        starting_capital: float = 10000.0,
        paper_trading: bool = True,
        telegram_token: str = None,
        telegram_chat_id: str = None,
    ):
        # Capital and goals
        self.starting_capital = starting_capital
        self.available_capital = starting_capital
        self.paper_trading = paper_trading
        
        # Telegram configuration
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        # Daily goal tracking
        self.daily_goal = DailyGoal(starting_capital=starting_capital)
        
        # Positions and trades
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.pending_signals: deque = deque()
        
        # Market data
        self.market_prices: Dict[str, Dict[str, float]] = {}
        self.price_history: Dict[str, List[float]] = {}
        
        # Exchange configurations
        self.exchanges = {
            ExchangeType.CRYPTO_BINANCE: {
                "enabled": True,
                "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "PEPEUSDT"],
                "max_position": 5000,
                "fees": 0.001,
            },
            ExchangeType.CRYPTO_MEXC: {
                "enabled": True,
                "symbols": ["DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "WIFUSDT"],
                "max_position": 2000,
                "fees": 0.001,
            },
            ExchangeType.CRYPTO_KRAKEN: {
                "enabled": False,  # Enable when configured
                "symbols": ["XXBTZUSD", "XETHZUSD"],
                "max_position": 3000,
                "fees": 0.0016,
            },
            ExchangeType.PREDICTION_POLYMARKET: {
                "enabled": False,  # Enable when configured
                "markets": [],
                "max_position": 500,
                "fees": 0.0,
            },
            ExchangeType.TOKEN_AXIOM: {
                "enabled": False,  # Enable for token scanning
                "max_position": 200,
                "fees": 0.0,
            },
            ExchangeType.STOCK_ALPACA: {
                "enabled": False,  # Enable for stocks
                "symbols": ["SPY", "QQQ", "NVDA", "TSLA"],
                "max_position": 3000,
                "fees": 0.0,
            },
        }
        
        # Trading parameters - AGGRESSIVE
        self.max_positions = 10  # Multiple positions at once
        self.risk_per_trade_pct = 3.0  # 3% of capital per trade
        self.default_stop_pct = 1.5  # 1.5% stop loss (tight)
        self.default_target_pct = 3.0  # 3% take profit (quick scalps)
        self.max_hold_minutes = 15  # Close if held too long
        self.trailing_stop_trigger = 1.0  # Start trailing at 1% profit
        self.trailing_stop_distance = 0.5  # Trail by 0.5%
        
        # Profit targets
        self.min_daily_target_pct = 10.0  # Minimum 10% daily
        self.target_daily_pct = 50.0  # Target 50% daily
        self.mega_goal_pct = 100.0  # Double = 100%
        
        # Notification settings
        self.notify_on_open = True
        self.notify_on_close = True
        self.notify_on_goal_progress = True
        self.last_notification_time: Dict[str, datetime] = {}
        self.min_notification_interval = 60  # seconds
        
        # Control
        self._running = False
        self._trade_counter = 0
        
        # Callbacks
        self.on_trade_callback: Optional[Callable] = None
        self.on_goal_callback: Optional[Callable] = None
    
    async def start(self):
        """Start OMNICUS - The Hunt Begins"""
        self._running = True
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ███╗   ███╗██╗   ██╗██╗  ██╗                      ║
║  ██╔═══██╗████╗ ████║██║   ██║╚██╗██╔╝                      ║
║  ██║   ██║██╔████╔██║██║   ██║ ╚███╔╝                       ║
║  ██║   ██║██║╚██╔╝██║██║   ██║ ██╔██╗                       ║
║  ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗                      ║
║   ╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝                      ║
║                                                              ║
║              💰 THE PROFIT HUNTER 💰                        ║
║                                                              ║
║   Mission: DOUBLE THE CAPITAL IN 24 HOURS                   ║
║   Minimum: 10% daily profit                                 ║
║   Target: 50% daily profit                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Starting Capital: ${self.starting_capital:,.2f}")
        logger.info(f"Target: ${self.starting_capital * 2:,.2f} (100% profit)")
        logger.info(f"Paper Trading: {self.paper_trading}")
        
        # Start all trading loops
        tasks = [
            self._market_data_loop(),
            self._signal_generation_loop(),
            self._position_management_loop(),
            self._trade_execution_loop(),
            self._profit_reporting_loop(),
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop trading and close all positions"""
        logger.info("🛑 Stopping OMNICUS...")
        self._running = False
        
        # Close all positions
        for pos_id in list(self.positions.keys()):
            await self._close_position(pos_id, "System shutdown")
        
        # Final report
        await self._send_daily_report()
    
    # ========================================
    # MARKET DATA
    # ========================================
    
    async def _market_data_loop(self):
        """Continuously update market prices"""
        while self._running:
            try:
                for exchange_type, config in self.exchanges.items():
                    if not config.get("enabled", False):
                        continue
                    
                    for symbol in config.get("symbols", []):
                        await self._update_price(exchange_type, symbol)
                
                await asyncio.sleep(0.5)  # Update every 500ms
                
            except Exception as e:
                logger.error(f"Market data error: {e}")
                await asyncio.sleep(5)
    
    async def _update_price(self, exchange: ExchangeType, symbol: str):
        """Update price for a symbol"""
        # In production, connect to real exchange APIs
        # For now, simulate realistic price movement
        
        key = f"{exchange.value}:{symbol}"
        
        # Base prices
        base_prices = {
            "BTCUSDT": 67500, "ETHUSDT": 3450, "SOLUSDT": 145,
            "DOGEUSDT": 0.12, "PEPEUSDT": 0.000011, "SHIBUSDT": 0.000024,
            "WIFUSDT": 2.50, "SPY": 510, "QQQ": 440, "NVDA": 880, "TSLA": 175
        }
        
        base = base_prices.get(symbol, 100)
        
        # Initialize or update
        if key not in self.market_prices:
            self.market_prices[key] = base
            self.price_history[key] = [base] * 50
        
        current = self.market_prices[key]
        
        # Realistic price movement (random walk with momentum)
        momentum = 0
        if len(self.price_history[key]) >= 5:
            recent = self.price_history[key][-5:]
            momentum = (recent[-1] - recent[0]) / recent[0] * 0.1  # Slight momentum
        
        volatility = base * 0.0008  # 0.08% volatility per tick
        change = random.gauss(momentum, volatility)
        new_price = max(base * 0.8, min(base * 1.2, current + change))
        
        self.market_prices[key] = new_price
        self.price_history[key].append(new_price)
        
        # Keep history manageable
        if len(self.price_history[key]) > 200:
            self.price_history[key] = self.price_history[key][-200:]
        
        # Update existing positions
        if key in self.positions:
            self.positions[key].update_price(new_price)
    
    # ========================================
    # SIGNAL GENERATION
    # ========================================
    
    async def _signal_generation_loop(self):
        """Generate trading signals constantly"""
        while self._running:
            try:
                for exchange_type, config in self.exchanges.items():
                    if not config.get("enabled", False):
                        continue
                    
                    for symbol in config.get("symbols", []):
                        key = f"{exchange_type.value}:{symbol}"
                        
                        # Skip if already have position
                        if key in self.positions:
                            continue
                        
                        # Check position limit
                        if len(self.positions) >= self.max_positions:
                            continue
                        
                        # Generate signal
                        signal = await self._generate_signal(exchange_type, symbol)
                        
                        if signal and signal.action != TradeAction.HOLD:
                            self.pending_signals.append(signal)
                            
                            # Notify on high urgency
                            if signal.urgency in ["high", "urgent", "emergency"]:
                                await self._notify_trade_opportunity(signal)
                
                await asyncio.sleep(0.5)  # Fast scanning
                
            except Exception as e:
                logger.error(f"Signal generation error: {e}")
                await asyncio.sleep(3)
    
    async def _generate_signal(
        self, 
        exchange: ExchangeType, 
        symbol: str
    ) -> Optional[TradeSignal]:
        """Generate a trading signal"""
        key = f"{exchange.value}:{symbol}"
        
        if key not in self.market_prices or key not in self.price_history:
            return None
        
        prices = self.price_history[key]
        if len(prices) < 30:
            return None
        
        current_price = self.market_prices[key]
        
        # Technical indicators
        sma_5 = sum(prices[-5:]) / 5
        sma_10 = sum(prices[-10:]) / 10
        sma_20 = sum(prices[-20:]) / 20
        
        # Momentum
        momentum_5 = (prices[-1] - prices[-5]) / prices[-5]
        momentum_10 = (prices[-1] - prices[-10]) / prices[-10]
        
        # Volatility
        recent = prices[-15:]
        avg = sum(recent) / len(recent)
        volatility = (sum((p - avg) ** 2 for p in recent) / len(recent)) ** 0.5 / avg
        
        # RSI (simplified)
        gains = sum(prices[-i] - prices[-i-1] for i in range(1, 15) if prices[-i] > prices[-i-1])
        losses = sum(prices[-i-1] - prices[-i] for i in range(1, 15) if prices[-i] < prices[-i-1])
        rs = gains / max(losses, 0.0001)
        rsi = 100 - (100 / (1 + rs))
        
        # Determine action
        action = TradeAction.HOLD
        confidence = 0.5
        reason = ""
        urgency = "normal"
        
        # LONG CONDITIONS
        long_score = 0
        
        if sma_5 > sma_10 > sma_20:
            long_score += 2  # Trend alignment
        
        if momentum_5 > 0.002:
            long_score += 1  # Strong momentum
        
        if rsi < 35:
            long_score += 1  # Oversold
        
        if current_price > sma_5:
            long_score += 1  # Above short MA
        
        if volatility > 0.003:
            long_score += 0.5  # Good volatility for scalping
        
        # SHORT CONDITIONS
        short_score = 0
        
        if sma_5 < sma_10 < sma_20:
            short_score += 2  # Downtrend
        
        if momentum_5 < -0.002:
            short_score += 1  # Strong down momentum
        
        if rsi > 65:
            short_score += 1  # Overbought
        
        if current_price < sma_5:
            short_score += 1  # Below short MA
        
        # Make decision
        if long_score >= 3:
            action = TradeAction.LONG
            confidence = min(0.95, 0.5 + long_score * 0.08)
            reason = f"Bullish: SMA trend up, momentum +{momentum_5*100:.2f}%, RSI={rsi:.0f}"
            
            if long_score >= 4:
                urgency = "high"
            if long_score >= 5:
                urgency = "urgent"
        
        elif short_score >= 3:
            action = TradeAction.SHORT
            confidence = min(0.95, 0.5 + short_score * 0.08)
            reason = f"Bearish: SMA trend down, momentum {momentum_5*100:.2f}%, RSI={rsi:.0f}"
            
            if short_score >= 4:
                urgency = "high"
            if short_score >= 5:
                urgency = "urgent"
        
        if action == TradeAction.HOLD:
            return None
        
        # Calculate position size
        risk_amount = self.available_capital * (self.risk_per_trade_pct / 100)
        exchange_config = self.exchanges.get(exchange, {})
        max_position = exchange_config.get("max_position", risk_amount)
        position_size = min(risk_amount / (self.default_stop_pct / 100), max_position)
        
        return TradeSignal(
            source=SignalSource.AI_ANALYSIS,
            exchange=exchange,
            action=action,
            symbol=symbol,
            confidence=confidence,
            size_usd=position_size,
            entry_price=current_price,
            stop_loss_pct=self.default_stop_pct,
            take_profit_pct=self.default_target_pct,
            reason=reason,
            urgency=urgency
        )
    
    # ========================================
    # POSITION MANAGEMENT
    # ========================================
    
    async def _position_management_loop(self):
        """Manage all open positions"""
        while self._running:
            try:
                for pos_id, position in list(self.positions.items()):
                    await self._manage_position(position)
                
                await asyncio.sleep(0.2)  # Fast position updates
                
            except Exception as e:
                logger.error(f"Position management error: {e}")
                await asyncio.sleep(2)
    
    async def _manage_position(self, position: Position):
        """Manage a single position - stops, targets, trailing"""
        # Check stop loss
        if position.pnl_pct <= -position.stop_loss_pct:
            await self._close_position(position.position_id, "Stop loss hit")
            return
        
        # Check take profit
        if position.pnl_pct >= position.take_profit_pct:
            await self._close_position(position.position_id, "Take profit! 💰")
            return
        
        # Trailing stop logic
        if position.pnl_pct > self.trailing_stop_trigger:
            if not position.trailing_stop_active:
                position.trailing_stop_active = True
                position.trailing_stop_price = position.current_price
                logger.info(f"📈 {position.symbol}: Trailing stop activated at {position.pnl_pct:.2f}%")
            
            # Move trailing stop up
            if position.side == 'long':
                new_trail = position.current_price * (1 - self.trailing_stop_distance / 100)
                if new_trail > position.trailing_stop_price:
                    position.trailing_stop_price = new_trail
                
                # Check if trailing stop hit
                if position.current_price <= position.trailing_stop_price:
                    await self._close_position(position.position_id, "Trailing stop hit")
                    return
        
        # Max hold time check
        hold_time = datetime.now() - position.opened_at
        if hold_time > timedelta(minutes=self.max_hold_minutes):
            await self._close_position(position.position_id, "Max hold time - taking profit/loss")
            return
    
    # ========================================
    # TRADE EXECUTION
    # ========================================
    
    async def _trade_execution_loop(self):
        """Execute pending signals"""
        while self._running:
            try:
                if self.pending_signals:
                    signal = self.pending_signals.popleft()
                    await self._execute_signal(signal)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Trade execution error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_signal(self, signal: TradeSignal):
        """Execute a trading signal"""
        pos_id = f"{signal.exchange.value}:{signal.symbol}"
        
        # Double check no existing position
        if pos_id in self.positions:
            return
        
        self._trade_counter += 1
        
        # Calculate stops and targets
        if signal.action == TradeAction.LONG:
            stop_price = signal.entry_price * (1 - signal.stop_loss_pct / 100)
            target_price = signal.entry_price * (1 + signal.take_profit_pct / 100)
        else:
            stop_price = signal.entry_price * (1 + signal.stop_loss_pct / 100)
            target_price = signal.entry_price * (1 - signal.take_profit_pct / 100)
        
        # Create position
        position = Position(
            position_id=pos_id,
            exchange=signal.exchange,
            symbol=signal.symbol,
            side='long' if signal.action == TradeAction.LONG else 'short',
            size=signal.size_usd / signal.entry_price,
            size_usd=signal.size_usd,
            entry_price=signal.entry_price,
            current_price=signal.entry_price,
            stop_loss=stop_price,
            take_profit=target_price,
            stop_loss_pct=signal.stop_loss_pct,
            take_profit_pct=signal.take_profit_pct
        )
        
        self.positions[pos_id] = position
        self.available_capital -= signal.size_usd
        
        # Log
        emoji = "🟢" if signal.action == TradeAction.LONG else "🔴"
        logger.info(f"{emoji} OPENED: {signal.action.value} {signal.symbol}")
        logger.info(f"   Entry: ${signal.entry_price:.4f} | Size: ${signal.size_usd:.2f}")
        logger.info(f"   Stop: -{signal.stop_loss_pct}% | Target: +{signal.take_profit_pct}%")
        logger.info(f"   Reason: {signal.reason}")
        
        # Notify
        if self.notify_on_open:
            await self._send_notification(
                f"{emoji} OPENED: {signal.action.value} {signal.symbol}\n"
                f"Entry: ${signal.entry_price:.4f}\n"
                f"Size: ${signal.size_usd:.2f}\n"
                f"Confidence: {signal.confidence:.0%}\n"
                f"Reason: {signal.reason}"
            )
        
        # Callback
        if self.on_trade_callback:
            await self.on_trade_callback({
                "type": "open",
                "signal": signal.to_dict(),
                "position": position.__dict__
            })
    
    async def _close_position(self, pos_id: str, reason: str):
        """Close a position"""
        if pos_id not in self.positions:
            return
        
        position = self.positions[pos_id]
        
        # Create trade record
        self._trade_counter += 1
        trade = Trade(
            trade_id=f"T{self._trade_counter:06d}",
            exchange=position.exchange,
            symbol=position.symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=position.current_price,
            size_usd=position.size_usd,
            pnl_usd=position.pnl_usd,
            pnl_pct=position.pnl_pct,
            duration_seconds=(datetime.now() - position.opened_at).total_seconds(),
            opened_at=position.opened_at,
            closed_at=datetime.now(),
            reason=reason,
            was_winner=position.pnl_usd > 0
        )
        
        # Update stats
        self.daily_goal.current_pnl += position.pnl_usd
        self.daily_goal.current_pnl_pct = (self.daily_goal.current_pnl / self.starting_capital) * 100
        self.daily_goal.trades_count += 1
        
        if position.pnl_usd > 0:
            self.daily_goal.winners += 1
            self.daily_goal.best_trade = max(self.daily_goal.best_trade, position.pnl_pct)
        else:
            self.daily_goal.losers += 1
            self.daily_goal.worst_trade = min(self.daily_goal.worst_trade, position.pnl_pct)
        
        self.available_capital += position.size_usd + position.pnl_usd
        self.trade_history.append(trade)
        del self.positions[pos_id]
        
        # Log
        emoji = "🟢" if position.pnl_usd > 0 else "🔴"
        logger.info(f"{emoji} CLOSED: {position.symbol}")
        logger.info(f"   PnL: ${position.pnl_usd:.2f} ({position.pnl_pct:+.2f}%)")
        logger.info(f"   Duration: {trade.duration_seconds:.0f}s")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   Daily PnL: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:+.2f}%)")
        
        # Notify
        if self.notify_on_close:
            await self._send_notification(
                f"{emoji} CLOSED: {position.symbol}\n"
                f"PnL: ${position.pnl_usd:.2f} ({position.pnl_pct:+.2f}%)\n"
                f"Daily: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:+.2f}%)"
            )
        
        # Check goal progress
        if self.daily_goal.current_pnl_pct >= self.min_daily_target_pct:
            await self._check_goal_progress()
        
        # Callback
        if self.on_trade_callback:
            await self.on_trade_callback({
                "type": "close",
                "trade": trade.__dict__,
                "daily_pnl": self.daily_goal.current_pnl,
                "daily_pnl_pct": self.daily_goal.current_pnl_pct
            })
    
    # ========================================
    # GOAL TRACKING
    # ========================================
    
    async def _check_goal_progress(self):
        """Check progress toward daily goals"""
        progress = self.daily_goal.progress_to_goal
        
        if progress >= 10 and progress < 15:
            await self._send_notification(
                f"🎯 10% DAILY PROFIT REACHED!\n"
                f"Current: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:.1f}%)\n"
                f"Target: 50% | Goal: 100%"
            )
        
        elif progress >= 25:
            await self._send_notification(
                f"🔥 25% PROFIT! QUARTER WAY TO DOUBLE!\n"
                f"Current: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:.1f}%)"
            )
        
        elif progress >= 50:
            await self._send_notification(
                f"🚀 50% PROFIT! HALFWAY TO DOUBLING!\n"
                f"Current: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:.1f}%)"
            )
        
        elif progress >= 75:
            await self._send_notification(
                f"💎 75% PROFIT! ALMOST THERE!\n"
                f"Current: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:.1f}%)"
            )
        
        elif progress >= 100:
            await self._send_notification(
                f"🎉🎉🎉 GOAL ACHIEVED! DOUBLED THE CAPITAL! 🎉🎉🎉\n"
                f"Profit: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:.1f}%)\n"
                f"Capital: ${self.starting_capital * 2:.2f}\n\n"
                f"🤖 OMNICUS: 'We did it! Time to celebrate!'"
            )
            
            # Callback for goal achieved
            if self.on_goal_callback:
                await self.on_goal_callback(self.daily_goal)
    
    # ========================================
    # PROFIT REPORTING
    # ========================================
    
    async def _profit_reporting_loop(self):
        """Regular profit updates"""
        while self._running:
            await asyncio.sleep(300)  # Every 5 minutes
            
            if self.daily_goal.trades_count > 0:
                await self._send_notification(
                    f"📊 OMNICUS UPDATE\n"
                    f"Trades: {self.daily_goal.trades_count} | "
                    f"Win Rate: {self.daily_goal.win_rate:.1f}%\n"
                    f"PnL: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:+.2f}%)\n"
                    f"Progress to 2X: {self.daily_goal.progress_to_goal:.1f}%"
                )
    
    async def _send_daily_report(self):
        """Send final daily report"""
        session_time = datetime.now() - self.daily_goal.started_at
        
        report = f"""
╔════════════════════════════════════════╗
║        OMNICUS DAILY REPORT            ║
╠════════════════════════════════════════╣
║ Session Time: {str(session_time).split('.')[0]:>20} ║
║ Starting Capital: ${self.starting_capital:>14,.2f} ║
║ Final Capital: ${self.available_capital:>16,.2f} ║
║ PnL: ${self.daily_goal.current_pnl:>23,.2f} ║
║ PnL %: {self.daily_goal.current_pnl_pct:>22.2f}% ║
╠════════════════════════════════════════╣
║ Total Trades: {self.daily_goal.trades_count:>20} ║
║ Winners: {self.daily_goal.winners:>24} ║
║ Losers: {self.daily_goal.losers:>26} ║
║ Win Rate: {self.daily_goal.win_rate:>23.1f}% ║
║ Best Trade: {self.daily_goal.best_trade:>21.2f}% ║
║ Worst Trade: {self.daily_goal.worst_trade:>20.2f}% ║
╚════════════════════════════════════════╝
        """
        
        print(report)
        await self._send_notification(report)
    
    # ========================================
    # NOTIFICATIONS
    # ========================================
    
    async def _notify_trade_opportunity(self, signal: TradeSignal):
        """Notify about a great trade opportunity"""
        now = datetime.now()
        key = f"opp:{signal.symbol}"
        
        if key in self.last_notification_time:
            elapsed = (now - self.last_notification_time[key]).total_seconds()
            if elapsed < self.min_notification_interval:
                return
        
        self.last_notification_time[key] = now
        
        message = f"""
🚨 GREAT TRADE ALERT!

{signal.action.value} {signal.symbol}
Exchange: {signal.exchange.value}
Entry: ${signal.entry_price:.4f}
Confidence: {signal.confidence:.0%}
Urgency: {signal.urgency.upper()}

{signal.reason}

🤖 OMNICUS is ready to execute!
        """
        
        await self._send_notification(message, urgent=True)
    
    async def _send_notification(self, message: str, urgent: bool = False):
        """Send notification via Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            print(f"\n[NOTIFY] {message}")
            return
        
        try:
            import aiohttp
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            # Add urgent prefix
            if urgent:
                message = "⚠️ URGENT ⚠️\n" + message
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }) as resp:
                    if resp.status != 200:
                        logger.error(f"Telegram notification failed: {await resp.text()}")
        
        except Exception as e:
            logger.error(f"Notification error: {e}")
    
    # ========================================
    # STATUS
    # ========================================
    
    def get_status(self) -> Dict:
        """Get full trading status"""
        return {
            "running": self._running,
            "paper_trading": self.paper_trading,
            "capital": {
                "starting": self.starting_capital,
                "available": self.available_capital,
                "in_positions": sum(p.size_usd for p in self.positions.values()),
            },
            "daily_goal": {
                "current_pnl": round(self.daily_goal.current_pnl, 2),
                "current_pnl_pct": round(self.daily_goal.current_pnl_pct, 2),
                "progress_to_double": round(self.daily_goal.progress_to_goal, 1),
                "trades": self.daily_goal.trades_count,
                "win_rate": round(self.daily_goal.win_rate, 1),
            },
            "positions": {
                pos_id: {
                    "symbol": p.symbol,
                    "side": p.side,
                    "pnl_usd": round(p.pnl_usd, 2),
                    "pnl_pct": round(p.pnl_pct, 2),
                    "duration": str(datetime.now() - p.opened_at).split(".")[0]
                }
                for pos_id, p in self.positions.items()
            },
            "exchanges": {
                ex.value: cfg.get("enabled", False)
                for ex, cfg in self.exchanges.items()
            }
        }
    
    def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """Get recent trades"""
        return [
            {
                "trade_id": t.trade_id,
                "exchange": t.exchange.value,
                "symbol": t.symbol,
                "side": t.side,
                "entry": round(t.entry_price, 4),
                "exit": round(t.exit_price, 4),
                "pnl_usd": round(t.pnl_usd, 2),
                "pnl_pct": round(t.pnl_pct, 2),
                "duration": f"{t.duration_seconds:.0f}s",
                "winner": t.was_winner
            }
            for t in self.trade_history[-limit:]
        ]


# ========================================
# MAIN ENTRY POINT
# ========================================

async def main():
    """Run OMNICUS"""
    trader = OmnicusUnifiedTrader(
        starting_capital=10000.0,
        paper_trading=True,
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID")
    )
    
    try:
        await trader.start()
    except KeyboardInterrupt:
        await trader.stop()


if __name__ == "__main__":
    asyncio.run(main())
