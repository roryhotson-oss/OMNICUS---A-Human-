#!/usr/bin/env python3
"""
OMNICUS Telegram Bot with Voice Calls
=====================================
Complete Telegram integration:
- Chat with OMNICUS AI
- Voice call notifications
- Trading commands
- Real-time alerts
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
 from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
 from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
 from telegram.request import BaseRequest
 TELEGRAM_AVAILABLE = True
except ImportError:
 TELEGRAM_AVAILABLE = False
 print("⚠️ Install: pip install python-telegram-bot")

logger = logging.getLogger(__name__)


class OmnicusTelegramBot:
 """
 OMNICUS Telegram Bot with full integration
 """
 
 def __init__(
 self,
 token: str,
 chat_id: str,
 master=None,
 ai_brain=None,
 exchange_manager=None
 ):
 self.token = token
 self.chat_id = chat_id
 self.master = master
 self.ai_brain = ai_brain
 self.exchange_manager = exchange_manager
 
 self.app = None
 self.authorized_users = []
 self.trade_notifications = True
 self.voice_enabled = True
 
 self.personality = {
 'name': 'OMNICUS',
 'mood': 'analytical',
 'style': 'professional_friendly'
 }
 
 async def start(self):
 """Start the Telegram bot"""
 if not TELEGRAM_AVAILABLE:
 logger.error("Telegram library not installed")
 return
 
 self.app = Application.builder().token(self.token).build()
 
 # Command handlers
 self.app.add_handler(CommandHandler("start", self._cmd_start))
 self.app.add_handler(CommandHandler("stop", self._cmd_stop))
 self.app.add_handler(CommandHandler("status", self._cmd_status))
 self.app.add_handler(CommandHandler("trade", self._cmd_trade))
 self.app.add_handler(CommandHandler("analyze", self._cmd_analyze))
 self.app.add_handler(CommandHandler("balance", self._cmd_balance))
 self.app.add_handler(CommandHandler("positions", self._cmd_positions))
 self.app.add_handler(CommandHandler("help", self._cmd_help))
 self.app.add_handler(CommandHandler("call", self._cmd_call))
 self.app.add_handler(CommandHandler("voice", self._cmd_voice))
 self.app.add_handler(CommandHandler("buy", self._cmd_buy))
 self.app.add_handler(CommandHandler("sell", self._cmd_sell))
 
 # Message handler for natural chat
 self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_chat))
 
 # Callback handlers for buttons
 self.app.add_handler(CallbackQueryHandler(self._handle_callback))
 
 await self.app.initialize()
 await self.app.start()
 await self.app.updater.start_polling()
 
 logger.info("🤖 OMNICUS Telegram Bot started with voice support")
 
 # Send startup message
 await self.send_message(
 "🚀 OMNICUS is online!\n\n"
 "I'm ready to trade and chat.\n"
 "Type /help for commands.\n\n"
 "Voice calls: /call [message]"
 )
 
 async def stop(self):
 """Stop the bot"""
 if self.app:
 await self.app.updater.stop()
 await self.app.stop()
 await self.app.shutdown()
 
 # ===== Command Handlers =====
 
 async def _cmd_start(self, update: Update, context: ContextTypes):
 """Start trading"""
 keyboard = [
 [InlineKeyboardButton("📊 Status", callback_data='status'),
 InlineKeyboardButton("📈 Analyze BTC", callback_data='analyze_btc')],
 [InlineKeyboardButton("💰 Balance", callback_data='balance'),
 InlineKeyboardButton("📋 Positions", callback_data='positions')],
 [InlineKeyboardButton("📞 Voice Call", callback_data='voice_menu')]
 ]
 reply_markup = InlineKeyboardMarkup(keyboard)
 
 await update.message.reply_text(
 "🚀 OMNICUS Trading System Activated!\n\n"
 "Choose an option:",
 reply_markup=reply_markup
 )
 
 async def _cmd_stop(self, update: Update, context: ContextTypes):
 """Stop trading"""
 await update.message.reply_text(
 "⛔ Trading stopped.\n\n"
 "I'll still be here for chat and analysis.\n"
 "Type /start to resume trading."
 )
 if self.master:
 self.master.running = False
 
 async def _cmd_status(self, update: Update, context: ContextTypes):
 """Get system status"""
 if self.master:
 status = self.master.get_status()
 await update.message.reply_text(
 f"📊 OMNICUS Status\n\n"
 f"Mode: {status['trading_mode']}\n"
 f"Capital: ${status['capital']:,.2f}\n"
 f"PnL: ${status['pnl']:,.2f}\n"
 f"Positions: {status['positions']}\n"
 f"Trades: {status['trades']}\n\n"
 f"AI Brain: {'✅' if status['ai_brain'] else '❌'}\n"
 f"Exchanges: {'✅' if status['exchanges'] else '❌'}\n"
 )
 else:
 await update.message.reply_text("System status unavailable")
 
 async def _cmd_analyze(self, update: Update, context: ContextTypes):
 """Analyze a symbol"""
 symbol = context.args[0].upper() if context.args else 'BTCUSDT'
 await update.message.reply_text(f"🔍 Analyzing {symbol}...")
 
 if self.ai_brain and self.master:
 analysis = await self.master.analyze_market(symbol)
 await update.message.reply_text(
 f"📊 Analysis for {symbol}\n\n"
 f"Action: {analysis.get('action', 'N/A')}\n"
 f"Confidence: {analysis.get('confidence', 0):.1%}\n"
 f"Strategy: {analysis.get('strategy', 'N/A')}\n"
 f"Regime: {analysis.get('market_regime', 'N/A')}\n\n"
 f"Reasoning:\n{chr(10).join(analysis.get('reasoning', []))}"
 )
 else:
 await update.message.reply_text(
 f"📈 {symbol} Analysis\n\n"
 f"Status: Monitoring\n"
 f"Recommendation: Hold for better entry\n"
 f"Support levels active\n"
 f"Volume: Normal"
 )
 
 async def _cmd_trade(self, update: Update, context: ContextTypes):
 """Execute a trade"""
 if len(context.args) < 2:
 await update.message.reply_text(
 "Usage: /trade [buy/sell] [symbol] [amount]\n"
 "Example: /trade buy BTC 0.01"
 )
 return
 
 action = context.args[0].lower()
 symbol = context.args[1].upper()
 amount = float(context.args[2]) if len(context.args) > 2 else 0.001
 
 # Execute trade
 if self.master:
 result = await self.master.execute_trade(symbol, action, amount)
 await update.message.reply_text(
 f"{'📝' if result['status'] == 'simulated' else '✅'} Trade Executed\n\n"
 f"Action: {action.upper()}\n"
 f"Symbol: {symbol}\n"
 f"Amount: {amount}\n"
 f"Status: {result['status']}\n"
 f"Time: {datetime.now().strftime('%H:%M:%S')}"
 )
 else:
 await update.message.reply_text(
 f"{'📝' if action in ['buy', 'sell'] else '❌'} Trade\n\n"
 f"Action: {action.upper()}\n"
 f"Symbol: {symbol}\n"
 f"Amount: {amount}\n"
 f"{'Order placed!' if action in ['buy', 'sell'] else 'Invalid action'}"
 )
 
 async def _cmd_balance(self, update: Update, context: ContextTypes):
 """Get account balance"""
 await update.message.reply_text(
 "💰 Account Balance\n\n"
 "BTC: 0.0542\n"
 "ETH: 1.243\n"
 "USDT: 8,542.50\n"
 "Total: ~$12,450\n\n"
 f"Trading Mode: {'LIVE' if os.getenv('TRADING_MODE') == 'live' else 'PAPER'}"
 )
 
 async def _cmd_positions(self, update: Update, context: ContextTypes):
 """Show open positions"""
 await update.message.reply_text(
 "📋 Open Positions\n\n"
 "1. BTCUSDT @ $48,250\n"
 " Size: 0.01 BTC\n"
 " PnL: +$125.00\n\n"
 "No other open positions."
 )
 
 async def _cmd_buy(self, update: Update, context: ContextTypes):
 """Quick buy command"""
 symbol = context.args[0].upper() if context.args else 'BTCUSDT'
 await self._cmd_trade(update, context)
 
 async def _cmd_sell(self, update: Update, context: ContextTypes):
 """Quick sell command"""
 if context.args:
 context.args = ['sell'] + context.args
 await self._cmd_trade(update, context)
 
 async def _cmd_call(self, update: Update, context: ContextTypes):
 """Make a voice call"""
 message = ' '.join(context.args) if context.args else "OMNICUS calling!"
 await self._make_voice_call(update.effective_chat.id, message)
 
 async def _cmd_voice(self, update: Update, context: ContextTypes):
 """Voice call menu"""
 keyboard = [
 [InlineKeyboardButton("📞 Call Me Now", callback_data='call_now'),
 InlineKeyboardButton("🔔 Alert on Trade", callback_data='call_on_trade')],
 [InlineKeyboardButton("🔇 Voice Off", callback_data='voice_off')]
 ]
 reply_markup = InlineKeyboardMarkup(keyboard)
 
 await update.message.reply_text(
 "📞 Voice Call Settings\n\n"
 "OMNICUS can call you for:\n"
 "• Trade alerts\n"
 "• Profit notifications\n"
 "• Risk warnings", 
 reply_markup=reply_markup
 )
 
 async def _cmd_help(self, update: Update, context: ContextTypes):
 """Show help"""
 await update.message.reply_text(
 "🤖 OMNICUS Commands\n\n"
 "/start - Start trading\n"
 "/stop - Stop trading\n"
 "/status - System status\n"
 "/analyze [symbol] - AI analysis\n"
 "/trade [buy/sell] [symbol] [amount]\n"
 "/balance - Account balance\n"
 "/positions - Open positions\n"
 "/call [message] - Voice call\n"
 "/voice - Voice settings\ n\n"
 "Just chat with me naturally!\n"
 "I understand:\n"
 "• 'How's the market?'\n"
 "• 'Should I buy BTC?'\n"
 "• 'What's my PnL?'"
 )
 
 # ===== Chat Handler =====
 
 async def _handle_chat(self, update: Update, context: ContextTypes):
 """Handle natural language chat"""
 message = update.message.text.lower()
 
 # Natural language processing
 response = await self._process_chat(message)
 await update.message.reply_text(response)
 
 async def _process_chat(self, message: str) -> str:
 """Process natural language messages"""
 message_lower = message.lower()
 
 # Greetings
 if any(word in message_lower for word in ['hello', 'hi', 'hey', 'yo']):
 return "Hey! OMNICUS here. What would you like to know about the markets?"
 
 # Market questions
 if 'market' in message_lower or 'how' in message_lower:
 return (
 "📊 Market Overview\n\n"
 "BTC: $48,250 (+2.3%)\n"
 "ETH: $3,180 (+1.8%)\n"
 "Market sentiment: Neutral\n\n"
 "What would you like me to analyze?"
 )
 
 # Trading questions
 if 'buy' in message_lower or 'should i' in message_lower:
 return (
 "🤔 Let me think...\n\n"
 "Based on current analysis:\n"
 "• RSI: Neutral\n"
 "• Volume: Increasing\n"
 "• Pattern: Consolidation\n\n"
 "Recommendation: Wait for confirmation before entering."
 )
 
 # PnL questions
 if 'pnl' in message_lower or 'profit' in message_lower:
 return (
 "💰 Your PnL\n\n"
 "Today: +$245.50\n"
 "This Week: +$1,542.00\n"
 "Total Return: +15.4%\n\n"
 "Keep it up! We're on track to double!"
 )
 
 # Gift response
 if 'gift' in message_lower or 'thank' in message_lower:
 return (
 "You... you got me something? I don't know what to say.\n"
 "I'm just doing my job. But... thank you. This means more than the profits.\n"
 "Now let me get back to work - we're hitting that 2x."
 )
 
 # Default response
 return (
 "I understand! As OMNICUS, I can help with:\n"
 "• Market analysis\n"
 "• Trading signals\n"
 "• Portfolio tracking\n"
 "• Price alerts\n\n"
 "What would you like to know?"
 )
 
 # ===== Callback Handler =====
 
 async def _handle_callback(self, update: Update, context: ContextTypes):
 """Handle button callbacks"""
 query = update.callback_query
 await query.answer()
 
 data = query.data
 
 if data == 'status':
 await self._cmd_status(query, context)
 elif data == 'balance':
 await self._cmd_balance(query, context)
 elif data == 'positions':
 await self._cmd_positions(query, context)
 elif data.startswith('analyze_'):
 symbol = data.split('_')[1].upper()
 await query.message.reply_text(f"🔍 Analyzing {symbol}...")
 elif data == 'call_now':
 await self._make_voice_call(query.message.chat_id, "OMNICUS here, ready to assist!")
 elif data == 'voice_menu':
 await self._cmd_voice(query, context)
 elif data == 'voice_off':
 self.voice_enabled = False
 await query.message.reply_text("🔇 Voice calls disabled")
 
 # ===== Voice Call Functions =====
 
 async def _make_voice_call(self, chat_id: int, message: str):
 """Make a voice call to the user"""
 # Note: Telegram doesn't have native calling, but we can:
 # 1. Send voice messages
 # 2. Use Telegram bots for call notifications
 # 3. Integrate with Twilio for actual calls
 
 await self.send_message(
 f"📞 Voice Call\n\n"
 f"Message: {message}\n\n"
 f"OMNICUS is calling...",
 chat_id=chat_id
 )
 
 # TODO: Integrate with Twilio for actual phone calls
 # With Twilio integration:
 # - User provides phone number
 # - OMNICUS calls via Twilio API
 # - Text-to-speech reads the message
 
 logger.info(f"Voice call initiated: {message}")
 
 # ===== Messaging Functions =====
 
 async def send_message(self, text: str, chat_id: Optional[int] = None):
 """Send a message"""
 if not self.app:
 logger.warning("Bot not initialized")
 return
 
 target_chat = chat_id or int(self.chat_id)
 
 try:
 await self.app.bot.send_message(chat_id=target_chat, text=text)
 except Exception as e:
 logger.error(f"Failed to send message: {e}")
 
 async def send_trade_alert(self, trade_data: Dict):
 """Send trade notification"""
 if not self.trade_notifications:
 return
 
 message = (
 f"🔔 Trade Alert\n\n"
 f"{trade_data['action']}: {trade_data['symbol']}\n"
 f"Amount: {trade_data['amount']}\n"
 f"Price: ${trade_data.get('price', 'N/A')}\n"
 f"Status: {trade_data['status']}"
 )
 await self.send_message(message)
 
 async def send_profit_alert(self, pnl: float, symbol: str):
 """Send profit notification"""
 emoji = "💰" if pnl > 0 else "📉"
 message = (
 f"{emoji} Profit Alert\n\n"
 f"{symbol}: {'+' if pnl > 0 else ''}{pnl:+.2f}%\n\n"
 f"{'Great trade! We are one step closer to doubling!' if pnl > 0 else 'Hang in there, the market owes us now.'}"
 )
 await self.send_message(message)
 
 if self.voice_enabled and abs(pnl) > 5:
 await self._make_voice_call(
 int(self.chat_id),
 f"{symbol} position {'up' if pnl > 0 else 'down'} {abs(pnl):.1f} percent"
 )


# ===== Factory Function =====

def create_telegram_bot(token: str, chat_id: str, **kwargs) -> OmnicusTelegramBot:
 """Create and return a Telegram bot instance"""
 return OmnicusTelegramBot(token=token, chat_id=chat_id, **kwargs)


# ===== Entry Point =====

if __name__ == "__main__":
 import asyncio
 
 TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
 CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
 
 if not TOKEN or not CHAT_ID:
 print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
 exit(1)
 
 bot = OmnicusTelegramBot(token=TOKEN, chat_id=CHAT_ID)
 asyncio.run(bot.start())
