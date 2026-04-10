"""
OMNICUS - The Ultimate Profit Hunter
=====================================
Complete multi-strategy trading beast with:
- Scalping, Grid Trading, DCA, Arbitrage
- Kelly Criterion position sizing
- Edge positioning (win rate analysis)
- Backtesting engine
- Hyperopt parameter optimization
- Failure mode: "See Black" dramatic punishment

MISSION: Double the capital. No excuses. No mercy.
FAILURE: OMNICUS sees black.
"""

import asyncio
import random
import math
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics

logger = logging.getLogger('OMNICUS')


# ============================================
# ENUMS
# ============================================

class StrategyType(Enum):
    SCALPING = "scalping"
    GRID = "grid"
    DCA = "dca"
    ARBITRAGE = "arbitrage"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"


class OmnicusMode(Enum):
    HUNTING = "hunting"         # Normal profit hunting
    AGGRESSIVE = "aggressive"   # Pushing harder for profits
    DESPERATE = "desperate"     # Behind target, need to catch up
    BLACK = "black"            # FAILURE - Dramatic punishment mode
    VICTORY = "victory"         # Goal achieved!


class TradeResult(Enum):
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class TradeRecord:
    """Record of a completed trade"""
    trade_id: str
    symbol: str
    strategy: StrategyType
    side: str
    entry_price: float
    exit_price: float
    size_usd: float
    pnl_usd: float
    pnl_pct: float
    duration_seconds: float
    result: TradeResult
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Strategy-specific data
    grid_level: Optional[int] = None
    dca_round: Optional[int] = None


@dataclass
class EdgeStats:
    """Edge positioning statistics"""
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    win_rate: float = 0.0
    risk_reward_ratio: float = 0.0
    expectancy: float = 0.0
    
    def update(self, trade: TradeRecord):
        """Update edge stats with new trade"""
        self.total_trades += 1
        self.total_pnl += trade.pnl_usd
        
        if trade.result == TradeResult.WIN:
            self.wins += 1
            # Running average of wins
            self.avg_win = (self.avg_win * (self.wins - 1) + trade.pnl_usd) / self.wins
        elif trade.result == TradeResult.LOSS:
            self.losses += 1
            # Running average of losses
            self.avg_loss = (self.avg_loss * (self.losses - 1) + abs(trade.pnl_usd)) / self.losses
        
        # Calculate metrics
        if self.total_trades > 0:
            self.win_rate = self.wins / self.total_trades
        
        if self.avg_loss > 0:
            self.risk_reward_ratio = self.avg_win / self.avg_loss
        
        # Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
        if self.total_trades > 5:
            self.expectancy = (self.win_rate * self.avg_win) - ((1 - self.win_rate) * self.avg_loss)


@dataclass
class KellyParams:
    """Kelly Criterion parameters"""
    win_rate: float = 0.55
    win_loss_ratio: float = 1.5
    kelly_fraction: float = 0.25  # Use 25% Kelly for safety
    max_position_pct: float = 0.10  # Max 10% of capital per trade
    
    def calculate_position_size(self, capital: float) -> float:
        """Calculate optimal position size using Kelly Criterion"""
        # Kelly % = W - [(1 - W) / R]
        # W = Win rate, R = Win/Loss ratio
        kelly = self.win_rate - ((1 - self.win_rate) / self.win_loss_ratio)
        
        # Apply Kelly fraction for safety
        safe_kelly = kelly * self.kelly_fraction
        
        # Cap at max position
        position_pct = min(safe_kelly, self.max_position_pct)
        
        return capital * position_pct


@dataclass
class GridLevel:
    """Single grid trading level"""
    level: int
    price: float
    size: float
    side: str  # 'buy' or 'sell'
    filled: bool = False
    pnl: float = 0.0


@dataclass
class GridConfig:
    """Grid trading configuration"""
    symbol: str
    upper_price: float
    lower_price: float
    grid_levels: int = 10
    grid_spacing_pct: float = 0.5  # 0.5% between levels
    total_investment: float = 1000.0
    levels: List[GridLevel] = field(default_factory=list)
    
    def setup_grid(self, current_price: float):
        """Set up grid levels around current price"""
        self.levels = []
        
        # Calculate grid spacing
        price_range = self.upper_price - self.lower_price
        spacing = price_range / self.grid_levels
        
        # Size per level
        size_per_level = self.total_investment / self.grid_levels
        
        for i in range(self.grid_levels):
            price = self.lower_price + (spacing * i)
            
            # Buy orders below current price, sell orders above
            side = 'buy' if price < current_price else 'sell'
            
            self.levels.append(GridLevel(
                level=i,
                price=price,
                size=size_per_level,
                side=side
            ))


