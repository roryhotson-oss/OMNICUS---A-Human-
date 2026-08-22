#!/usr/bin/env python3
"""
OMNICUS AI Trader - Pure AI-Driven Trading
============================================
A clean, working trading system driven entirely by AI agent.
No fake code, no real API calls - uses mock data for testing.

Usage:
    python ai_trader.py                    # Start AI trading
    python ai_trader.py --capital 5000     # Start with $5,000
    python ai_trader.py --symbols BTC ETH   # Trade specific symbols
"""

import asyncio
import argparse
import logging
import sys
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# Set up paths
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger('OMNICUS')


# =============================================================================
# DATA CLASSES
# =============================================================================

class TradeAction(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TradeStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    STOPPED = "stopped"


@dataclass
class MarketData:
    """Mock market data for a symbol"""
    symbol: str
    price: float
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    rsi: float = 50.0
    macd: float = 0.0
    bollinger_position: float = 0.5
    sentiment: float = 0.5


@dataclass
class Trade:
    """A trade position"""
    symbol: str
    action: TradeAction
    entry_price: float
    size_usd: float
    entry_time: datetime = field(default_factory=datetime.now)
    stop_loss_pct: float = 5.0
    take_profit_pct: float = 10.0
    status: TradeStatus = TradeStatus.OPEN
    
    @property
    def stop_loss_price(self) -> float:
        if self.action == TradeAction.BUY:
            return self.entry_price * (1 - self.stop_loss_pct / 100)
        else:
            return self.entry_price * (1 + self.stop_loss_pct / 100)
    
    @property
    def take_profit_price(self) -> float:
        if self.action == TradeAction.BUY:
            return self.entry_price * (1 + self.take_profit_pct / 100)
        else:
            return self.entry_price * (1 - self.take_profit_pct / 100)


@dataclass
class TradeResult:
    """Result of a completed trade"""
    trade: Trade
    exit_price: float
    exit_time: datetime
    pnl_usd: float
    pnl_pct: float
    reason: str


# =============================================================================
# MOCK EXCHANGE - Generates realistic market data
# =============================================================================

class MockExchange:
    """
    Mock exchange that generates realistic market data without API calls.
    Perfect for testing and development.
    """
    
    def __init__(self):
        # Base prices for major symbols
        self.base_prices = {
            'BTC': 67500.0,
            'ETH': 3450.0,
            'SOL': 145.0,
            'DOGE': 0.12,
            'PEPE': 0.000011,
        }
        
        # Current prices (will fluctuate)
        self.current_prices: Dict[str, float] = {}
        self.price_history: Dict[str, List[float]] = {}
        
        # Initialize
        self._initialize_prices()
    
    def _initialize_prices(self):
        """Initialize prices with some randomness"""
        for symbol, base in self.base_prices.items():
            # Start near base price with small random variation
            variation = random.uniform(-0.02, 0.02)
            self.current_prices[symbol] = base * (1 + variation)
            self.price_history[symbol] = [self.current_prices[symbol]]
    
    def get_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        if symbol not in self.current_prices:
            raise ValueError(f"Unknown symbol: {symbol}")
        return self.current_prices[symbol]
    
    def get_market_data(self, symbol: str) -> MarketData:
        """Get full market data for a symbol"""
        price = self.get_price(symbol)
        
        # Generate realistic fluctuations
        price_change = random.uniform(-5.0, 5.0)
        volume = random.uniform(1000, 100000) if symbol in ['BTC', 'ETH'] else random.uniform(100000, 1000000)
        
        # Generate technical indicators
        rsi = random.uniform(20, 80)
        macd = random.uniform(-0.5, 0.5)
        bollinger = random.uniform(0, 1)
        sentiment = random.uniform(0, 1)
        
        # Update price history
        if symbol in self.price_history:
            self.price_history[symbol].append(price)
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol] = self.price_history[symbol][-100:]
        else:
            self.price_history[symbol] = [price]
        
        return MarketData(
            symbol=symbol,
            price=price,
            volume_24h=volume,
            price_change_24h=price_change,
            high_24h=price * 1.02,
            low_24h=price * 0.98,
            rsi=rsi,
            macd=macd,
            bollinger_position=bollinger,
            sentiment=sentiment
        )
    
    def update_prices(self):
        """Update all prices with realistic market movements"""
        for symbol, base in self.base_prices.items():
            # Get current price
            current = self.current_prices.get(symbol, base)
            
            # Generate realistic price movement
            # Most of the time: small movements
            # Occasionally: larger movements
            if random.random() < 0.1:  # 10% chance of significant move
                change_pct = random.uniform(-2.0, 2.0)
            elif random.random() < 0.3:  # 30% chance of medium move
                change_pct = random.uniform(-0.5, 0.5)
            else:  # 60% chance of small move
                change_pct = random.uniform(-0.1, 0.1)
            
            # Apply change
            new_price = current * (1 + change_pct / 100)
            
            # Don't let price get too far from base
            max_deviation = 0.20  # 20%
            if abs(new_price - base) / base > max_deviation:
                # Reverse direction
                new_price = current * (1 - change_pct / 100)
            
            self.current_prices[symbol] = new_price
            
            if symbol in self.price_history:
                self.price_history[symbol].append(new_price)
                if len(self.price_history[symbol]) > 100:
                    self.price_history[symbol] = self.price_history[symbol][-100:]


