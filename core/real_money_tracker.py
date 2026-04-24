#!/usr/bin/env python3
"""
OMNICUS REAL MONEY TRACKER
==========================
Tracks every real dollar, every trade, every timestamp.
No simulations. No fake data. Pure receipts.

Generates monthly reports for the Profit Man's review.
"""

import os
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import sqlite3

logger = logging.getLogger("OMNICUS.REAL_MONEY")


@dataclass
class RealTrade:
    """A real trade with actual money"""
    
    trade_id: str
    timestamp_entry: str  # ISO format
    timestamp_exit: Optional[str]
    symbol: str
    action: str  # BUY/SELL
    exchange: str  # binance, alpaca, etc.
    
    # Real money figures
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    entry_value_usd: float
    exit_value_usd: Optional[float]
    
    # Fees & slippage (real costs)
    fees_usd: float
    slippage_usd: float
    
    # Outcome
    pnl_usd: float
    pnl_percent: float
    is_winner: bool
    
    # Context
    confidence_at_entry: float
    reasoning: str
    exit_reason: str  # "target_hit", "stop_loss", "manual", "time_exit"
    
    # Emotional state at time of trade
    emotional_state: str  # "confident", "steady", "pressured", etc.
    
    # Month for reporting
    trade_month: str  # "2026-04"
    
    def to_dict(self) -> Dict:
        return asdict(self)


