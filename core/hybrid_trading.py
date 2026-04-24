#!/usr/bin/env python3
"""
OMNICUS HYBRID TRADING ENGINE
=============================
Hybrid Trading: Paper trades for learning + Real trades when confidence is high.

This module enables OMNICUS to:
1. Paper trade by default (learning mode, no risk)
2. Execute real trades only when confidence exceeds threshold (85%+)
3. Track performance separately for paper vs real
4. Learn from paper trades before risking real capital

"Double the money. Period."
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("OMNICUS.HYBRID")


class TradeMode(Enum):
    PAPER = "paper"
    REAL = "real"
    HYBRID = "hybrid"


@dataclass
class HybridConfig:
    """Configuration for hybrid trading"""
    
    # Confidence threshold for real trades
    confidence_threshold: float = 0.85
    
    # Max position size for real trades (% of capital)
    max_real_position_percent: float = 2.0
    
    # Number of paper trades before allowing real trades
    paper_learning_trades: int = 50
    
    # Current paper trade count
    paper_trades_completed: int = 0
    
    # Enable/disable hybrid mode
    hybrid_enabled: bool = True
    
    # Minimum capital for real trading
    min_capital_for_real: float = 1000.0
    
    # Daily loss limit for real trading (stop if exceeded)
    daily_loss_limit: float = 500.0
    
    # Daily profit target (celebrate when hit)
    daily_profit_target: float = 1000.0


@dataclass
class TradeRecord:
    """Record of a single trade (paper or real)"""
    
    trade_id: str
    mode: TradeMode
    symbol: str
    action: str  # BUY/SELL
    amount: float
    entry_price: float
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    confidence: float = 0.0
    reasoning: str = ""
    opened_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    is_winner: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "trade_id": self.trade_id,
            "mode": self.mode.value,
            "symbol": self.symbol,
            "action": self.action,
            "amount": self.amount,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "is_winner": self.is_winner,
            "notes": self.notes
        }


class HybridTradingEngine:
    """
    Hybrid Trading Engine for OMNICUS
    
    Manages both paper and real trading:
    - Paper trades: Always allowed, for learning
    - Real trades: Only when confidence > threshold AND conditions met
    
    The engine tracks:
    - Paper trading performance (learning metrics)
    - Real trading performance (actual P/L)
    - Confidence calibration (is OMNICUS overconfident?)
    - Learning progress (when to graduate to more real trades)
    """
    
    def __init__(self, config: HybridConfig = None):
        self.config = config or HybridConfig()
        
        # Performance tracking
        self.paper_trades: list[TradeRecord] = []
        self.real_trades: list[TradeRecord] = []
        
        # Capital tracking
        self.paper_capital: float = 10000.0
        self.real_capital: float = 10000.0
        self.paper_pnl: float = 0.0
        self.real_pnl: float = 0.0
        
        # Daily tracking
        self.daily_real_pnl: float = 0.0
        self.daily_real_trades: int = 0
        self.last_reset_date: Optional[datetime] = None
        
        # State
        self.is_trading: bool = False
        self.trading_mode: TradeMode = TradeMode.PAPER
        
        logger.info("🔀 Hybrid Trading Engine initialized")
        logger.info(f"   Confidence threshold for real trades: {self.config.confidence_threshold:.0%}")
        logger.info(f"   Max real position: {self.config.max_real_position_percent}%")
        logger.info(f"   Paper learning trades required: {self.config.paper_learning_trades}")
    
    def should_trade_real(self, confidence: float, symbol: str = None) -> Tuple[bool, str]:
        """
        Determine if a trade should be executed with real money
        
        Args:
            confidence: AI confidence level (0.0 to 1.0)
            symbol: Trading symbol
            
        Returns:
            Tuple of (should_trade_real, reason)
        """
        # Check hybrid mode enabled
        if not self.config.hybrid_enabled:
            return False, "Hybrid mode disabled"
        
        # Check confidence threshold
        if confidence < self.config.confidence_threshold:
            return False, f"Confidence {confidence:.0%} below threshold {self.config.confidence_threshold:.0%}"
        
        # Check paper learning requirement
        if self.config.paper_trades_completed < self.config.paper_learning_trades:
            remaining = self.config.paper_learning_trades - self.config.paper_trades_completed
            return False, f"Need {remaining} more paper trades before real trading"
        
        # Check capital
        if self.real_capital < self.config.min_capital_for_real:
            return False, f"Real capital ${self.real_capital:.2f} below minimum ${self.config.min_capital_for_real:.2f}"
        
        # Check daily loss limit
        if self.daily_real_pnl <= -self.config.daily_loss_limit:
            return False, f"Daily loss limit ${self.config.daily_loss_limit:.2f} reached"
        
        # All checks passed
        return True, f"Confidence {confidence:.0%} exceeds threshold - REAL TRADE APPROVED"
    
    def execute_trade(
        self,
        symbol: str,
        action: str,
        amount: float,
        entry_price: float,
        confidence: float,
        reasoning: str,
        force_mode: TradeMode = None
    ) -> TradeRecord:
        """
        Execute a trade (paper or real based on conditions)
        
        Args:
            symbol: Trading symbol
            action: BUY or SELL
            amount: Trade amount in USD
            entry_price: Entry price
            confidence: AI confidence level
            reasoning: Trade reasoning
            force_mode: Force paper or real mode (optional)
            
        Returns:
            TradeRecord with trade details
        """
        # Determine mode
        if force_mode:
            mode = force_mode
            mode_reason = f"Force {mode.value} mode"
        else:
            should_real, mode_reason = self.should_trade_real(confidence, symbol)
            mode = TradeMode.REAL if should_real else TradeMode.PAPER
        
        # Create trade record
        trade_id = f"{mode.value}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{symbol}"
        
        trade = TradeRecord(
            trade_id=trade_id,
            mode=mode,
            symbol=symbol,
            action=action,
            amount=amount,
            entry_price=entry_price,
            confidence=confidence,
            reasoning=reasoning
        )
        
        # Execute based on mode
        if mode == TradeMode.PAPER:
            self._execute_paper_trade(trade)
            self.config.paper_trades_completed += 1
            logger.info(f"📝 PAPER TRADE: {action} {symbol} ${amount:.2f} @ ${entry_price:.2f}")
        else:
            self._execute_real_trade(trade)
            logger.info(f"💰 REAL TRADE: {action} {symbol} ${amount:.2f} @ ${entry_price:.2f}")
        
        logger.info(f"   Reason: {mode_reason}")
        logger.info(f"   Confidence: {confidence:.0%}")
        
        return trade
    
    def _execute_paper_trade(self, trade: TradeRecord):
        """Execute a paper trade (simulated)"""
        self.paper_trades.append(trade)
        # Paper trades don't affect real capital
        logger.debug(f"   Paper capital: ${self.paper_capital:,.2f}")
    
    def _execute_real_trade(self, trade: TradeRecord):
        """Execute a real trade (would connect to exchange)"""
        self.real_trades.append(trade)
        self.daily_real_trades += 1
        # Real trades would actually execute on exchange
        # For now, just track them
        logger.debug(f"   Real capital: ${self.real_capital:,.2f}")
    
    def close_trade(
        self,
        trade: TradeRecord,
        exit_price: float,
        notes: str = ""
    ) -> float:
        """
        Close an open trade and calculate P/L
        
        Args:
            trade: The trade to close
            exit_price: Exit price
            notes: Optional notes
            
        Returns:
            P/L amount
        """
        # Calculate P/L
        if trade.action.upper() == "BUY":
            pnl = (exit_price - trade.entry_price) * (trade.amount / trade.entry_price)
        else:  # SELL
            pnl = (trade.entry_price - exit_price) * (trade.amount / trade.entry_price)
        
        pnl_percent = (pnl / trade.amount) * 100
        
        # Update trade record
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.closed_at = datetime.now()
        trade.is_winner = pnl > 0
        trade.notes = notes
        
        # Update capital based on mode
        if trade.mode == TradeMode.PAPER:
            self.paper_capital += pnl
            self.paper_pnl += pnl
        else:
            self.real_capital += pnl
            self.real_pnl += pnl
            self.daily_real_pnl += pnl
        
        # Log result
        emoji = "✅" if pnl > 0 else "❌"
        mode_emoji = "📝" if trade.mode == TradeMode.PAPER else "💰"
        
        logger.info(f"{emoji} {mode_emoji} CLOSED: {trade.symbol} | P/L: ${pnl:,.2f} ({pnl_percent:+.2f}%)")
        logger.info(f"   Entry: ${trade.entry_price:.2f} → Exit: ${exit_price:.2f}")
        
        if pnl > 0:
            self._on_win(trade)
        else:
            self._on_loss(trade)
        
        return pnl
    
    def _on_win(self, trade: TradeRecord):
        """Handle winning trade"""
        if trade.mode == TradeMode.REAL and trade.pnl >= self.config.daily_profit_target:
            logger.info(f"🎉 DAILY PROFIT TARGET REACHED! +${trade.pnl:,.2f}")
        
        if trade.pnl >= 500:
            logger.info(f"🔥 BIG WIN! +${trade.pnl:,.2f}")
    
    def _on_loss(self, trade: TradeRecord):
        """Handle losing trade"""
        if trade.mode == TradeMode.REAL:
            if abs(self.daily_real_pnl) >= self.config.daily_loss_limit:
                logger.warning(f"⚠️ DAILY LOSS LIMIT REACHED! Stopping real trading.")
                self.is_trading = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive trading statistics"""
        # Paper stats
        paper_wins = sum(1 for t in self.paper_trades if t.is_winner)
        paper_win_rate = (paper_wins / len(self.paper_trades) * 100) if self.paper_trades else 0
        
        # Real stats
        real_wins = sum(1 for t in self.real_trades if t.is_winner)
        real_win_rate = (real_wins / len(self.real_trades) * 100) if self.real_trades else 0
        
        # Learning progress
        learning_progress = min(1.0, self.config.paper_trades_completed / self.config.paper_learning_trades)
        ready_for_real = learning_progress >= 1.0
        
        return {
            "mode": "hybrid" if self.config.hybrid_enabled else "paper" if self.trading_mode == TradeMode.PAPER else "real",
            "paper_trading": {
                "trades": len(self.paper_trades),
                "wins": paper_wins,
                "losses": len(self.paper_trades) - paper_wins,
                "win_rate": f"{paper_win_rate:.1f}%",
                "pnl": f"${self.paper_pnl:,.2f}",
                "capital": f"${self.paper_capital:,.2f}",
            },
            "real_trading": {
                "trades": len(self.real_trades),
                "wins": real_wins,
                "losses": len(self.real_trades) - real_wins,
                "win_rate": f"{real_win_rate:.1f}%",
                "pnl": f"${self.real_pnl:,.2f}",
                "capital": f"${self.real_capital:,.2f}",
                "daily_pnl": f"${self.daily_real_pnl:,.2f}",
                "daily_trades": self.daily_real_trades,
            },
            "learning_progress": {
                "paper_trades_completed": self.config.paper_trades_completed,
                "paper_trades_required": self.config.paper_learning_trades,
                "progress_percent": f"{learning_progress:.0%}",
                "ready_for_real": ready_for_real,
            },
            "configuration": {
                "confidence_threshold": f"{self.config.confidence_threshold:.0%}",
                "max_real_position": f"{self.config.max_real_position_percent}%",
                "daily_loss_limit": f"${self.config.daily_loss_limit:,.2f}",
                "daily_profit_target": f"${self.config.daily_profit_target:,.2f}",
            }
        }
    
    def reset_daily(self):
        """Reset daily tracking (call at start of new trading day)"""
        self.daily_real_pnl = 0.0
        self.daily_real_trades = 0
        self.last_reset_date = datetime.now()
        logger.info("📅 Daily trading stats reset")
    
    def calibrate_confidence(self) -> Dict[str, float]:
        """
        Analyze if OMNICUS's confidence matches actual performance
        
        Returns:
            Calibration metrics
        """
        all_trades = self.paper_trades + self.real_trades
        
        if not all_trades:
            return {"error": "No trades to analyze"}
        
        # Group by confidence ranges
        high_conf = [t for t in all_trades if t.confidence >= 0.8]
        med_conf = [t for t in all_trades if 0.6 <= t.confidence < 0.8]
        low_conf = [t for t in all_trades if t.confidence < 0.6]
        
        def win_rate(trades):
            if not trades:
                return 0.0
            wins = sum(1 for t in trades if t.is_winner)
            return wins / len(trades)
        
        return {
            "high_confidence_win_rate": win_rate(high_conf),
            "medium_confidence_win_rate": win_rate(med_conf),
            "low_confidence_win_rate": win_rate(low_conf),
            "total_trades_analyzed": len(all_trades),
            "calibration_note": "High confidence should have highest win rate"
        }


# Singleton instance
_hybrid_engine: Optional[HybridTradingEngine] = None


def get_hybrid_engine() -> HybridTradingEngine:
    """Get or create the hybrid trading engine singleton"""
    global _hybrid_engine
    if _hybrid_engine is None:
        _hybrid_engine = HybridTradingEngine()
    return _hybrid_engine


if __name__ == "__main__":
    # Test the hybrid engine
    logging.basicConfig(level=logging.INFO)
    
    engine = get_hybrid_engine()
    
    print("\n" + "="*60)
    print("HYBRID TRADING ENGINE TEST")
    print("="*60 + "\n")
    
    # Simulate some paper trades
    for i in range(5):
        trade = engine.execute_trade(
            symbol="BTCUSDT",
            action="BUY",
            amount=1000,
            entry_price=50000,
            confidence=0.70,
            reasoning="Test paper trade"
        )
        engine.close_trade(trade, exit_price=50000 * (1 + (0.05 if i % 2 == 0 else -0.03)))
    
    print("\n" + "-"*60)
    print("STATS AFTER PAPER TRADES:")
    print("-"*60)
    import json
    print(json.dumps(engine.get_stats(), indent=2))
    
    print("\n" + "="*60 + "\n")
