"""
OMNICUS Soul Engine
===================
The emotional core that makes OMNICUS feel, talk, and connect.
"""

from .personality import (
 OMNICUSPersonality,
 PersonalityTraits,
 CommunicationStyle,
)

from .voice import (
 VoiceEngine,
 VoiceConfig,
 VoiceMode,
 VOICE_ENGINE,
)

from .emotions import (
 HappinessLevel,
 EmotionalState,
)

__all__ = [
 "OMNICUSPersonality",
 "PersonalityTraits",
 "CommunicationStyle",
 "VoiceEngine",
 "VoiceConfig",
 "VoiceMode",
 "VOICE_ENGINE",
 "HappinessLevel",
 "EmotionalState",
]