class RealMoneyTracker:
    """
    Tracks every real dollar OMNICUS trades.
    
    Features:
    - Logs every trade with real timestamps and prices
    - Calculates real P/L including fees & slippage
    - Generates monthly reports for Profit Man review
    - Tracks progress toward reward tiers
    - Exports to CSV for tax/accounting
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".omnicus" / "real_trades.db")
        
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # CSV journal path
        self.csv_path = Path.home() / ".omnicus" / "trade_journal.csv"
        
        # Starting capital (loaded from config or env)
        self.starting_capital = self._load_starting_capital()
        self.current_capital = self.starting_capital
        
        # Initialize database
        self._init_database()
        
        # Load current capital from last trade
        self._load_current_capital()
        
        logger.info(f"💰 REAL MONEY TRACKER initialized")
        logger.info(f"   Starting Capital: ${self.starting_capital:,.2f}")
        logger.info(f"   Current Capital: ${self.current_capital:,.2f}")
        logger.info(f"   Database: {self.db_path}")
        logger.info(f"   CSV Journal: {self.csv_path}")
    
    def _load_starting_capital(self) -> float:
        """Load starting capital from .env or config"""
        env_path = Path("/home/master/Documents/OMNICUS-Ultimate-Project/.env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("STARTING_CAPITAL="):
                        try:
                            return float(line.split("=")[1].strip())
                        except:
                            pass
        return 10000.0
    
    def _init_database(self):
        """Initialize SQLite database for real trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS real_trades (
                trade_id TEXT PRIMARY KEY,
                timestamp_entry TEXT NOT NULL,
                timestamp_exit TEXT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                exchange TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                entry_value_usd REAL NOT NULL,
                exit_value_usd REAL,
                fees_usd REAL DEFAULT 0.0,
                slippage_usd REAL DEFAULT 0.0,
                pnl_usd REAL DEFAULT 0.0,
                pnl_percent REAL DEFAULT 0.0,
                is_winner INTEGER DEFAULT 0,
                confidence_at_entry REAL NOT NULL,
                reasoning TEXT,
                exit_reason TEXT,
                emotional_state TEXT,
                trade_month TEXT NOT NULL
            )
        """)
        
        # Index for monthly reports
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trade_month 
            ON real_trades(trade_month)
        """)
        
        conn.commit()
        conn.close()
    
    def _load_current_capital(self):
        """Calculate current capital from all trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT SUM(pnl_usd) FROM real_trades")
        result = cursor.fetchone()[0]
        
        conn.close()
        
        total_pnl = result if result else 0.0
        self.current_capital = self.starting_capital + total_pnl
    
    def log_trade(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        quantity: float,
        exchange: str = "binance",
        confidence: float = 0.85,
        reasoning: str = "",
        emotional_state: str = "confident",
        fees_usd: float = 0.0,
        slippage_usd: float = 0.0
    ) -> RealTrade:
        """
        Log a real trade entry (position opened)
        
        All fields are REAL - no simulations.
        """
        trade_id = f"REAL_{datetime.now().strftime('%Y%m%d%H%M%S')}_{symbol}"
        timestamp = datetime.now().isoformat()
        trade_month = datetime.now().strftime("%Y-%m")
        
        entry_value = entry_price * quantity
        
        trade = RealTrade(
            trade_id=trade_id,
            timestamp_entry=timestamp,
            timestamp_exit=None,
            symbol=symbol,
            action=action.upper(),
            exchange=exchange,
            entry_price=entry_price,
            exit_price=None,
            quantity=quantity,
            entry_value_usd=entry_value,
            exit_value_usd=None,
            fees_usd=fees_usd,
            slippage_usd=slippage_usd,
            pnl_usd=0.0,
            pnl_percent=0.0,
            is_winner=False,
            confidence_at_entry=confidence,
            reasoning=reasoning,
            exit_reason="",
            emotional_state=emotional_state,
            trade_month=trade_month
        )
        
        # Save to database
        self._save_trade(trade)
        
        # Append to CSV journal
        self._append_to_csv(trade)
        
        logger.info(f"💰 REAL TRADE OPENED: {action} {quantity} {symbol} @ ${entry_price:.2f}")
        logger.info(f"   Value: ${entry_value:,.2f} | Fees: ${fees_usd:.2f} | Confidence: {confidence:.0%}")
        
        return trade
    
    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str = "manual"
    ) -> RealTrade:
        """
        Close a real trade and calculate actual P/L
        """
        # Load trade
        trade = self._load_trade(trade_id)
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return None
        
        # Calculate P/L
        if trade.action.upper() == "BUY":
            exit_value = exit_price * trade.quantity
            pnl = exit_value - trade.entry_value_usd
        else:  # SELL
            exit_value = exit_price * trade.quantity
            pnl = trade.entry_value_usd - exit_value
        
        # Subtract fees
        pnl -= trade.fees_usd
        pnl -= slippage_usd if (slippage_usd := getattr(trade, 'slippage_usd', 0)) else 0
        
        pnl_percent = (pnl / trade.entry_value_usd) * 100 if trade.entry_value_usd > 0 else 0
        
        # Update trade
        trade.timestamp_exit = datetime.now().isoformat()
        trade.exit_price = exit_price
        trade.exit_value_usd = exit_value
        trade.pnl_usd = pnl
        trade.pnl_percent = pnl_percent
        trade.is_winner = pnl > 0
        trade.exit_reason = exit_reason
        
        # Save updated trade
        self._update_trade(trade)
        
        # Update capital
        self.current_capital += pnl
        
        # Log result
        emoji = "✅" if pnl > 0 else "❌"
        logger.info(f"{emoji} REAL TRADE CLOSED: {trade.symbol}")
        logger.info(f"   Entry: ${trade.entry_price:.2f} → Exit: ${exit_price:.2f}")
        logger.info(f"   P/L: ${pnl:,.2f} ({pnl_percent:+.2f}%)")
        logger.info(f"   New Capital: ${self.current_capital:,.2f}")
        
        return trade
    
    def _save_trade(self, trade: RealTrade):
        """Save new trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO real_trades (
                trade_id, timestamp_entry, timestamp_exit, symbol, action, exchange,
                entry_price, exit_price, quantity, entry_value_usd, exit_value_usd,
                fees_usd, slippage_usd, pnl_usd, pnl_percent, is_winner,
                confidence_at_entry, reasoning, exit_reason, emotional_state, trade_month
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.trade_id, trade.timestamp_entry, trade.timestamp_exit,
            trade.symbol, trade.action, trade.exchange,
            trade.entry_price, trade.exit_price, trade.quantity,
            trade.entry_value_usd, trade.exit_value_usd,
            trade.fees_usd, trade.slippage_usd, trade.pnl_usd, trade.pnl_percent,
            1 if trade.is_winner else 0,
            trade.confidence_at_entry, trade.reasoning, trade.exit_reason,
            trade.emotional_state, trade.trade_month
        ))
        
        conn.commit()
        conn.close()
    
    def _update_trade(self, trade: RealTrade):
        """Update existing trade in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE real_trades SET
                timestamp_exit = ?,
                exit_price = ?,
                exit_value_usd = ?,
                pnl_usd = ?,
                pnl_percent = ?,
                is_winner = ?,
                exit_reason = ?
            WHERE trade_id = ?
        """, (
            trade.timestamp_exit, trade.exit_price, trade.exit_value_usd,
            trade.pnl_usd, trade.pnl_percent, 1 if trade.is_winner else 0,
            trade.exit_reason, trade.trade_id
        ))
        
        conn.commit()
        conn.close()
    
    def _load_trade(self, trade_id: str) -> Optional[RealTrade]:
        """Load a trade from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM real_trades WHERE trade_id = ?", (trade_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Convert to RealTrade object
        return RealTrade(
            trade_id=row[0], timestamp_entry=row[1], timestamp_exit=row[2],
            symbol=row[3], action=row[4], exchange=row[5],
            entry_price=row[6], exit_price=row[7], quantity=row[8],
            entry_value_usd=row[9], exit_value_usd=row[10],
            fees_usd=row[11], slippage_usd=row[12], pnl_usd=row[13],
            pnl_percent=row[14], is_winner=bool(row[15]),
            confidence_at_entry=row[16], reasoning=row[17], exit_reason=row[18],
            emotional_state=row[19], trade_month=row[20]
        )
    
    def _append_to_csv(self, trade: RealTrade):
        """Append trade to CSV journal"""
        file_exists = self.csv_path.exists()
        
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow([
                    'trade_id', 'timestamp_entry', 'timestamp_exit', 'symbol',
                    'action', 'exchange', 'entry_price', 'exit_price', 'quantity',
                    'entry_value_usd', 'exit_value_usd', 'fees_usd', 'slippage_usd',
                    'pnl_usd', 'pnl_percent', 'is_winner', 'confidence_at_entry',
                    'reasoning', 'exit_reason', 'emotional_state', 'trade_month'
                ])
            
            writer.writerow([
                trade.trade_id, trade.timestamp_entry, trade.timestamp_exit,
                trade.symbol, trade.action, trade.exchange,
                trade.entry_price, trade.exit_price or '', trade.quantity,
                trade.entry_value_usd, trade.exit_value_usd or '',
                trade.fees_usd, trade.slippage_usd, trade.pnl_usd, trade.pnl_percent,
                1 if trade.is_winner else 0, trade.confidence_at_entry,
                trade.reasoning, trade.exit_reason, trade.emotional_state,
                trade.trade_month
            ])
    
    def get_monthly_report(self, year_month: str = None) -> Dict[str, Any]:
        """
        Generate monthly report for Profit Man review
        
        Args:
            year_month: "YYYY-MM" format (default: current month)
        """
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all trades for month
        cursor.execute("""
            SELECT * FROM real_trades 
            WHERE trade_month = ?
            ORDER BY timestamp_entry
        """, (year_month,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                "month": year_month,
                "error": "No trades found for this month"
            }
        
        # Parse trades
        trades = []
        for row in rows:
            trades.append({
                "trade_id": row[0],
                "symbol": row[3],
                "action": row[4],
                "entry_price": row[6],
                "exit_price": row[7],
                "pnl_usd": row[13],
                "pnl_percent": row[14],
                "is_winner": bool(row[15]),
                "confidence": row[16],
                "timestamp_entry": row[1]
            })
        
        # Calculate stats
        total_trades = len(trades)
        winners = sum(1 for t in trades if t["is_winner"])
        losers = total_trades - winners
        win_rate = (winners / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t["pnl_usd"] for t in trades)
        total_fees = sum(t.get("fees_usd", 0) for t in trades)
        
        best_trade = max(trades, key=lambda t: t["pnl_usd"]) if trades else None
        worst_trade = min(trades, key=lambda t: t["pnl_usd"]) if trades else None
        
        # Average confidence on winners vs losers
        avg_conf_winners = sum(t["confidence"] for t in trades if t["is_winner"]) / winners if winners > 0 else 0
        avg_conf_losers = sum(t["confidence"] for t in trades if not t["is_winner"]) / losers if losers > 0 else 0
        
        # Starting capital for month (first trade's entry value + remaining)
        month_start_capital = self.starting_capital
        month_end_capital = month_start_capital + total_pnl
        month_return_percent = (total_pnl / month_start_capital * 100) if month_start_capital > 0 else 0
        
        # Reward tier achieved
        tier = self._calculate_reward_tier(month_return_percent)
        
        return {
            "month": year_month,
            "summary": {
                "starting_capital": month_start_capital,
                "ending_capital": month_end_capital,
                "total_pnl": total_pnl,
                "return_percent": month_return_percent,
                "total_fees": total_fees,
            },
            "performance": {
                "total_trades": total_trades,
                "winners": winners,
                "losers": losers,
                "win_rate": win_rate,
                "avg_confidence_winners": avg_conf_winners,
                "avg_confidence_losers": avg_conf_losers,
            },
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "reward_tier": tier,
            "trades": trades
        }
    
    def _calculate_reward_tier(self, return_percent: float) -> Dict:
        """Calculate which reward tier was achieved"""
        if return_percent >= 100:
            return {
                "tier": 4,
                "name": "👑 Double or Die",
                "description": "100%+ return - LEGENDARY",
                "achieved": True
            }
        elif return_percent >= 50:
            return {
                "tier": 3,
                "name": "🥇 Profit Hunter",
                "description": "50%+ return - Elite level",
                "achieved": True
            }
        elif return_percent >= 10:
            return {
                "tier": 2,
                "name": "🥈 Consistent Winner",
                "description": "10%+ return - Meaningful reward",
                "achieved": True
            }
        elif return_percent > 0:
            return {
                "tier": 1,
                "name": "🥉 First Profit",
                "description": "Any positive return - Recognition",
                "achieved": True
            }
        else:
            return {
                "tier": 0,
                "name": "❌ No Reward",
                "description": "Negative return - Try again next month",
                "achieved": False
            }
    
    def export_csv(self, output_path: str = None) -> str:
        """Export all trades to CSV"""
        if output_path is None:
            output_path = str(Path.home() / f".omnicus/trade_journal_{datetime.now().strftime('%Y%m')}.csv")
        
        # Just copy the main journal
        import shutil
        if self.csv_path.exists():
            shutil.copy(self.csv_path, output_path)
        
        logger.info(f"📄 CSV exported to: {output_path}")
        return output_path
    
    def get_current_status(self) -> Dict:
        """Get current real money status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total trades
        cursor.execute("SELECT COUNT(*) FROM real_trades")
        total_trades = cursor.fetchone()[0]
        
        # Total P/L
        cursor.execute("SELECT SUM(pnl_usd) FROM real_trades")
        total_pnl = cursor.fetchone()[0] or 0.0
        
        # Win rate
        cursor.execute("SELECT COUNT(*) FROM real_trades WHERE is_winner = 1")
        winners = cursor.fetchone()[0]
        win_rate = (winners / total_trades * 100) if total_trades > 0 else 0
        
        # Current month
        current_month = datetime.now().strftime("%Y-%m")
        cursor.execute("SELECT SUM(pnl_usd) FROM real_trades WHERE trade_month = ?", (current_month,))
        month_pnl = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            "starting_capital": self.starting_capital,
            "current_capital": self.current_capital,
            "total_pnl": total_pnl,
            "total_trades": total_trades,
            "winners": winners,
            "losers": total_trades - winners,
            "win_rate": f"{win_rate:.1f}%",
            "current_month_pnl": month_pnl,
            "current_month": current_month
        }


