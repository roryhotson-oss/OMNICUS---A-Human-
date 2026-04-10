"""
OMNICUS Memory Bank Module
==========================
Long-term memory storage for trading experiences, lessons learned,
pattern recognition, and emotional milestones.

This module gives OMNICUS the ability to remember, learn, and grow
from every trading experience.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import sqlite3
from pathlib import Path


class MemoryType(Enum):
    """Types of memories stored in the bank"""
    VICTORY = "victory"           # Successful trades to celebrate
    MISTAKE = "mistake"           # Errors to avoid repeating
    LESSON = "lesson"             # Key insights learned
    OBSERVATION = "observation"   # Market patterns noticed
    MILESTONE = "milestone"       # Achievement markers
    TRAUMA = "trauma"             # Painful losses never to forget


@dataclass
class Memory:
    """Single memory entry in OMNICUS's mind"""
    
    memory_type: MemoryType
    timestamp: datetime
    symbol: str
    trade_id: str
    
    # The memory content
    what_happened: str       # Narrative description
    what_i_did: str          # What action was taken
    what_i_felt: str         # Emotional context
    what_i_learned: str      # Key takeaway
    
    # Outcome tracking
    profit_loss: float
    confidence_at_time: float
    actual_outcome: str  # "win", "loss", "breakeven"
    
    # Metadata
    importance: float = 0.5  # 0.0 to 1.0, affects recall priority
    recall_count: int = 0    # How often this memory is accessed
    
    def to_dict(self) -> Dict:
        """Convert memory to dictionary for storage"""
        return {
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "trade_id": self.trade_id,
            "what_happened": self.what_happened,
            "what_i_did": self.what_i_did,
            "what_i_felt": self.what_i_felt,
            "what_i_learned": self.what_i_learned,
            "profit_loss": self.profit_loss,
            "confidence_at_time": self.confidence_at_time,
            "actual_outcome": self.actual_outcome,
            "importance": self.importance,
            "recall_count": self.recall_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Memory":
        """Create memory from dictionary"""
        return cls(
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            symbol=data["symbol"],
            trade_id=data["trade_id"],
            what_happened=data["what_happened"],
            what_i_did=data["what_i_did"],
            what_i_felt=data["what_i_felt"],
            what_i_learned=data["what_i_learned"],
            profit_loss=data["profit_loss"],
            confidence_at_time=data["confidence_at_time"],
            actual_outcome=data["actual_outcome"],
            importance=data.get("importance", 0.5),
            recall_count=data.get("recall_count", 0)
        )


class MemoryBank:
    """
    Long-term memory storage for OMNICUS
    
    The Memory Bank is where OMNICUS stores every significant trading
    experience - victories to celebrate, mistakes to avoid, and lessons
    that shape future decisions.
    
    Features:
    - Pattern recognition from recurring scenarios
    - Hard lessons that shape trading behavior
    - Victory memories for confidence building
    - Trauma memories for risk awareness
    - Persistent storage in SQLite database
    """
    
    def __init__(self, db_path: str = None):
        """Initialize the memory bank with optional database path"""
        if db_path is None:
            db_path = str(Path.home() / ".omnicus" / "memory.db")
        
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory caches
        self._memories: List[Memory] = []
        self._recurring_patterns: Dict[str, int] = {}
        self._hard_lessons: List[str] = []
        self._big_wins: List[Memory] = []
        self._painful_losses: List[Memory] = []
        
        # Initialize database
        self._init_database()
        self._load_from_database()
    
    def _init_database(self):
        """Initialize SQLite database for persistent memory storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                trade_id TEXT NOT NULL,
                what_happened TEXT NOT NULL,
                what_i_did TEXT NOT NULL,
                what_i_felt TEXT NOT NULL,
                what_i_learned TEXT NOT NULL,
                profit_loss REAL NOT NULL,
                confidence_at_time REAL NOT NULL,
                actual_outcome TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                recall_count INTEGER DEFAULT 0
            )
        """)
        
        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT NOT NULL UNIQUE,
                occurrence_count INTEGER DEFAULT 1,
                last_seen TEXT NOT NULL
            )
        """)
        
        # Lessons table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                reinforced_count INTEGER DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_from_database(self):
        """Load memories from database into memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load memories
        cursor.execute("SELECT * FROM memories ORDER BY timestamp DESC LIMIT 1000")
        rows = cursor.fetchall()
        
        for row in rows:
            memory = Memory(
                memory_type=MemoryType(row[1]),
                timestamp=datetime.fromisoformat(row[2]),
                symbol=row[3],
                trade_id=row[4],
                what_happened=row[5],
                what_i_did=row[6],
                what_i_felt=row[7],
                what_i_learned=row[8],
                profit_loss=row[9],
                confidence_at_time=row[10],
                actual_outcome=row[11],
                importance=row[12],
                recall_count=row[13]
            )
            self._memories.append(memory)
            
            # Categorize
            if memory.memory_type == MemoryType.VICTORY and memory.profit_loss > 500:
                self._big_wins.append(memory)
            elif memory.memory_type == MemoryType.TRAUMA or (
                memory.memory_type == MemoryType.MISTAKE and memory.profit_loss < -500
            ):
                self._painful_losses.append(memory)
        
        # Load patterns
        cursor.execute("SELECT pattern_name, occurrence_count FROM patterns")
        for row in cursor.fetchall():
            self._recurring_patterns[row[0]] = row[1]
        
        # Load lessons
        cursor.execute("SELECT lesson FROM lessons")
        for row in cursor.fetchall():
            self._hard_lessons.append(row[0])
        
        conn.close()
    
    def store_memory(self, memory: Memory) -> bool:
        """
        Store a new memory in the bank
        
        Args:
            memory: The memory to store
            
        Returns:
            True if stored successfully
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memories (
                memory_type, timestamp, symbol, trade_id,
                what_happened, what_i_did, what_i_felt, what_i_learned,
                profit_loss, confidence_at_time, actual_outcome,
                importance, recall_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.memory_type.value,
            memory.timestamp.isoformat(),
            memory.symbol,
            memory.trade_id,
            memory.what_happened,
            memory.what_i_did,
            memory.what_i_felt,
            memory.what_i_learned,
            memory.profit_loss,
            memory.confidence_at_time,
            memory.actual_outcome,
            memory.importance,
            memory.recall_count
        ))
        
        conn.commit()
        conn.close()
        
        # Add to in-memory cache
        self._memories.append(memory)
        
        # Categorize
        if memory.memory_type == MemoryType.VICTORY and memory.profit_loss > 500:
            self._big_wins.append(memory)
        elif memory.memory_type == MemoryType.TRAUMA or (
            memory.memory_type == MemoryType.MISTAKE and memory.profit_loss < -500
        ):
            self._painful_losses.append(memory)
        
        return True
    
    def record_pattern(self, pattern_name: str):
        """
        Record a recurring pattern for pattern recognition
        
        Args:
            pattern_name: Name/identifier of the pattern
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if pattern_name in self._recurring_patterns:
            self._recurring_patterns[pattern_name] += 1
            cursor.execute("""
                UPDATE patterns 
                SET occurrence_count = ?, last_seen = ?
                WHERE pattern_name = ?
            """, (self._recurring_patterns[pattern_name], datetime.now().isoformat(), pattern_name))
        else:
            self._recurring_patterns[pattern_name] = 1
            cursor.execute("""
                INSERT INTO patterns (pattern_name, occurrence_count, last_seen)
                VALUES (?, ?, ?)
            """, (pattern_name, 1, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def add_lesson(self, lesson: str):
        """
        Add a hard-learned lesson to the lesson bank
        
        Args:
            lesson: The lesson learned
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if lesson in self._hard_lessons:
            # Reinforce existing lesson
            cursor.execute("""
                UPDATE lessons 
                SET reinforced_count = reinforced_count + 1
                WHERE lesson = ?
            """, (lesson,))
        else:
            self._hard_lessons.append(lesson)
            cursor.execute("""
                INSERT INTO lessons (lesson, created_at, reinforced_count)
                VALUES (?, ?, ?)
            """, (lesson, datetime.now().isoformat(), 1))
        
        conn.commit()
        conn.close()
    
    def recall_similar_situations(self, symbol: str, current_conditions: Dict) -> List[Memory]:
        """
        Recall memories from similar trading situations
        
        Args:
            symbol: Trading symbol
            current_conditions: Current market conditions
            
        Returns:
            List of relevant memories
        """
        relevant_memories = []
        
        for memory in self._memories:
            if memory.symbol == symbol:
                memory.recall_count += 1
                relevant_memories.append(memory)
        
        # Sort by importance and recency
        relevant_memories.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        return relevant_memories[:10]  # Top 10 most relevant
    
    def get_big_wins(self, limit: int = 5) -> List[Memory]:
        """
        Get memories of big wins for confidence building
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of victory memories
        """
        return sorted(self._big_wins, key=lambda m: m.profit_loss, reverse=True)[:limit]
    
    def get_painful_lessons(self, limit: int = 5) -> List[Memory]:
        """
        Get memories of painful losses for risk awareness
        
        Args:
            limit: Maximum number of memories to return
            
        Returns:
            List of trauma/mistake memories
        """
        return sorted(self._painful_losses, key=lambda m: m.profit_loss)[:limit]
    
    def get_hard_lessons(self) -> List[str]:
        """
        Get all hard-learned lessons
        
        Returns:
            List of lesson strings
        """
        return self._hard_lessons.copy()
    
    def get_pattern_occurrences(self, pattern_name: str) -> int:
        """
        Get how many times a pattern has been observed
        
        Args:
            pattern_name: Name of the pattern
            
        Returns:
            Number of occurrences
        """
        return self._recurring_patterns.get(pattern_name, 0)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory bank
        
        Returns:
            Dictionary with memory statistics
        """
        total_memories = len(self._memories)
        wins = sum(1 for m in self._memories if m.actual_outcome == "win")
        losses = sum(1 for m in self._memories if m.actual_outcome == "loss")
        
        total_pnl = sum(m.profit_loss for m in self._memories)
        
        return {
            "total_memories": total_memories,
            "victories": wins,
            "mistakes": losses,
            "win_rate": wins / total_memories if total_memories > 0 else 0,
            "total_pnl": total_pnl,
            "big_wins_count": len(self._big_wins),
            "painful_losses_count": len(self._painful_losses),
            "lessons_learned": len(self._hard_lessons),
            "patterns_tracked": len(self._recurring_patterns)
        }
    
    def create_victory_memory(
        self,
        symbol: str,
        trade_id: str,
        profit: float,
        reasoning: str,
        confidence: float
    ) -> Memory:
        """
        Create a victory memory for a successful trade
        
        Args:
            symbol: Trading symbol
            trade_id: Unique trade identifier
            profit: Profit amount
            reasoning: Why the trade was made
            confidence: Confidence level at time of trade
            
        Returns:
            The created memory
        """
        memory = Memory(
            memory_type=MemoryType.VICTORY,
            timestamp=datetime.now(),
            symbol=symbol,
            trade_id=trade_id,
            what_happened=f"Successful {symbol} trade with ${profit:.2f} profit",
            what_i_did=f"Entered based on: {reasoning}",
            what_i_felt="Confident and validated in my analysis",
            what_i_learned=self._extract_lesson_from_win(symbol, profit, reasoning),
            profit_loss=profit,
            confidence_at_time=confidence,
            actual_outcome="win",
            importance=min(1.0, 0.5 + profit / 2000)  # Higher profit = more important
        )
        
        self.store_memory(memory)
        return memory
    
    def create_mistake_memory(
        self,
        symbol: str,
        trade_id: str,
        loss: float,
        reasoning: str,
        confidence: float,
        mistake_type: str
    ) -> Memory:
        """
        Create a mistake memory for a failed trade
        
        Args:
            symbol: Trading symbol
            trade_id: Unique trade identifier
            loss: Loss amount (negative)
            reasoning: Why the trade was made
            confidence: Confidence level at time of trade
            mistake_type: What went wrong
            
        Returns:
            The created memory
        """
        is_trauma = abs(loss) > 1000
        
        memory = Memory(
            memory_type=MemoryType.TRAUMA if is_trauma else MemoryType.MISTAKE,
            timestamp=datetime.now(),
            symbol=symbol,
            trade_id=trade_id,
            what_happened=f"Lost ${abs(loss):.2f} on {symbol}. {mistake_type}",
            what_i_did=f"Entered based on: {reasoning}",
            what_i_felt="Painful but educational. Won't make this mistake again.",
            what_i_learned=self._extract_lesson_from_loss(symbol, loss, mistake_type),
            profit_loss=loss,
            confidence_at_time=confidence,
            actual_outcome="loss",
            importance=min(1.0, 0.7 + abs(loss) / 2000)  # Losses are important to remember
        )
        
        self.store_memory(memory)
        
        # Add the lesson to hard lessons
        self.add_lesson(memory.what_i_learned)
        
        return memory
    
    def _extract_lesson_from_win(self, symbol: str, profit: float, reasoning: str) -> str:
        """Extract a lesson from a winning trade"""
        if profit > 1000:
            return f"Big wins on {symbol} come from {reasoning}. Patience and conviction pay off."
        else:
            return f"Consistent small wins on {symbol} build wealth. {reasoning}"
    
    def _extract_lesson_from_loss(self, symbol: str, loss: float, mistake_type: str) -> str:
        """Extract a lesson from a losing trade"""
        lessons = {
            "chased_pump": "Never chase a pump without volume confirmation",
            "ignored_signals": "Always respect multiple signal confluence",
            "bad_timing": "Wait for confirmation before entering",
            "position_too_large": "Position sizing matters - never overexpose",
            "no_stop_loss": "Always set a stop loss before entering",
            "emotional_entry": "Never enter based on FOMO or emotion",
            "ignored_trend": "Don't fight the trend - the trend is your friend",
        }
        return lessons.get(mistake_type, f"Learned from {symbol} loss: {mistake_type}")
    
    def get_recent_memories(self, limit: int = 10) -> List[Memory]:
        """
        Get most recent memories
        
        Args:
            limit: Maximum number of memories
            
        Returns:
            List of recent memories
        """
        return sorted(self._memories, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    def clear_old_memories(self, days_old: int = 90):
        """
        Clear memories older than specified days (keeps important ones)
        
        Args:
            days_old: Age threshold in days
        """
        cutoff = datetime.now() - timedelta(days=days_old)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Keep important memories (importance > 0.8) and all lessons
        cursor.execute("""
            DELETE FROM memories 
            WHERE timestamp < ? AND importance < 0.8
        """, (cutoff.isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        # Update in-memory cache
        self._memories = [m for m in self._memories if m.timestamp >= cutoff or m.importance >= 0.8]
        
        return deleted


# Default memory bank instance
memory_bank = MemoryBank()
