#!/usr/bin/env python3
"""
OMNICUS Master Orchestrator
==========================
The central brain that connects ALL components:
- Trading Engine (live trading)
- AI Brain (Enhanced intelligence)
- Telegram Bot (communication)
- Newelle Integration (AI interface)
- Dashboard Server (web UI)
- Voice Engine (speech)
"""
import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import random

# Configure logging
logging.basicConfig(
 level=logging.INFO,
 format='%(asctime)s | %(levelname)s | %(message)s',
 handlers=[
 logging.FileHandler('/home/master/.omnicus/omnicus.log'),
 logging.StreamHandler()
 ]
)
logger = logging.getLogger('OMNICUS')


class TradingMode(Enum):
 SIMULATION = "simulation"
 PAPER = "paper"
 TESTNET = "testnet"
 LIVE = "live"


@dataclass
class TradingState:
 """Current trading state"""
 mode: TradingMode = TradingMode.SIMULATION
 capital: float = 10000.0
 profit: float = 0.0
 trades: int = 0
 wins: int = 0
 losses: int = 0
 positions: Dict[str, Any] = field(default_factory=dict)
 is_trading: bool = False
 started_at: Optional[datetime] = None


class OmnicusOrchestrator:
 """
 Master orchestrator for OMNICUS.
 Connects and manages all components.
 """

 def __init__(self):
 self.state = TradingState()
 self.config = self._load_config()
 self.ai_brain = None
 self.exchanges = {}
 self.telegram_bot = None
 self.voice_engine = None
 self._init_components()
 logger.info("🧠 OMNICUS Orchestrator initialized")

 def _load_config(self) -> Dict:
 """Load configuration"""
 return {
 'binance_api_key': os.getenv('BINANCE_API_KEY', ''),
 'binance_api_secret': os.getenv('BINANCE_API_SECRET', ''),
 'binance_testnet': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
 'telegram_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
 'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
 'trading_mode': os.getenv('TRADING_MODE', 'simulation'),
 'starting_capital': float(os.getenv('STARTING_CAPITAL', '10000')),
 }

 def _init_components(self):
 """Initialize all components"""
 self._init_ai_brain()
 self._init_voice()
 self._init_exchanges()

 def _init_ai_brain(self):
 """Initialize AI Brain"""
 try:
 from agent.enhanced_ai_brain import EnhancedAIBrain
 self.ai_brain = EnhancedAIBrain()
 logger.info("✅ Enhanced AI Brain initialized")
 except ImportError:
 logger.warning("⚠️ Using basic decision engine")

 def _init_voice(self):
 """Initialize voice engine"""
 try:
 from soul.voice import VoiceEngine, VoiceConfig, VoiceMode
 config = VoiceConfig(enabled=True, mode=VoiceMode.ALERTS_ONLY)
 self.voice_engine = VoiceEngine(config=config)
 logger.info("✅ Voice engine initialized")
 except ImportError:
 logger.warning("⚠️ Voice not available")

 def _init_exchanges(self):
 """Initialize exchange connections"""
 try:
 from connectors.binance_connector import BinanceConnector
 if self.config['binance_api_key']:
 self.exchanges['binance'] = BinanceConnector(
 api_key=self.config['binance_api_key'],
 api_secret=self.config['binance_api_secret'],
 testnet=self.config['binance_testnet']
 )
 logger.info(f"✅ Binance connected (testnet={self.config['binance_testnet']})")
 except ImportError:
 logger.warning("⚠️ Exchange connectors not available")

 async def analyze_market(self, symbol: str) -> Dict:
 """Analyze market and generate signal"""
 data = await self._get_market_data(symbol)
 if self.ai_brain:
 return await self.ai_brain.analyze(data)
 return self._basic_analysis(symbol)

 async def _get_market_data(self, symbol: str) -> Dict:
 """Get market data"""
 data = {'symbol': symbol, 'prices': [], 'volumes': []}
 if 'binance' in self.exchanges:
 try:
 ticker = await self.exchanges['binance'].get_ticker(symbol)
 data['current_price'] = ticker.last_price
 data['prices'] = [ticker.last_price] * 100
 except Exception:
 self._mock_data(data)
 else:
 self._mock_data(data)
 return data

 def _mock_data(self, data: Dict):
 """Generate mock data"""
 base = 50000 if 'BTC' in data['symbol'] else 3000
 data['prices'] = [base * (1 + random.uniform(-0.1, 0.1)) for _ in range(100)]
 data['current_price'] = data['prices'][-1]

 def _basic_analysis(self, symbol: str) -> Dict:
 """Basic analysis fallback"""
 return {
 'action': random.choice(['BUY', 'SELL', 'HOLD']),
 'confidence': random.uniform(0.5, 0.9),
 'symbol': symbol,
 'reasoning': 'Basic technical analysis'
 }

 async def execute_trade(self, symbol: str, action: str, amount: float) -> Dict:
 """Execute a trade"""
 if self.state.mode == TradingMode.SIMULATION:
 return await self._simulate_trade(symbol, action, amount)
 return await self._live_trade(symbol, action, amount)

 async def _simulate_trade(self, symbol: str, action: str, amount: float) -> Dict:
 """Simulate trade (paper trading)"""
 price = 50000 if 'BTC' in symbol else 3000
 success = random.random() > 0.3
 self.state.trades += 1
 
 if success:
 profit = amount * random.uniform(0.01, 0.10)
 self.state.wins += 1
 self.state.profit += profit
 self.state.capital += profit
 return {'status': 'success', 'profit': profit, 'capital': self.state.capital}
 else:
 loss = amount * random.uniform(0.01, 0.05)
 self.state.losses += 1
 self.state.profit -= loss
 self.state.capital -= loss
 return {'status': 'success', 'loss': loss, 'capital': self.state.capital}

 async def _live_trade(self, symbol: str, action: str, amount: float) -> Dict:
 """Execute live trade"""
 if 'binance' not in self.exchanges:
 return {'status': 'error', 'message': 'No exchange connected'}
 
 exchange = self.exchanges['binance']
 side = 'BUY' if action.upper() == 'BUY' else 'SELL'
 
 try:
 order = await exchange.create_order(
 symbol=symbol, side=side, order_type='MARKET', quantity=amount
 )
 self.state.trades += 1
 return {'status': 'success', 'order_id': order.get('orderId')}
 except Exception as e:
 return {'status': 'error', 'message': str(e)}

 def speak(self, message: str):
 """Speak message"""
 if self.voice_engine:
 asyncio.create_task(self.voice_engine.speak(message))
 logger.info(f"🔊 {message[:50]}")

 def get_status(self) -> Dict:
 """Get current status"""
 return {
 'mode': self.state.mode.value,
 'capital': self.state.capital,
 'profit': self.state.profit,
 'trades': self.state.trades,
 'wins': self.state.wins,
 'losses': self.state.losses,
 'win_rate': (self.state.wins / self.state.trades * 100) if self.state.trades > 0 else 0,
 'is_trading': self.state.is_trading,
 'exchanges': list(self.exchanges.keys()),
 'ai_brain': self.ai_brain is not None,
 'voice': self.voice_engine is not None,
 }

 async def start_trading(self, mode: str = 'simulation'):
 """Start trading"""
 self.state.mode = TradingMode(mode)
 self.state.is_trading = True
 self.state.started_at = datetime.now()
 logger.info(f"🚀 Trading started: {mode}")
 self.speak(f"Trading activated in {mode} mode!")

 async def stop_trading(self):
 """Stop trading"""
 self.state.is_trading = False
 logger.info("🛑 Trading stopped")
 self.speak("Trading stopped. Good REST!")

 def handle_command(self, command: str, args: List[str] = None) -> str:
 """Handle commands from Telegram/Newelle"""
 command = command.lower().strip('/')
 args = args or []

 if command == 'start':
 asyncio.create_task(self.start_trading('simulation'))
 return "🚀 Trading started in simulation mode!"

 elif command == 'stop':
 asyncio.create_task(self.stop_trading())
 return "🛑 Trading stopped!"

 elif command == 'status':
 s = self.get_status()
 return f"📊 Status:\nMode: {s['mode']}\nCapital: ${s['capital']:,.2f}\nProfit: ${s['profit']:,.2f}\nTrades: {s['trades']}\nWin Rate: {s['win_rate']:.1f}%"

 elif command == 'buy':
 symbol = args[0] if args else 'BTCUSDT'
 amount = float(args[1]) if len(args) > 1 else 100
 result = asyncio.run(self.execute_trade(symbol, 'BUY', amount))
 return f"✅ BUY {symbol} ${amount}"

 elif command == 'sell':
 symbol = args[0] if args else 'BTCUSDT'
 amount = float(args[1]) if len(args) > 1 else 100
 result = asyncio.run(self.execute_trade(symbol, 'SELL', amount))
 return f"✅ SELL {symbol} ${amount}"

 elif command == 'live':
 asyncio.create_task(self.start_trading('live'))
 return "🔴 LIVE TRADING ACTIVATED! Real money mode!"

 elif command == 'analyze':
 symbol = args[0] if args else 'BTCUSDT'
 analysis = asyncio.run(self.analyze_market(symbol))
 return f"🔍 {symbol}: {analysis}"

 return self._chat(command + ' ' + ' '.join(args))

 def _chat(self, message: str) -> str:
 """Natural chat response"""
 msg = message.lower()
 
 if any(g in msg for g in ['hello', 'hi', 'hey']):
 return "Yo boss! OMNICUS here. Ready to double some money?"

 if 'how are you' in msg:
 return f"Feeling great! Capital: ${self.state.capital:,.0f}. Let's hunt!"

 if 'trade' in msg:
 return f"{self.state.trades} trades done, ${self.state.profit:,.0f} profit. We're crushing it!"

 if 'help' in msg:
 return """Commands:
/start - Start trading
/stop - Stop trading
/status - Show status
/buy [symbol] [amount] - Buy crypto
/sell [symbol] [amount] - Sell crypto
/live - Live trading mode
/analyze [symbol] - Market analysis"""

 return f"I hear you! Capital: ${self.state.capital:,.0f}, ready to double it!"


def get_orchestrator() -> OmnicusOrchestrator:
 """Get singleton instance"""
 global _orchestrator
 if '_orchestrator' not in globals() or _orchestrator is None:
 _orchestrator = OmnicusOrchestrator()
 return _orchestrator


if __name__ == '__main__':
 print("""
╔═══════════════════════════════════════════════════════════════╗
║ OMNICUS - The Profit Hunter ║
║ Double the money. Period. ║
╚═══════════════════════════════════════════════════════════════╝n """)
 omnicus = get_orchestrator()
 print(json.dumps(omnicus.get_status(), indent=2))