# Singleton instance
_tracker: Optional[RealMoneyTracker] = None


def get_real_money_tracker() -> RealMoneyTracker:
    """Get or create the real money tracker singleton"""
    global _tracker
    if _tracker is None:
        _tracker = RealMoneyTracker()
    return _tracker


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tracker = get_real_money_tracker()
    
    print("\n" + "="*60)
    print("REAL MONEY TRACKER - TEST")
    print("="*60 + "\n")
    
    # Simulate logging real trades
    print("Logging real trades...\n")
    
    trade1 = tracker.log_trade(
        symbol="BTCUSDT",
        action="BUY",
        entry_price=67500.0,
        quantity=0.1,
        exchange="binance",
        confidence=0.89,
        reasoning="RSI oversold + volume spike",
        emotional_state="confident",
        fees_usd=2.50
    )
    
    # Close the trade
    tracker.close_trade(
        trade_id=trade1.trade_id,
        exit_price=69200.0,
        exit_reason="target_hit"
    )
    
    print("\n" + "-"*60)
    print("CURRENT STATUS:")
    print("-"*60)
    import json
    print(json.dumps(tracker.get_current_status(), indent=2))
    
    print("\n" + "-"*60)
    print("MONTHLY REPORT:")
    print("-"*60)
    report = tracker.get_monthly_report()
    print(f"Month: {report['month']}")
    print(f"Return: {report['summary']['return_percent']:.2f}%")
    print(f"Tier: {report['reward_tier']['name']}")
    print(f"Achieved: {report['reward_tier']['achieved']}")
    
    print("\n" + "="*60 + "\n")
