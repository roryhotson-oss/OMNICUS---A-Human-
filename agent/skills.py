"""
OMNICUS Skill Registry Module
=============================
Dynamic skill management for trading abilities, strategies,
and learned capabilities.

This module allows OMNICUS to develop, improve, and combine
different trading skills over time.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from enum import Enum
import json
import math


class SkillCategory(Enum):
    """Categories of trading skills"""
    ANALYSIS = "analysis"           # Market analysis skills
    EXECUTION = "execution"         # Trade execution skills
    RISK_MANAGEMENT = "risk"        # Risk management skills
    PATTERN_RECOGNITION = "pattern" # Pattern detection skills
    SENTIMENT = "sentiment"         # Sentiment analysis skills
    TIMING = "timing"               # Entry/exit timing skills
    PORTFOLIO = "portfolio"         # Portfolio management skills
    ADAPTATION = "adaptation"       # Learning and adaptation skills


class SkillLevel(Enum):
    """Skill proficiency levels"""
    NOVICE = 1          # Just learned, low accuracy
    BEGINNER = 2        # Basic understanding
    INTERMEDIATE = 3    # Decent performance
    ADVANCED = 4        # Good performance
    EXPERT = 5          # Excellent performance
    MASTER = 6          # Top-tier performance


@dataclass
class SkillExperience:
    """Record of experience with a skill"""
    
    total_uses: int = 0
    successful_uses: int = 0
    total_pnl: float = 0.0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    
    def record_use(self, success: bool, pnl: float = 0.0):
        """Record a skill usage"""
        self.total_uses += 1
        self.last_used = datetime.now()
        
        if success:
            self.successful_uses += 1
            self.last_success = datetime.now()
        
        self.total_pnl += pnl
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_uses == 0:
            return 0.0
        return self.successful_uses / self.total_uses
    
    @property
    def average_pnl(self) -> float:
        """Calculate average PnL per use"""
        if self.total_uses == 0:
            return 0.0
        return self.total_pnl / self.total_uses


@dataclass
class Skill:
    """
    A trading skill that OMNICUS can develop and improve
    
    Skills are learned abilities that improve with practice.
    Each skill has a level, experience, and can be combined
    with other skills for better results.
    """
    
    name: str
    category: SkillCategory
    description: str
    
    # Skill proficiency
    level: SkillLevel = SkillLevel.NOVICE
    experience: SkillExperience = field(default_factory=SkillExperience)
    
    # Skill parameters
    base_accuracy: float = 0.5       # Base accuracy when first learned
    current_accuracy: float = 0.5    # Current accuracy level
    confidence_modifier: float = 1.0 # How this affects confidence
    
    # Learning parameters
    learning_rate: float = 0.1       # How fast skill improves
    decay_rate: float = 0.01         # How fast skill decays without use
    
    # Dependencies
    prerequisites: List[str] = field(default_factory=list)
    synergies: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)
    
    def use(self, success: bool, pnl: float = 0.0) -> float:
        """
        Use the skill and potentially improve it
        
        Args:
            success: Whether the skill use was successful
            pnl: Profit or loss from the skill use
            
        Returns:
            Updated accuracy
        """
        # Record experience
        self.experience.record_use(success, pnl)
        
        # Update accuracy based on outcome
        if success:
            # Improve accuracy (diminishing returns)
            improvement = self.learning_rate * (1.0 - self.current_accuracy)
            self.current_accuracy = min(0.95, self.current_accuracy + improvement)
        else:
            # Small accuracy reduction (but not too harsh)
            self.current_accuracy = max(0.3, self.current_accuracy - self.learning_rate * 0.5)
        
        # Check for level up
        self._check_level_up()
        
        return self.current_accuracy
    
    def _check_level_up(self):
        """Check if skill should level up"""
        level_thresholds = {
            SkillLevel.NOVICE: (5, 0.45),
            SkillLevel.BEGINNER: (15, 0.55),
            SkillLevel.INTERMEDIATE: (40, 0.65),
            SkillLevel.ADVANCED: (100, 0.75),
            SkillLevel.EXPERT: (250, 0.85),
            SkillLevel.MASTER: (500, 0.92),
        }
        
        current_level_value = self.level.value
        
        for level, (min_uses, min_accuracy) in level_thresholds.items():
            if level.value > current_level_value:
                if self.experience.total_uses >= min_uses and self.current_accuracy >= min_accuracy:
                    self.level = level
                    # Boost confidence modifier on level up
                    self.confidence_modifier = min(1.5, self.confidence_modifier + 0.1)
    
    def decay(self):
        """Apply decay to unused skill (call periodically)"""
        if self.experience.last_used:
            days_unused = (datetime.now() - self.experience.last_used).days
            if days_unused > 7:
                decay_amount = self.decay_rate * (days_unused / 7)
                self.current_accuracy = max(self.base_accuracy, 
                                           self.current_accuracy - decay_amount)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "level": self.level.value,
            "current_accuracy": round(self.current_accuracy, 3),
            "experience": {
                "total_uses": self.experience.total_uses,
                "successful_uses": self.experience.successful_uses,
                "total_pnl": round(self.experience.total_pnl, 2),
                "success_rate": round(self.experience.success_rate, 3),
            },
            "confidence_modifier": round(self.confidence_modifier, 2),
            "prerequisites": self.prerequisites,
            "synergies": self.synergies,
            "tags": list(self.tags),
        }


class SkillRegistry:
    """
    Central registry for all trading skills
    
    The Skill Registry manages OMNICUS's trading abilities,
    tracks their development, and helps combine skills for
    better trading decisions.
    
    Features:
    - Register and manage trading skills
    - Track skill development over time
    - Combine skills for enhanced analysis
    - Discover skill synergies
    - Learn new skills from experience
    """
    
    def __init__(self):
        """Initialize the skill registry"""
        self._skills: Dict[str, Skill] = {}
        self._category_index: Dict[SkillCategory, List[str]] = {
            cat: [] for cat in SkillCategory
        }
        
        # Initialize with base trading skills
        self._initialize_base_skills()
    
    def _initialize_base_skills(self):
        """Initialize OMNICUS with fundamental trading skills"""
        
        # Analysis Skills
        self.register_skill(Skill(
            name="technical_analysis",
            category=SkillCategory.ANALYSIS,
            description="Analyze price charts, indicators, and patterns",
            base_accuracy=0.55,
            current_accuracy=0.55,
            tags={"core", "charts", "indicators"}
        ))
        
        self.register_skill(Skill(
            name="volume_analysis",
            category=SkillCategory.ANALYSIS,
            description="Analyze trading volume patterns and trends",
            base_accuracy=0.50,
            current_accuracy=0.50,
            tags={"core", "volume", "momentum"}
        ))
        
        self.register_skill(Skill(
            name="whale_detection",
            category=SkillCategory.ANALYSIS,
            description="Detect large wallet movements and whale activity",
            base_accuracy=0.45,
            current_accuracy=0.45,
            tags={"advanced", "whales", "smart_money"}
        ))
        
        self.register_skill(Skill(
            name="sentiment_analysis",
            category=SkillCategory.SENTIMENT,
            description="Analyze market sentiment from news and social media",
            base_accuracy=0.50,
            current_accuracy=0.50,
            tags={"core", "sentiment", "news"}
        ))
        
        # Pattern Recognition Skills
        self.register_skill(Skill(
            name="trend_recognition",
            category=SkillCategory.PATTERN_RECOGNITION,
            description="Identify market trends and trend changes",
            base_accuracy=0.55,
            current_accuracy=0.55,
            tags={"core", "trends", "direction"}
        ))
        
        self.register_skill(Skill(
            name="support_resistance",
            category=SkillCategory.PATTERN_RECOGNITION,
            description="Identify support and resistance levels",
            base_accuracy=0.50,
            current_accuracy=0.50,
            tags={"core", "levels", "breakouts"}
        ))
        
        self.register_skill(Skill(
            name="breakout_detection",
            category=SkillCategory.PATTERN_RECOGNITION,
            description="Detect breakout patterns and opportunities",
            base_accuracy=0.45,
            current_accuracy=0.45,
            prerequisites=["support_resistance", "trend_recognition"],
            tags={"advanced", "breakouts", "momentum"}
        ))
        
        # Risk Management Skills
        self.register_skill(Skill(
            name="position_sizing",
            category=SkillCategory.RISK_MANAGEMENT,
            description="Calculate optimal position sizes based on risk",
            base_accuracy=0.60,
            current_accuracy=0.60,
            tags={"core", "risk", "sizing"}
        ))
        
        self.register_skill(Skill(
            name="stop_loss_placement",
            category=SkillCategory.RISK_MANAGEMENT,
            description="Determine optimal stop loss levels",
            base_accuracy=0.55,
            current_accuracy=0.55,
            tags={"core", "risk", "protection"}
        ))
        
        self.register_skill(Skill(
            name="risk_assessment",
            category=SkillCategory.RISK_MANAGEMENT,
            description="Assess overall portfolio and trade risk",
            base_accuracy=0.55,
            current_accuracy=0.55,
            tags={"core", "risk", "assessment"}
        ))
        
        # Timing Skills
        self.register_skill(Skill(
            name="entry_timing",
            category=SkillCategory.TIMING,
            description="Identify optimal entry points",
            base_accuracy=0.50,
            current_accuracy=0.50,
            tags={"core", "timing", "entry"}
        ))
        
        self.register_skill(Skill(
            name="exit_timing",
            category=SkillCategory.TIMING,
            description="Identify optimal exit points",
            base_accuracy=0.50,
            current_accuracy=0.50,
            tags={"core", "timing", "exit"}
        ))
        
        # Portfolio Skills
        self.register_skill(Skill(
            name="diversification",
            category=SkillCategory.PORTFOLIO,
            description="Manage portfolio diversification",
            base_accuracy=0.55,
            current_accuracy=0.55,
            tags={"core", "portfolio", "diversity"}
        ))
        
        self.register_skill(Skill(
            name="correlation_analysis",
            category=SkillCategory.PORTFOLIO,
            description="Analyze correlations between assets",
            base_accuracy=0.50,
            current_accuracy=0.50,
            tags={"advanced", "portfolio", "correlation"}
        ))
        
        # Adaptation Skills
        self.register_skill(Skill(
            name="market_adaptation",
            category=SkillCategory.ADAPTATION,
            description="Adapt strategy to changing market conditions",
            base_accuracy=0.45,
            current_accuracy=0.45,
            tags={"advanced", "adaptation", "flexibility"}
        ))
        
        self.register_skill(Skill(
            name="mistake_learning",
            category=SkillCategory.ADAPTATION,
            description="Learn from trading mistakes",
            base_accuracy=0.55,
            current_accuracy=0.55,
            tags={"core", "learning", "improvement"}
        ))
    
    def register_skill(self, skill: Skill) -> bool:
        """
        Register a new skill in the registry
        
        Args:
            skill: The skill to register
            
        Returns:
            True if registered successfully
        """
        if skill.name in self._skills:
            return False
        
        self._skills[skill.name] = skill
        self._category_index[skill.category].append(skill.name)
        
        return True
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name
        
        Args:
            name: Skill name
            
        Returns:
            The skill or None if not found
        """
        return self._skills.get(name)
    
    def use_skill(self, name: str, success: bool, pnl: float = 0.0) -> float:
        """
        Use a skill and update its accuracy
        
        Args:
            name: Skill name
            success: Whether the use was successful
            pnl: Profit or loss from the skill use
            
        Returns:
            Updated accuracy, or 0 if skill not found
        """
        skill = self._skills.get(name)
        if skill:
            return skill.use(success, pnl)
        return 0.0
    
    def get_skills_by_category(self, category: SkillCategory) -> List[Skill]:
        """
        Get all skills in a category
        
        Args:
            category: Skill category
            
        Returns:
            List of skills in the category
        """
        return [self._skills[name] for name in self._category_index[category]]
    
    def get_top_skills(self, limit: int = 5) -> List[Skill]:
        """
        Get top skills by accuracy
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of top skills
        """
        sorted_skills = sorted(
            self._skills.values(),
            key=lambda s: s.current_accuracy,
            reverse=True
        )
        return sorted_skills[:limit]
    
    def get_skills_for_trade(self, trade_type: str) -> List[Skill]:
        """
        Get relevant skills for a specific trade type
        
        Args:
            trade_type: Type of trade (e.g., "breakout", "trend_follow")
            
        Returns:
            List of relevant skills
        """
        skill_mapping = {
            "breakout": ["breakout_detection", "volume_analysis", "entry_timing"],
            "trend_follow": ["trend_recognition", "technical_analysis", "position_sizing"],
            "reversal": ["support_resistance", "technical_analysis", "exit_timing"],
            "momentum": ["volume_analysis", "trend_recognition", "entry_timing"],
            "risk_reduced": ["risk_assessment", "stop_loss_placement", "position_sizing"],
        }
        
        skill_names = skill_mapping.get(trade_type, ["technical_analysis", "risk_assessment"])
        return [self._skills[name] for name in skill_names if name in self._skills]
    
    def calculate_combined_accuracy(self, skill_names: List[str]) -> float:
        """
        Calculate combined accuracy when using multiple skills together
        
        Args:
            skill_names: List of skill names to combine
            
        Returns:
            Combined accuracy
        """
        if not skill_names:
            return 0.5
        
        skills = [self._skills[name] for name in skill_names if name in self._skills]
        
        if not skills:
            return 0.5
        
        # Weighted average based on skill levels
        total_weight = 0
        weighted_accuracy = 0
        
        for skill in skills:
            weight = skill.level.value  # Higher level = more weight
            weighted_accuracy += skill.current_accuracy * weight
            total_weight += weight
        
        base_accuracy = weighted_accuracy / total_weight if total_weight > 0 else 0.5
        
        # Synergy bonus
        synergy_bonus = self._calculate_synergy_bonus(skill_names)
        
        return min(0.95, base_accuracy + synergy_bonus)
    
    def _calculate_synergy_bonus(self, skill_names: List[str]) -> float:
        """Calculate bonus from skill synergies"""
        bonus = 0.0
        
        for name in skill_names:
            skill = self._skills.get(name)
            if skill:
                for synergy_name in skill.synergies:
                    if synergy_name in skill_names:
                        bonus += 0.02  # Small bonus per synergy
        
        return min(0.15, bonus)  # Cap at 15% bonus
    
    def get_skill_recommendations(self, context: Dict) -> List[str]:
        """
        Get recommended skills for a given context
        
        Args:
            context: Trading context (market conditions, etc.)
            
        Returns:
            List of recommended skill names
        """
        recommendations = []
        
        # Always recommend core skills
        recommendations.extend(["technical_analysis", "risk_assessment"])
        
        # Add based on context
        volatility = context.get("volatility", "normal")
        if volatility == "high":
            recommendations.extend(["stop_loss_placement", "position_sizing"])
        
        trend = context.get("trend", "sideways")
        if trend != "sideways":
            recommendations.append("trend_recognition")
        
        volume = context.get("volume", "normal")
        if volume == "spike":
            recommendations.extend(["volume_analysis", "whale_detection"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for name in recommendations:
            if name not in seen and name in self._skills:
                seen.add(name)
                unique.append(name)
        
        return unique
    
    def learn_new_skill(self, name: str, category: SkillCategory, description: str) -> Skill:
        """
        Learn a completely new skill
        
        Args:
            name: Skill name
            category: Skill category
            description: Skill description
            
        Returns:
            The newly created skill
        """
        skill = Skill(
            name=name,
            category=category,
            description=description,
            base_accuracy=0.40,  # Start low
            current_accuracy=0.40,
            level=SkillLevel.NOVICE,
        )
        
        self.register_skill(skill)
        return skill
    
    def decay_unused_skills(self):
        """Apply decay to all unused skills"""
        for skill in self._skills.values():
            skill.decay()
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the skill registry
        
        Returns:
            Dictionary with registry statistics
        """
        total_skills = len(self._skills)
        
        # Count by level
        level_counts = {}
        for level in SkillLevel:
            level_counts[level.name] = sum(
                1 for s in self._skills.values() if s.level == level
            )
        
        # Count by category
        category_counts = {
            cat.name: len(skills) 
            for cat, skills in self._category_index.items()
        }
        
        # Average accuracy
        avg_accuracy = sum(s.current_accuracy for s in self._skills.values()) / total_skills
        
        # Most used skills
        most_used = sorted(
            self._skills.values(),
            key=lambda s: s.experience.total_uses,
            reverse=True
        )[:5]
        
        return {
            "total_skills": total_skills,
            "average_accuracy": round(avg_accuracy, 3),
            "by_level": level_counts,
            "by_category": category_counts,
            "most_used": [{"name": s.name, "uses": s.experience.total_uses} for s in most_used],
            "top_skills": [s.to_dict() for s in self.get_top_skills()],
        }
    
    def to_dict(self) -> Dict:
        """Convert entire registry to dictionary"""
        return {
            "skills": {name: skill.to_dict() for name, skill in self._skills.items()},
            "stats": self.get_registry_stats(),
        }


# Default skill registry instance
skill_registry = SkillRegistry()
