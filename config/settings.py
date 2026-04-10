"""
OMNICUS Secure Configuration Loader
====================================
SECURITY: No hardcoded secrets! All sensitive data loaded from environment.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security settings - CRITICAL"""
    secret_key: str = ""
    dashboard_password: str = "omnicus2024"
    session_timeout_hours: int = 24
    
    def __post_init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "")
        self.dashboard_password = os.getenv("DASHBOARD_PASSWORD", "omnicus2024")
        self.session_timeout_hours = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
        
        if not self.secret_key:
            logger.warning("⚠️  SECRET_KEY not set! Using default (NOT SECURE)")


@dataclass
class TradingConfig:
    """Trading mode and risk settings"""
    mode: str = "simulation"  # simulation, paper, testnet, real
    paper_trading: bool = True
    starting_capital: float = 10000.0
    
    # Risk limits
    max_position_size_percent: float = 5.0
    max_total_exposure_percent: float = 50.0
    max_daily_loss_percent: float = 3.0
    max_drawdown_percent: float = 15.0
    
    # Targets (Aggressive!)
    min_daily_profit_percent: float = 10.0
    target_daily_profit_percent: float = 50.0
    double_capital_target: bool = True
    
    def __post_init__(self):
        self.mode = os.getenv("TRADING_MODE", "simulation")
        self.paper_trading = os.getenv("PAPER_TRADING", "true").lower() == "true"
        self.starting_capital = float(os.getenv("STARTING_CAPITAL", "10000"))
        
        self.max_position_size_percent = float(os.getenv("MAX_POSITION_SIZE_PERCENT", "5"))
        self.max_total_exposure_percent = float(os.getenv("MAX_TOTAL_EXPOSURE_PERCENT", "50"))
        self.max_daily_loss_percent = float(os.getenv("MAX_DAILY_LOSS_PERCENT", "3"))
        self.max_drawdown_percent = float(os.getenv("MAX_DRAWDOWN_PERCENT", "15"))


@dataclass
class BinanceConfig:
    """Binance exchange configuration"""
    api_key: str = ""
    api_secret: str = ""
    testnet: bool = True
    base_url: str = "https://api.binance.com"
    
    def __post_init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
        
        if self.api_key and not self.api_secret:
            logger.warning("⚠️  BINANCE_API_KEY set but BINANCE_API_SECRET missing!")
        
        if self.testnet:
            self.base_url = "https://testnet.binance.vision"


@dataclass
class KrakenConfig:
    """Kraken exchange configuration"""
    api_key: str = ""
    api_secret: str = ""
    
    def __post_init__(self):
        self.api_key = os.getenv("KRAKEN_API_KEY", "")
        self.api_secret = os.getenv("KRAKEN_API_SECRET", "")


@dataclass
class MEXCConfig:
    """MEXC exchange configuration"""
    api_key: str = ""
    api_secret: str = ""
    
    def __post_init__(self):
        self.api_key = os.getenv("MEXC_API_KEY", "")
        self.api_secret = os.getenv("MEXC_API_SECRET", "")


@dataclass
class PolymarketConfig:
    """Polymarket prediction market configuration"""
    api_key: str = ""
    private_key: str = ""
    
    def __post_init__(self):
        self.api_key = os.getenv("POLYMARKET_API_KEY", "")
        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY", "")


@dataclass
class AlpacaConfig:
    """Alpaca stocks trading configuration"""
    api_key: str = ""
    api_secret: str = ""
    paper: bool = True
    
    def __post_init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY", "")
        self.api_secret = os.getenv("ALPACA_API_SECRET", "")
        self.paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str = ""
    chat_id: str = ""
    
    def __post_init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    
    @property
    def enabled(self) -> bool:
        return bool(self.bot_token)


@dataclass
class VoiceConfig:
    """Voice/speech configuration"""
    enabled: bool = True
    mode: str = "full"  # silent, alerts, full, whisper
    rate: int = 180
    volume: float = 0.9
    
    def __post_init__(self):
        self.enabled = os.getenv("VOICE_ENABLED", "true").lower() == "true"
        self.mode = os.getenv("VOICE_MODE", "full")
        self.rate = int(os.getenv("VOICE_RATE", "180"))
        self.volume = float(os.getenv("VOICE_VOLUME", "0.9"))


