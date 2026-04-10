#!/usr/bin/env python3
"""
AI Trading Agent - Unified multi-exchange autonomous trading
Coordinates trading across crypto, prediction markets, and token scanning
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import os

from .trading_mode import TradingMode, RiskLevel, SignalSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    """Signal from AI or scanner to execute a trade"""
    source: str  # 'axiom', 'ai_analysis', 'manual', 'scheduled'
    exchange: str  # 'binance', 'polymarket', 'kraken', 'mexc'
    action: str  # 'buy', 'sell', 'hold'
    symbol: str
    confidence: float
    size_usd: float
    entry_price: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'exchange': self.exchange,
            'action': self.action,
            'symbol': self.symbol,
            'confidence': self.confidence,
            'size_usd': self.size_usd,
            'entry_price': self.entry_price,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Position:
    """Open position tracking"""
    exchange: str
    symbol: str
    side: str  # 'long', 'short'
    size: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    pnl_usd: float
    pnl_pct: float
    opened_at: datetime
    trailing_stop_active: bool = False
    trailing_stop_price: Optional[float] = None


class AITradingAgent:
    """
    Central AI trading agent that coordinates:
    - Multi-exchange execution (Binance, Polymarket, Kraken, MEXC)
    - Signal evaluation from Axiom scanner
    - Risk management and position sizing
    - Claude/DeepSeek AI decision integration
    """

    def __init__(
        self,
        config_path: str = "exchange_config.json",
        paper_trade: bool = True,
    ):
        self.config_path = config_path
        self.paper_trade = paper_trade
        self.config: Dict[str, Any] = {}
        self.positions: Dict[str, Position] = {}
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        self.session_start: datetime = datetime.now()

        # AI decision callback (to be set by MCP server)
        self.ai_decision_callback: Optional[Callable] = None

        # Exchange connections (would be actual API clients)
        self.exchanges: Dict[str, Any] = {}

        self._load_config()

    def _load_config(self):
        """Load exchange configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded config for {len(self.config.get('exchanges', {}))} exchanges")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
            self.config = {}

    async def evaluate_signal(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        AI evaluation of a trading signal.
        Uses Claude/DeepSeek to make final trading decision.
        """
        ai_config = self.config.get('ai_trading', {})

        # Check risk limits first
        if not self._check_risk_limits(signal):
            return {
                'action': 'reject',
                'reason': 'Risk limits exceeded',
                'confidence': 0.0
            }

        # If AI callback is set, get AI decision
        if self.ai_decision_callback:
            ai_decision = await self.ai_decision_callback(signal)
            return ai_decision

        # Default: evaluate based on confidence thresholds
        min_confidence = ai_config.get('auto_trade_threshold', 0.85)

        if signal.confidence >= min_confidence:
            return {
                'action': 'execute',
                'confidence': signal.confidence,
                'reason': f"Signal confidence {signal.confidence:.2f} >= threshold {min_confidence}"
            }
        else:
            return {
                'action': 'hold',
                'confidence': signal.confidence,
                'reason': f"Signal confidence {signal.confidence:.2f} < threshold {min_confidence}"
            }

    async def execute_trade(self, signal: TradeSignal) -> Dict[str, Any]:
        """
        Execute a trade across the appropriate exchange.
        Handles paper trading vs live trading.
        """
        exchange_name = signal.exchange

        if exchange_name not in self.config.get('exchanges', {}):
            return {'success': False, 'error': f'Unknown exchange: {exchange_name}'}

        exchange_config = self.config['exchanges'][exchange_name]

        # Check exchange-specific limits
        limits = exchange_config.get('risk_limits', {})
        if signal.size_usd > limits.get('max_position_size_usd', float('inf')):
            return {
                'success': False,
                'error': f'Position size {signal.size_usd} exceeds max {limits["max_position_size_usd"]}'
            }

        if self.daily_trades >= limits.get('max_daily_trades', 999):
            return {'success': False, 'error': 'Daily trade limit reached'}

        # Calculate position parameters
        stop_loss = signal.stop_loss_pct or self.config['ai_trading']['risk_management'].get('stop_loss_pct', 5.0)
        take_profit = signal.take_profit_pct or self.config['ai_trading']['risk_management'].get('take_profit_pct', 15.0)

        if self.paper_trade:
            logger.info(f"[PAPER] {signal.action.upper()} {signal.size_usd} USD of {signal.symbol} on {exchange_name}")
            logger.info(f"[PAPER] Reason: {signal.reason}")

            # Simulate position opening
            position = Position(
                exchange=exchange_name,
                symbol=signal.symbol,
                side='long' if signal.action == 'buy' else 'short',
                size=signal.size_usd,
                entry_price=signal.entry_price or 0,
                current_price=signal.entry_price or 0,
                stop_loss=stop_loss,
                take_profit=take_profit,
                pnl_usd=0,
                pnl_pct=0,
                opened_at=datetime.now()
            )

            self.positions[f"{exchange_name}:{signal.symbol}"] = position
            self.daily_trades += 1

            return {
                'success': True,
                'paper_trade': True,
                'position': position.__dict__,
                'signal': signal.to_dict()
            }

        # Live trading would go here (disabled in paper mode)
        return {'success': False, 'error': 'Live trading not enabled'}

    async def close_position(
        self,
        exchange: str,
        symbol: str,
        reason: str = "manual"
    ) -> Dict[str, Any]:
        """Close an open position"""
        pos_key = f"{exchange}:{symbol}"

        if pos_key not in self.positions:
            return {'success': False, 'error': 'Position not found'}

        position = self.positions[pos_key]

        if self.paper_trade:
            logger.info(f"[PAPER] CLOSE position {symbol} on {exchange}")
            logger.info(f"[PAPER] PnL: ${position.pnl_usd:.2f} ({position.pnl_pct:.2f}%)")
            logger.info(f"[PAPER] Reason: {reason}")

            # Update daily PnL
            self.daily_pnl += position.pnl_usd

            del self.positions[pos_key]

            return {
                'success': True,
                'paper_trade': True,
                'pnl_usd': position.pnl_usd,
                'pnl_pct': position.pnl_pct
            }

        return {'success': False, 'error': 'Live trading not enabled'}

    def _check_risk_limits(self, signal: TradeSignal) -> bool:
        """Check global risk limits before executing"""
        ai_config = self.config.get('ai_trading', {})
        rm = ai_config.get('risk_management', {})

        # Check daily loss limit
        max_loss = rm.get('max_loss_per_day_usd', 500)
        if self.daily_pnl < -max_loss:
            logger.warning(f"Daily loss limit reached: ${abs(self.daily_pnl):.2f} > ${max_loss}")
            return False

        # Check total exposure
        total_exposure = sum(p.size for p in self.positions.values())
        max_exposure = rm.get('global_max_exposure_usd', 50000)
        if total_exposure + signal.size_usd > max_exposure:
            logger.warning(f"Exposure limit reached: ${total_exposure} + ${signal.size_usd} > ${max_exposure}")
            return False

        return True

    async def update_positions(self, prices: Dict[str, Dict[str, float]]):
        """Update position prices and check stops"""
        for pos_key, position in list(self.positions.items()):
            if position.exchange in prices and position.symbol in prices[position.exchange]:
                position.current_price = prices[position.exchange][position.symbol]

                # Calculate PnL
                if position.side == 'long':
                    position.pnl_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
                else:
                    position.pnl_pct = ((position.entry_price - position.current_price) / position.entry_price) * 100

                position.pnl_usd = position.size * (position.pnl_pct / 100)

                # Check stop loss
                if position.pnl_pct <= -position.stop_loss:
                    await self.close_position(position.exchange, position.symbol, "stop_loss")
                    continue

                # Check take profit
                if position.pnl_pct >= position.take_profit:
                    await self.close_position(position.exchange, position.symbol, "take_profit")
                    continue

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'paper_trade': self.paper_trade,
            'positions': {k: p.__dict__ for k, p in self.positions.items()},
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'session_duration': str(datetime.now() - self.session_start),
            'total_exposure_usd': sum(p.size for p in self.positions.values()),
            'exchanges_configured': list(self.config.get('exchanges', {}).keys())
        }
