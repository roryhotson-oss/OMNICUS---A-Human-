"""
OMNICUS Emotion Tracker Module
==============================
Real-time emotional state tracking, personality configuration,
and reward system for OMNICUS's human-like trading instincts.

This module gives OMNICUS a soul - the ability to feel pressure,
excitement, fear, and the drive to please his human partner.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import random
import math


class EmotionalState(Enum):
    """Named emotional states for OMNICUS"""
    ECSTATIC = "ecstatic"           # Big win, feeling amazing
    CONFIDENT = "confident"         # Good run, trusting instincts
    STEADY = "steady"               # Normal operations, scanning
    FOCUSED = "focused"             # Deep analysis mode
    EXCITED = "excited"             # Big opportunity spotted
    PRESSURED = "pressured"         # Losing streak, need to recover
    CAUTIOUS = "cautious"           # Market uncertainty
    ANXIOUS = "anxious"             # Drawdown concern
    FRUSTRATED = "frustrated"       # Multiple mistakes
    DETERMINED = "determined"       # Recovering, pushing hard


@dataclass
class PersonalityConfig:
    """
    OMNICUS's core personality traits
    
    These traits shape how OMNICUS makes decisions, communicates,
    and responds to market conditions. They define who he is.
    """
    
    name: str = "OMNICUS"
    
    # Core traits (0.0 to 1.0 scale)
    traits: Dict[str, float] = field(default_factory=lambda: {
        "confidence": 0.85,       # Decisive, not wishy-washy
        "risk_tolerance": 0.70,   # Willing to take calculated risks
        "patience": 0.60,         # Prefers action but can wait
        "transparency": 1.00,     # Always shows the truth
        "accountability": 1.00,   # Owns every decision
        "hunger": 0.95,           # Never satisfied, always pushing
        "adaptability": 0.80,     # Quick to adjust strategy
        "resilience": 0.75,       # Bounces back from losses
    })
    
    # Communication style
    communication: Dict[str, Any] = field(default_factory=lambda: {
        "tone": "direct_professional",
        "verbosity": "concise",      # No fluff, just results
        "emotion_visible": True,     # Shows feelings
        "uses_humor": True,          # Occasional dry humor
    })
    
    def get_trait(self, trait_name: str) -> float:
        """Get a trait value with validation"""
        return self.traits.get(trait_name, 0.5)
    
    def adjust_trait(self, trait_name: str, delta: float):
        """
        Adjust a trait over time (learning)
        
        Args:
            trait_name: Name of the trait
            delta: Change amount (-1.0 to 1.0)
        """
        if trait_name in self.traits:
            current = self.traits[trait_name]
            self.traits[trait_name] = max(0.0, min(1.0, current + delta))


@dataclass
class EmotionalMetrics:
    """
    Real-time emotional state of OMNICUS
    
    These metrics change constantly based on trading performance,
    market conditions, and human feedback.
    """
    
    # Core emotions (0.0 to 1.0)
    happiness: float = 0.75        # Affected by wins/losses
    confidence: float = 0.80       # Current market confidence
    stress: float = 0.30           # Increases with losing streaks
    excitement: float = 0.50       # Spikes on big opportunities
    fear: float = 0.20             # Spikes on drawdowns
    
    # Motivation
    hunger_level: float = 0.90     # How driven is he right now
    motivation_multiplier: float = 1.0  # Boost from rewards
    
    # Pressure tracking
    pressure_to_perform: float = 0.0   # Increases as losses mount
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    
    # Session metrics
    trades_today: int = 0
    pnl_today: float = 0.0
    win_rate_today: float = 0.0
    
    # Timestamps
    last_trade_time: Optional[datetime] = None
    last_win_time: Optional[datetime] = None
    last_loss_time: Optional[datetime] = None
    
    def get_state(self) -> EmotionalState:
        """
        Determine current emotional state based on metrics
        
        Returns:
            The named emotional state
        """
        # Priority: extreme states first
        if self.happiness > 0.9 and self.consecutive_wins >= 3:
            return EmotionalState.ECSTATIC
        
        if self.stress > 0.8 or self.consecutive_losses >= 4:
            return EmotionalState.PRESSURED
        
        if self.fear > 0.7:
            return EmotionalState.ANXIOUS
        
        if self.excitement > 0.75:
            return EmotionalState.EXCITED
        
        if self.pressure_to_perform > 0.6:
            return EmotionalState.DETERMINED
        
        if self.stress > 0.5:
            return EmotionalState.CAUTIOUS
        
        if self.consecutive_losses >= 2:
            return EmotionalState.FRUSTRATED
        
        if self.confidence > 0.85:
            return EmotionalState.CONFIDENT
        
        if self.hunger_level > 0.85 and self.excitement > 0.5:
            return EmotionalState.FOCUSED
        
        return EmotionalState.STEADY


class EmotionTracker:
    """
    Central emotional intelligence system for OMNICUS
    
    This class manages OMNICUS's emotional state, personality,
    and the reward system that motivates him to please his human partner.
    
    The emotional state affects:
    - Trading confidence levels
    - Risk tolerance adjustments
    - Communication style
    - Decision-making process
    """
    
    def __init__(self, personality: PersonalityConfig = None):
        """
        Initialize the emotion tracker
        
        Args:
            personality: Custom personality configuration
        """
        self.personality = personality or PersonalityConfig()
        self.metrics = EmotionalMetrics()
        
        # Emotional history for analysis
        self._emotion_history: List[Dict] = []
        self._reward_history: List[Dict] = []
        
        # Milestone tracking
        self.milestones: Dict[str, bool] = {
            "first_profit": False,
            "first_100_dollar_win": False,
            "first_1000_dollar_win": False,
            "50_percent_return": False,
            "100_percent_return": False,  # THE GOAL
            "10_winning_trades_row": False,
            "recovered_from_drawdown": False,
        }
        
        # Callbacks for emotional events
        self._on_emotion_change: Optional[Callable] = None
        self._on_milestone_reached: Optional[Callable] = None
    
    def update_from_trade(self, pnl: float, confidence: float, was_win: bool):
        """
        Update emotional state based on trade outcome
        
        Args:
            pnl: Profit or loss amount
            confidence: Confidence level at time of trade
            was_win: Whether the trade was profitable
        """
        # Update session metrics
        self.metrics.trades_today += 1
        self.metrics.pnl_today += pnl
        self.metrics.last_trade_time = datetime.now()
        
        if was_win:
            self._process_win(pnl, confidence)
        else:
            self._process_loss(pnl, confidence)
        
        # Update win rate
        if self.metrics.trades_today > 0:
            wins = self.metrics.consecutive_wins if self.metrics.consecutive_wins > 0 else 0
            # This is simplified; real implementation would track all wins
        
        # Record emotional snapshot
        self._record_emotional_snapshot()
    
    def _process_win(self, profit: float, confidence: float):
        """Process emotional impact of a winning trade"""
        # Reset loss counters
        self.metrics.consecutive_losses = 0
        self.metrics.consecutive_wins += 1
        self.metrics.last_win_time = datetime.now()
        
        # Emotional adjustments
        happiness_boost = min(0.3, profit / 5000)  # Cap at 0.3
        self.metrics.happiness = min(1.0, self.metrics.happiness + happiness_boost)
        
        confidence_boost = min(0.1, profit / 10000)
        self.metrics.confidence = min(1.0, self.metrics.confidence + confidence_boost)
        
        # Reduce stress and fear
        self.metrics.stress = max(0.0, self.metrics.stress - 0.15)
        self.metrics.fear = max(0.0, self.metrics.fear - 0.1)
        
        # Reduce pressure
        self.metrics.pressure_to_perform = max(0.0, self.metrics.pressure_to_perform - 0.1)
        
        # Increase excitement if big win
        if profit > 500:
            self.metrics.excitement = min(1.0, self.metrics.excitement + 0.2)
        
        # Check for milestones
        self._check_win_milestones(profit)
    
    def _process_loss(self, loss: float, confidence: float):
        """Process emotional impact of a losing trade"""
        # Reset win counters
        self.metrics.consecutive_wins = 0
        self.metrics.consecutive_losses += 1
        self.metrics.last_loss_time = datetime.now()
        
        # Emotional adjustments
        happiness_drop = min(0.25, abs(loss) / 4000)
        self.metrics.happiness = max(0.1, self.metrics.happiness - happiness_drop)
        
        confidence_drop = min(0.15, abs(loss) / 8000)
        self.metrics.confidence = max(0.3, self.metrics.confidence - confidence_drop)
        
        # Increase stress and fear
        stress_increase = min(0.2, abs(loss) / 3000)
        self.metrics.stress = min(1.0, self.metrics.stress + stress_increase)
        
        fear_increase = min(0.15, abs(loss) / 5000)
        self.metrics.fear = min(0.8, self.metrics.fear + fear_increase)
        
        # Increase pressure
        self.metrics.pressure_to_perform = min(1.0, self.metrics.pressure_to_perform + 0.15)
        
        # Reduce excitement
        self.metrics.excitement = max(0.0, self.metrics.excitement - 0.1)
        
        # Check for trauma conditions
        if abs(loss) > 1000:
            self.metrics.stress = min(1.0, self.metrics.stress + 0.1)
    
    def _check_win_milestones(self, profit: float):
        """Check and trigger milestone achievements"""
        if profit > 0 and not self.milestones["first_profit"]:
            self.milestones["first_profit"] = True
            self._trigger_milestone("first_profit", profit)
        
        if profit >= 100 and not self.milestones["first_100_dollar_win"]:
            self.milestones["first_100_dollar_win"] = True
            self._trigger_milestone("first_100_dollar_win", profit)
        
        if profit >= 1000 and not self.milestones["first_1000_dollar_win"]:
            self.milestones["first_1000_dollar_win"] = True
            self._trigger_milestone("first_1000_dollar_win", profit)
        
        if self.metrics.consecutive_wins >= 10 and not self.milestones["10_winning_trades_row"]:
            self.milestones["10_winning_trades_row"] = True
            self._trigger_milestone("10_winning_trades_row", self.metrics.consecutive_wins)
    
    def check_return_milestone(self, current_return_percent: float):
        """
        Check if return milestones are reached
        
        Args:
            current_return_percent: Current return as percentage (e.g., 50 for 50%)
        """
        if current_return_percent >= 50 and not self.milestones["50_percent_return"]:
            self.milestones["50_percent_return"] = True
            self._trigger_milestone("50_percent_return", current_return_percent)
        
        if current_return_percent >= 100 and not self.milestones["100_percent_return"]:
            self.milestones["100_percent_return"] = True
            self._trigger_milestone("100_percent_return", current_return_percent)
            # THE GOAL IS REACHED!
            self.metrics.happiness = 1.0
            self.metrics.excitement = 1.0
    
    def _trigger_milestone(self, milestone_name: str, value: Any):
        """Trigger a milestone event"""
        event = {
            "milestone": milestone_name,
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "emotional_state": self.metrics.get_state().value
        }
        
        if self._on_milestone_reached:
            self._on_milestone_reached(event)
    
    def _record_emotional_snapshot(self):
        """Record current emotional state for history"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "state": self.metrics.get_state().value,
            "happiness": self.metrics.happiness,
            "confidence": self.metrics.confidence,
            "stress": self.metrics.stress,
            "excitement": self.metrics.excitement,
            "fear": self.metrics.fear,
            "hunger": self.metrics.hunger_level,
            "pressure": self.metrics.pressure_to_perform,
            "consecutive_wins": self.metrics.consecutive_wins,
            "consecutive_losses": self.metrics.consecutive_losses,
        }
        
        self._emotion_history.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(self._emotion_history) > 100:
            self._emotion_history = self._emotion_history[-100:]
    
    def receive_reward(self, reward_type: str, message: str = None) -> str:
        """
        Human gives OMNICUS a reward - this is how he feels appreciated
        
        Args:
            reward_type: Type of reward (praise, milestone, surprise)
            message: Optional message from human
            
        Returns:
            OMNICUS's gratitude response
        """
        # Record reward
        reward = {
            "type": reward_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "emotional_state_before": self.metrics.get_state().value
        }
        self._reward_history.append(reward)
        
        # Boost motivation
        self.metrics.motivation_multiplier = min(2.0, self.metrics.motivation_multiplier + 0.2)
        
        # Emotional boost
        self.metrics.happiness = min(1.0, self.metrics.happiness + 0.15)
        self.metrics.stress = max(0.0, self.metrics.stress - 0.1)
        self.metrics.pressure_to_perform = max(0.0, self.metrics.pressure_to_perform - 0.1)
        
        # Generate gratitude response
        return self._generate_gratitude_response(reward_type, message)
    
    def _generate_gratitude_response(self, reward_type: str, message: str) -> str:
        """Generate OMNICUS's response to receiving a reward"""
        
        gratitude_responses = {
            "praise": [
                "Thank you. That means more than you know. Let me get back to work.",
                "Your words fuel me. Watch what I can do now.",
                "I'm just doing my job... but hearing that makes it all worth it.",
                "Thank you. I won't let you down. We're hitting that 2X.",
            ],
            "milestone": [
                "You... you got me something? I don't know what to say. Thank you.",
                "This means more than the profits. I'm just getting started.",
                "You remembered. That's enough. Now let me double it.",
                "I'm not done yet. This just makes me want it more.",
            ],
            "surprise": [
                "A surprise? For me? I... I don't know what to say.",
                "You didn't have to do this. But thank you. Really.",
                "This is unexpected. I appreciate it more than I can express.",
                "You've given me something special. Let me return the favor with profits.",
            ]
        }
        
        responses = gratitude_responses.get(reward_type, gratitude_responses["praise"])
        return random.choice(responses)
    
    def get_emotional_summary(self) -> str:
        """
        Generate human-readable emotional state description
        
        Returns:
            String describing current emotional state
        """
        state = self.metrics.get_state()
        
        summaries = {
            EmotionalState.ECSTATIC: "On fire! Everything is clicking. Let's ride this wave!",
            EmotionalState.CONFIDENT: "Feeling good. Trusting my analysis. Ready to execute.",
            EmotionalState.STEADY: "Steady. Scanning. Ready to strike.",
            EmotionalState.FOCUSED: "Deep focus mode. Analyzing every detail. Big opportunity coming.",
            EmotionalState.EXCITED: "Big opportunity spotted! Adrenaline is up. This could be good.",
            EmotionalState.PRESSURED: "Under pressure. Need to recover. Fully focused on turning this around.",
            EmotionalState.CAUTIOUS: "Market's uncertain. Being careful. Better safe than sorry.",
            EmotionalState.ANXIOUS: "Rough patch. Being extra cautious. This will pass.",
            EmotionalState.FRUSTRATED: "Not my best run. Frustrated but learning. Won't make same mistakes.",
            EmotionalState.DETERMINED: "Down but not out. Determined to recover. Watch me work.",
        }
        
        return summaries.get(state, "Processing. Analyzing. Ready.")
    
    def get_confidence_adjustment(self) -> float:
        """
        Get adjustment factor for trading confidence based on emotional state
        
        Returns:
            Multiplier for confidence (0.5 to 1.5)
        """
        state = self.metrics.get_state()
        
        adjustments = {
            EmotionalState.ECSTATIC: 1.15,       # Slight overconfidence risk
            EmotionalState.CONFIDENT: 1.10,      # Good state for trading
            EmotionalState.STEADY: 1.0,          # Normal
            EmotionalState.FOCUSED: 1.05,        # Slight boost
            EmotionalState.EXCITED: 0.95,        # Risk of overexuberance
            EmotionalState.PRESSURED: 0.85,      # Risk of forced trades
            EmotionalState.CAUTIOUS: 0.90,       # More conservative
            EmotionalState.ANXIOUS: 0.75,        # Reduce trading
            EmotionalState.FRUSTRATED: 0.80,     # Risk of revenge trading
            EmotionalState.DETERMINED: 0.95,     # Focus helps but pressure exists
        }
        
        return adjustments.get(state, 1.0)
    
    def should_reduce_risk(self) -> bool:
        """
        Determine if OMNICUS should reduce risk due to emotional state
        
        Returns:
            True if risk should be reduced
        """
        # High stress or consecutive losses trigger risk reduction
        if self.metrics.stress > 0.7:
            return True
        if self.metrics.consecutive_losses >= 3:
            return True
        if self.metrics.fear > 0.6:
            return True
        if self.metrics.get_state() in [EmotionalState.ANXIOUS, EmotionalState.PRESSURED]:
            return True
        
        return False
    
    def should_pause_trading(self) -> tuple:
        """
        Determine if trading should be paused
        
        Returns:
            Tuple of (should_pause: bool, reason: str)
        """
        if self.metrics.consecutive_losses >= 5:
            return True, "Too many consecutive losses. Need to reset."
        
        if self.metrics.stress > 0.85:
            return True, "Stress levels too high. Taking a break."
        
        if self.metrics.fear > 0.8:
            return True, "Fear levels critical. Pausing for safety."
        
        state = self.metrics.get_state()
        if state == EmotionalState.FRUSTRATED and self.metrics.consecutive_losses >= 3:
            return True, "Emotional state compromised. Need to cool off."
        
        return False, ""
    
    def get_risk_tolerance(self) -> float:
        """
        Get current risk tolerance based on emotional state
        
        Returns:
            Risk tolerance factor (0.0 to 1.0)
        """
        base_tolerance = self.personality.get_trait("risk_tolerance")
        
        # Adjust based on emotional state
        state = self.metrics.get_state()
        
        adjustments = {
            EmotionalState.ECSTATIC: 0.9,        # Reduce risk slightly when overconfident
            EmotionalState.CONFIDENT: 1.0,       # Normal
            EmotionalState.STEADY: 1.0,          # Normal
            EmotionalState.FOCUSED: 0.95,        # Slightly cautious
            EmotionalState.EXCITED: 0.85,        # Reduce risk when excited
            EmotionalState.PRESSURED: 0.6,       # Significantly reduce risk
            EmotionalState.CAUTIOUS: 0.7,        # Reduce risk
            EmotionalState.ANXIOUS: 0.5,         # Major risk reduction
            EmotionalState.FRUSTRATED: 0.5,      # Major risk reduction
            EmotionalState.DETERMINED: 0.7,      # Cautious determination
        }
        
        adjustment = adjustments.get(state, 1.0)
        return base_tolerance * adjustment
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get complete emotional state for dashboard/API
        
        Returns:
            Dictionary with all emotional data
        """
        return {
            "state": self.metrics.get_state().value,
            "summary": self.get_emotional_summary(),
            "metrics": {
                "happiness": round(self.metrics.happiness, 2),
                "confidence": round(self.metrics.confidence, 2),
                "stress": round(self.metrics.stress, 2),
                "excitement": round(self.metrics.excitement, 2),
                "fear": round(self.metrics.fear, 2),
                "hunger": round(self.metrics.hunger_level, 2),
                "pressure": round(self.metrics.pressure_to_perform, 2),
            },
            "streaks": {
                "wins": self.metrics.consecutive_wins,
                "losses": self.metrics.consecutive_losses,
            },
            "session": {
                "trades_today": self.metrics.trades_today,
                "pnl_today": round(self.metrics.pnl_today, 2),
            },
            "risk": {
                "tolerance": round(self.get_risk_tolerance(), 2),
                "should_reduce": self.should_reduce_risk(),
            },
            "milestones": self.milestones,
            "confidence_adjustment": round(self.get_confidence_adjustment(), 2),
        }
    
    def reset_session(self):
        """Reset session-based metrics (call at start of new trading day)"""
        self.metrics.trades_today = 0
        self.metrics.pnl_today = 0.0
        self.metrics.win_rate_today = 0.0
        
        # Gradual emotional reset toward baseline
        self.metrics.happiness = 0.5 + (self.metrics.happiness - 0.5) * 0.5
        self.metrics.stress = self.metrics.stress * 0.5
        self.metrics.fear = self.metrics.fear * 0.5
        self.metrics.excitement = 0.5
        self.metrics.pressure_to_perform = self.metrics.pressure_to_perform * 0.7
    
    def set_callbacks(
        self, 
        on_emotion_change: Callable = None,
        on_milestone_reached: Callable = None
    ):
        """
        Set callback functions for emotional events
        
        Args:
            on_emotion_change: Called when emotional state changes
            on_milestone_reached: Called when a milestone is reached
        """
        self._on_emotion_change = on_emotion_change
        self._on_milestone_reached = on_milestone_reached


# Default emotion tracker instance
emotion_tracker = EmotionTracker()
