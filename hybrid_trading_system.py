#!/usr/bin/env python3
"""
Hybrid Trading System - Main Trading Engine
FIXED VERSION - Fixed async issues, implemented real stop-loss monitoring
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import threading
import time

from trading_mode import TradingMode, SignalSource, RiskLevel
from trading_agent import AITradingAgent, TradeSignal
from core.database_manager import DatabaseManager
from core.ai_decision_engine import AIDecisionEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HybridTradingSystem:
    """
    Main trading system that coordinates:
    - Multi-exchange trading
    - AI decision making
    - Risk management
    - Performance tracking
    - Learning and adaptation
    """
    
    def __init__(
        self,
        trading_mode: TradingMode = TradingMode.SIMULATION,
        initial_balance: float = 100000.0,
        config_path: str = "exchange_config.json"
    ):
        self.trading_mode = trading_mode
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.config_path = config_path
        
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
        self.happiness_score = 100.0
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.trading_agent = AITradingAgent(
            config_path=config_path,
            paper_trade=(trading_mode == TradingMode.SIMULATION)
        )
        self.ai_engine = AIDecisionEngine()
        
        # Callbacks for dashboard updates
        self.status_callback: Optional[Callable] = None
        self.trade_callback: Optional[Callable] = None
        
        # Background tasks
        self._background_task: Optional[asyncio.Task] = None
        self._trading_task: Optional[asyncio.Task] = None
        self.update_interval = 30  # seconds
        
        # Position tracking for stop-loss
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"Hybrid Trading System initialized")
        logger.info(f"Mode: {trading_mode.value}")
        logger.info(f"Initial Balance: ${initial_balance:,.2f}")
    
    async def start_live_tracking(self):
        """Start live price tracking and trading - FIXED: Now async"""
        if self.is_running:
            logger.warning("Trading system is already running")
            return
        
        self.is_running = True
        logger.info("🚀 Starting live trading system...")
        
        # Initialize database
        self._initialize_database()
        
        # Start background monitoring task - FIXED: Proper async task creation
        self._background_task = asyncio.create_task(self._run_background_tasks())
        
        # Start trading loop
        self._trading_task = asyncio.create_task(self._trading_loop())
        
        logger.info("✅ Trading system started successfully")
    
    async def stop(self):
        """Stop the trading system"""
        self.is_running = False
        logger.info("🛑 Trading system stopped")
        
        # Cancel background tasks
        if self._background_task:
            self._background_task.cancel()
        if self._trading_task:
            self._trading_task.cancel()
        
        # Save session data
        self._save_session_data()
    
    async def execute_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """Execute a trading signal through the AI agent"""
        logger.info(f"Executing signal: {signal.action} {signal.symbol} ({signal.confidence:.2f})")
        
        # Evaluate with AI engine
        ai_decision = await self.ai_engine.evaluate_signal(signal)
        
        if ai_decision.get('action') == 'reject':
            logger.info(f"AI rejected signal: {ai_decision.get('reason')}")
            return {'success': False, 'reason': ai_decision.get('reason')}
        
        # Execute through trading agent
        result = await self.trading_agent.execute_trade(signal)
        
        if result.get('success'):
            self.total_trades += 1
            
            # Track position for stop-loss monitoring
            if signal.action.lower() == 'buy':
                self.positions[signal.symbol] = {
                    'entry_price': signal.entry_price,
                    'size': signal.size_usd,
                    'stop_loss_pct': signal.stop_loss_pct or 5.0,
                    'take_profit_pct': signal.take_profit_pct or 10.0,
                    'entry_time': datetime.now(),
                    'trailing_stop_active': False,
                    'highest_price': signal.entry_price
                }
            
            # Update happiness score
            self._update_happiness_score(result)
            
            # Log trade to database
            await self._log_trade(signal, result)
            
            # Notify dashboard
            if self.trade_callback:
                self.trade_callback(signal, result)
            
            logger.info(f"Trade executed successfully: {signal.action} {signal.symbol}")
        else:
            logger.warning(f"Trade failed: {result.get('error')}")
        
        return result
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Get current market data for specified symbols"""
        market_data = {}
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                for symbol in symbols:
                    try:
                        # Get real price from Binance API
                        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                market_data[symbol] = {
                                    'price': float(data.get('lastPrice', 0)),
                                    'change_24h': float(data.get('priceChangePercent', 0)),
                                    'volume': float(data.get('volume', 0)),
                                    'high_24h': float(data.get('highPrice', 0)),
                                    'low_24h': float(data.get('lowPrice', 0)),
                                    'timestamp': datetime.now().isoformat()
                                }
                            else:
                                logger.warning(f"Failed to get data for {symbol}")
                    except Exception as e:
                        logger.error(f"Error fetching {symbol}: {e}")
                        
        except Exception as e:
            logger.error(f"Market data fetch error: {e}")
            # Return empty dict on failure
            return {}
        
        return market_data
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        agent_status = self.trading_agent.get_status()
        
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
                'max_drawdown': self.max_drawdown,
                'happiness_score': self.happiness_score
            },
            'positions': self.positions,
            'exposure': agent_status.get('total_exposure_usd', 0),
            'ai_engine': {
                'confidence': self.ai_engine.current_confidence,
                'last_analysis': self.ai_engine.last_analysis_time
            }
        }
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def set_trade_callback(self, callback: Callable):
        """Set callback for trade notifications"""
        self.trade_callback = callback
    
    async def _run_background_tasks(self):
        """Run background monitoring tasks - FIXED: Now fully async"""
        while self.is_running:
            try:
                # Update position prices
                await self._update_positions()
                
                # Check for stop losses and take profits
                await self._check_stop_losses()
                
                # Update dashboard
                if self.status_callback:
                    self.status_callback(self.get_system_status())
                
                # AI learning
                self._ai_learning_update()
                
                self.last_update = datetime.now()
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                logger.info("Background tasks cancelled")
                break
            except Exception as e:
                logger.error(f"Background task error: {e}")
                await asyncio.sleep(5)
    
    async def _trading_loop(self):
        """Main trading loop"""
        while self.is_running:
            try:
                # Generate trading signals
                signals = await self._generate_signals()
                
                # Process signals
                for signal in signals:
                    if self.is_running:
                        await self.execute_signal(signal)
                
                # Wait for next iteration
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                logger.info("Trading loop cancelled")
                break
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(30)
    
    async def _generate_signals(self) -> List[TradeSignal]:
        """Generate trading signals using AI engine"""
        signals = []
        
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        market_data = await self.get_market_data(symbols)
        
        for symbol in symbols:
            if symbol in market_data:
                signal = await self.ai_engine.generate_signal(
                    symbol, market_data.get(symbol, {})
                )
                
                if signal and signal.confidence > 0.7:
                    signals.append(signal)
        
        return signals
    
    async def _update_positions(self):
        """Update position prices and calculate PnL - IMPLEMENTED"""
        if not self.positions:
            return
        
        symbols = list(self.positions.keys())
        market_data = await self.get_market_data(symbols)
        
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol]['price']
                position['current_price'] = current_price
                
                # Update highest price for trailing stop
                if current_price > position.get('highest_price', 0):
                    position['highest_price'] = current_price
                    position['trailing_stop_active'] = True
                
                # Calculate unrealized PnL
                entry_price = position['entry_price']
                if entry_price and entry_price > 0:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    position['unrealized_pnl_pct'] = pnl_pct
                    position['unrealized_pnl'] = position['size'] * (pnl_pct / 100)
    
    async def _check_stop_losses(self):
        """Check and trigger stop losses - IMPLEMENTED"""
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
                continue
            
            # Check trailing stop (if price dropped from highest)
            if position.get('trailing_stop_active'):
                highest_price = position.get('highest_price', current_price)
                trailing_stop_pct = 3.0  # 3% trailing stop
                
                drop_from_high = ((highest_price - current_price) / highest_price) * 100
                if drop_from_high >= trailing_stop_pct:
                    logger.info(f"📈 Trailing stop triggered for {symbol}")
                    positions_to_close.append((symbol, 'trailing_stop', pnl_pct))
        
        # Close positions
        for symbol, reason, pnl_pct in positions_to_close:
            await self._close_position(symbol, reason, pnl_pct)
    
    async def _close_position(self, symbol: str, reason: str, pnl_pct: float):
        """Close a position and record the result"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Update performance metrics
        pnl = position.get('unrealized_pnl', 0)
        self.total_pnl += pnl
        self.daily_pnl += pnl
        
        if pnl > 0:
            self.winning_trades += 1
            self.happiness_score = min(100, self.happiness_score + 1)
        else:
            self.losing_trades += 1
            self.happiness_score = max(0, self.happiness_score - 2)
        
        # Update max drawdown
        if pnl < 0 and abs(pnl) > self.max_drawdown:
            self.max_drawdown = abs(pnl)
        
        # Log to database
        try:
            self.db_manager.close_position(
                session_id=getattr(self, 'session_id', ''),
                symbol=symbol,
                exit_price=position.get('current_price', 0)
            )
        except Exception as e:
            logger.error(f"Failed to log position close: {e}")
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(f"Closed position {symbol}: {reason}, PnL: ${pnl:.2f} ({pnl_pct:.2f}%)")
    
    def _ai_learning_update(self):
        """Update AI learning based on performance"""
        if self.daily_pnl > 0:
            self.happiness_score = min(100, self.happiness_score + 0.1)
        elif self.daily_pnl < 0:
            self.happiness_score = max(0, self.happiness_score - 0.2)
        
        # Update AI engine weights based on performance
        if self.total_trades > 0 and self.total_trades % 10 == 0:
            win_rate = self.winning_trades / self.total_trades
            self.ai_engine.update_weights({'win_rate': win_rate})
    
    def _update_happiness_score(self, trade_result: Dict[str, Any]):
        """Update happiness score based on trade result"""
        if trade_result.get('success'):
            self.winning_trades += 1
            self.happiness_score = min(100, self.happiness_score + 1)
        else:
            self.losing_trades += 1
            self.happiness_score = max(0, self.happiness_score - 2)
    
    def _initialize_database(self):
        """Initialize database for session"""
        try:
            session_id = self.db_manager.create_session(
                trading_mode=self.trading_mode.value,
                initial_balance=self.initial_balance
            )
            self.session_id = session_id
            logger.info(f"Database session created: {session_id}")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    async def _log_trade(self, signal: TradeSignal, result: Dict[str, Any]):
        """Log trade to database"""
        try:
            self.db_manager.log_trade(
                session_id=self.session_id,
                signal=signal.to_dict(),
                result=result
            )
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
    
    def _save_session_data(self):
        """Save session data before shutdown"""
        try:
            self.db_manager.update_session(
                session_id=self.session_id,
                final_balance=self.current_balance,
                total_trades=self.total_trades,
                final_pnl=self.total_pnl
            )
            logger.info("Session data saved successfully")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")


# Convenience function to run the system
async def run_trading_system(
    mode: str = "simulation",
    initial_balance: float = 100000.0
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
        initial_balance=initial_balance
    )
    
    await system.start_live_tracking()
    
    try:
        # Keep running
        while system.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(run_trading_system())
