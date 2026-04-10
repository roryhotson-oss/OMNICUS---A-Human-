"""
OMNICUS Active Trader
=====================
Continuous scalping engine that's always in the market.
Long, short, buy, sell - OMNICUS is always hunting profits.

This is where OMNICUS comes alive - constantly watching,
constantly trading, constantly learning.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import deque


class TradeAction(Enum):
    LONG = "LONG"       # Buy to open
    SHORT = "SHORT"     # Sell to open
    CLOSE_LONG = "CLOSE_LONG"
    CLOSE_SHORT = "CLOSE_SHORT"
    HOLD = "HOLD"


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


@dataclass
class Position:
    """Active trading position"""
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    unrealized_pnl: float = 0.0
    pnl_percent: float = 0.0
    
    def update(self, current_price: float):
        """Update position with current price"""
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
            self.pnl_percent = ((current_price - self.entry_price) / self.entry_price) * 100
        elif self.side == PositionSide.SHORT:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
            self.pnl_percent = ((self.entry_price - current_price) / self.entry_price) * 100


@dataclass
class Trade:
    """Completed trade record"""
    trade_id: str
    symbol: str
    action: TradeAction
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    duration_seconds: float
    entry_time: datetime
    exit_time: datetime
    reason: str


@dataclass
class ScalpSignal:
    """Signal for scalping"""
    symbol: str
    action: TradeAction
    confidence: float
    urgency: str  # "normal", "high", "urgent"
    reason: str
    suggested_entry: float
    stop_loss: float
    take_profit: float
    timestamp: datetime = field(default_factory=datetime.now)


class ActiveTrader:
    """
    OMNICUS's Active Trading Engine
    
    This is where OMNICUS comes alive. He's constantly:
    - Scanning markets for opportunities
    - Opening and closing positions
    - Managing risk with stops and targets
    - Learning from every trade
    
    Scalping mode means quick in-and-out trades,
    always hunting for small but consistent profits.
    """
    
    def __init__(
        self,
        brain: "AIBrain" = None,
        notify_callback: Callable = None,
        trade_callback: Callable = None,
        paper_trading: bool = True
    ):
        """
        Initialize active trader
        
        Args:
            brain: OMNICUS brain instance
            notify_callback: Function to call for notifications (Telegram, etc.)
            trade_callback: Function to call when trade executes
            paper_trading: Use simulated trading
        """
        self.brain = brain
        self.notify_callback = notify_callback
        self.trade_callback = trade_callback
        self.paper_trading = paper_trading
        
        # Trading state
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.pending_signals: deque = deque()
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_pnl = 0.0
        self.session_start = datetime.now()
        
        # Scalping parameters
        self.max_positions = 3
        self.risk_per_trade = 0.02  # 2%
        self.default_stop_percent = 0.015  # 1.5%
        self.default_target_percent = 0.03  # 3%
        self.max_hold_time = timedelta(minutes=30)  # Close if held too long
        
        # Market data cache
        self.market_prices: Dict[str, float] = {}
        self.price_history: Dict[str, List[float]] = {}
        
        # Trading symbols
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        
        # Control
        self._running = False
        self._trade_id_counter = 0
        
        # Last notification time (to avoid spam)
        self._last_notification = {}
        self._min_notification_interval = 300  # 5 minutes
    
    async def start(self):
        """Start the active trading loop"""
        self._running = True
        print("\n🚀 OMNICUS ACTIVE TRADER STARTED")
        print("=" * 50)
        print("   Mode: SCALPING")
        print(f"   Paper Trading: {self.paper_trading}")
        print(f"   Symbols: {', '.join(self.symbols)}")
        print(f"   Max Positions: {self.max_positions}")
        print("=" * 50 + "\n")
        
        # Start parallel tasks
        tasks = [
            self._market_scanner(),
            self._signal_generator(),
            self._position_manager(),
            self._trade_executor(),
        ]
        
        await asyncio.gather(*tasks)
    
    async def stop(self):
        """Stop trading and close all positions"""
        self._running = False
        
        # Close all positions
        for symbol, position in list(self.positions.items()):
            await self._close_position(symbol, "System shutdown")
    
    async def _market_scanner(self):
        """Continuously scan market for price updates"""
        while self._running:
            try:
                for symbol in self.symbols:
                    # In production, this would connect to Binance WebSocket
                    # For now, simulate price movement
                    await self._update_price(symbol)
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"Scanner error: {e}")
                await asyncio.sleep(5)
    
    async def _update_price(self, symbol: str):
        """Update price for a symbol"""
        # Simulated price movement
        # In production, fetch from Binance/Exchange
        base_prices = {"BTCUSDT": 50000, "ETHUSDT": 3000, "SOLUSDT": 100}
        base = base_prices.get(symbol, 100)
        
        # Random walk with some trend
        if symbol not in self.market_prices:
            self.market_prices[symbol] = base
        
        current = self.market_prices[symbol]
        change = random.gauss(0, base * 0.0005)  # Small random movement
        new_price = max(base * 0.9, min(base * 1.1, current + change))
        
        self.market_prices[symbol] = new_price
        
        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(new_price)
        
        # Keep last 100 prices
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
        
        # Update existing positions
        if symbol in self.positions:
            self.positions[symbol].update(new_price)
    
    async def _signal_generator(self):
        """Generate trading signals based on market conditions"""
        while self._running:
            try:
                for symbol in self.symbols:
                    # Skip if we already have a position
                    if symbol in self.positions:
                        continue
                    
                    # Skip if max positions reached
                    if len(self.positions) >= self.max_positions:
                        continue
                    
                    # Generate signal based on price action
                    signal = await self._generate_scalp_signal(symbol)
                    
                    if signal and signal.action != TradeAction.HOLD:
                        self.pending_signals.append(signal)
                        print(f"📊 Signal: {signal.action.value} {symbol} @ ${signal.suggested_entry:.2f}")
                        print(f"   Confidence: {signal.confidence:.0%} | Urgency: {signal.urgency}")
                        print(f"   Reason: {signal.reason}")
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Signal generator error: {e}")
                await asyncio.sleep(5)
    
    async def _generate_scalp_signal(self, symbol: str) -> Optional[ScalpSignal]:
        """Generate a scalping signal for a symbol"""
        if symbol not in self.market_prices or symbol not in self.price_history:
            return None
        
        prices = self.price_history[symbol]
        if len(prices) < 20:
            return None
        
        current_price = self.market_prices[symbol]
        
        # Calculate simple indicators
        sma_5 = sum(prices[-5:]) / 5
        sma_20 = sum(prices[-20:]) / 20
        
        # Momentum
        momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        
        # Volatility
        recent = prices[-10:]
        avg = sum(recent) / len(recent)
        volatility = sum((p - avg) ** 2 for p in recent) / len(recent) ** 0.5 / avg
        
        # Determine action
        action = TradeAction.HOLD
        confidence = 0.5
        reason = ""
        urgency = "normal"
        
        # LONG conditions
        if sma_5 > sma_20 and momentum > 0.001 and current_price > sma_5:
            action = TradeAction.LONG
            confidence = min(0.9, 0.55 + abs(momentum) * 10 + volatility * 5)
            reason = f"Bullish momentum: SMA5 > SMA20, momentum +{momentum:.2%}"
            
            if momentum > 0.005:
                urgency = "high"
            if momentum > 0.01:
                urgency = "urgent"
        
        # SHORT conditions
        elif sma_5 < sma_20 and momentum < -0.001 and current_price < sma_5:
            action = TradeAction.SHORT
            confidence = min(0.9, 0.55 + abs(momentum) * 10 + volatility * 5)
            reason = f"Bearish momentum: SMA5 < SMA20, momentum {momentum:.2%}"
            
            if momentum < -0.005:
                urgency = "high"
            if momentum < -0.01:
                urgency = "urgent"
        
        if action == TradeAction.HOLD:
            return None
        
        # Calculate stop and target
        if action == TradeAction.LONG:
            stop_loss = current_price * (1 - self.default_stop_percent)
            take_profit = current_price * (1 + self.default_target_percent)
        else:  # SHORT
            stop_loss = current_price * (1 + self.default_stop_percent)
            take_profit = current_price * (1 - self.default_target_percent)
        
        signal = ScalpSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            urgency=urgency,
            reason=reason,
            suggested_entry=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Notify on high urgency signals
        if urgency in ["high", "urgent"]:
            await self._notify_great_trade(signal)
        
        return signal
    
    async def _notify_great_trade(self, signal: ScalpSignal):
        """Notify about a great trade opportunity"""
        now = datetime.now()
        symbol = signal.symbol
        
        # Check if we recently notified for this symbol
        if symbol in self._last_notification:
            elapsed = (now - self._last_notification[symbol]).total_seconds()
            if elapsed < self._min_notification_interval:
                return
        
        self._last_notification[symbol] = now
        
        message = f"""
