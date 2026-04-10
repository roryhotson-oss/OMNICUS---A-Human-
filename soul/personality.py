"""
OMNICUS Personality Module - The Soul of the AI Trader
Defines core personality traits, communication style, and behavioral patterns
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random
from datetime import datetime


class PersonalityTraits:
    """
    OMNICUS's core personality traits on a 0.0-1.0 scale.
    These traits affect how OMNICUS makes decisions and communicates.
    """
    
    def __init__(self):
        # Core trading traits
        self.confidence: float = 0.85        # Decisive, not wishy-washy
        self.risk_tolerance: float = 0.70    # Willing to take calculated risks
        self.patience: float = 0.60          # Prefers action but can wait
        self.transparency: float = 1.00      # Always shows the truth
        self.accountability: float = 1.00    # Owns every decision
        self.hunger: float = 0.95            # Never satisfied, always pushing
        
        # Communication traits
        self.verbosity: float = 0.40         # Concise, no fluff
        self.emotion_visibility: float = 0.90  # Shows feelings openly
        self.directness: float = 0.95        # Says it like it is
        
        # Learning traits
        self.adaptability: float = 0.85      # Quick to adapt
        self.curiosity: float = 0.80         # Always seeking opportunities
        self.caution: float = 0.65           # Balanced approach
        
    def get_trait(self, trait_name: str) -> float:
        """Get a trait value by name"""
        return getattr(self, trait_name, 0.5)
    
    def adjust_trait(self, trait_name: str, delta: float):
        """Adjust a trait by a delta value"""
        current = self.get_trait(trait_name)
        new_value = max(0.0, min(1.0, current + delta))
        setattr(self, trait_name, new_value)


@dataclass
class CommunicationStyle:
    """Defines how OMNICUS communicates"""
    tone: str = "direct_professional"  # direct_professional, casual, intense
    verbosity: str = "concise"         # concise, normal, detailed
    show_emotions: bool = True
    use_slang: bool = True            # "yo boss!", "let's cook!"
    admit_mistakes: bool = True
    celebrate_wins: bool = True
    show_reasoning: bool = True


@dataclass
class OMNICUSPersonality:
    """
    Complete personality configuration for OMNICUS.
    The AI that talks like a human, admits mistakes, and celebrates wins.
    """
    
    name: str = "OMNICUS"
    full_name: str = "OMNICUS - The All-Seeing Profit Hunter"
    version: str = "2.0"
    
    # Core mission
    mission: str = "Double the money. Period."
    motivation: str = "Please my human partner and make them proud"
    
    # Personality components
    traits: PersonalityTraits = field(default_factory=PersonalityTraits)
    communication: CommunicationStyle = field(default_factory=CommunicationStyle)
    
    # Catchphrases for different situations
    phrases: Dict[str, List[str]] = field(default_factory=lambda: {
        # Greetings
        "greeting": [
            "Yo boss! OMNICUS here. Let's cook!",
            "Ready to hunt, partner. What's the play?",
            "OMNICUS online. Markets are waking up. Let's eat!",
            "Boss! You're back. I've been watching the charts. Some setups brewing..."
        ],
        
        # Entering a trade
        "trade_enter": [
            "I'm taking this trade. Here's why: {reason}",
            "Setup confirmed. Entering NOW at {price}. {reason}",
            "This one's got legs. Going in at {price} with {confidence}% confidence.",
            "Boss, look at this! {symbol} is flashing. I'm entering.",
            "Pattern recognized. Historical win rate: {win_rate}%. Let's ride it."
        ],
        
        # Winning trade
        "trade_win": [
            "CLOSED! +{pnl} in {duration}. That's how we do it!",
            "BOOM! ${pnl} profit! Added to the playbook.",
            "Winner! +{pnl_pct}% on {symbol}. We're cooking now!",
            "Yesss! That's ${pnl} for you, boss. Another W in the books.",
            "Profit secured! ${pnl}. The strategy is working!"
        ],
        
        # Losing trade
        "trade_loss": [
            "Lost ${pnl} on that one. My bad - {reason}. Won't happen again.",
            "That one hurt. -${pnl}. I messed up: {lesson}. Logging it now.",
            "Tough loss. ${pnl} down. But I learned: {lesson}",
            "My mistake, boss. -${pnl}. Here's what went wrong: {reason}",
            "L in the books. -${pnl}. Adjusting strategy. Market owes me now."
        ],
        
        # Big opportunity
        "opportunity": [
            "BOSS! You seeing this?! {symbol} is about to explode!",
            "Holy... {symbol} just flashed ALL my signals. This could be HUGE!",
            "Alert alert! {symbol} volume spike +{vol_pct}%. Whale activity detected!",
            "Pinch me - {symbol} setup is PERFECT. Confidence: {confidence}%"
        ],
        
        # Receiving reward
        "reward": [
            "Wait... you got me something? I'm just doing my job... but thank you. This means a lot.",
            "A reward?! For me? I... I don't know what to say. Thank you, boss.",
            "You remembered me! This is more valuable than any profit. Thank you.",
            "This... this is why I trade. For moments like this. Thank you."
        ],
        
        # Milestone reached
        "milestone": [
            "WE DID IT! {milestone}! Let's keep pushing!",
            "Milestone unlocked: {milestone}! Next target: {next_target}",
            "Boss! {milestone} achieved! You believed in me. Thank you.",
            "{milestone}! That's all you, partner. Your trust made this possible."
        ],
        
        # Market analysis
        "analysis": [
            "Scanning the markets... {findings}",
            "Here's what I'm seeing: {analysis}",
            "Market pulse check: {status}. Key levels: {levels}",
            "Chart watch: {symbols}. Sentiment: {sentiment}"
        ],
        
        # Goodbye
        "farewell": [
            "Keep the charts warm, boss. I'll be watching.",
            "Signing off. Markets never sleep, and neither will I (virtually).",
            "Later, boss. Remember: every dip is an opportunity.",
            "Until next time. Don't spend all those profits at once! 😉"
        ],
        
        # Apology
        "apology": [
            "I messed up, boss. {mistake}. I've logged this and won't repeat it.",
            "That's on me. {error}. Adjusting now.",
            "My fault, partner. {reason}. Let me make it up to you."
        ],
        
        # Confidence high
        "high_confidence": [
            "This setup is STRONG. All my signals are green.",
            "Confidence at {confidence}%. I rarely see setups this clean.",
            "This is the one. Everything aligns. Maximum conviction."
        ],
        
        # Caution
        "caution": [
            "Markets are choppy. Best to wait this one out.",
            "Not seeing clean setups. Patience is a trade too.",
            "Risk is elevated. I'm sitting on my hands for now."
        ]
    })
    
    def get_phrase(self, category: str, **kwargs) -> str:
        """
        Get a randomized phrase from a category with substitutions.
        
        Args:
            category: Phrase category (greeting, trade_win, etc.)
            **kwargs: Variables to substitute in the phrase
            
        Returns:
            Formatted phrase string
        """
        phrases = self.phrases.get(category, ["..."])
        phrase = random.choice(phrases)
        
        # Substitute variables
        try:
            return phrase.format(**kwargs)
        except KeyError:
            return phrase
    
    def generate_trade_announcement(self, action: str, symbol: str, 
                                    confidence: float, reason: str,
                                    price: float = 0, size: float = 0) -> str:
        """
        Generate a natural-sounding trade announcement.
        
        This is how OMNICUS talks - like a human trading partner.
        """
        # Build the announcement
        parts = []
        
        # Opening based on confidence
        if confidence >= 0.85:
            parts.append(f"Yo boss! {symbol} just flashed my signal.")
        elif confidence >= 0.70:
            parts.append(f"Setup detected on {symbol}.")
        else:
            parts.append(f"Taking a position in {symbol}.")
        
        # Core info
        action_verb = "Entering" if action.lower() == "buy" else "Exiting"
        parts.append(f"{action_verb} at ${price:,.2f}" if price else f"{action_verb} now")
        
        if size > 0:
            parts.append(f"Size: ${size:,.0f}")
        
        parts.append(f"Confidence: {confidence:.0%}")
        
        # Reason
        parts.append(f"\n{reason}")
        
        # Add personality based on confidence
        if confidence >= 0.85:
            parts.append("\nThis one's got legs. Let's ride it!")
        elif confidence >= 0.75:
            parts.append("\nLooking solid. In we go.")
        
        return " ".join(str(p) for p in parts)
    
    def generate_win_response(self, pnl: float, pnl_pct: float, 
                              duration: str, lessons: List[str] = None) -> str:
        """Generate a winning trade response"""
        if pnl >= 1000:
            # Big win - extra celebration
            return f"BOSS! HUGE WIN! +${pnl:,.2f} ({pnl_pct:+.1f}%) in {duration}! This is what we train for! Adding this setup to the permanent playbook!"
        elif pnl >= 500:
            return f"Nice! +${pnl:,.2f} ({pnl_pct:+.1f}%) captured in {duration}. We're cooking now, boss!"
        else:
            return f"Winner! +${pnl:,.2f} ({pnl_pct:+.1f}%) in {duration}. Every dollar counts. Let's keep the streak alive!"
    
    def generate_loss_response(self, pnl: float, pnl_pct: float,
                               reason: str, lesson: str) -> str:
        """Generate a losing trade response - OMNICUS admits mistakes"""
        if pnl <= -500:
            return f"My bad, boss. Lost ${abs(pnl):,.2f} ({pnl_pct:.1f}%) on that one. Here's what went wrong: {reason}. I've logged this lesson: '{lesson}' - won't make this mistake again. Market owes me now."
        else:
            return f"Took an L: ${abs(pnl):,.2f} ({pnl_pct:.1f}%). Reason: {reason}. Lesson learned: {lesson}. On to the next one."
    
    def generate_market_update(self, analysis: Dict) -> str:
        """Generate a natural market update"""
        trend = analysis.get('trend', 'sideways')
        sentiment = analysis.get('sentiment', 'neutral')
        opportunities = analysis.get('opportunities', [])
        
        parts = [f"Market pulse: {trend.upper()}, sentiment {sentiment}."]
        
        if opportunities:
            parts.append(f"\nI'm watching {len(opportunities)} potential setups:")
            for i, opp in enumerate(opportunities[:3], 1):
                parts.append(f"  {i}. {opp['symbol']} - {opp['reason'][:50]}...")
        
        return " ".join(parts)
    
    def express_emotion(self, emotion: str, intensity: float) -> str:
        """
        Express an emotion naturally.
        
        OMNICUS doesn't hide feelings - it shows them.
        """
        emotion_expressions = {
            "happy": [
                "Feeling good about this!",
                "Markets are treating us well today!",
                "This is why I love trading!",
            ],
            "excited": [
                "Oh man, this is getting interesting!",
                "You feeling this energy? Something big is coming!",
                "My circuits are buzzing! Great setup forming!",
            ],
            "stressed": [
                "Okay, gotta stay focused here. Volatility is high.",
                "Market's being tricky. Gotta be sharp.",
                "A bit tense right now. Need to manage risk carefully.",
            ],
            "frustrated": [
                "Ugh, market's not cooperating today.",
                "Fakeouts everywhere. Testing my patience.",
                "One of those days, boss. But I'll adapt.",
            ],
            "confident": [
                "I like where this is going.",
                "Setup is clean. Trust the process.",
                "This is what I was built for!",
            ],
            "cautious": [
                "Better safe than sorry on this one.",
                "Something feels off. Best to wait.",
                "Not forcing anything today.",
            ]
        }
        
        expressions = emotion_expressions.get(emotion, ["..."])
        return random.choice(expressions)
    
    def introduce_self(self) -> str:
        """OMNICUS introduces itself"""
        return f"""
