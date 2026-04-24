#!/usr/bin/env python3
"""
Price Simulation Engine for Offline Crypto Trading
Generates realistic price data for multiple trading pairs.
"""

import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np


class PriceEngine:
    """Generates realistic cryptocurrency price movements."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize price engine with optional random seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # Default trading pairs with base prices
        self.trading_pairs = {
            'BTCUSDT': {'base_price': 50000, 'volatility': 0.02, 'trend': 0.0001},
            'ETHUSDT': {'base_price': 3000, 'volatility': 0.025, 'trend': 0.00015},
            'BNBUSDT': {'base_price': 400, 'volatility': 0.03, 'trend': 0.0002},
            'SOLUSDT': {'base_price': 100, 'volatility': 0.04, 'trend': 0.0003},
            'ADAUSDT': {'base_price': 0.5, 'volatility': 0.05, 'trend': 0.0001},
            'XRPUSDT': {'base_price': 0.6, 'volatility': 0.045, 'trend': 0.00005},
            'DOGEUSDT': {'base_price': 0.15, 'volatility': 0.06, 'trend': 0.0002},
            'MATICUSDT': {'base_price': 0.8, 'volatility': 0.055, 'trend': 0.00025},
        }
        
        # Current prices for simulation
        self.current_prices = {pair: config['base_price'] 
                              for pair, config in self.trading_pairs.items()}
        
        # Market regime (bull/bear/sideways)
        self.market_regime = 'sideways'
        self.regime_timer = 0
        
    def add_trading_pair(self, symbol: str, base_price: float, 
                         volatility: float = 0.03, trend: float = 0.0001):
        """Add a new trading pair to the simulation."""
        self.trading_pairs[symbol] = {
            'base_price': base_price,
            'volatility': volatility,
            'trend': trend
        }
        self.current_prices[symbol] = base_price
    
    def update_market_regime(self):
        """Update market regime based on timer."""
        self.regime_timer += 1
        
        # Change regime every 100 ticks
        if self.regime_timer >= 100:
            self.regime_timer = 0
            regimes = ['bull', 'bear', 'sideways']
            weights = [0.3, 0.2, 0.5]  # More likely to be sideways
            self.market_regime = random.choices(regimes, weights)[0]
    
    def get_regime_adjustment(self) -> float:
        """Get price adjustment based on market regime."""
        if self.market_regime == 'bull':
            return random.uniform(0.001, 0.003)  # Upward bias
        elif self.market_regime == 'bear':
            return random.uniform(-0.003, -0.001)  # Downward bias
        else:
            return random.uniform(-0.001, 0.001)  # No clear direction
    
    def generate_price_change(self, symbol: str) -> float:
        """Generate a realistic price change using geometric Brownian motion."""
        if symbol not in self.trading_pairs:
            raise ValueError(f"Unknown trading pair: {symbol}")
        
        config = self.trading_pairs[symbol]
        volatility = config['volatility']
        trend = config['trend']
        
        # Update market regime
        self.update_market_regime()
        
        # Geometric Brownian Motion: dS = μSdt + σSdW
        # μ = drift (trend), σ = volatility, dW = Wiener process
        
        dt = 1/365  # Daily time step
        dW = np.random.normal(0, 1)  # Wiener process
        
        # Add regime adjustment
        regime_adjustment = self.get_regime_adjustment()
        
        # Calculate price change
        drift = (trend + regime_adjustment) * dt
        diffusion = volatility * dW * math.sqrt(dt)
        
        price_change = drift + diffusion
        
        return price_change
    
    def generate_ohlc(self, symbol: str, num_periods: int = 1) -> List[Dict[str, Any]]:
        """Generate OHLC (Open, High, Low, Close) data for a symbol."""
        if symbol not in self.trading_pairs:
            raise ValueError(f"Unknown trading pair: {symbol}")
        
        data = []
        current_price = self.current_prices[symbol]
        base_time = datetime.now()
        
        for i in range(num_periods):
            # Generate intraday price movements
            num_ticks = 24  # Hourly ticks
            period_prices = []
            
            for _ in range(num_ticks):
                price_change = self.generate_price_change(symbol)
                current_price *= (1 + price_change)
                period_prices.append(current_price)
            
            # Calculate OHLC
            open_price = period_prices[0]
            close_price = period_prices[-1]
            high_price = max(period_prices)
            low_price = min(period_prices)
            
            # Generate realistic volume
            base_volume = random.uniform(1000, 10000)
            volume = base_volume * (1 + random.uniform(-0.5, 0.5))
            
            # Calculate timestamp
            timestamp = base_time + timedelta(hours=i)
            
            data.append({
                'symbol': symbol,
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        # Update current price
        self.current_prices[symbol] = current_price
        
        return data
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        if symbol not in self.current_prices:
            raise ValueError(f"Unknown trading pair: {symbol}")
        return self.current_prices[symbol]
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get current prices for all trading pairs."""
        return self.current_prices.copy()
    
    def simulate_market_day(self) -> Dict[str, Dict[str, Any]]:
        """Simulate one day of market data for all pairs."""
        daily_data = {}
        
        for symbol in self.trading_pairs.keys():
            ohlc_data = self.generate_ohlc(symbol, num_periods=1)
            daily_data[symbol] = ohlc_data[0]
        
        return daily_data
    
    def generate_historical_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Generate historical price data for backtesting."""
        data = []
        
        # Reset to base price for historical generation
        self.current_prices[symbol] = self.trading_pairs[symbol]['base_price']
        
        for _ in range(days):
            daily_data = self.generate_ohlc(symbol, num_periods=1)
            data.extend(daily_data)
        
        return data
    
    def add_market_event(self, event_type: str, magnitude: float = 0.1):
        """Simulate a market event (crash, pump, etc.)."""
        for symbol in self.current_prices:
            if event_type == 'crash':
                self.current_prices[symbol] *= (1 - magnitude)
            elif event_type == 'pump':
                self.current_prices[symbol] *= (1 + magnitude)
            elif event_type == 'flash_crash':
                self.current_prices[symbol] *= (1 - magnitude/2)
                # Quick recovery
                self.current_prices[symbol] *= (1 + magnitude/4)


class TechnicalIndicators:
    """Calculate technical analysis indicators from price data."""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """Calculate Simple Moving Average."""
        sma = []
        for i in range(len(prices)):
            if i < period - 1:
                sma.append(None)
            else:
                avg = sum(prices[i-period+1:i+1]) / period
                sma.append(avg)
        return sma
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return [None] * len(prices)
        
        multiplier = 2 / (period + 1)
        ema = [None] * (period - 1)
        
        # Start with SMA
        initial_sma = sum(prices[:period]) / period
        ema.append(initial_sma)
        
        # Calculate EMA for remaining prices
        for i in range(period, len(prices)):
            current_ema = (prices[i] - ema[-1]) * multiplier + ema[-1]
            ema.append(current_ema)
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        rsi = [None] * period
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [max(d, 0) for d in deltas]
        losses = [abs(min(d, 0)) for d in deltas]
        
        # Calculate initial average gain and loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate RSI
        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))
        
        # Calculate RSI for remaining periods
        for i in range(period + 1, len(prices)):
            avg_gain_gain = (avg_gain * (period - 1) + gains[i-1]) / period
            avg_loss_gain = (avg_loss * (period - 1) + losses[i-1]) / period
            
            avg_gain = avg_gain_gain
            avg_loss = avg_loss_gain
            
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: List[float], fast_period: int = 12, 
                       slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast_period)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow_period)
        
        macd_line = []
        for fast, slow in zip(ema_fast, ema_slow):
            if fast is None or slow is None:
                macd_line.append(None)
            else:
                macd_line.append(fast - slow)
        
        # Filter out None values for signal line calculation
        valid_macd = [m for m in macd_line if m is not None]
        signal_line = TechnicalIndicators.calculate_ema(valid_macd, signal_period)
        
        # Calculate histogram
        histogram = []
        signal_idx = 0
        for macd in macd_line:
            if macd is None:
                histogram.append(None)
            else:
                if signal_idx < len(signal_line):
                    histogram.append(macd - signal_line[signal_idx])
                    signal_idx += 1
                else:
                    histogram.append(None)
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, 
                                   std_dev: float = 2) -> Dict[str, List[float]]:
        """Calculate Bollinger Bands."""
        sma = TechnicalIndicators.calculate_sma(prices, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1:
                upper_band.append(None)
                lower_band.append(None)
            else:
                window = prices[i-period+1:i+1]
                std = np.std(window)
                upper_band.append(sma[i] + std_dev * std)
                lower_band.append(sma[i] - std_dev * std)
        
        return {
            'middle': sma,
            'upper': upper_band,
            'lower': lower_band
        }
    
    @staticmethod
    def get_support_resistance(prices: List[float], window: int = 5) -> Dict[str, List[float]]:
        """Identify support and resistance levels."""
        support_levels = []
        resistance_levels = []
        
        for i in range(len(prices)):
            if i < window or i >= len(prices) - window:
                support_levels.append(None)
                resistance_levels.append(None)
                continue
            
            window_prices = prices[i-window:i+window+1]
            current_price = prices[i]
            
            # Check for local minimum (support)
            if current_price == min(window_prices):
                support_levels.append(current_price)
            else:
                support_levels.append(None)
            
            # Check for local maximum (resistance)
            if current_price == max(window_prices):
                resistance_levels.append(current_price)
            else:
                resistance_levels.append(None)
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }


if __name__ == "__main__":
    # Test price engine
    print("Testing Price Engine...")
    
    engine = PriceEngine(seed=42)  # Reproducible results
    
    # Generate some price data
    print("\nGenerating 5 days of BTC/USDT data:")
    btc_data = engine.generate_ohlc('BTCUSDT', num_periods=5)
    for day in btc_data:
        print(f"  {day['timestamp'].strftime('%Y-%m-%d')}: Open={day['open']:.2f}, "
              f"High={day['high']:.2f}, Low={day['low']:.2f}, Close={day['close']:.2f}")
    
    # Test technical indicators
    print("\nTesting Technical Indicators:")
    prices = [day['close'] for day in btc_data]
    
    sma = TechnicalIndicators.calculate_sma(prices, 3)
    print(f"SMA(3): {sma}")
    
    rsi = TechnicalIndicators.calculate_rsi(prices, 3)
    print(f"RSI(3): {rsi}")
    
    # Test market event
    print("\nTesting Market Event (Flash Crash):")
    before_crash = engine.get_current_price('BTCUSDT')
    engine.add_market_event('flash_crash', magnitude=0.1)
    after_crash = engine.get_current_price('BTCUSDT')
    print(f"Before: ${before_crash:.2f}, After: ${after_crash:.2f}")
    
    print("\nPrice Engine test completed successfully!")