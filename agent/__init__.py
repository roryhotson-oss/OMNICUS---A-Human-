"""
OMNICUS Agent Package
=====================
"""

from .ai_brain import (
    AIBrain,
    DecisionType,
    ConfidenceLevel,
    MarketContext,
    TradeSignal,
    AnalysisResult,
)

from .memory_bank import (
    MemoryBank,
    Memory,
    MemoryType,
)

from .emotions import (
    EmotionTracker,
    EmotionalState,
    PersonalityConfig,
    EmotionalMetrics,
)

from .skills import (
    SkillRegistry,
    Skill,
    SkillCategory,
    SkillLevel,
    SkillExperience,
)

from .tools import (
    ToolKit,
    Tool,
    ToolType,
    ToolResult,
)

from .workflow import (
    WorkflowEngine,
    Workflow,
    WorkflowType,
    WorkflowState,
)


def create_omnicus_brain(
    personality=None,
    db_path=None,
    min_confidence=0.65,
    max_position_percent=5.0,
    risk_per_trade_percent=2.0
):
    """Create a fully initialized OMNICUS AI Brain"""
    if personality is None:
        personality = PersonalityConfig()
    
    memory = MemoryBank(db_path=db_path or "/tmp/omnicus_memory.db")
    emotions = EmotionTracker(personality=personality)
    skills = SkillRegistry()
    tools = ToolKit()
    workflow = WorkflowEngine()
    
    return AIBrain(
        memory_bank=memory,
        emotion_tracker=emotions,
        skill_registry=skills,
        toolkit=tools,
        workflow_engine=workflow,
        personality=personality,
    )


__all__ = [
    'AIBrain', 'DecisionType', 'ConfidenceLevel', 'MarketContext',
    'TradeSignal', 'AnalysisResult', 'MemoryBank', 'Memory', 'MemoryType',
    'EmotionTracker', 'EmotionalState', 'PersonalityConfig', 'EmotionalMetrics',
    'SkillRegistry', 'Skill', 'SkillCategory', 'SkillLevel', 'SkillExperience',
    'ToolKit', 'Tool', 'ToolType', 'ToolResult',
    'WorkflowEngine', 'Workflow', 'WorkflowType', 'WorkflowState',
    'create_omnicus_brain',
]
