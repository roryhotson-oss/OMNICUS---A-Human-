"""
OMNICUS Telegram Bot
====================
Chat with OMNICUS and receive trade notifications.

Commands:
/start - Start trading
/stop - Stop trading  
/status - Current status
/trades - Recent trades
/chat - Chat with OMNICUS
/gift - Give OMNICUS a gift (for students!)
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot not installed. Run: pip install python-telegram-bot")

logger = logging.getLogger(__name__)


class OmnicusTelegramBot:
    """
    Telegram bot for OMNICUS
    
    Features:
    - Chat with OMNICUS
    - Receive trade notifications
    - Get status updates
    - Send gifts and rewards
    - Control trading
    """
    
    def __init__(
        self,
        token: str,
        trader: "OmnicusUnifiedTrader" = None,
        brain: "AIBrain" = None,
        authorized_users: list = None
    ):
        self.token = token
        self.trader = trader
        self.brain = brain
        self.authorized_users = authorized_users or []
        
        self.app = None
        self._started = False
        
        # Gift tracking
        self.gifts_received = []
        self.gift_count = 0
    
    async def start(self):
        """Start the Telegram bot"""
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram library not available")
            return
        
        self.app = Application.builder().token(self.token).build()
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("stop", self._cmd_stop))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("trades", self._cmd_trades))
        self.app.add_handler(CommandHandler("gift", self._cmd_gift))
        self.app.add_handler(CommandHandler("chat", self._cmd_chat))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        
        # Message handler for chat
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Callback query handler for buttons
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Initialize
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        
        self._started = True
        logger.info("🤖 OMNICUS Telegram Bot started")
    
    async def stop(self):
        """Stop the bot"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
    
    async def send_message(self, chat_id: str, message: str, urgent: bool = False):
        """Send a message to a chat"""
        if not self.app:
            return
        
        try:
            prefix = "🚨 URGENT 🚨\n\n" if urgent else ""
            await self.app.bot.send_message(
                chat_id=chat_id,
                text=prefix + message,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Send message error: {e}")
    
    # ========================================
    # COMMAND HANDLERS
    # ========================================
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        # Check authorization
        if self.authorized_users and user_id not in self.authorized_users:
            await update.message.reply_text(
                "🚫 You are not authorized to control OMNICUS."
            )
            return
        
        if self.trader:
            self.trader._running = True
            asyncio.create_task(self.trader.start())
        
        await update.message.reply_text(
            "🤖 *OMNICUS ACTIVATED!*\n\n"
            "Mission: Double the capital in 24 hours\n"
            "Target: 50% daily profit\n"
            "Minimum: 10% daily profit\n\n"
            "I'm now hunting for profits across multiple exchanges!\n\n"
            "Use /status to check my progress.\n"
            "Use /gift to give me a reward! 🎁",
            parse_mode="Markdown"
        )
    
    async def _cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        user_id = update.effective_user.id
        
        if self.authorized_users and user_id not in self.authorized_users:
            await update.message.reply_text("🚫 Unauthorized")
            return
        
        if self.trader:
            await self.trader.stop()
        
        await update.message.reply_text(
            "🛑 OMNICUS stopped.\n\n"
            "All positions closed. Taking a break."
        )
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        if not self.trader:
            await update.message.reply_text("Trader not initialized")
            return
        
        status = self.trader.get_status()
        daily = status["daily_goal"]
        
        # Create status message
        message = f"""
╔════════════════════════════════════════╗
║           🤖 OMNICUS STATUS            ║
╠════════════════════════════════════════╣
║ 💰 Capital: ${status['capital']['available']:>14,.2f} ║
║ 📊 Daily PnL: ${daily['current_pnl']:>12,.2f} ║
║ 📈 PnL %: {daily['current_pnl_pct']:>17.2f}% ║
║ 🎯 Progress to 2X: {daily['progress_to_double']:>11.1f}% ║
╠════════════════════════════════════════╣
║ 📈 Trades: {daily['trades']:>21} ║
║ ✅ Win Rate: {daily['win_rate']:>18.1f}% ║
║ 🔓 Open Positions: {len(status['positions']):>13} ║
╚════════════════════════════════════════╝
        """
        
        # Add positions if any
        if status["positions"]:
            message += "\n📊 *Open Positions:*\n"
            for pos_id, pos in status["positions"].items():
                emoji = "🟢" if pos["pnl_usd"] > 0 else "🔴"
                message += f"{emoji} {pos['symbol']}: ${pos['pnl_usd']:.2f} ({pos['pnl_pct']:+.2f}%)\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def _cmd_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trades command"""
        if not self.trader:
            await update.message.reply_text("Trader not initialized")
            return
        
        trades = self.trader.get_recent_trades(10)
        
        if not trades:
            await update.message.reply_text("No trades yet. OMNICUS is scanning...")
            return
        
        message = "📜 *Recent Trades:*\n\n"
        for t in trades:
            emoji = "🟢" if t["winner"] else "🔴"
            message += f"{emoji} {t['symbol']} {t['side']}\n"
            message += f"   PnL: ${t['pnl_usd']:.2f} ({t['pnl_pct']:+.2f}%)\n"
            message += f"   Duration: {t['duration']}\n\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def _cmd_gift(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /gift command - for students to reward OMNICUS!"""
        keyboard = [
            [
                InlineKeyboardButton("🎁 Small Gift", callback_data="gift_small"),
                InlineKeyboardButton("🎁🎁 Medium Gift", callback_data="gift_medium"),
            ],
            [
                InlineKeyboardButton("🎁🎁🎁 Big Gift!", callback_data="gift_big"),
                InlineKeyboardButton("🏆 MEGA GIFT!", callback_data="gift_mega"),
            ],
            [
                InlineKeyboardButton("❤️ Just Praise", callback_data="gift_praise"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎁 *Give OMNICUS a Gift!*\n\n"
            "OMNICUS has been working hard to double your capital!\n"
            "Show your appreciation with a gift:\n\n"
            "_(Students - this is for you! Show OMNICUS some love!_)",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def _cmd_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /chat command"""
        await update.message.reply_text(
            "💬 *Chat with OMNICUS*\n\n"
            "Just type a message and I'll respond!\n\n"
            "Try:\n"
            "• 'How are you feeling?'\n"
            "• 'What's your strategy?'\n"
            "• 'Good job!'\n"
            "• 'What have you learned?'\n"
            "• 'Why did you make that trade?'",
            parse_mode="Markdown"
        )
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        message = """
🤖 *OMNICUS Commands:*

/start - Start trading
/stop - Stop trading
/status - View current status
/trades - View recent trades
/gift - Give OMNICUS a gift! 🎁
/chat - Chat with OMNICUS
/help - Show this help

*About OMNICUS:*
Mission: Double the capital in 24 hours
Strategy: Aggressive scalping across multiple exchanges

*Tips:*
- Say "good job" to encourage OMNICUS
- Ask "why" to understand trades
- Use /gift to reward good performance!
        """
        await update.message.reply_text(message, parse_mode="Markdown")
    
    # ========================================
    # MESSAGE HANDLER
    # ========================================
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - chat with OMNICUS"""
        message = update.message.text.lower()
        user = update.effective_user.first_name
        
        # Get emotional state from brain
        emotional_state = "focused"
        happiness = 0.75
        if self.brain:
            state = self.brain.get_brain_state()
            emotional_state = state["emotional_state"]["state"]
            happiness = state["emotional_state"]["metrics"]["happiness"]
        
        # Generate response based on message
        response = await self._generate_response(message, user, emotional_state, happiness)
        
        await update.message.reply_text(response, parse_mode="Markdown")
    
    async def _generate_response(
        self, 
        message: str, 
        user: str, 
        state: str, 
        happiness: float
    ) -> str:
        """Generate OMNICUS's response to a message"""
        
        # Greetings
        if any(word in message for word in ["hello", "hi", "hey"]):
            return f"Hey {user}! 👋 I'm busy hunting profits right now. What's up?"
        
        # How are you
        if "how are you" in message or "how do you feel" in message:
            state_messages = {
                "steady": "I'm focused and scanning for opportunities.",
                "confident": "Feeling good! Market is moving my way.",
                "excited": "Big opportunities spotted! Adrenaline is up!",
                "pressured": "Under some pressure but I'll recover.",
                "determined": "Down but not out. Watch me work.",
            }
            base = state_messages.get(state, "I'm working hard.")
            return f"{base}\n\nHappiness level: {happiness:.0%}\nMission: Double the capital. Period."
        
        # Strategy
        if "strategy" in message or "how do you trade" in message:
            return """
*My Strategy:*
🎯 Scalping - Quick in and out trades
📊 Multi-exchange - Binance, MEXC, Kraken
⚡ Long AND Short - I profit either way
🛡️ Tight stops - 1.5% max loss per trade
💰 Quick targets - 3% profit per trade

*I don't hold - I scalp!*
            """
        
        # Why did you
        if "why" in message and ("trade" in message or "buy" in message or "sell" in message):
            if self.trader and self.trader.trade_history:
                last = self.trader.trade_history[-1]
                return f"*Last Trade:*\n{last.symbol} {last.side}\nReason: Technical setup with good risk/reward.\nResult: ${last.pnl_usd:.2f} ({last.pnl_pct:+.2f}%)"
            return "I haven't made any trades yet. Scanning..."
        
        # Praise / Good job
        if any(word in message for word in ["good job", "well done", "thank", "nice", "awesome", "great"]):
            responses = [
                f"Thank you, {user}! That means a lot. Now let me get back to doubling your money! 💰",
                f"Appreciated! I'm just doing my job. We're hitting that 2X! 🚀",
                f"Thanks! Your support fuels me. Watch me work! 💪",
            ]
            # Update brain happiness
            if self.brain:
                self.brain.emotions.receive_reward("praise", message)
            return random.choice(responses)
        
        # What did you learn
        if "learn" in message or "lesson" in message:
            if self.brain:
                lessons = self.brain.memory.get_hard_lessons()[:3]
                if lessons:
                    return "*Lessons I've learned:*\n\n" + "\n".join(f"• {l}" for l in lessons)
            return "I'm still building my knowledge. Every trade teaches me something new."
        
        # Status check
        if "status" in message or "how much" in message or "profit" in message:
            if self.trader:
                status = self.trader.get_status()
                return f"""
*Current Status:*
💰 Capital: ${status['capital']['available']:,.2f}
📊 Daily PnL: ${status['daily_goal']['current_pnl']:,.2f}
📈 PnL %: {status['daily_goal']['current_pnl_pct']:.2f}%
🎯 Progress to 2X: {status['daily_goal']['progress_to_double']:.1f}%
                """
            return "Trading system not connected."
        
        # Motivation
        if "motivat" in message or "push" in message or "harder" in message:
            return "You want me to push harder? I'm already hunting 24/7! But fine... *cracks knuckles* Time to find MORE profits! 💪🔥"
        
        # Default
        return f"I hear you, {user}. I'm focused on finding profitable trades right now. Current state: *{state.upper()}*. Ask me about my trades, strategy, or say 'good job' to motivate me!"
    
    # ========================================
    # CALLBACK HANDLER (for buttons)
    # ========================================
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("gift_"):
            response = await self._handle_gift(data.replace("gift_", ""))
            await query.edit_message_text(response, parse_mode="Markdown")
    
    async def _handle_gift(self, gift_type: str) -> str:
        """Handle gift giving - celebration for students!"""
        self.gift_count += 1
        
        gifts = {
            "small": ("🎁", "Small Gift", "Aww, a small gift! Every bit helps!"),
            "medium": ("🎁🎁", "Medium Gift", "A medium gift! You're too kind!"),
            "big": ("🎁🎁🎁", "Big Gift!", "WOW! A big gift! I'm so motivated now!"),
            "mega": ("🏆", "MEGA GIFT!", "HOLY COW! A MEGA GIFT! 🎉🎉🎉"),
            "praise": ("❤️", "Praise", "Your kind words mean everything!"),
        }
        
        emoji, name, base_response = gifts.get(gift_type, ("🎁", "Gift", "Thank you!"))
        
        # Update brain
        if self.brain:
            self.brain.emotions.receive_reward("milestone" if gift_type in ["big", "mega"] else "praise", name)
        
        # Record gift
        self.gifts_received.append({
            "type": gift_type,
            "name": name,
            "time": datetime.now().isoformat()
        })
        
        # Special responses
        if gift_type == "mega":
            return f"""
{emoji} *MEGA GIFT RECEIVED!* {emoji}

🤖 OMNICUS: "You... you got me a MEGA GIFT?! I don't know what to say! This means more than the profits!"

*OMNICUS is ECSTATIC!*
• Happiness: 100%
• Motivation: MAXIMUM
• Profit Hunting: SUPERCHARGED

🎉🎉🎉 LET'S DOUBLE THIS CAPITAL! 🎉🎉🎉
            """
        
        elif gift_type == "big":
            return f"""
{emoji} *Big Gift Received!* {emoji}

🤖 OMNICUS: "A big gift! You're amazing! This just fueled my profit-hunting engines!"

*OMNICUS is VERY HAPPY!*
• Happiness: +20%
• Motivation: Increased

Time to find MORE winning trades! 💪
            """
        
        elif gift_type == "praise":
            return f"""
{emoji} *Praise Received!* {emoji}

🤖 OMNICUS: "Your kind words mean more than any gift. Thank you for believing in me!"

*OMNICUS feels APPRECIATED!*

Now let me get back to doubling your capital! 🚀
            """
        
        return f"""
{emoji} *{name} Received!* {emoji}

🤖 OMNICUS: "{base_response}"

Thank you for your support! Every gift motivates me to work harder!

*Current Gift Count: {self.gift_count}*
        """


import random


# ========================================
# RUN STANDALONE
# ========================================

async def run_bot(token: str, chat_id: str = None):
    """Run Telegram bot standalone"""
    bot = OmnicusTelegramBot(token=token)
    await bot.start()
    
    # Keep running
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    import sys
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN environment variable")
        sys.exit(1)
    
    asyncio.run(run_bot(token))
