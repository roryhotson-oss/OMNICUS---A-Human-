#!/usr/bin/env python3
"""
Database Manager - Database Integration
FIXED VERSION - Bug fixed: wining_trades -> winning_trades, added SQL injection protection
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Whitelist of valid column names for SQL injection protection
VALID_SESSION_COLUMNS = {
    'final_balance', 'total_trades', 'winning_trades', 'losing_trades',
    'total_pnl', 'max_drawdown', 'happiness_score', 'status', 'end_time'
}

VALID_POSITION_COLUMNS = {
    'current_price', 'unrealized_pnl', 'unrealized_pnl_pct', 
    'stop_loss', 'take_profit', 'trailing_stop_price', 'status', 'closed_at'
}


class DatabaseManager:
    """
    Database manager for the AI trading system.
    Manages: Trading sessions, Trade history, Performance metrics, AI decisions, Market data
    """
    
    def __init__(self, db_path: str = "crypto_trading.db"):
        self.db_path = db_path
        self.connection = None
        self._initialize_database()
        logger.info(f"Database Manager initialized: {db_path}")
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            cursor = self.connection.cursor()
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    trading_mode TEXT NOT NULL,
                    initial_balance REAL NOT NULL,
                    final_balance REAL,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0,
                    max_drawdown REAL DEFAULT 0,
                    happiness_score REAL DEFAULT 100,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            
            # Create trades table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    trade_id TEXT UNIQUE,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    action TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL,
                    status TEXT DEFAULT 'pending',
                    pnl REAL,
                    pnl_percentage REAL,
                    fees REAL DEFAULT 0,
                    signal_confidence REAL,
                    ai_reasoning TEXT,
                    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exit_time TIMESTAMP,
                    stop_loss REAL,
                    take_profit REAL,
                    FOREIGN KEY (session_id) REFERENCES trading_sessions (session_id)
                )
            """)
            
            # Create market_data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume_24h REAL,
                    change_24h REAL,
                    high_24h REAL,
                    low_24h REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp
                ON market_data (symbol, timestamp);
            """)
            
            # Create ai_decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    risk_level TEXT,
                    technical_score REAL,
                    sentiment_score REAL,
                    momentum_score REAL,
                    volume_score REAL,
                    whale_score REAL,
                    reasoning TEXT,
                    indicators TEXT,  
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES trading_sessions (session_id)
                )
            """)
            
            # Create performance_metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES trading_sessions (session_id)
                )
            """)
            
            # Create positions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    side TEXT NOT NULL,
                    size REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL,
                    unrealized_pnl REAL,
                    unrealized_pnl_pct REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    trailing_stop_price REAL,
                    status TEXT DEFAULT 'open',
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES trading_sessions (session_id)
                )
            """)
            
            self.connection.commit()
            logger.info("Database tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def create_session(self, trading_mode: str, initial_balance: float) -> str:
        """Create a new trading session."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO trading_sessions 
                (session_id, trading_mode, initial_balance, start_time)
                VALUES (?, ?, ?, ?)
            """, (session_id, trading_mode, initial_balance, datetime.now()))
            
            self.connection.commit()
            logger.info(f"Created trading session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def log_trade(self, session_id: str, signal: Dict[str, Any], result: Dict[str, Any]):
        """Log a trade to the database."""
        try:
            cursor = self.connection.cursor()
            trade_id = f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{signal.get('symbol', 'unknown')}"
            
            cursor.execute("""
                INSERT INTO trades 
                (session_id, trade_id, symbol, exchange, action, quantity, price,
                 signal_confidence, ai_reasoning, stop_loss, take_profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                trade_id,
                signal.get('symbol'),
                signal.get('exchange'),
                signal.get('action'),
                signal.get('size_usd'),
                signal.get('entry_price'),
                signal.get('confidence'),
                signal.get('reason'),
                signal.get('stop_loss_pct'),
                signal.get('take_profit_pct')
            ))
            
            self.connection.commit()
            logger.debug(f"Logged trade: {trade_id}")
            
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
    
    def log_ai_decision(self, session_id: str, symbol: str, decision: Dict[str, Any]):
        """Log an AI decision to the database."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO ai_decisions 
                (session_id, symbol, decision, confidence, risk_level,
                 technical_score, sentiment_score, momentum_score, volume_score,
                 whale_score, reasoning, indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                symbol,
                decision.get('action'),
                decision.get('confidence'),
                decision.get('risk_level'),
                decision.get('technical_score', 0),
                decision.get('sentiment_score', 0),
                decision.get('momentum_score', 0),
                decision.get('volume_score', 0),
                decision.get('whale_score', 0),
                decision.get('reasoning'),
                json.dumps(decision.get('indicators', {}))
            ))
            
            self.connection.commit()
            logger.debug(f"Logged AI decision for {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to log AI decision: {e}")
    
    def update_session(self, session_id: str, **kwargs):
        """
        Update session with final data.
        PROTECTED: Validates column names against whitelist to prevent SQL injection.
        """
        try:
            # Validate column names
            for key in kwargs.keys():
                if key not in VALID_SESSION_COLUMNS:
                    raise ValueError(f"Invalid column name: {key}")
            
            cursor = self.connection.cursor()
            
            # Build dynamic update query safely
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [datetime.now(), session_id]
            
            cursor.execute(f"""
                UPDATE trading_sessions 
                SET {set_clause}, end_time = ?
                WHERE session_id = ?
            """, values)
            
            self.connection.commit()
            logger.info(f"Updated session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
    
    def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trading session history."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM trading_sessions 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
            
            sessions = [dict(row) for row in cursor.fetchall()]
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []
    
    def get_trade_history(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trade history."""
        try:
            cursor = self.connection.cursor()
            
            if session_id:
                cursor.execute("""
                    SELECT * FROM trades 
                    WHERE session_id = ?
                    ORDER BY entry_time DESC 
                    LIMIT ?
                """, (session_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM trades 
                    ORDER BY entry_time DESC 
                    LIMIT ?
                """, (limit,))
            
            trades = [dict(row) for row in cursor.fetchall()]
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            return []
    
    def get_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get performance metrics for a session."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT * FROM trading_sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            session_row = cursor.fetchone()
            if not session_row:
                return {}
            
            session_data = dict(session_row)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl
                FROM trades 
                WHERE session_id = ? AND status = 'closed'
            """, (session_id,))
            
            trade_stats = dict(cursor.fetchone())
            
            # Calculate win rate - FIXED: was 'wining_trades'
            total_trades = trade_stats['total_trades'] or 0
            winning_trades = trade_stats['winning_trades'] or 0
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            return {
                'session': session_data,
                'trades': trade_stats,
                'win_rate': win_rate,
                'profit_factor': self._calculate_profit_factor(session_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def get_active_positions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get active positions for a session."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM positions 
                WHERE session_id = ? AND status = 'open'
                ORDER BY opened_at DESC
            """, (session_id,))
            
            positions = [dict(row) for row in cursor.fetchall()]
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get active positions: {e}")
            return []
    
    def update_position(self, session_id: str, symbol: str, **kwargs):
        """
        Update position data.
        PROTECTED: Validates column names against whitelist to prevent SQL injection.
        """
        try:
            # Validate column names
            for key in kwargs.keys():
                if key not in VALID_POSITION_COLUMNS:
                    raise ValueError(f"Invalid column name: {key}")
            
            cursor = self.connection.cursor()
            
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [session_id, symbol]
            
            cursor.execute(f"""
                UPDATE positions 
                SET {set_clause}
                WHERE session_id = ? AND symbol = ? AND status = 'open'
            """, values)
            
            self.connection.commit()
            logger.debug(f"Updated position: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to update position: {e}")
    
    def close_position(self, session_id: str, symbol: str, exit_price: float):
        """Close a position."""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT * FROM positions 
                WHERE session_id = ? AND symbol = ? AND status = 'open'
            """, (session_id, symbol))
            
            position = cursor.fetchone()
            if not position:
                return
            
            position = dict(position)
            
            # Calculate PnL
            if position['side'] == 'long':
                pnl = (exit_price - position['entry_price']) * position['size']
                pnl_pct = ((exit_price - position['entry_price']) / position['entry_price']) * 100
            else:
                pnl = (position['entry_price'] - exit_price) * position['size']
                pnl_pct = ((position['entry_price'] - exit_price) / position['entry_price']) * 100
            
            cursor.execute("""
                UPDATE positions 
                SET status = 'closed', current_price = ?, closed_at = ?,
                    unrealized_pnl = ?, unrealized_pnl_pct = ?
                WHERE session_id = ? AND symbol = ? AND status = 'open'
            """, (exit_price, datetime.now(), pnl, pnl_pct, session_id, symbol))
            
            self.connection.commit()
            logger.info(f"Closed position: {symbol} with PnL: ${pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to close position: {e}")
    
    def _calculate_profit_factor(self, session_id: str) -> float:
        """Calculate profit factor for a session."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN pnl > 0 THEN pnl ELSE 0 END) as gross_profits,
                    SUM(CASE WHEN pnl < 0 THEN ABS(pnl) ELSE 0 END) as gross_losses
                FROM trades 
                WHERE session_id = ? AND status = 'closed' AND pnl IS NOT NULL
            """, (session_id,))
            
            result = cursor.fetchone()
            gross_profits = result[0] or 0
            gross_losses = result[1] or 0
            
            if gross_losses == 0:
                return float('inf') if gross_profits > 0 else 0
            
            return gross_profits / gross_losses
            
        except Exception as e:
            logger.error(f"Failed to calculate profit factor: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