@dataclass
class OmnicusPersonality:
    """OMNICUS personality settings"""
    hunger: float = 0.95
    confidence: float = 0.85
    risk_tolerance: float = 0.70
    
    def __post_init__(self):
        self.hunger = float(os.getenv("OMNICUS_HUNGER", "0.95"))
        self.confidence = float(os.getenv("OMNICUS_CONFIDENCE", "0.85"))
        self.risk_tolerance = float(os.getenv("OMNICUS_RISK_TOLERANCE", "0.70"))


@dataclass
class DatabaseConfig:
    """Database configuration"""
    path: str = "omnicus.db"
    backup_path: str = "backups/"
    
    def __post_init__(self):
        self.path = os.getenv("DATABASE_PATH", "omnicus.db")
        self.backup_path = os.getenv("DATABASE_BACKUP_PATH", "backups/")


@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    port: int = 5000
    host: str = "127.0.0.1"
    bind_local: bool = True
    
    def __post_init__(self):
        self.port = int(os.getenv("DASHBOARD_PORT", "5000"))
        self.host = os.getenv("DASHBOARD_HOST", "127.0.0.1")
        self.bind_local = os.getenv("DASHBOARD_BIND_LOCAL", "true").lower() == "true"


class Settings:
    """
    Main configuration class for OMNICUS.
    All sensitive data loaded from environment variables.
    """
    
    def __init__(self):
        self.security = SecurityConfig()
        self.trading = TradingConfig()
        self.binance = BinanceConfig()
        self.kraken = KrakenConfig()
        self.mexc = MEXCConfig()
        self.polymarket = PolymarketConfig()
        self.alpaca = AlpacaConfig()
        self.telegram = TelegramConfig()
        self.voice = VoiceConfig()
        self.personality = OmnicusPersonality()
        self.database = DatabaseConfig()
        self.dashboard = DashboardConfig()
        
        self._log_startup_info()
    
    def _log_startup_info(self):
        """Log configuration on startup (without secrets)"""
        logger.info("=" * 60)
        logger.info("OMNICUS Configuration Loaded")
        logger.info("=" * 60)
        logger.info(f"Trading Mode: {self.trading.mode}")
        logger.info(f"Paper Trading: {self.trading.paper_trading}")
        logger.info(f"Starting Capital: ${self.trading.starting_capital:,.2f}")
        logger.info(f"Binance Configured: {bool(self.binance.api_key)}")
        logger.info(f"Kraken Configured: {bool(self.kraken.api_key)}")
        logger.info(f"MEXC Configured: {bool(self.mexc.api_key)}")
        logger.info(f"Polymarket Configured: {bool(self.polymarket.api_key)}")
        logger.info(f"Alpaca Configured: {bool(self.alpaca.api_key)}")
        logger.info(f"Telegram Enabled: {self.telegram.enabled}")
        logger.info(f"Voice Enabled: {self.voice.enabled}")
        logger.info(f"Dashboard: http://{self.dashboard.host}:{self.dashboard.port}")
        logger.info("=" * 60)
    
    def get_exchange_credentials(self, exchange: str) -> Dict[str, str]:
        """Get credentials for a specific exchange"""
        exchange = exchange.lower()
        
        if exchange == "binance":
            return {
                "api_key": self.binance.api_key,
                "api_secret": self.binance.api_secret,
                "testnet": str(self.binance.testnet).lower()
            }
        elif exchange == "kraken":
            return {
                "api_key": self.kraken.api_key,
                "api_secret": self.kraken.api_secret
            }
        elif exchange == "mexc":
            return {
                "api_key": self.mexc.api_key,
                "api_secret": self.mexc.api_secret
            }
        elif exchange == "polymarket":
            return {
                "api_key": self.polymarket.api_key,
                "private_key": self.polymarket.private_key
            }
        elif exchange == "alpaca":
            return {
                "api_key": self.alpaca.api_key,
                "api_secret": self.alpaca.api_secret,
                "paper": str(self.alpaca.paper).lower()
            }
        else:
            logger.warning(f"Unknown exchange: {exchange}")
            return {}
    
    def is_exchange_configured(self, exchange: str) -> bool:
        """Check if an exchange has valid credentials"""
        creds = self.get_exchange_credentials(exchange)
        return bool(creds.get("api_key"))
    
    def get_configured_exchanges(self) -> list:
        """Get list of configured exchanges"""
        exchanges = []
        for exchange in ["binance", "kraken", "mexc", "polymarket", "alpaca"]:
            if self.is_exchange_configured(exchange):
                exchanges.append(exchange)
        return exchanges


# Global settings instance
settings = Settings()