🚨 GREAT TRADE ALERT from OMNICUS!

{signal.action.value} {signal.symbol}
Entry: ${signal.suggested_entry:.2f}
Stop Loss: ${signal.stop_loss:.2f}
Take Profit: ${signal.take_profit:.2f}
Confidence: {signal.confidence:.0%}
Urgency: {signal.urgency.upper()}

Reason: {signal.reason}

This is the one you've been waiting for!
"""
        
        if self.notify_callback:
            await self.notify_callback(message, urgency=signal.urgency)
        
        print(f"\n{'='*50}")
        print("🚨 GREAT TRADE ALERT!")
        print(f"{'='*50}")
        print(message)
    
    async def _position_manager(self):
        """Manage existing positions - stops, targets, time limits"""
        while self._running:
            try:
                for symbol, position in list(self.positions.items()):
                    current_price = self.market_prices.get(symbol, position.entry_price)
                    
                    # Check stop loss
                    if position.side == PositionSide.LONG:
                        if current_price <= position.stop_loss:
                            await self._close_position(symbol, "Stop loss hit")
                            continue
                        if current_price >= position.take_profit:
                            await self._close_position(symbol, "Take profit hit! 🎉")
                            continue
                    
                    elif position.side == PositionSide.SHORT:
                        if current_price >= position.stop_loss:
                            await self._close_position(symbol, "Stop loss hit")
                            continue
                        if current_price <= position.take_profit:
                            await self._close_position(symbol, "Take profit hit! 🎉")
                            continue
                    
                    # Check max hold time
                    hold_time = datetime.now() - position.entry_time
                    if hold_time > self.max_hold_time:
                        await self._close_position(symbol, "Max hold time exceeded")
                        continue
                    
                    # Trailing stop (move stop to breakeven after 1% profit)
                    if position.pnl_percent > 1.0:
                        if position.side == PositionSide.LONG:
                            position.stop_loss = max(position.stop_loss, position.entry_price)
                        else:
                            position.stop_loss = min(position.stop_loss, position.entry_price)
                
                await asyncio.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                print(f"Position manager error: {e}")
                await asyncio.sleep(5)
    
    async def _trade_executor(self):
        """Execute pending trade signals"""
        while self._running:
            try:
                if self.pending_signals:
                    signal = self.pending_signals.popleft()
                    await self._execute_signal(signal)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Trade executor error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_signal(self, signal: ScalpSignal):
        """Execute a trading signal"""
        symbol = signal.symbol
        
        # Check if position already exists
        if symbol in self.positions:
            return
        
        # Determine quantity
        capital = 10000  # Would get from account
        risk_amount = capital * self.risk_per_trade
        stop_distance = abs(signal.suggested_entry - signal.stop_loss)
        quantity = risk_amount / stop_distance if stop_distance > 0 else 0.01
        
        # Create position
        position = Position(
            symbol=symbol,
            side=PositionSide.LONG if signal.action == TradeAction.LONG else PositionSide.SHORT,
            entry_price=signal.suggested_entry,
            quantity=quantity,
            entry_time=datetime.now(),
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit
        )
        
        self.positions[symbol] = position
        
        print(f"\n✅ OPENED: {signal.action.value} {symbol}")
        print(f"   Entry: ${signal.suggested_entry:.2f}")
        print(f"   Size: {quantity:.6f}")
        print(f"   Stop: ${signal.stop_loss:.2f} | Target: ${signal.take_profit:.2f}")
        print(f"   Reason: {signal.reason}")
        
        # Notify trade callback
        if self.trade_callback:
            await self.trade_callback({
                "type": "open",
                "symbol": symbol,
                "action": signal.action.value,
                "entry": signal.suggested_entry,
                "quantity": quantity,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "reason": signal.reason
            })
    
    async def _close_position(self, symbol: str, reason: str):
        """Close a position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        current_price = self.market_prices.get(symbol, position.entry_price)
        
        # Calculate final PnL
        position.update(current_price)
        pnl = position.unrealized_pnl
        pnl_percent = position.pnl_percent
        
        # Create trade record
        self._trade_id_counter += 1
        trade = Trade(
            trade_id=f"T{self._trade_id_counter:06d}",
            symbol=symbol,
            action=TradeAction.CLOSE_LONG if position.side == PositionSide.LONG else TradeAction.CLOSE_SHORT,
            entry_price=position.entry_price,
            exit_price=current_price,
            quantity=position.quantity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            duration_seconds=(datetime.now() - position.entry_time).total_seconds(),
            entry_time=position.entry_time,
            exit_time=datetime.now(),
            reason=reason
        )
        
        # Update stats
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        self.total_pnl += pnl
        
        # Remove position
        del self.positions[symbol]
        self.trade_history.append(trade)
        
        # Print result
        result_emoji = "🟢" if pnl > 0 else "🔴"
        print(f"\n{result_emoji} CLOSED: {symbol}")
        print(f"   Entry: ${position.entry_price:.2f} → Exit: ${current_price:.2f}")
        print(f"   PnL: ${pnl:.2f} ({pnl_percent:+.2f}%)")
        print(f"   Duration: {trade.duration_seconds:.0f}s")
        print(f"   Reason: {reason}")
        
        # Notify trade callback
        if self.trade_callback:
            await self.trade_callback({
                "type": "close",
                "symbol": symbol,
                "entry": position.entry_price,
                "exit": current_price,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "reason": reason
            })
        
        # Learn from trade (update brain)
        if self.brain:
            from agent import DecisionType
            action = DecisionType.ENTER_LONG if position.side == PositionSide.LONG else DecisionType.ENTER_SHORT
            # Create a signal for learning
            from agent import TradeSignal
            signal = TradeSignal(
                symbol=symbol,
                action=action,
                confidence=0.6,
                reasoning=reason
            )
            await self.brain.learn_from_outcome(
                signal=signal,
                outcome_pnl=pnl,
                outcome_type="win" if pnl > 0 else "loss",
                hold_duration=trade.duration_seconds / 3600,
                exit_reason=reason
            )
    
    def get_status(self) -> Dict:
        """Get current trading status"""
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        session_time = datetime.now() - self.session_start
        
        return {
            "running": self._running,
            "paper_trading": self.paper_trading,
            "positions": len(self.positions),
            "position_details": {
                symbol: {
                    "side": pos.side.value,
                    "entry": pos.entry_price,
                    "current_pnl": pos.unrealized_pnl,
                    "pnl_percent": pos.pnl_percent,
                    "duration": str(datetime.now() - pos.entry_time).split(".")[0]
                }
                for symbol, pos in self.positions.items()
            },
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate": f"{win_rate:.1%}",
            "total_pnl": round(self.total_pnl, 2),
            "session_time": str(session_time).split(".")[0],
            "pending_signals": len(self.pending_signals)
        }
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Get recent trades"""
        return [
            {
                "trade_id": t.trade_id,
                "symbol": t.symbol,
                "action": t.action.value,
                "entry": t.entry_price,
                "exit": t.exit_price,
                "pnl": round(t.pnl, 2),
                "pnl_percent": round(t.pnl_percent, 2),
                "duration": f"{t.duration_seconds:.0f}s",
                "reason": t.reason,
                "time": t.exit_time.isoformat()
            }
            for t in self.trade_history[-limit:]
        ]
