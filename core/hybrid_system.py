#!/usr/bin/env python3
"""
OMNICUS Hybrid Trading System
=============================
Main trading engine that coordinates everything:
- AI Brain (decision making)
- Soul Engine (personality, voice, emotions)
- Exchange Connectors (trading execution)
- Risk Management (position sizing, stop losses)
- Learning System (memory, skills)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import os

# Core components
from .trading_mode import TradingMode, RiskLevel
from .trading_agent import AITradingAgent, TradeSignal, Position

# Import from sibling packages
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import with error handling
try:
    from agent.ai_brain import AIBrain, MarketContext
    from soul.personality import OMNICUSPersonality
    from soul.voice import VoiceEngine, VoiceMode
    from connectors.unified import UnifiedExchangeManager
    from config.settings import settings
except ImportError as e:
    import logging as log_module
    logger = log_module.getLogger('OMNICUS')
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Please ensure agent/, soul/, connectors/, and config/ directories exist in project root")
    raise

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger('OMNICUS')


class HybridTradingSystem:
    """
    The complete OMNICUS trading system.
    
    Integrates:
    - AI Brain for trading decisions
    - Soul Engine for personality and voice
    - Exchange connectors for execution
    - Risk management
    - Learning and memory
    """
    
    def __init__(
        self,
        trading_mode: TradingMode = TradingMode.SIMULATION,
        initial_balance: float = 10000.0,
        enable_voice: bool = True
    ):
        self.trading_mode = trading_mode
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # System state
        self.is_running = False
        self.session_start = datetime.now()
        self.last_update = datetime.now()
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0
        
        # Initialize OMNICUS's personality and voice
        self.personality = OMNICUSPersonality()
        self.voice = VoiceEngine() if enable_voice else None
        
        # AI Brain
        self.brain = AIBrain()
        
        # Exchange manager
        self.exchanges = UnifiedExchangeManager()
        
        # Position tracking
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        # Callbacks for dashboard updates
        self.status_callback: Optional[Callable] = None
        self.trade_callback: Optional[Callable] = None
        
        # Background tasks
        self._background_task: Optional[asyncio.Task] = None
        self._trading_task: Optional[asyncio.Task] = None
        
        logger.info("=" * 60)
        logger.info("OMNICUS Hybrid Trading System initialized")
        logger.info(f"Mode: {trading_mode.value}")
        logger.info(f"Initial Balance: ${initial_balance:,.2f}")
        logger.info(f"Voice: {'Enabled' if enable_voice else 'Disabled'}")
        logger.info("=" * 60)
    
    async def start(self):
        """Start the trading system"""
        if self.is_running:
            logger.warning("Trading system is already running")
            return
        
        self.is_running = True
        
        # Greet the user
        if self.voice:
            self.voice.say_greeting()
        
        # Connect to exchanges
        await self._connect_exchanges()
        
        # Start background tasks
        self._background_task = asyncio.create_task(self._run_background_tasks())
        self._trading_task = asyncio.create_task(self._trading_loop())
        
        logger.info("🚀 OMNICUS is now LIVE and hunting for profits!")
    
    async def stop(self):
        """Stop the trading system"""
        self.is_running = False
        
        # Say goodbye
        if self.voice:
            self.voice.say_farewell()
        
        # Cancel background tasks
        if self._background_task:
            self._background_task.cancel()
        if self._trading_task:
            self._trading_task.cancel()
        
        # Disconnect from exchanges
        await self.exchanges.disconnect_all()
        
        logger.info("🛑 Trading system stopped")
    
    async def _connect_exchanges(self):
        """Connect to all configured exchanges"""
        credentials = {}
        
        # Get credentials from secure config
        if settings.binance.api_key:
            credentials["binance"] = {
                "api_key": settings.binance.api_key,
                "api_secret": settings.binance.api_secret,
                "testnet": str(settings.binance.testnet).lower()
            }
        
        if credentials:
            results = await self.exchanges.connect_all(credentials)
            for exchange, connected in results.items():
                if connected:
                    logger.info(f"✅ Connected to {exchange}")
                else:
                    logger.warning(f"⚠️  Failed to connect to {exchange}")
        else:
            logger.warning("No exchange credentials configured")
    
    async def execute_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """Execute a trading signal through the AI agent"""
        logger.info(f"Executing signal: {signal.action} {signal.symbol} ({signal.confidence:.2f})")
        
        # Let OMNICUS announce the trade
        if self.voice:
            self.voice.alert_trade_entered(
                symbol=signal.symbol,
                action=signal.action,
                price=signal.entry_price or 0,
                confidence=signal.confidence
            )
        
        # Evaluate with AI brain
        context = MarketContext(
            symbol=signal.symbol,
            current_price=signal.entry_price or 0
        )
        
        brain_signal = await self.brain.generate_signal(context)
        
        # Execute through exchange manager
        result = await self.exchanges.place_order(
            exchange=signal.exchange,
            symbol=signal.symbol,
            side="buy" if signal.action == "buy" else "sell",
            order_type="market",
            quantity=signal.size_usd
        )
        
        if result.success:
            self.total_trades += 1
            
            # Track position
            self.positions[signal.symbol] = {
                'entry_price': signal.entry_price,
                'size': signal.size_usd,
                'stop_loss_pct': signal.stop_loss_pct or 5.0,
                'take_profit_pct': signal.take_profit_pct or 10.0,
                'entry_time': datetime.now(),
                'signal': signal.to_dict()
            }
            
            # Notify callback
            if self.trade_callback:
                self.trade_callback(signal, result)
            
            logger.info(f"Trade executed: {signal.action} {signal.symbol}")
        else:
            logger.warning(f"Trade failed: {result.message}")
        
        return result.to_dict() if hasattr(result, 'to_dict') else result
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Get current market data for specified symbols"""
        market_data = {}
        
        for symbol in symbols:
            try:
                price = await self.exchanges.exchanges.get("binance").get_price(symbol)
                if price > 0:
                    market_data[symbol] = {
                        'price': price,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.debug(f"Error getting data for {symbol}: {e}")
        
        return market_data
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'system': {
                'is_running': self.is_running,
                'trading_mode': self.trading_mode.value,
                'session_start': self.session_start.isoformat(),
                'last_update': self.last_update.isoformat(),
                'uptime': str(datetime.now() - self.session_start)
            },
            'performance': {
                'initial_balance': self.initial_balance,
                'current_balance': self.current_balance,
                'total_pnl': self.total_pnl,
                'daily_pnl': self.daily_pnl,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'max_drawdown': self.max_drawdown
            },
            'positions': self.positions,
            'brain_state': self.brain.get_brain_state(),
            'exchanges': self.exchanges.get_status()
        }
    
    def set_callbacks(self, status_callback: Callable = None, trade_callback: Callable = None):
        """Set callbacks for status updates and trade notifications"""
        self.status_callback = status_callback
        self.trade_callback = trade_callback
    
    async def _run_background_tasks(self):
        """Run background monitoring tasks"""
        while self.is_running:
            try:
                # Update position prices
                await self._update_positions()
                
                # Check stop losses and take profits
                await self._check_exit_conditions()
                
                # Update dashboard
                if self.status_callback:
                    self.status_callback(self.get_system_status())
                
                self.last_update = datetime.now()
                
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background task error: {e}")
                await asyncio.sleep(5)
    
    async def _trading_loop(self):
        """Main trading loop"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        
        while self.is_running:
            try:
                # Get market data
                market_data = await self.get_market_data(symbols)
                
                # Analyze each symbol
                for symbol, data in market_data.items():
                    context = MarketContext(
                        symbol=symbol,
                        current_price=data['price']
                    )
                    
                    # Generate signal from brain
                    signal = await self.brain.generate_signal(context)
                    
                    # If high confidence signal, execute
                    if signal.confidence > 0.8 and signal.action.value != "no_action":
                        trade_signal = TradeSignal(
                            source="ai_analysis",
                            exchange="binance",
                            action="buy" if "buy" in signal.action.value else "sell",
                            symbol=symbol,
                            confidence=signal.confidence,
                            size_usd=500,  # Fixed size for now
                            entry_price=data['price'],
                            reason=signal.reasoning
                        )
                        
                        await self.execute_signal(trade_signal)
                
                # Wait before next iteration
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(30)
    
    async def _update_positions(self):
        """Update position prices and calculate PnL"""
        if not self.positions:
            return
        
        symbols = list(self.positions.keys())
        market_data = await self.get_market_data(symbols)
        
        for symbol, position in self.positions.items():
            if symbol in market_data:
                position['current_price'] = market_data[symbol]['price']
                
                # Calculate PnL
                if position['entry_price'] and position['entry_price'] > 0:
                    pnl_pct = ((position['current_price'] - position['entry_price']) / position['entry_price']) * 100
                    position['unrealized_pnl_pct'] = pnl_pct
                    position['unrealized_pnl'] = position['size'] * (pnl_pct / 100)
    
    async def _check_exit_conditions(self):
        """Check and trigger stop losses and take profits"""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            current_price = position.get('current_price', 0)
            entry_price = position.get('entry_price', 0)
            stop_loss_pct = position.get('stop_loss_pct', 5.0)
            take_profit_pct = position.get('take_profit_pct', 10.0)
            
            if not current_price or not entry_price:
                continue
            
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Check stop loss
            if pnl_pct <= -stop_loss_pct:
                logger.warning(f"🛑 Stop loss triggered for {symbol}: {pnl_pct:.2f}%")
                positions_to_close.append((symbol, 'stop_loss', pnl_pct))
                continue
            
            # Check take profit
            if pnl_pct >= take_profit_pct:
                logger.info(f"💰 Take profit triggered for {symbol}: {pnl_pct:.2f}%")
                positions_to_close.append((symbol, 'take_profit', pnl_pct))
        
        # Close positions
        for symbol, reason, pnl_pct in positions_to_close:
            await self._close_position(symbol, reason, pnl_pct)
    
    async def _close_position(self, symbol: str, reason: str, pnl_pct: float):
        """Close a position and record the result"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        pnl = position.get('unrealized_pnl', 0)
        
        # Update performance metrics
        self.total_pnl += pnl
        self.daily_pnl += pnl
        
        if pnl > 0:
            self.winning_trades += 1
            if self.voice:
                self.voice.alert_big_win(pnl, symbol)
        else:
            self.losing_trades += 1
            if self.voice:
                self.voice.alert_big_loss(pnl, symbol)
        
        # Update max drawdown
        if pnl < 0 and abs(pnl) > self.max_drawdown:
            self.max_drawdown = abs(pnl)
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"Closed position {symbol}: {reason}, PnL: ${pnl:.2f} ({pnl_pct:.2f}%)")


# Convenience function to run the system
async def run_trading_system(
    mode: str = "simulation",
    initial_balance: float = 10000.0,
    enable_voice: bool = True
):
    """Run the trading system"""
    mode_map = {
        'simulation': TradingMode.SIMULATION,
        'testnet': TradingMode.TESTNET,
        'mainnet': TradingMode.MAINNET
    }
    
    trading_mode = mode_map.get(mode.lower(), TradingMode.SIMULATION)
    
    system = HybridTradingSystem(
        trading_mode=trading_mode,
        initial_balance=initial_balance,
        enable_voice=enable_voice
    )
    
    await system.start()
    
    try:
        while system.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(run_trading_system())
