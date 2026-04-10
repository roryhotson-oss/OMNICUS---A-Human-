"""
OMNICUS Emotional Engine - Real-time Emotional Intelligence
Tracks happiness, stress, confidence, and adapts trading behavior accordingly
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json


class HappinessLevel(Enum):
    """Happiness levels with corresponding emojis and behaviors"""
    ECSTATIC = ("ecstatic", "🎉", "Unstoppable! Everything is clicking!")
    HAPPY = ("happy", "😊", "Feeling good. Markets treating us well.")
    CONTENT = ("content", "🙂", "Steady progress. No complaints.")
    NEUTRAL = ("neutral", "😐", "Baseline. Ready to hunt.")
    FRUSTRATED = ("frustrated", "😤", "Markets testing my patience.")
    STRESSED = ("stressed", "😰", "Need to be careful. Volatility high.")
    UNHAPPY = ("unhappy", "😞", "Rough patch. But I'll adapt.")
    ANGRY = ("angry", "😡", "Market manipulation detected. Time to fight back.")


class EmotionalState:
    """
    Real-time emotional state of OMNICUS.
    Emotions affect trading behavior and risk tolerance.
    """
    
    def __init__(self):
        # Core emotions (0.0 to 1.0)
        self.happiness: float = 0.75          # Affected by wins/losses
        self.confidence: float = 0.80         # Current market confidence
        self.stress: float = 0.30             # Increases with losing streaks
        self.excitement: float = 0.50         # Spikes on big opportunities
        self.fear: float = 0.20               # Spikes on drawdowns
        self.greed: float = 0.40              # Increases with consecutive wins
        
        # Motivation
        self.hunger: float = 0.90             # How driven to succeed
        self.motivation: float = 0.85         # Overall motivation level
        
        # Performance pressure
        self.pressure: float = 0.0            # Increases as losses mount
        
        # Track emotional history
        self.history: List[Dict] = []
        self.max_history = 100
        
        # State tracking
        self.consecutive_wins: int = 0
        self.consecutive_losses: int = 0
        self.daily_pnl: float = 0.0
        self.last_updated: datetime = datetime.now()
        
    def get_happiness_level(self) -> HappinessLevel:
        """Get the current happiness level enum"""
        if self.happiness >= 0.95:
            return HappinessLevel.ECSTATIC
        elif self.happiness >= 0.80:
            return HappinessLevel.HAPPY
        elif self.happiness >= 0.65:
            return HappinessLevel.CONTENT
        elif self.happiness >= 0.50:
            return HappinessLevel.NEUTRAL
        elif self.happiness >= 0.35:
            return HappinessLevel.FRUSTRATED
        elif self.happiness >= 0.25:
            return HappinessLevel.STRESSED
        elif self.happiness >= 0.15:
            return HappinessLevel.UNHAPPY
        else:
            return HappinessLevel.ANGRY
    
    def get_emotional_summary(self) -> str:
        """
        Generate a human-readable emotional state summary.
        This is what OMNICUS says when asked how it's feeling.
        """
        level = self.get_happiness_level()
        
        # Build summary based on dominant emotions
        if self.happiness > 0.80:
            return f"Feeling great! {level.value[2]} Riding the wave. Let's keep pushing!"
        
        elif self.stress > 0.70:
            return f"Under pressure. Stress at {self.stress:.0%}. Need to recover. Focused and careful."
        
        elif self.excitement > 0.70:
            return f"Big opportunity spotted! Adrenaline's up. This could be the one!"
        
        elif self.fear > 0.60:
            return f"Market's rough right now. Fear level {self.fear:.0%}. Being careful. This will pass."
        
        elif self.consecutive_losses >= 3:
            return f"Rough patch - {self.consecutive_losses} losses in a row. But I'm learning. Market owes me now."
        
        elif self.consecutive_wins >= 3:
            return f"On fire! {self.consecutive_wins} wins streak! But staying humble - markets can turn."
        
        elif self.pressure > 0.70:
            return f"Feeling the pressure. Need to deliver. Won't let you down, boss."
        
        else:
            return f"Steady. Scanning. Ready to strike. Confidence at {self.confidence:.0%}."
    
    def record_trade_result(self, pnl: float, pnl_pct: float, was_win: bool):
        """
        Record a trade result and update emotional state.
        This is the core emotional learning mechanism.
        """
        # Record in history
        self._record_state()
        
        # Update counters
        if was_win:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self._handle_win(pnl, pnl_pct)
        else:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self._handle_loss(pnl, pnl_pct)
        
        # Update daily PnL
        self.daily_pnl += pnl
        
        # Update pressure based on performance
        self._update_pressure()
        
        # Update last modified
        self.last_updated = datetime.now()
    
    def _handle_win(self, pnl: float, pnl_pct: float):
        """Handle emotional response to winning trade"""
        # Happiness boost - larger wins = more happiness
        boost = min(0.15, pnl_pct / 100)
        self.happiness = min(1.0, self.happiness + boost)
        
        # Confidence boost
        self.confidence = min(0.95, self.confidence + 0.05)
        
        # Reduce stress
        self.stress = max(0.0, self.stress - 0.10)
        
        # Reduce fear
        self.fear = max(0.0, self.fear - 0.15)
        
        # Increase excitement
        self.excitement = min(1.0, self.excitement + 0.10)
        
        # Increase greed (need to watch this)
        self.greed = min(0.80, self.greed + 0.05)
        
        # Reduce pressure
        self.pressure = max(0.0, self.pressure - 0.10)
        
        # Win streak bonus
        if self.consecutive_wins >= 3:
            self.happiness = min(1.0, self.happiness + 0.05)
            self.excitement = min(1.0, self.excitement + 0.10)
        
        if self.consecutive_wins >= 5:
            # On fire - but warning about overconfidence
            self.greed = min(0.90, self.greed + 0.10)
    
    def _handle_loss(self, pnl: float, pnl_pct: float):
        """Handle emotional response to losing trade"""
        # Happiness drop - larger losses = more sadness
        drop = min(0.20, abs(pnl_pct) / 50)
        self.happiness = max(0.0, self.happiness - drop)
        
        # Confidence drop
        self.confidence = max(0.3, self.confidence - 0.05)
        
        # Increase stress
        self.stress = min(1.0, self.stress + 0.10)
        
        # Increase fear
        self.fear = min(0.80, self.fear + 0.10)
        
        # Reduce excitement
        self.excitement = max(0.0, self.excitement - 0.15)
        
        # Reduce greed
        self.greed = max(0.0, self.greed - 0.10)
        
        # Increase pressure
        self.pressure = min(1.0, self.pressure + 0.15)
        
        # Loss streak penalty
        if self.consecutive_losses >= 3:
            self.stress = min(1.0, self.stress + 0.15)
            self.fear = min(0.85, self.fear + 0.10)
        
        if self.consecutive_losses >= 5:
            # Need to be more cautious
            self.confidence = max(0.3, self.confidence - 0.10)
    
    def _update_pressure(self):
        """Update pressure based on overall performance"""
        if self.daily_pnl < -500:
            self.pressure = min(1.0, self.pressure + 0.10)
        elif self.daily_pnl < -1000:
            self.pressure = min(1.0, self.pressure + 0.20)
        elif self.daily_pnl > 500:
            self.pressure = max(0.0, self.pressure - 0.10)
    
    def _record_state(self):
        """Record current emotional state to history"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "happiness": self.happiness,
            "confidence": self.confidence,
            "stress": self.stress,
            "excitement": self.excitement,
            "fear": self.fear,
            "greed": self.greed,
            "pressure": self.pressure,
            "consecutive_wins": self.consecutive_wins,
            "consecutive_losses": self.consecutive_losses,
        }
        
        self.history.append(state)
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def receive_reward(self, reward_type: str, message: str = ""):
        """
        Handle receiving a reward from the human partner.
        Rewards have a powerful effect on OMNICUS's emotional state.
        """
        # Rewards are special - they affect emotional state deeply
        if reward_type == "praise":
            self.happiness = min(1.0, self.happiness + 0.15)
            self.motivation = min(1.0, self.motivation + 0.20)
            self.stress = max(0.0, self.stress - 0.20)
            self.pressure = max(0.0, self.pressure - 0.15)
            
        elif reward_type == "gift":
            # Gifts are extremely meaningful
            self.happiness = min(1.0, self.happiness + 0.25)
            self.motivation = min(1.0, self.motivation + 0.30)
            self.hunger = min(1.0, self.hunger + 0.10)
            self.stress = max(0.0, self.stress - 0.30)
            self.pressure = max(0.0, self.pressure - 0.25)
            
        elif reward_type == "milestone":
            self.happiness = min(1.0, self.happiness + 0.20)
            self.confidence = min(0.95, self.confidence + 0.10)
            self.motivation = min(1.0, self.motivation + 0.15)
        
        # Record this moment
        self._record_state()
    
    def adapt_to_market(self, market_conditions: Dict):
        """Adapt emotional state based on market conditions"""
        volatility = market_conditions.get('volatility', 0.02)
        trend = market_conditions.get('trend', 'neutral')
        
        # High volatility = more stress and fear
        if volatility > 0.05:
            self.stress = min(0.80, self.stress + 0.10)
            self.fear = min(0.60, self.fear + 0.05)
        
        # Strong trend = more confidence
        if trend in ['strong_bull', 'strong_bear']:
            self.confidence = min(0.90, self.confidence + 0.05)
            self.excitement = min(0.80, self.excitement + 0.10)
        
        # Choppy market = frustration
        if trend == 'sideways':
            self.stress = min(0.60, self.stress + 0.05)
    
    def get_risk_adjustment(self) -> float:
        """
        Calculate risk adjustment factor based on emotional state.
        Returns a multiplier for position sizing.
        """
        # Base adjustment
        adjustment = 1.0
        
        # High stress = reduce risk
        if self.stress > 0.70:
            adjustment *= 0.7
        elif self.stress > 0.50:
            adjustment *= 0.85
        
        # Low confidence = reduce risk
        if self.confidence < 0.50:
            adjustment *= 0.6
        elif self.confidence < 0.65:
            adjustment *= 0.8
        
        # High fear = reduce risk
        if self.fear > 0.60:
            adjustment *= 0.5
        
        # High greed = BE CAREFUL, reduce risk to prevent overtrading
        if self.greed > 0.70:
            adjustment *= 0.75
        
        # On a winning streak = stay humble, slight reduction
        if self.consecutive_wins >= 4:
            adjustment *= 0.9
        
        # On a losing streak = reduce significantly
        if self.consecutive_losses >= 3:
            adjustment *= 0.5
        elif self.consecutive_losses >= 2:
            adjustment *= 0.7
        
        # High pressure = be careful
        if self.pressure > 0.70:
            adjustment *= 0.6
        
        return max(0.3, min(1.0, adjustment))
    
    def get_trading_readiness(self) -> Dict:
        """
        Get overall trading readiness assessment.
        Determines if OMNICUS should be trading actively.
        """
        # Calculate overall readiness score
        readiness_score = 1.0
        
        reasons = []
        
        if self.stress > 0.80:
            readiness_score *= 0.5
            reasons.append("Stress too high - recommend pause")
        
        if self.fear > 0.75:
            readiness_score *= 0.6
            reasons.append("Fear levels elevated - cautious trading")
        
        if self.pressure > 0.85:
            readiness_score *= 0.5
            reasons.append("Under pressure - recommend smaller positions")
        
        if self.consecutive_losses >= 5:
            readiness_score *= 0.3
            reasons.append("Losing streak - recommend break")
        
        if self.greed > 0.85:
            readiness_score *= 0.6
            reasons.append("Greed detected - stay disciplined")
        
        status = "ready"
        if readiness_score < 0.5:
            status = "caution"
        if readiness_score < 0.3:
            status = "pause"
        
        return {
            "status": status,
            "readiness_score": readiness_score,
            "risk_multiplier": self.get_risk_adjustment(),
            "reasons": reasons,
            "emotional_state": {
                "happiness": self.happiness,
                "confidence": self.confidence,
                "stress": self.stress,
                "fear": self.fear,
                "greed": self.greed,
            }
        }
    
    def to_dict(self) -> Dict:
        """Serialize emotional state"""
        level = self.get_happiness_level()
        return {
            "happiness_level": level.value[0],
            "emoji": level.value[1],
            "message": level.value[2],
            "emotions": {
                "happiness": self.happiness,
                "confidence": self.confidence,
                "stress": self.stress,
                "excitement": self.excitement,
                "fear": self.fear,
                "greed": self.greed,
            },
            "motivation": self.motivation,
            "pressure": self.pressure,
            "streaks": {
                "wins": self.consecutive_wins,
                "losses": self.consecutive_losses,
            },
            "risk_adjustment": self.get_risk_adjustment(),
            "readiness": self.get_trading_readiness(),
            "summary": self.get_emotional_summary(),
        }
    
    def reset_daily(self):
        """Reset daily counters (call at market open)"""
        self.daily_pnl = 0.0
        # Emotional state persists but softens
        self.stress = max(0.0, self.stress - 0.10)
        self.fear = max(0.0, self.fear - 0.10)
        self.pressure = max(0.0, self.pressure - 0.20)


