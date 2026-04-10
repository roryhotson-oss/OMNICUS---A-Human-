#!/usr/bin/env python3
"""
OMNICUS - The Profit Hunter
===========================
Main entry point for running the complete OMNICUS system.

MISSION: Double the capital in 24 hours.

Usage:
    python main.py                        # Run everything
    python main.py --mode trader          # Just the trader
    python main.py --mode dashboard       # Just the dashboard
    python main.py --mode telegram        # Just the Telegram bot

Security:
    - All API keys loaded from environment
    - No hardcoded secrets
    - Dashboard binds to localhost by default
"""

import asyncio
import argparse
import logging
import os
import sys
import multiprocessing
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/omnicus.log')
    ]
)
logger = logging.getLogger('OMNICUS')


def print_banner():
    """Print OMNICUS banner"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗ ███╗   ███╗██╗   ██╗██╗  ██╗                           ║
║  ██╔═══██╗████╗ ████║██║   ██║╚██╗██╔╝                           ║
║  ██║   ██║██╔████╔██║██║   ██║ ╚███╔╝                            ║
║  ██║   ██║██║╚██╔╝██║██║   ██║ ██╔██╗                            ║
║  ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗                           ║
║   ╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝                           ║
║                                                                   ║
║                    💰 THE PROFIT HUNTER 💰                       ║
║                                                                   ║
║   ════════════════════════════════════════════════════════════   ║
║                                                                   ║
║   🎯 MISSION: Double the capital in 24 hours                     ║
║   📊 Minimum: 10% daily profit                                   ║
║   🚀 Target: 50% daily profit                                    ║
║   💎 Goal: 100% (Double!)                                        ║
║                                                                   ║
║   ════════════════════════════════════════════════════════════   ║
║                                                                   ║
║   🤖 Multi-Exchange: Binance, MEXC, Kraken                       ║
║   🎲 Prediction Markets: Polymarket                              ║
║   🔍 Token Scanner: Axiom, Pump.fun                              ║
║   📈 Stocks: Alpaca                                              ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)


async def run_trader():
    """Run the unified trader"""
    from core.hybrid_system import HybridTradingSystem, TradingMode
    
    # Get settings
    trading_mode = os.getenv("TRADING_MODE", "simulation")
    mode_map = {
        'simulation': TradingMode.SIMULATION,
        'testnet': TradingMode.TESTNET,
        'mainnet': TradingMode.MAINNET
    }
    
    trader = HybridTradingSystem(
        trading_mode=mode_map.get(trading_mode, TradingMode.SIMULATION),
        initial_balance=float(os.getenv("STARTING_CAPITAL", 10000)),
        enable_voice=os.getenv("VOICE_ENABLED", "true").lower() == "true"
    )
    
    try:
        await trader.start()
        
        # Keep running
        while trader.is_running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Stopping trader...")
        await trader.stop()


def run_dashboard(port: int = 5000):
    """Run the web dashboard"""
    from api.server import run_server
    logger.info(f"🌐 Starting Dashboard on port {port}")
    run_server(port=port)


async def run_telegram_bot():
    """Run Telegram bot"""
    from telegram_bot import OmnicusTelegramBot
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    
    bot = OmnicusTelegramBot(token=token)
    await bot.start()
    
    # Keep running
    while True:
        await asyncio.sleep(1)


async def run_full_system(port: int = 5000):
    """Run everything: Trader + Dashboard + Telegram"""
    from core.hybrid_system import HybridTradingSystem, TradingMode
    from soul import OMNICUSPersonality, VoiceEngine
    
    # Show personality intro
    personality = OMNICUSPersonality()
    print(personality.introduce_self())
    
    # Initialize voice
    voice = VoiceEngine()
    voice.say_greeting()
    
    # Create trader
    trading_mode = os.getenv("TRADING_MODE", "simulation")
    mode_map = {
        'simulation': TradingMode.SIMULATION,
        'testnet': TradingMode.TESTNET,
        'mainnet': TradingMode.MAINNET
    }
    
    trader = HybridTradingSystem(
        trading_mode=mode_map.get(trading_mode, TradingMode.SIMULATION),
        initial_balance=float(os.getenv("STARTING_CAPITAL", 10000)),
        enable_voice=True
    )
    
    # Start trader in background
    trader_task = asyncio.create_task(trader.start())
    
    # Start dashboard in separate process
    dashboard_process = multiprocessing.Process(target=run_dashboard, args=(port,))
    dashboard_process.start()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                     🚀 OMNICUS IS LIVE! 🚀                       ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║   💹 Trading: ACTIVE                                              ║
║   🌐 Dashboard: http://localhost:{port}                           ║
║   🎯 Mission: Double the capital                                  ║
║                                                                   ║
║   ════════════════════════════════════════════════════════════   ║
║                                                                   ║
║   Watch OMNICUS hunt for profits!                                ║
║   Chat with him on Telegram!                                     ║
║   Give him gifts to motivate him! 🎁                             ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Wait for trader to complete (runs forever until stopped)
        await trader_task
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await trader.stop()
        dashboard_process.terminate()


def check_security():
    """Check for security issues"""
    issues = []
    
    # Check for .env file
    if not Path(".env").exists():
        issues.append("⚠️  .env file not found - copy .env.example and configure")
    
    # Check SECRET_KEY
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key:
        issues.append("⚠️  SECRET_KEY not set - generate a secure random key")
    elif len(secret_key) < 32:
        issues.append("⚠️  SECRET_KEY too short - use at least 32 characters")
    
    # Check for hardcoded keys in code (basic check)
    dangerous_patterns = ["api_key =", "api_secret =", "password ="]
    for py_file in Path(".").rglob("*.py"):
        if "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text()
            for pattern in dangerous_patterns:
                if pattern in content and "os.getenv" not in content and "env(" not in content:
                    issues.append(f"⚠️  Potential hardcoded secret in {py_file}")
        except:
            pass
    
    if issues:
        print("\n🔒 Security Check:")
        for issue in issues:
            print(f"  {issue}")
        print()
    else:
        print("✅ Security check passed\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="OMNICUS - The Profit Hunter",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--mode",
        choices=["full", "trader", "dashboard", "telegram"],
        default="full",
        help="Operating mode"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("DASHBOARD_PORT", 5000)),
        help="Dashboard port"
    )
    
    parser.add_argument(
        "--capital",
        type=float,
        default=float(os.getenv("STARTING_CAPITAL", 10000)),
        help="Starting capital"
    )
    
    parser.add_argument(
        "--paper",
        action="store_true",
        default=os.getenv("PAPER_TRADING", "true").lower() == "true",
        help="Paper trading mode"
    )
    
    parser.add_argument(
        "--voice",
        action="store_true",
        default=os.getenv("VOICE_ENABLED", "true").lower() == "true",
        help="Enable voice"
    )
    
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip security check"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Security check
    if not args.skip_security:
        check_security()
    
    # Log configuration
    logger.info(f"Starting Capital: ${args.capital:,.2f}")
    logger.info(f"Paper Trading: {args.paper}")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Voice: {'Enabled' if args.voice else 'Disabled'}")
    
    # Get Telegram config
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    logger.info(f"Telegram: {'Configured' if telegram_token else 'Not configured'}")
    
    # Run based on mode
    if args.mode == "full":
        asyncio.run(run_full_system(args.port))
    
    elif args.mode == "trader":
        asyncio.run(run_trader())
    
    elif args.mode == "dashboard":
        run_dashboard(args.port)
    
    elif args.mode == "telegram":
        if not telegram_token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            sys.exit(1)
        asyncio.run(run_telegram_bot())


if __name__ == "__main__":
    main()
