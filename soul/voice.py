"""
OMNICUS Voice Engine
====================
Voice synthesis and recognition for OMNICUS.
Uses pyttsx3 for text-to-speech and SpeechRecognition for voice input.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import asyncio
import logging
import sys
import threading

logger = logging.getLogger('OMNICUS.Voice')


class VoiceMode(Enum):
    """Voice operation modes"""
    SILENT = "silent"
    ALERTS_ONLY = "alerts_only"
    FULL = "full"
    INTERACTIVE = "interactive"


@dataclass
class VoiceConfig:
    """Voice engine configuration"""
    enabled: bool = True
    mode: VoiceMode = VoiceMode.ALERTS_ONLY
    volume: float = 0.8
    rate: int = 200
    voice_id: Optional[str] = None
    use_pyttsx3: bool = True


class VoiceEngine:
    """
    Voice synthesis engine for OMNICUS.
    Supports multiple TTS backends and voice recognition.
    """
    
    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig()
        self._speaking = False
        self._lock = threading.Lock()
        self._loop = None
        
        # Initialize TTS engine
        self._tts_engine = None
        self._init_tts()
        
        # Initialize speech recognition
        self._recognizer = None
        self._microphone = None
        self._init_speech_recognition()
        
        logger.info(f"Voice Engine initialized - Mode: {self.config.mode.value}")
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        if not self.config.enabled or not self.config.use_pyttsx3:
            return
        
        try:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            
            # Configure engine
            if self._tts_engine:
                self._tts_engine.setProperty('volume', self.config.volume)
                self._tts_engine.setProperty('rate', self.config.rate)
                
                # Set voice if specified
                if self.config.voice_id:
                    voices = self._tts_engine.getProperty('voices')
                    for voice in voices:
                        if self.config.voice_id in str(voice.id):
                            self._tts_engine.setProperty('voice', voice.id)
                            break
            
            logger.info("TTS engine initialized with pyttsx3")
        except ImportError:
            logger.warning("pyttsx3 not available - voice synthesis disabled")
            self._tts_engine = None
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self._tts_engine = None
    
    def _init_speech_recognition(self):
        """Initialize speech recognition"""
        if not self.config.enabled:
            return
        
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._microphone = sr.Microphone()
            logger.info("Speech recognition initialized")
        except ImportError:
            logger.warning("speech_recognition not available - voice input disabled")
            self._recognizer = None
        except Exception as e:
            logger.error(f"Failed to initialize speech recognition: {e}")
            self._recognizer = None
    
    def _should_speak(self) -> bool:
        """Check if voice should be used based on mode"""
        if not self.config.enabled:
            return False
        if self.config.mode == VoiceMode.SILENT:
            return False
        return True
    
    async def speak(self, text: str, emotion: str = "neutral") -> bool:
        """
        Speak text with emotional tone.
        
        Args:
            text: Text to speak
            emotion: Emotional context (affects tone/rate)
            
        Returns:
            True if speech was successful, False otherwise
        """
        if not self._should_speak():
            return False
        
        if not self._tts_engine:
            logger.debug("No TTS engine available")
            return False
        
        # Adjust voice properties based on emotion
        original_rate = self._tts_engine.getProperty('rate')
        original_volume = self._tts_engine.getProperty('volume')
        
        try:
            # Apply emotion-based modifications
            if emotion == "excited" or emotion == "happy":
                self._tts_engine.setProperty('rate', original_rate + 30)
                self._tts_engine.setProperty('volume', min(1.0, original_volume + 0.1))
            elif emotion == "stressed" or emotion == "urgent":
                self._tts_engine.setProperty('rate', original_rate + 50)
            elif emotion == "sad" or emotion == "apology":
                self._tts_engine.setProperty('rate', original_rate - 20)
                self._tts_engine.setProperty('volume', max(0.5, original_volume - 0.1))
            
            with self._lock:
                self._speaking = True
                
                # Run in separate thread to avoid blocking
                def _speak_thread():
                    try:
                        self._tts_engine.say(text)
                        self._tts_engine.runAndWait()
                    except Exception as e:
                        logger.error(f"Error in speech synthesis: {e}")
                    finally:
                        self._speaking = False
                
                thread = threading.Thread(target=_speak_thread)
                thread.start()
                thread.join(timeout=10)  # Timeout after 10 seconds
                
                if thread.is_alive():
                    logger.warning("Speech synthesis timed out")
                    self._speaking = False
                
            return True
            
        except Exception as e:
            logger.error(f"Speech error: {e}")
            self._speaking = False
            return False
        finally:
            # Restore original properties
            self._tts_engine.setProperty('rate', original_rate)
            self._tts_engine.setProperty('volume', original_volume)
    
    def speak_sync(self, text: str, emotion: str = "neutral") -> bool:
        """Synchronous speak method"""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.speak(text, emotion))
        except RuntimeError:
            # No event loop running
            return asyncio.run(self.speak(text, emotion))
    
    async def listen(self, timeout: float = 5.0, phrase_time_limit: float = 10.0) -> Optional[str]:
        """
        Listen for voice input.
        
        Args:
            timeout: Seconds to wait for speech
            phrase_time_limit: Maximum seconds for a phrase
            
        Returns:
            Recognized text, or None if failed
        """
        if not self._recognizer or not self._microphone:
            logger.debug("Speech recognition not available")
            return None
        
        try:
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            # Use Google Web Speech API
            text = self._recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text
            
        except Exception as e:
            logger.debug(f"Speech recognition error: {e}")
            return None
    
    def say_greeting(self):
        """Speak a greeting message"""
        greetings = [
            "OMNICUS online. Ready to hunt for profits.",
            "Boss, I'm here. Let's make some money.",
            "The profit hunter is active. What's the play?",
            "Markets are calling. Let's answer."
        ]
        import random
        greeting = random.choice(greetings)
        asyncio.create_task(self.speak(greeting, emotion="confident"))
    
    def say_farewell(self):
        """Speak a farewell message"""
        farewells = [
            "Signing off, boss. Markets never sleep.",
            "OMNICUS out. Stay profitable.",
            "Until next time. Don't spend all those profits at once.",
            "Going dark. Wake me when the markets move."
        ]
        import random
        farewell = random.choice(farewells)
        asyncio.create_task(self.speak(farewell, emotion="neutral"))
    
    def alert_trade_entered(self, symbol: str, action: str, price: float, confidence: float):
        """Announce a new trade"""
        action_word = "buying" if action.lower() == "buy" else "selling"
        message = f"Entering trade: {action_word} {symbol} at {price:.2f} with {confidence:.0%} confidence."
        asyncio.create_task(self.speak(message, emotion="confident"))
    
    def alert_trade_closed(self, symbol: str, pnl: float, duration: str):
        """Announce a closed trade"""
        if pnl > 0:
            message = f"Closed {symbol}. Profit: plus {pnl:.2f} dollars. {duration}."
            emotion = "happy"
        else:
            message = f"Closed {symbol}. Loss: minus {abs(pnl):.2f} dollars. {duration}."
            emotion = "sad"
        asyncio.create_task(self.speak(message, emotion=emotion))
    
    def alert_high_confidence(self, symbol: str, confidence: float):
        """Alert about high confidence opportunity"""
        message = f"High confidence alert: {symbol} at {confidence:.0%}. This looks strong."
        asyncio.create_task(self.speak(message, emotion="excited"))
    
    def alert_risk_warning(self, message: str):
        """Alert about risk"""
        asyncio.create_task(self.speak(f"Risk warning: {message}", emotion="stressed"))
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self._speaking
    
    def stop(self):
        """Stop current speech"""
        self._speaking = False
        if self._tts_engine:
            try:
                self._tts_engine.stop()
            except:
                pass
    
    def set_mode(self, mode: VoiceMode):
        """Set voice operation mode"""
        self.config.mode = mode
        logger.info(f"Voice mode set to: {mode.value}")
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self.config.volume = max(0.0, min(1.0, volume))
        if self._tts_engine:
            self._tts_engine.setProperty('volume', self.config.volume)
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        self.config.rate = rate
        if self._tts_engine:
            self._tts_engine.setProperty('rate', rate)


# Global voice engine instance
VOICE_ENGINE = VoiceEngine()


__all__ = [
    "VoiceEngine",
    "VoiceConfig",
    "VoiceMode",
    "VOICE_ENGINE",
]