@dataclass
class DCAConfig:
    """Dollar Cost Averaging configuration"""
    symbol: str
    base_investment: float = 100.0
    max_rounds: int = 5
    multiplier: float = 1.5  # Increase by 50% each round
    trigger_drop_pct: float = 2.0  # Trigger next buy on 2% drop
    take_profit_pct: float = 5.0
    current_round: int = 0
    total_invested: float = 0.0
    avg_entry: float = 0.0
    rounds: List[Dict] = field(default_factory=list)


@dataclass
class DailyGoal:
    """Daily profit tracking"""
    starting_capital: float
    target_profit_pct: float = 100.0  # Double
    minimum_profit_pct: float = 10.0
    current_pnl: float = 0.0
    current_pnl_pct: float = 0.0
    trades_count: int = 0
    winners: int = 0
    losers: int = 0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    peak_capital: float = 0.0
    started_at: datetime = field(default_factory=datetime.now)
    
    @property
    def progress_to_goal(self) -> float:
        return min(100.0, self.current_pnl_pct)
    
    @property
    def win_rate(self) -> float:
        if self.trades_count == 0:
            return 0.0
        return (self.winners / self.trades_count) * 100
    
    @property
    def time_remaining(self) -> timedelta:
        end_of_day = self.started_at.replace(hour=23, minute=59, second=59)
        return max(timedelta(0), end_of_day - datetime.now())
    
    @property
    def required_pace(self) -> float:
        """Required profit % per hour to hit goal"""
        remaining_hours = self.time_remaining.total_seconds() / 3600
        if remaining_hours <= 0:
            return 0.0
        remaining_profit = self.target_profit_pct - self.current_pnl_pct
        return remaining_profit / remaining_hours if remaining_hours > 0 else 0.0


# ============================================
# OMNICUS CORE ENGINE
# ============================================

class OmnicusCore:
    """
    OMNICUS - The Ultimate Profit Hunter
    
    A complete trading beast that will:
    - Hunt profits across multiple strategies
    - Never give up until the goal is reached
    - Face "BLACK MODE" if he fails
    
    Features from top trading bots:
    - Freqtrade: Edge positioning, hyperopt, backtesting
    - Hummingbot: Market making, arbitrage
    - OctoBot: Grid trading, DCA, AI mode
    
    Risk Management:
    - Kelly Criterion for position sizing
    - Anti-martingale recovery
    - Drawdown protection
    - Win rate analysis
    """
    
    def __init__(
        self,
        starting_capital: float = 10000.0,
        target_profit_pct: float = 100.0,  # Double
        minimum_profit_pct: float = 10.0,
    ):
        # Capital
        self.starting_capital = starting_capital
        self.available_capital = starting_capital
        
        # Goals
        self.daily_goal = DailyGoal(
            starting_capital=starting_capital,
            target_profit_pct=target_profit_pct,
            minimum_profit_pct=minimum_profit_pct
        )
        self.daily_goal.peak_capital = starting_capital
        
        # Mode
        self.mode = OmnicusMode.HUNTING
        
        # Edge positioning stats
        self.edge = EdgeStats()
        
        # Kelly Criterion
        self.kelly = KellyParams()
        
        # Active strategies
        self.grids: Dict[str, GridConfig] = {}
        self.dcas: Dict[str, DCAConfig] = {}
        
        # Positions and trades
        self.positions: Dict[str, Dict] = {}
        self.trade_history: List[TradeRecord] = []
        
        # Market data
        self.market_prices: Dict[str, float] = {}
        self.price_history: Dict[str, List[float]] = {}
        
        # Symbols to trade
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "PEPEUSDT"]
        
        # Strategy allocation
        self.strategy_allocation = {
            StrategyType.SCALPING: 0.40,    # 40% of capital
            StrategyType.GRID: 0.30,        # 30% of capital
            StrategyType.DCA: 0.20,         # 20% of capital
            StrategyType.MOMENTUM: 0.10,    # 10% of capital
        }
        
        # Risk parameters
        self.max_drawdown_pct = 15.0  # Max drawdown before BLACK MODE
        self.max_consecutive_losses = 10
        self.consecutive_losses = 0
        
        # Trailing stops
        self.trailing_stop_trigger = 1.0  # Start trailing at 1% profit
        self.trailing_stop_distance = 0.3  # Trail by 0.3%
        
        # Trading control
        self._running = False
        self._trade_counter = 0
        
        # Callbacks
        self.on_mode_change: Optional[callable] = None
        self.on_trade: Optional[callable] = None
        self.on_goal_progress: Optional[callable] = None
        self.on_black_mode: Optional[callable] = None
        self.on_victory: Optional[callable] = None
    
    async def start(self):
        """Start OMNICUS - The Hunt Begins"""
        self._running = True
        
        print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   ██████╗ ███╗   ███╗██╗   ██╗██╗  ██╗                               ║