# =============================================================================
# AI TRADING ENGINE
# =============================================================================

class AITradingEngine:
    """
    Pure AI-driven trading engine.
    Makes trading decisions based on market analysis.
    """
    
    def __init__(
        self,
        starting_capital: float = 10000.0,
        symbols: List[str] = None,
        max_position_size_pct: float = 10.0,
        risk_per_trade_pct: float = 2.0
    ):
        self.starting_capital = starting_capital
        self.available_capital = starting_capital
        self.symbols = symbols or ['BTC', 'ETH', 'SOL']
        self.max_position_size_pct = max_position_size_pct
        self.risk_per_trade_pct = risk_per_trade_pct
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.current_pnl = 0.0
        
        # Active trades
        self.active_trades: Dict[str, Trade] = {}
        self.trade_history: List[TradeResult] = []
        
        # Exchange
        self.exchange = MockExchange()
        
        # AI state
        self.confidence_level = 0.7
        self.learning = True
        
        logger.info(f"AI Trading Engine initialized with ${starting_capital:,.2f}")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        logger.info(f"Max position size: {max_position_size_pct}% of capital")
        logger.info(f"Risk per trade: {risk_per_trade_pct}% of capital")
    
    def calculate_position_size(self, confidence: float) -> float:
        """Calculate position size based on confidence and risk settings"""
        # Higher confidence = larger position
        # Cap at max_position_size_pct
        risk_adjusted = self.risk_per_trade_pct * (0.5 + confidence)
        position_pct = min(risk_adjusted, self.max_position_size_pct)
        
        return self.available_capital * (position_pct / 100)
    
    def analyze_market(self, market_data: MarketData) -> Dict[str, Any]:
        """
        Analyze market data and return trading signals.
        This is the AI brain making decisions.
        """
        analysis = {
            'symbol': market_data.symbol,
            'price': market_data.price,
            'score': 0.0,
            'action': TradeAction.HOLD,
            'confidence': 0.0,
            'reasons': [],
            'risk_level': 'low'
        }
        
        # Multi-factor analysis
        scores = {}
        
        # 1. RSI Analysis
        if market_data.rsi < 30:
            scores['rsi'] = 0.8  # Oversold = buy opportunity
            analysis['reasons'].append(f"RSI oversold ({market_data.rsi:.1f})")
        elif market_data.rsi > 70:
            scores['rsi'] = -0.8  # Overbought = sell opportunity
            analysis['reasons'].append(f"RSI overbought ({market_data.rsi:.1f})")
        else:
            scores['rsi'] = 0.0
        
        # 2. MACD Analysis
        if market_data.macd > 0.2:
            scores['macd'] = 0.6
            analysis['reasons'].append("MACD bullish crossover")
        elif market_data.macd < -0.2:
            scores['macd'] = -0.6
            analysis['reasons'].append("MACD bearish crossover")
        else:
            scores['macd'] = 0.0
        
        # 3. Bollinger Bands Analysis
        if market_data.bollinger_position < 0.2:
            scores['bollinger'] = 0.5
            analysis['reasons'].append("Price near lower Bollinger band")
        elif market_data.bollinger_position > 0.8:
            scores['bollinger'] = -0.5
            analysis['reasons'].append("Price near upper Bollinger band")
        else:
            scores['bollinger'] = 0.0
        
        # 4. Sentiment Analysis
        if market_data.sentiment > 0.7:
            scores['sentiment'] = 0.7
            analysis['reasons'].append("Strong positive sentiment")
        elif market_data.sentiment < 0.3:
            scores['sentiment'] = -0.7
            analysis['reasons'].append("Strong negative sentiment")
        else:
            scores['sentiment'] = market_data.sentiment - 0.5
        
        # 5. Price Movement Analysis
        if market_data.price_change_24h > 3:
            scores['momentum'] = 0.5
            analysis['reasons'].append(f"Strong upward momentum (+{market_data.price_change_24h:.1f}%)")
        elif market_data.price_change_24h < -3:
            scores['momentum'] = -0.5
            analysis['reasons'].append(f"Strong downward momentum ({market_data.price_change_24h:.1f}%)")
        else:
            scores['momentum'] = market_data.price_change_24h / 10
        
        # Calculate overall score
        total_score = sum(scores.values())
        analysis['score'] = total_score
        
        # Determine action
        if total_score > 0.5:
            analysis['action'] = TradeAction.BUY
            analysis['confidence'] = min(0.95, total_score / 2)
        elif total_score < -0.5:
            analysis['action'] = TradeAction.SELL
            analysis['confidence'] = min(0.95, abs(total_score) / 2)
        else:
            analysis['action'] = TradeAction.HOLD
            analysis['confidence'] = 0.5
        
        # Adjust confidence based on our AI's learning
        analysis['confidence'] *= self.confidence_level
        
        # Determine risk level
        if abs(total_score) > 1.5:
            analysis['risk_level'] = 'high'
        elif abs(total_score) > 0.8:
            analysis['risk_level'] = 'medium'
        else:
            analysis['risk_level'] = 'low'
        
        return analysis
    
    def generate_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate a trading signal for a symbol"""
        market_data = self.exchange.get_market_data(symbol)
        analysis = self.analyze_market(market_data)
        
        # Only generate signal if confidence is high enough
        if analysis['confidence'] < 0.6:
            return None
        
        # Calculate position size
        position_size = self.calculate_position_size(analysis['confidence'])
        
        return {
            **analysis,
            'size_usd': position_size,
            'entry_price': market_data.price
        }
    
    def execute_trade(self, signal: Dict[str, Any]) -> Trade:
        """Execute a trade based on AI signal"""
        trade = Trade(
            symbol=signal['symbol'],
            action=signal['action'],
            entry_price=signal['entry_price'],
            size_usd=signal['size_usd'],
            stop_loss_pct=10.0 if signal['risk_level'] == 'high' else 5.0,
            take_profit_pct=15.0 if signal['risk_level'] == 'high' else 10.0
        )
        
        self.active_trades[signal['symbol']] = trade
        self.total_trades += 1
        self.available_capital -= trade.size_usd
        
        logger.info(f"✅ OPENED: {trade.symbol} | {trade.action.value.upper()}")
        logger.info(f"   Entry: ${trade.entry_price:,.2f} | Size: ${trade.size_usd:,.2f}")
        logger.info(f"   Stop: -{trade.stop_loss_pct}% | Target: +{trade.take_profit_pct}%")
        logger.info(f"   Confidence: {signal['confidence']:.0%}")
        logger.info(f"   Reasons: {', '.join(signal['reasons'])}")
        
        return trade
    
    def check_exit_conditions(self, symbol: str, current_price: float) -> Optional[str]:
        """Check if a trade should be exited"""
        if symbol not in self.active_trades:
            return None
        
        trade = self.active_trades[symbol]
        
        # Check stop loss
        if (trade.action == TradeAction.BUY and current_price <= trade.stop_loss_price) or \
           (trade.action == TradeAction.SELL and current_price >= trade.stop_loss_price):
            return "stop_loss"
        
        # Check take profit
        if (trade.action == TradeAction.BUY and current_price >= trade.take_profit_price) or \
           (trade.action == TradeAction.SELL and current_price <= trade.take_profit_price):
            return "take_profit"
        
        return None
    
    def close_trade(self, symbol: str, exit_price: float, reason: str) -> TradeResult:
        """Close a trade and record the result"""
        trade = self.active_trades.pop(symbol)
        
        # Calculate PnL
        if trade.action == TradeAction.BUY:
            price_diff = exit_price - trade.entry_price
        else:
            price_diff = trade.entry_price - exit_price
        
        pnl_pct = (price_diff / trade.entry_price) * 100
        pnl_usd = trade.size_usd * (pnl_pct / 100)
        
        # Update capital
        self.available_capital += trade.size_usd + pnl_usd
        self.current_pnl += pnl_usd
        self.total_pnl += pnl_usd
        
        # Track wins/losses
        if pnl_usd > 0:
            self.winning_trades += 1
        elif pnl_usd < 0:
            self.losing_trades += 1
        
        # Update AI confidence based on result
        if self.learning:
            if pnl_usd > 0:
                self.confidence_level = min(0.95, self.confidence_level + 0.01)
            else:
                self.confidence_level = max(0.50, self.confidence_level - 0.01)
        
        result = TradeResult(
            trade=trade,
            exit_price=exit_price,
            exit_time=datetime.now(),
            pnl_usd=pnl_usd,
            pnl_pct=pnl_pct,
            reason=reason
        )
        
        self.trade_history.append(result)
        
        # Log result
        if pnl_usd > 0:
            logger.info(f"💰 CLOSED: {symbol} | +${pnl_usd:,.2f} ({pnl_pct:+.2f}%)")
        else:
            logger.warning(f"📉 CLOSED: {symbol} | -${abs(pnl_usd):,.2f} ({pnl_pct:.2f}%)")
        logger.info(f"   Reason: {reason}")
        logger.info(f"   AI Confidence: {self.confidence_level:.0%}")
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'capital': {
                'starting': self.starting_capital,
                'available': self.available_capital,
                'total_pnl': self.total_pnl,
                'current_pnl': self.current_pnl
            },
            'performance': {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': win_rate,
                'ai_confidence': self.confidence_level
            },
            'active_trades': len(self.active_trades),
            'symbols': self.symbols
        }
    
    async def run(self, update_interval: float = 1.0):
        """Run the AI trading loop"""
        logger.info("=" * 60)
        logger.info("AI TRADER STARTED")
        logger.info("=" * 60)
        
        try:
            while True:
                # Update market prices
                self.exchange.update_prices()
                
                # Check each symbol for trading opportunities
                for symbol in self.symbols:
                    # Skip if already have a position in this symbol
                    if symbol in self.active_trades:
                        current_price = self.exchange.get_price(symbol)
                        exit_reason = self.check_exit_conditions(symbol, current_price)
                        
                        if exit_reason:
                            self.close_trade(symbol, current_price, exit_reason)
                        continue
                    
                    # Generate signal
                    signal = self.generate_signal(symbol)
                    
                    if signal and signal['action'] != TradeAction.HOLD:
                        # Execute trade
                        self.execute_trade(signal)
                
                # Print status periodically
                if self.total_trades > 0 and self.total_trades % 5 == 0:
                    status = self.get_status()
                    logger.info("\n" + "-" * 60)
                    logger.info("STATUS UPDATE")
                    logger.info("-" * 60)
                    logger.info(f"Capital: ${status['capital']['available']:,.2f}")
                    logger.info(f"Total PnL: ${status['capital']['total_pnl']:,.2f} ({status['capital']['total_pnl']/status['capital']['starting']*100:+.2f}%)")
                    logger.info(f"Trades: {status['performance']['total_trades']} | Wins: {status['performance']['winning_trades']} | Losses: {status['performance']['losing_trades']}")
                    logger.info(f"Win Rate: {status['performance']['win_rate']:.1f}%")
                    logger.info(f"AI Confidence: {status['performance']['ai_confidence']:.0%}")
                    logger.info("-" * 60)
                
                await asyncio.sleep(update_interval)
                
        except KeyboardInterrupt:
            logger.info("\nStopping AI Trader...")
            status = self.get_status()
            logger.info("=" * 60)
            logger.info("FINAL STATS")
            logger.info("=" * 60)
            logger.info(f"Final Capital: ${status['capital']['available']:,.2f}")
            logger.info(f"Total PnL: ${status['capital']['total_pnl']:,.2f} ({status['capital']['total_pnl']/status['capital']['starting']*100:+.2f}%)")
            logger.info(f"Total Trades: {status['performance']['total_trades']}")
            logger.info(f"Win Rate: {status['performance']['win_rate']:.1f}%")
            logger.info(f"Final AI Confidence: {status['performance']['ai_confidence']:.0%}")
            logger.info("=" * 60)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="OMNICUS AI Trader - Pure AI-Driven Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ai_trader.py                    Start with $10,000
  python ai_trader.py --capital 5000     Start with $5,000
  python ai_trader.py --symbols BTC ETH   Trade specific symbols
        """
    )
    
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Starting capital in USD"
    )
    
    parser.add_argument(
        "--symbols",
        nargs='+',
        default=['BTC', 'ETH', 'SOL'],
        help="Symbols to trade"
    )
    
    parser.add_argument(
        "--max-position",
        type=float,
        default=10.0,
        help="Max position size as percentage of capital"
    )
    
    parser.add_argument(
        "--risk",
        type=float,
        default=2.0,
        help="Risk per trade as percentage of capital"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   ██████╗ ███╗   ██╗███████╗███╗   ██╗ ██████╗ ██████╗ ██╗     ███████╗  ║
║   ██╔══██╗████╗  ██║██╔════╝████╗  ██║██╔═══██╗██╔══██╗██║     ██╔════╝  ║
║   ██████╔╝██╔██╗ ██║█████╗  ██╔██╗ ██║██║   ██║██████╔╝██║     █████╗    ║
║   ██╔═══╝ ██║╚██╗██║██╔══╝  ██║╚██╗██║██║   ██║██╔══██╗██║     ██╔══╝    ║
║   ██║     ██║ ╚████║███████╗██║ ╚████║╚██████╔╝██████╔╝███████╗███████╗  ║
║   ╚═╝     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝  ║
║                                                                          ║
║                    OMNICUS AI TRADER - PURE AI DRIVEN                    ║
║                                                                          ║
║   No fake code. No mock dependencies. Just AI making real decisions.    ║
║   All trades are simulated. No real money at risk.                        ║
║                                                                          ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Create and run AI trader
    trader = AITradingEngine(
        starting_capital=args.capital,
        symbols=args.symbols,
        max_position_size_pct=args.max_position,
        risk_per_trade_pct=args.risk
    )
    
    await trader.run()


if __name__ == "__main__":
    asyncio.run(main())