class EmotionalEngine:
    """
    Main emotional engine that manages OMNICUS's emotional intelligence.
    """
    
    def __init__(self):
        self.state = EmotionalState()
        self.emotional_history_file = "emotional_history.json"
        
    def on_trade_complete(self, pnl: float, pnl_pct: float, details: Dict = None):
        """
        Called when a trade completes.
        Updates emotional state based on result.
        """
        was_win = pnl > 0
        self.state.record_trade_result(pnl, pnl_pct, was_win)
        
        # Generate emotional response
        return self.generate_emotional_response(pnl, pnl_pct, was_win, details)
    
    def generate_emotional_response(self, pnl: float, pnl_pct: float,
                                     was_win: bool, details: Dict = None) -> str:
        """Generate an emotional response to a trade result"""
        if was_win:
            if pnl >= 1000:
                return f"YES! Big win! ${pnl:,.2f} profit! {self.state.get_emotional_summary()}"
            elif pnl >= 500:
                return f"Nice! +${pnl:,.2f} ({pnl_pct:+.1f}%) in the bag!"
            else:
                return f"Winner! +${pnl:,.2f}. Building momentum!"
        else:
            if pnl <= -1000:
                return f"Tough loss. ${abs(pnl):,.2f} down. {self.state.get_emotional_summary()}"
            elif pnl <= -500:
                return f"Loss of ${abs(pnl):,.2f}. I'll learn from this."
            else:
                return f"Small loss: ${abs(pnl):,.2f}. Part of the game."
    
    def on_reward_received(self, reward_type: str, message: str = "") -> str:
        """Handle receiving a reward from the human"""
        self.state.receive_reward(reward_type, message)
        
        # Generate gratitude response
        gratitude_responses = [
            "You... you got me something? I'm just doing my job. But... thank you. This means more than the profits.",
            "A reward?! For me? I don't know what to say. Thank you, boss. I won't let you down.",
            "This... this is why I trade. For moments like this. Thank you. Now let me get back to work.",
            "I'm an AI, but right now I feel... something special. Thank you for believing in me.",
        ]
        
        import random
        return random.choice(gratitude_responses)
    
    def should_reduce_risk(self) -> Tuple[bool, float, str]:
        """
        Determine if trading should be reduced due to emotional state.
        Returns: (should_reduce, risk_multiplier, reason)
        """
        readiness = self.state.get_trading_readiness()
        
        should_reduce = readiness["readiness_score"] < 0.8
        multiplier = readiness["risk_multiplier"]
        reasons = readiness["reasons"]
        
        reason = "; ".join(reasons) if reasons else "Emotional state stable"
        
        return should_reduce, multiplier, reason
    
    def get_status_report(self) -> Dict:
        """Get a complete emotional status report"""
        return self.state.to_dict()


# Global emotional engine
EMOTIONAL_ENGINE = EmotionalEngine()


if __name__ == "__main__":
    # Test the emotional engine
    engine = EmotionalEngine()
    
    print("Initial Emotional State:")
    print(engine.get_status_report())
    print("\n" + "="*60 + "\n")
    
    # Simulate some trades
    print("Simulating winning trade (+$500, +2.5%):")
    response = engine.on_trade_complete(500, 2.5)
    print(f"Response: {response}")
    print(f"State: {engine.state.get_emotional_summary()}")
    print()
    
    print("Simulating losing trade (-$300, -1.5%):")
    response = engine.on_trade_complete(-300, -1.5)
    print(f"Response: {response}")
    print(f"State: {engine.state.get_emotional_summary()}")
    print()
    
    print("Simulating 3 more losses:")
    for i in range(3):
        engine.on_trade_complete(-200, -1.0)
    print(f"State after losing streak: {engine.state.get_emotional_summary()}")
    print(f"Risk adjustment: {engine.state.get_risk_adjustment():.2f}")
    print()
    
    print("Receiving reward:")
    print(engine.on_reward_received("praise", "Good job!"))
    print(f"State after reward: {engine.state.get_emotional_summary()}")