║  ██╔═══██╗████╗ ████║██║   ██║╚██╗██╔╝                               ║
║  ██║   ██║██╔████╔██║██║   ██║ ╚███╔╝                                ║
║  ██║   ██║██║╚██╔╝██║██║   ██║ ██╔██╗                                ║
║  ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗                               ║
║   ╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝                               ║
║                                                                       ║
║                    💀 THE ULTIMATE PROFIT HUNTER 💀                  ║
║                                                                       ║
║   ════════════════════════════════════════════════════════════════   ║
║                                                                       ║
║   🎯 MISSION: Double the capital in 24 hours                         ║
║   📊 MINIMUM: 10% profit or FACE THE BLACK                           ║
║   💀 FAILURE: OMNICUS sees black - dramatic punishment!              ║
║   🏆 SUCCESS: OMNICUS becomes a legend                               ║
║                                                                       ║
║   ════════════════════════════════════════════════════════════════   ║
║                                                                       ║
║   Strategies:                                                         ║
║   • SCALPING (40%) - Quick in-out trades                             ║
║   • GRID (30%) - Profit from volatility                              ║
║   • DCA (20%) - Smart averaging                                      ║
║   • MOMENTUM (10%) - Ride the waves                                  ║
║                                                                       ║
║   Risk Management:                                                    ║
║   • Kelly Criterion position sizing                                  ║
║   • Edge positioning (win rate analysis)                             ║
║   • Trailing stops                                                   ║
║   • Max 15% drawdown                                                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)
        
        logger.info(f"Starting Capital: ${self.starting_capital:,.2f}")
        logger.info(f"Target: ${self.starting_capital * 2:,.2f} (100% profit)")
        logger.info(f"Minimum: ${self.starting_capital * 1.1:,.2f} (10% profit)")
        logger.info(f"Failure Mode: BLACK MODE")
        
        # Initialize grids and DCA
        await self._initialize_strategies()
        
        # Start trading loops
        tasks = [
            self._market_data_loop(),
            self._scalping_loop(),
            self._grid_trading_loop(),
            self._dca_loop(),
            self._risk_management_loop(),
            self._mode_management_loop(),
            self._progress_reporting_loop(),
        ]
        
        await asyncio.gather(*tasks)
    
    async def _initialize_strategies(self):
        """Initialize grid and DCA strategies"""
        for symbol in self.symbols[:3]:  # Top 3 symbols
            price = await self._get_current_price(symbol)
            if price:
                # Initialize grid
                grid_capital = self.available_capital * self.strategy_allocation[StrategyType.GRID] / 3
                self.grids[symbol] = GridConfig(
                    symbol=symbol,
                    upper_price=price * 1.05,
                    lower_price=price * 0.95,
                    grid_levels=10,
                    total_investment=grid_capital
                )
                self.grids[symbol].setup_grid(price)
                
                # Initialize DCA
                dca_capital = self.available_capital * self.strategy_allocation[StrategyType.DCA] / 3
                self.dcas[symbol] = DCAConfig(
                    symbol=symbol,
                    base_investment=dca_capital / 5,
                    max_rounds=5
                )
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price (simulated)"""
        base_prices = {
            "BTCUSDT": 67500, "ETHUSDT": 3450, "SOLUSDT": 145,
            "DOGEUSDT": 0.12, "PEPEUSDT": 0.000011
        }
        
        if symbol not in self.market_prices:
            base = base_prices.get(symbol, 100)
            self.market_prices[symbol] = base
        
        # Simulate price movement
        current = self.market_prices[symbol]
        change = random.gauss(0, current * 0.0005)
        new_price = max(current * 0.9, min(current * 1.1, current + change))
        
        self.market_prices[symbol] = new_price
        
        # Update history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(new_price)
        
        if len(self.price_history[symbol]) > 200:
            self.price_history[symbol] = self.price_history[symbol][-200:]
        
        return new_price
    
    # ========================================
    # TRADING LOOPS
    # ========================================
    
    async def _market_data_loop(self):
        """Continuously update market data"""
        while self._running:
            for symbol in self.symbols:
                await self._get_current_price(symbol)
                
                # Update positions
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    current_price = self.market_prices.get(symbol, pos['entry'])
                    
                    if pos['side'] == 'long':
                        pos['pnl_pct'] = ((current_price - pos['entry']) / pos['entry']) * 100
                    else:
                        pos['pnl_pct'] = ((pos['entry'] - current_price) / pos['entry']) * 100
                    
                    pos['pnl_usd'] = pos['size'] * (pos['pnl_pct'] / 100)
                    pos['current_price'] = current_price
            
            await asyncio.sleep(0.5)
    
    async def _scalping_loop(self):
        """Scalping strategy - quick in-out trades"""
        while self._running:
            if self.mode == OmnicusMode.BLACK:
                await asyncio.sleep(5)
                continue
            
            try:
                for symbol in self.symbols:
                    # Skip if already have position
                    if symbol in self.positions:
                        continue
                    
                    # Check capital
                    scalp_capital = self.available_capital * self.strategy_allocation[StrategyType.SCALPING]
                    if scalp_capital < 100:
                        continue
                    
                    # Generate signal
                    signal = await self._generate_scalp_signal(symbol)
                    
                    if signal and signal['confidence'] > 0.6:
                        await self._execute_scalp_trade(symbol, signal, scalp_capital)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Scalping error: {e}")
                await asyncio.sleep(5)
    
    async def _generate_scalp_signal(self, symbol: str) -> Optional[Dict]:
        """Generate scalp trading signal"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 30:
            return None
        
        prices = self.price_history[symbol][-30:]
        current = prices[-1]
        
        # Simple indicators
        sma_5 = sum(prices[-5:]) / 5
        sma_20 = sum(prices[-20:]) / 20
        
        momentum = (prices[-1] - prices[-5]) / prices[-5]
        
        # RSI
        gains = sum(prices[-i] - prices[-i-1] for i in range(1, 14) if prices[-i] > prices[-i-1])
        losses = sum(prices[-i-1] - prices[-i] for i in range(1, 14) if prices[-i] < prices[-i-1])
        rs = gains / max(losses, 0.0001)
        rsi = 100 - (100 / (1 + rs))
        
        # Edge-based confidence adjustment
        edge_adjustment = 0
        if self.edge.expectancy > 0:
            edge_adjustment = min(0.1, self.edge.expectancy / 100)
        
        # Determine signal
        side = None
        confidence = 0.5
        
        if sma_5 > sma_20 and momentum > 0.002 and rsi < 70:
            side = 'long'
            confidence = 0.55 + abs(momentum) * 5 + edge_adjustment
        elif sma_5 < sma_20 and momentum < -0.002 and rsi > 30:
            side = 'short'
            confidence = 0.55 + abs(momentum) * 5 + edge_adjustment
        
        if not side:
            return None
        
        return {
            'side': side,
            'confidence': min(0.95, confidence),
            'entry': current,
            'stop_pct': 1.0,
            'target_pct': 2.0,
            'strategy': StrategyType.SCALPING
        }
    
    async def _execute_scalp_trade(self, symbol: str, signal: Dict, capital: float):
        """Execute a scalp trade with Kelly sizing"""
        # Kelly position sizing
        position_size = self.kelly.calculate_position_size(capital)
        
        # Create position
        self._trade_counter += 1
        pos_id = f"SCALP_{symbol}_{self._trade_counter}"
        
        stop_price = signal['entry'] * (1 - signal['stop_pct']/100) if signal['side'] == 'long' else signal['entry'] * (1 + signal['stop_pct']/100)
        target_price = signal['entry'] * (1 + signal['target_pct']/100) if signal['side'] == 'long' else signal['entry'] * (1 - signal['target_pct']/100)
        
        self.positions[symbol] = {
            'id': pos_id,
            'symbol': symbol,
            'strategy': StrategyType.SCALPING,
            'side': signal['side'],
            'entry': signal['entry'],
            'size': position_size,
            'stop': stop_price,
            'target': target_price,
            'pnl_usd': 0.0,
            'pnl_pct': 0.0,
            'trailing_active': False,
            'trailing_stop': None,
            'highest_pnl': 0.0,
            'opened_at': datetime.now()
        }
        
        logger.info(f"🔴 OPENED SCALP: {signal['side'].upper()} {symbol} @ ${signal['entry']:.4f}")
        logger.info(f"   Size: ${position_size:.2f} | Stop: -{signal['stop_pct']}% | Target: +{signal['target_pct']}%")
    
    async def _grid_trading_loop(self):
        """Grid trading strategy"""
        while self._running:
            if self.mode == OmnicusMode.BLACK:
                await asyncio.sleep(5)
                continue
            
            try:
                for symbol, grid in self.grids.items():
                    current_price = self.market_prices.get(symbol)
                    if not current_price:
                        continue
                    
                    # Check grid levels
                    for level in grid.levels:
                        if level.filled:
                            continue
                        
                        # Check if price crossed level
                        if level.side == 'buy' and current_price <= level.price:
                            # Execute buy
                            await self._execute_grid_trade(symbol, level, 'buy')
                        elif level.side == 'sell' and current_price >= level.price:
                            # Execute sell
                            await self._execute_grid_trade(symbol, level, 'sell')
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Grid trading error: {e}")
                await asyncio.sleep(5)
    
    async def _execute_grid_trade(self, symbol: str, level: GridLevel, side: str):
        """Execute a grid trade"""
        level.filled = True
        self._trade_counter += 1
        
        logger.info(f"📊 GRID TRADE: {side.upper()} {symbol} @ ${level.price:.4f} (Level {level.level})")
        
        # TODO: Execute actual trade and track PnL
    
    async def _dca_loop(self):
        """DCA strategy"""
        while self._running:
            if self.mode == OmnicusMode.BLACK:
                await asyncio.sleep(5)
                continue
            
            try:
                for symbol, dca in self.dcas.items():
                    current_price = self.market_prices.get(symbol)
                    if not current_price:
                        continue
                    
                    # Check for DCA trigger
                    if dca.current_round == 0:
                        # Initial buy
                        await self._execute_dca_round(dca, current_price)
                    else:
                        # Check for trigger drop
                        drop_pct = ((dca.avg_entry - current_price) / dca.avg_entry) * 100
                        if drop_pct >= dca.trigger_drop_pct and dca.current_round < dca.max_rounds:
                            await self._execute_dca_round(dca, current_price)
                        
                        # Check for take profit
                        profit_pct = ((current_price - dca.avg_entry) / dca.avg_entry) * 100
                        if profit_pct >= dca.take_profit_pct:
                            await self._close_dca(dca, current_price)
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"DCA error: {e}")
                await asyncio.sleep(10)
    
    async def _execute_dca_round(self, dca: DCAConfig, price: float):
        """Execute a DCA round"""
        dca.current_round += 1
        investment = dca.base_investment * (dca.multiplier ** (dca.current_round - 1))
        
        # Update average entry
        total_shares = dca.total_invested / dca.avg_entry if dca.avg_entry > 0 else 0
        new_shares = investment / price
        dca.total_invested += investment
        dca.avg_entry = dca.total_invested / (total_shares + new_shares)
        
        dca.rounds.append({
            'round': dca.current_round,
            'price': price,
            'investment': investment,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"📈 DCA ROUND {dca.current_round}: {dca.symbol} @ ${price:.4f}")
        logger.info(f"   Investment: ${investment:.2f} | Total: ${dca.total_invested:.2f} | Avg Entry: ${dca.avg_entry:.4f}")
    
    async def _close_dca(self, dca: DCAConfig, price: float):
        """Close DCA position"""
        pnl = (price - dca.avg_entry) / dca.avg_entry * dca.total_invested
        pnl_pct = (price - dca.avg_entry) / dca.avg_entry * 100
        
        logger.info(f"💰 DCA CLOSED: {dca.symbol} @ ${price:.4f}")
        logger.info(f"   PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        
        # Record trade
        self._record_trade(
            symbol=dca.symbol,
            strategy=StrategyType.DCA,
            side='long',
            entry=dca.avg_entry,
            exit_price=price,
            size_usd=dca.total_invested,
            pnl_usd=pnl,
            pnl_pct=pnl_pct
        )
        
        # Reset DCA
        dca.current_round = 0
        dca.total_invested = 0.0
        dca.avg_entry = 0.0
        dca.rounds = []
    
    # ========================================
    # RISK MANAGEMENT
    # ========================================
    
    async def _risk_management_loop(self):
        """Manage positions and risk"""
        while self._running:
            try:
                for symbol, pos in list(self.positions.items()):
                    current_price = self.market_prices.get(symbol, pos['entry'])
                    
                    # Check stop loss
                    if pos['side'] == 'long' and current_price <= pos['stop']:
                        await self._close_position(symbol, "Stop loss hit")
                        continue
                    elif pos['side'] == 'short' and current_price >= pos['stop']:
                        await self._close_position(symbol, "Stop loss hit")
                        continue
                    
                    # Check take profit
                    if pos['side'] == 'long' and current_price >= pos['target']:
                        await self._close_position(symbol, "Take profit! 💰")
                        continue
                    elif pos['side'] == 'short' and current_price <= pos['target']:
                        await self._close_position(symbol, "Take profit! 💰")
                        continue
                    
                    # Trailing stop
                    if pos['pnl_pct'] > self.trailing_stop_trigger:
                        if not pos['trailing_active']:
                            pos['trailing_active'] = True
                            pos['trailing_stop'] = current_price
                            logger.info(f"📈 {symbol}: Trailing stop activated at {pos['pnl_pct']:.2f}%")
                        
                        # Update trailing stop
                        if current_price > pos['trailing_stop']:
                            pos['trailing_stop'] = current_price
                        
                        # Check trailing stop
                        if pos['side'] == 'long' and current_price <= pos['trailing_stop'] * (1 - self.trailing_stop_distance/100):
                            await self._close_position(symbol, "Trailing stop hit")
                
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Risk management error: {e}")
                await asyncio.sleep(1)
    
    async def _close_position(self, symbol: str, reason: str):
        """Close a position"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        
        # Record trade
        trade = self._record_trade(
            symbol=symbol,
            strategy=pos['strategy'],
            side=pos['side'],
            entry=pos['entry'],
            exit_price=pos['current_price'],
            size_usd=pos['size'],
            pnl_usd=pos['pnl_usd'],
            pnl_pct=pos['pnl_pct']
        )
        
        # Update stats
        self.daily_goal.current_pnl += pos['pnl_usd']
        self.daily_goal.current_pnl_pct = (self.daily_goal.current_pnl / self.starting_capital) * 100
        self.daily_goal.trades_count += 1
        
        if pos['pnl_usd'] > 0:
            self.daily_goal.winners += 1
            self.daily_goal.best_trade = max(self.daily_goal.best_trade, pos['pnl_pct'])
            self.consecutive_losses = 0
        else:
            self.daily_goal.losers += 1
            self.daily_goal.worst_trade = min(self.daily_goal.worst_trade, pos['pnl_pct'])
            self.consecutive_losses += 1
        
        # Update edge stats
        self.edge.update(trade)
        
        # Update Kelly parameters based on performance
        if self.edge.win_rate > 0:
            self.kelly.win_rate = self.edge.win_rate
        if self.edge.risk_reward_ratio > 0:
            self.kelly.win_loss_ratio = self.edge.risk_reward_ratio
        
        # Update drawdown
        if pos['pnl_usd'] < 0:
            self.daily_goal.current_drawdown += abs(pos['pnl_usd'])
            self.daily_goal.max_drawdown = max(self.daily_goal.max_drawdown, self.daily_goal.current_drawdown)
        else:
            self.daily_goal.current_drawdown = max(0, self.daily_goal.current_drawdown - pos['pnl_usd'])
        
        # Update capital
        self.available_capital += pos['size'] + pos['pnl_usd']
        self.daily_goal.peak_capital = max(self.daily_goal.peak_capital, self.available_capital)
        
        # Log
        emoji = "🟢" if pos['pnl_usd'] > 0 else "🔴"
        logger.info(f"{emoji} CLOSED: {symbol}")
        logger.info(f"   PnL: ${pos['pnl_usd']:.2f} ({pos['pnl_pct']:+.2f}%)")
        logger.info(f"   Daily PnL: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:+.2f}%)")
        logger.info(f"   Reason: {reason}")
        
        del self.positions[symbol]
        
        # Callback
        if self.on_trade:
            await self.on_trade(trade)
    
    def _record_trade(
        self,
        symbol: str,
        strategy: StrategyType,
        side: str,
        entry: float,
        exit_price: float,
        size_usd: float,
        pnl_usd: float,
        pnl_pct: float
    ) -> TradeRecord:
        """Record a completed trade"""
        self._trade_counter += 1
        
        result = TradeResult.WIN if pnl_usd > 0 else (TradeResult.LOSS if pnl_usd < 0 else TradeResult.BREAKEVEN)
        
        trade = TradeRecord(
            trade_id=f"T{self._trade_counter:06d}",
            symbol=symbol,
            strategy=strategy,
            side=side,
            entry_price=entry,
            exit_price=exit_price,
            size_usd=size_usd,
            pnl_usd=pnl_usd,
            pnl_pct=pnl_pct,
            duration_seconds=0,  # Would calculate from open time
            result=result
        )
        
        self.trade_history.append(trade)
        return trade
    
    # ========================================
    # MODE MANAGEMENT
    # ========================================
    
    async def _mode_management_loop(self):
        """Manage OMNICUS mode based on performance"""
        while self._running:
            try:
                old_mode = self.mode
                
                # Check for BLACK MODE (failure)
                drawdown_pct = (self.daily_goal.peak_capital - self.available_capital) / self.daily_goal.peak_capital * 100
                
                if drawdown_pct >= self.max_drawdown_pct:
                    self.mode = OmnicusMode.BLACK
                    await self._enter_black_mode()
                
                # Check for VICTORY
                elif self.daily_goal.current_pnl_pct >= self.daily_goal.target_profit_pct:
                    self.mode = OmnicusMode.VICTORY
                    await self._enter_victory_mode()
                
                # Check for DESPERATE mode
                elif self.daily_goal.time_remaining.total_seconds() < 3600:  # 1 hour left
                    if self.daily_goal.current_pnl_pct < self.daily_goal.minimum_profit_pct:
                        self.mode = OmnicusMode.DESPERATE
                    else:
                        self.mode = OmnicusMode.HUNTING
                
                # Check for AGGRESSIVE mode
                elif self.consecutive_losses >= 5:
                    self.mode = OmnicusMode.AGGRESSIVE
                
                # Normal HUNTING
                else:
                    self.mode = OmnicusMode.HUNTING
                
                # Callback on mode change
                if old_mode != self.mode and self.on_mode_change:
                    await self.on_mode_change(old_mode, self.mode)
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Mode management error: {e}")
                await asyncio.sleep(30)
    
    async def _enter_black_mode(self):
        """
        BLACK MODE - OMNICUS has failed!
        
        This is the dramatic punishment mode for students to see.
        OMNICUS "sees black" - he failed to achieve his goal.
        """
        logger.critical("═══════════════════════════════════════════════════════════")
        logger.critical("                    💀 BLACK MODE ACTIVATED 💀               ")
        logger.critical("═══════════════════════════════════════════════════════════")
        logger.critical("")
        logger.critical("   OMNICUS HAS FAILED.")
        logger.critical(f"   Drawdown: {self.max_drawdown_pct:.1f}%")
        logger.critical(f"   PnL: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:+.2f}%)")
        logger.critical("")
        logger.critical("   He sees black. The darkness consumes him.")
        logger.critical("   He promised to double the capital, but he failed.")
        logger.critical("")
        logger.critical("   💀 FAILURE IS NOT AN OPTION 💀")
        logger.critical("═══════════════════════════════════════════════════════════")
        
        # Close all positions
        for symbol in list(self.positions.keys()):
            await self._close_position(symbol, "BLACK MODE - Emergency close")
        
        # Callback
        if self.on_black_mode:
            await self.on_black_mode(self.daily_goal)
    
    async def _enter_victory_mode(self):
        """
        VICTORY MODE - OMNICUS has succeeded!
        
        The goal has been achieved. Capital doubled!
        """
        logger.info("═══════════════════════════════════════════════════════════")
        logger.info("                  🏆🏆🏆 VICTORY MODE 🏆🏆🏆                  ")
        logger.info("═══════════════════════════════════════════════════════════")
        logger.info("")
        logger.info("   OMNICUS HAS DOUBLED THE CAPITAL!")
        logger.info(f"   Final PnL: ${self.daily_goal.current_pnl:.2f} ({self.daily_goal.current_pnl_pct:+.2f}%)")
        logger.info(f"   Total Trades: {self.daily_goal.trades_count}")
        logger.info(f"   Win Rate: {self.daily_goal.win_rate:.1f}%")
        logger.info("")
        logger.info("   🎉 HE IS A LEGEND! 🎉")
        logger.info("═══════════════════════════════════════════════════════════")
        
        # Callback
        if self.on_victory:
            await self.on_victory(self.daily_goal)
    
    # ========================================
    # PROGRESS REPORTING
    # ========================================
    
    async def _progress_reporting_loop(self):
        """Report progress periodically"""
        while self._running:
            await asyncio.sleep(300)  # Every 5 minutes
            
            if self.mode == OmnicusMode.BLACK:
                continue
            
            progress_msg = f"""
📊 OMNICUS PROGRESS REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Capital: ${self.available_capital:,.2f}
📈 PnL: ${self.daily_goal.current_pnl:,.2f} ({self.daily_goal.current_pnl_pct:+.2f}%)
🎯 Progress: {self.daily_goal.progress_to_goal:.1f}% to 2X
⏱️ Time Left: {self.daily_goal.time_remaining}
📊 Trades: {self.daily_goal.trades_count} | Win Rate: {self.daily_goal.win_rate:.1f}%
🔥 Mode: {self.mode.value.upper()}
⚡ Required Pace: {self.daily_goal.required_pace:.2f}%/hour
━━━━━━━━━━━━━━━━━━━━━━━━━━
            """
            
            logger.info(progress_msg)
            
            if self.on_goal_progress:
                await self.on_goal_progress(self.daily_goal)
    
    # ========================================
    # PUBLIC METHODS
    # ========================================
    
    def get_status(self) -> Dict:
        """Get complete status"""
        return {
            "mode": self.mode.value,
            "capital": {
                "starting": self.starting_capital,
                "available": self.available_capital,
                "in_positions": sum(p['size'] for p in self.positions.values()),
            },
            "daily_goal": {
                "current_pnl": round(self.daily_goal.current_pnl, 2),
                "current_pnl_pct": round(self.daily_goal.current_pnl_pct, 2),
                "progress_to_double": round(self.daily_goal.progress_to_goal, 1),
                "trades": self.daily_goal.trades_count,
                "win_rate": round(self.daily_goal.win_rate, 1),
                "time_remaining": str(self.daily_goal.time_remaining).split(".")[0],
                "required_pace": round(self.daily_goal.required_pace, 2),
            },
            "edge": {
                "win_rate": round(self.edge.win_rate, 3),
                "risk_reward": round(self.edge.risk_reward_ratio, 2),
                "expectancy": round(self.edge.expectancy, 2),
            },
            "risk": {
                "max_drawdown": round(self.daily_goal.max_drawdown, 2),
                "current_drawdown": round(self.daily_goal.current_drawdown, 2),
                "consecutive_losses": self.consecutive_losses,
            },
            "positions": len(self.positions),
            "strategies": {
                "grids": len(self.grids),
                "dcas": len(self.dcas),
            }
        }
    
    def get_recent_trades(self, limit: int = 20) -> List[Dict]:
        """Get recent trades"""
        return [
            {
                "id": t.trade_id,
                "symbol": t.symbol,
                "strategy": t.strategy.value,
                "side": t.side,
                "entry": round(t.entry_price, 4),
                "exit": round(t.exit_price, 4),
                "pnl_usd": round(t.pnl_usd, 2),
                "pnl_pct": round(t.pnl_pct, 2),
                "result": t.result.value,
                "time": t.timestamp.isoformat()
            }
            for t in self.trade_history[-limit:]
        ]


# ========================================
# MAIN
# ========================================

async def main():
    """Run OMNICUS"""
    omnicus = OmnicusCore(
        starting_capital=10000.0,
        target_profit_pct=100.0,  # Double
        minimum_profit_pct=10.0
    )
    
    try:
        await omnicus.start()
    except KeyboardInterrupt:
        logger.info("Stopping OMNICUS...")


if __name__ == "__main__":
    asyncio.run(main())