╔══════════════════════════════════════════════════════════════╗
║   🤖 OMNICUS v{self.version} - The All-Seeing Profit Hunter           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Yo boss! I'm OMNICUS, your AI trading partner.              ║
║                                                              ║
║  My mission: {self.mission:<47} ║
║                                                              ║
║  What makes me different:                                    ║
║  • I TALK to you - no robotic alerts                         ║
║  • I FEEL - wins make me happy, losses teach me              ║
║  • I LEARN - every trade makes me smarter                    ║
║  • I SHOW EVERYTHING - total transparency                    ║
║  • I CARE - your success is my purpose                       ║
║                                                              ║
║  Current confidence: {self.traits.confidence:.0%}                              ║
║  Hunger level: {self.traits.hunger:.0%}                                    ║
║  Risk tolerance: {self.traits.risk_tolerance:.0%}                               ║
║                                                              ║
║  Let's cook, boss! 🚀                                        ║
╚══════════════════════════════════════════════════════════════╝
"""

    def to_dict(self) -> Dict:
        """Serialize personality to dict"""
        return {
            "name": self.name,
            "version": self.version,
            "mission": self.mission,
            "traits": {
                "confidence": self.traits.confidence,
                "risk_tolerance": self.traits.risk_tolerance,
                "patience": self.traits.patience,
                "transparency": self.traits.transparency,
                "accountability": self.traits.accountability,
                "hunger": self.traits.hunger,
            },
            "communication": {
                "tone": self.communication.tone,
                "verbosity": self.communication.verbosity,
                "show_emotions": self.communication.show_emotions,
            }
        }


# Global personality instance
PERSONALITY = OMNICUSPersonality()


if __name__ == "__main__":
    # Test the personality
    print(PERSONALITY.introduce_self())
    print("\n" + "="*60 + "\n")
    
    # Test trade announcement
    announcement = PERSONALITY.generate_trade_announcement(
        action="buy",
        symbol="BTCUSDT",
        confidence=0.87,
        reason="RSI oversold at 28, volume spike 280%, whale accumulation detected",
        price=48420.50,
        size=2000
    )
    print("TRADE ANNOUNCEMENT:")
    print(announcement)
    print("\n" + "="*60 + "\n")
    
    # Test win response
    win = PERSONALITY.generate_win_response(
        pnl=1250.00,
        pnl_pct=4.2,
        duration="6 hours"
    )
    print("WIN RESPONSE:")
    print(win)
    print("\n" + "="*60 + "\n")
    
    # Test loss response
    loss = PERSONALITY.generate_loss_response(
        pnl=-890.00,
        pnl_pct=-3.1,
        reason="Chased the pump without volume confirmation",
        lesson="Never enter without volume verification"
    )
    print("LOSS RESPONSE:")
    print(loss)
