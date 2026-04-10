#!/usr/bin/env python3
"""
OMNICUS Live Trading Assistant
==============================
AI-powered trading assistant that can:
- Place real trades on exchanges
- Talk to you via voice and Telegram
- Analyze markets and make decisions
- Learn from every trade
"""

import asyncio
import logging
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.enhanced_ai_brain import EnhancedAIBrain, AIStrategy
from connectors.binance_connector import BinanceConnector
from soul.voice import VoiceEngine, VOICE_ENGINE
from soul.personality import OMNICUSPersonality

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
 """Result of a trade execution"""
 success: bool
 symbol: str
 action: str
 amount: float
 price: float
 pnl: float = 0.0
 message: str = ""


class OMNICUSTradingAssistant:
 """
 Complete Trading Assistant that can:
 - Analyze markets using Enhanced AI Brain
 - Execute trades on real exchanges
 - Talk via voice and text
 - Send Telegram messages
 - Learn from results
 """

 def __init__(self, mode: str = 'paper'):
 self.mode = mode # 'paper', 'testnet', 'live'
 self.ai_brain = EnhancedAIBrain()
 self.personality = OMNICUSPersonality()
 self.voice = VOICE_ENGINE
 self.exchange: Optional[BinanceConnector] = None
 self.telegram_bot = None
 self.running = False
 
 # Trading state
 self.capital = 10000.0
 self.positions: Dict[str, Dict] = {}
 self.trade_history: List[Dict] = []
 self.total_pnl = 0.0
 self.trades_today = 0
 
 # Risk management
 self.max_position_size = 0.05 # 5% of capital
 self.max_daily_trades = 20
 self.daily_loss_limit = 0.03 # 3% daily loss limit
 self.daily_loss = 0.0
 
 logger.info(f"🤖 OMNICUS Trading Assistant initialized in {mode} mode")
 
 async def initialize(self, api_key: str = '', api_secret: str = ''):
 """Initialize exchange connection and voice engine"""
 self.speak("Initializing OMNICUS Trading Assistant. Let me connect to the markets...")
 
 # Initialize exchange
 self.exchange = BinanceConnector(api_key=api_key, api_secret=api_secret)
 connected = await self.exchange.connect()
 
 if connected:
 self.speak("Successfully connected to Binance exchange. Ready to hunt profits!")
 else:
 self.speak("Connection to exchange failed. Running in simulation mode.")
 self.mode = 'paper'
 
 return connected
 
 def speak(self, text: str, emotion: str = 'neutral'):
 """
 Speak text using voice engine with personality.
 
 Args:
 text: What to say
 emotion: 'neutral', 'happy', 'excited', 'concerned', 'alert'
 """
 # Add personality to the message
 styled_text = self.personality.style_message(text, emotion)
 print(f"🗣️ OMNICUS: {styled_text}")
 
 # Speak via voice engine
 self.voice.speak_sync(styled_text, emotion)
 
 async def say(self, text: str, emotion: str = 'neutral'):
 """Async speak method"""
 self.speak(text, emotion)
 
 async def analyze_and_trade(self, symbol: str = 'BTCUSDT'):
 """
 Analyze market and potentially place a trade.
 
 Args:
 symbol: Trading pair to analyze
 
 Returns:
 TradeResult if trade executed, None if no action
 """
 self.speak(f"Analyzing {symbol}... Let me check the charts and signals.")
 
 # Get market data
 market_data = await self._get_market_data(symbol)
 
 if not market_data:
 self.speak(f"Unable to get data for {symbol}. Skipping this cycle.")
 return None
 
 # Analyze with AI
 signal = await self.ai_brain.analyze(market_data)
 
 # Generate reasoning speech
 reasoning_text = self._generate_reasoning_speech(signal)
 self.speak(reasoning_text)
 
 # Decide whether to trade
 if self._should_execute_trade(signal):
 result = await self._execute_trade(symbol, signal, market_data)
 return result
 
 return None
 
 async def _get_market_data(self, symbol: str) -> Optional[Dict]:
 """Get real-time market data"""
 try:
 if self.exchange and self.mode != 'paper':
 # Real data from exchange
 ticker = await self.exchange.get_ticker(symbol)
 klines = await self.exchange.get_klines(symbol, '1h', limit=100)
 
 prices = [k['close'] for k in klines]
 volumes = [k['volume'] for k in klines]
 
 return {
 'symbol': symbol,
 'prices': prices,
 'volumes': volumes,
 'current_price': ticker.last_price,
 'high_24h': ticker.high_24h,
 'low_24h': ticker.low_24h,
 'volume_24h': ticker.volume_24h
 }
 else:
 # Simulated data for paper trading
 return self._generate_simulated_data(symbol)
 
 except Exception as e:
 logger.error(f"Error getting market data: {e}")
 return None
 
 def _generate_simulated_data(self, symbol: str) -> Dict:
 """Generate simulated market data for paper trading"""
 base_prices = {
 'BTCUSDT': 50000,
 'ETHUSDT': 3000,
 'SOLUSDT': 100,
 'BNBUSDT': 400,
 'DOGEUSDT': 0.12
 }
 
 base = base_prices.get(symbol, 100)
 
 # Generate realistic price movements
 trend = random.choice([-1, 0, 1])
 volatility = random.uniform(0.01, 0.05)
 
 prices = [base]
 for _ in range(99):
 change = trend * random.uniform(0, volatility) * base
 noise = random.uniform(-volatility, volatility) * base
 prices.append(prices[-1] + change + noise)
 
 volumes = [random.uniform(100, 10000) for _ in range(100)]
 
 return {
 'symbol': symbol,
 'prices': prices,
 'volumes': volumes,
 'current_price': prices[-1],
 'high_24h': max(prices),
 'low_24h': min(prices),
 'volume_24h': sum(volumes)
 }
 
 def _should_execute_trade(self, signal) -> bool:
 """Determine if we should execute based on signal and risk rules"""
 # Check confidence threshold
 if signal.confidence < 0.65:
 return False
 
 # Check daily trade limit
 if self.trades_today >= self.max_daily_trades:
 return False
 
 # Check daily loss limit
 if self.daily_loss < -self.capital * self.daily_loss_limit:
 self.speak("We've hit the daily loss limit. Stopping trading for today.", 'concerned')
 return False
 
 # Strong signals only
 return signal.action in ['STRONG_BUY', 'STRONG_SELL', 'BUY', 'SELL']
 
 async def _execute_trade(self, symbol: str, signal, market_data: Dict) -> TradeResult:
 """Execute the trade"""
 action = signal.action
 price = market_data['current_price']
 
 # Calculate position size
 position_size = self.capital * self.max_position_size
 amount = position_size / price
 
 # Calculate stops
 if 'BUY' in action:
 stop_loss = price * 0.98 # 2% stop loss
 take_profit = price * 1.06 # 6% take profit
 else:
 stop_loss = price * 1.02
 take_profit = price * 0.94
 
 result = TradeResult(
 success=False,
 symbol=symbol,
 action=action,
 amount=amount,
 price=price
 )
 
 try:
 if self.mode == 'live' and self.exchange:
 # Real trade execution
 side = 'BUY' if 'BUY' in action else 'SELL'
 order = await self.exchange.create_order(
 symbol=symbol,
 side=side,
 order_type='MARKET',
 quantity=amount
 )
 
 if order:
 result.success = True
 self.speak(f"Trade executed! {action} on {symbol} at ${price:.2f}. Position size: ${position_size:.2f}", 'excited')
 else:
 self.speak(f"Trade execution failed. Something went wrong.", 'concerned')
 
 else:
 # Paper trading - simulate
 result.success = True
 self.speak(f"[PAPER] {action} on {symbol} at ${price:.2f}. Position: ${position_size:.2f}", 'neutral')
 
 # Update positions
 if result.success:
 self.trades_today += 1
 if symbol in self.positions:
 self.positions[symbol]['amount'] += amount
 self.positions[symbol]['avg_price'] = (self.positions[symbol]['avg_price'] + price) / 2
 else:
 self.positions[symbol] = {
 'amount': amount,
 'avg_price': price,
 'stop_loss': stop_loss,
 'take_profit': take_profit,
 'action': action
 }
 
 self.trade_history.append({
 'symbol': symbol,
 'action': action,
 'price': price,
 'amount': amount,
 'time': datetime.now().isoformat(),
 'confidence': signal.confidence,
 'reasoning': signal.reasoning
 })
 
 except Exception as e:
 logger.error(f"Trade execution error: {e}")
 self.speak(f"Error executing trade: {str(e)}", 'alert')
 
 return result
 
 def _generate_reasoning_speech(self, signal) -> str:
 """Generate natural speech from AI reasoning"""
 action = signal.action
 confidence = signal.confidence
 regime = signal.market_regime
 
 # Base message
 if 'BUY' in action:
 base = f"{signal.confidence*100:.0f}% confident BUY signal detected. "
 elif 'SELL' in action:
 base = f"{signal.confidence*100:.0f}% confident SELL signal detected. "
 else:
 base = "Holding position. No clear signal right now. "
 
 # Add reasoning
 if signal.reasoning:
 base += f"Reasons: {', '.join(signal.reasoning[:3])}. "
 
 # Add regime
 base += f"Market regime: {regime}. "
 
 # Add strategy
 base += f"Using {signal.strategy.value} strategy."
 
 return base
 
 async def check_positions(self):
 """Check existing positions for stop loss / take profit"""
 for symbol, position in self.positions.items():
 market_data = await self._get_market_data(symbol)
 if not market_data:
 continue
 
 current_price = market_data['current_price']
 
 # Check stop loss
 if position['action'] in ['BUY', 'STRONG_BUY']:
 if current_price <= position['stop_loss']:
 self.speak(f"Stop loss triggered on {symbol}! Closing position at ${current_price:.2f}", 'alert')
 await self._close_position(symbol, current_price)
 elif current_price >= position['take_profit']:
 self.speak(f"Take profit hit on {symbol}! Closing position at ${current_price:.2f}", 'excited')
 await self._close_position(symbol, current_price)
 
 async def _close_position(self, symbol: str, price: float):
 """Close a position"""
 if symbol not in self.positions:
 return
 
 position = self.positions[symbol]
 pnl = (price - position['avg_price']) * position['amount']
 if position['action'] not in ['BUY', 'STRONG_BUY']:
 pnl = -pnl
 
 self.total_pnl += pnl
 self.daily_loss += pnl
 
 del self.positions[symbol]
 
 if pnl > 0:
 self.speak(f"Position closed with profit of ${pnl:.2f}! Total PnL: ${self.total_pnl:.2f}", 'excited')
 self.ai_brain.update_performance(position.get('strategy', 'momentum'), pnl)
 else:
 self.speak(f"Position closed with loss of ${pnl:.2f}. Will learn from this. Total PnL: ${self.total_pnl:.2f}", 'concerned')
 self.ai_brain.update_performance(position.get('strategy', 'momentum'), pnl)
 
 async def run_trading_loop(self, symbols: List[str] = None, interval: int = 60):
 """
 Run continuous trading loop.
 
 Args:
 symbols: List of symbols to trade
 interval: Seconds between analysis cycles
 """
 if symbols is None:
 symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
 
 self.running = True
 self.speak(f"Starting trading loop! Monitoring {len(symbols)} pairs. Trading mode: {self.mode}", 'excited')
 
 cycle = 0
 while self.running:
 cycle += 1
 self.speak(f"--- Analysis Cycle {cycle} ---")
 
 for symbol in symbols:
 try:
 result = await self.analyze_and_trade(symbol)
 if result:
 logger.info(f"Trade executed: {result}")
 
 await asyncio.sleep(5) # Wait between symbols
 
 except Exception as e:
 logger.error(f"Error analyzing {symbol}: {e}")
 
 # Check existing positions
 await self.check_positions()
 
 # Report status
 self.speak(f"Cycle {cycle} complete. Positions: {len(self.positions)}, Daily PnL: ${self.total_pnl:.2f}")
 
 # Wait for next cycle
 await asyncio.sleep(interval)
 
 def stop(self):
 """Stop the trading loop"""
 self.running = False
 self.speak("Trading loop stopped. Closing all positions recommended.", 'alert')
 
 async def chat(self, user_input: str) -> str:
 """
 Natural language chat with OMNICUS.
 
 Args:
 user_input: User's message
 
 Returns:
 OMNICUS's response
 """
 user_lower = user_input.lower()
 
 # Status request
 if 'status' in user_lower or 'how are you' in user_lower:
 response = f"I'm doing great! Current capital: ${self.capital:.2f}, Total PnL: ${self.total_pnl:.2f}, Positions: {len(self.positions)}, Mode: {self.mode}"
 
 # Position info
 elif 'position' in user_lower or 'holding' in user_lower:
 if self.positions:
 pos_str = '\n'.join([f"{s}: {p['amount']:.4f} @ ${p['avg_price']:.2f}" for s, p in self.positions.items()])
 response = f"Current positions:\n{pos_str}"
 else:
 response = "No open positions right now."
 
 # Trade request
 elif 'buy' in user_lower or 'sell' in user_lower:
 words = user_lower.split()
 action = 'BUY' if 'buy' in user_lower else 'SELL'
 symbol = words[-1].upper() if words else 'BTCUSDT'
 if not symbol.endswith('USDT'):
 symbol += 'USDT'
 
 market_data = await self._get_market_data(symbol)
 if market_data:
 signal = await self.ai_brain.analyze(market_data)
 result = await self._execute_trade(symbol, signal, market_data)
 response = f"Executed {action} on {symbol} at ${market_data['current_price']:.2f}"
 else:
 response = f"Couldn't get data for {symbol}"
 
 # PnL request
 elif 'pnl' in user_lower or 'profit' in user_lower or 'loss' in user_lower:
 response = f"Total PnL: ${self.total_pnl:.2f} ({self.total_pnl/self.capital*100:.1f}%). Today's trades: {self.trades_today}. Daily loss: ${self.daily_loss:.2f}"
 
 # Stop request
 elif 'stop' in user_lower:
 self.stop()
 response = "Trading stopped. All positions should be reviewed."
 
 # Help request
 elif 'help' in user_lower:
 response = """I can help you with:
- 'status' - Check my current state
- 'positions' - View open positions
- 'buy SYMBOL' - Buy a symbol
- 'sell SYMBOL' - Sell a symbol
- 'pnl' - Check profit/loss
- 'stop' - Stop trading
- Analyze markets and trade automatically"""
 
 # Analysis request
 elif 'analyze' in user_lower:
 result = await self.analyze_and_trade('BTCUSDT')
 response = f"Analysis complete. Result: {result.action if result else 'No action taken'}"
 
 # Default conversational response
 else:
 response = self.personality.respond_to_message(user_input)
 
 # Speak the response
 self.speak(response)
 
 return response


async def main():
 """Main entry point"""
 print("""
╔═══════════════════════════════════════════════════════════════════╗
║ ║
║ ██████╗ ███╗ ███╗██╗ ██╗██╗ ██╗ ║
║ ██╔═══██╗████╗ ████║██║ ██║╚██╗██╔╝ ║
║ ██║ ██║██╔████╔██║██║ ██║ ╚███╔╝ ║
║ ██║ ██║██║╚██╔╝██║██║ ██║ ██╔██╗ ║
║ ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗ ║
║ ╚═════╝ ╚═╝ ╚═╝ ╚═════╝ ╚═╝ ╚═╝ ║
║ ║
║ 💰 LIVE TRADING ASSISTANT 💰 ║
║ ║
║ 🗣️ Ask me anything, I'll talk back! ║
║ 📊 I can analyze markets and place trades! ║
║ 🧠 AI-powered decisions! ║
║ ║
╚═══════════════════════════════════════════════════════════════════╝
""")
 
 # Create assistant
 assistant = OMNICUSTradingAssistant(mode='paper')
 
 # Initialize
 await assistant.initialize()
 
 # Demo: Chat with the assistant
 assistant.speak("""Hello! I'm OMNICUS, your AI trading assistant!
 
I can:
- Analyze markets and find trades
- Execute buy and sell orders
- Tell you about my positions and PnL
- Chat with you about anything!
 
Try asking me: 'status', 'analyze', 'buy BTC', or 'help'
 """)
 
 # Run a few analysis cycles
 for _ in range(3):
 await assistant.analyze_and_trade('BTCUSDT')
 await asyncio.sleep(2)
 await assistant.analyze_and_trade('ETHUSDT')
 await asyncio.sleep(2)
 
 # Final status
 await assistant.chat("status")


if __name__ == '__main__':
 asyncio.run(main())
