"""
OMNICUS ToolKit Module
======================
Collection of trading tools for analysis, execution, and monitoring.
These tools are OMNICUS's instruments for interacting with markets.

This module provides the practical tools OMNICUS needs to execute
his trading strategies and analyze market conditions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
import math
import statistics
import asyncio
import aiohttp
import hashlib
import hmac
import time


class ToolType(Enum):
    """Types of trading tools"""
    ANALYSIS = "analysis"           # Market analysis tools
    CALCULATION = "calculation"     # Mathematical calculations
    EXECUTION = "execution"         # Trade execution tools
    MONITORING = "monitoring"       # Position monitoring tools
    DATA = "data"                   # Data retrieval tools
    RISK = "risk"                   # Risk management tools


@dataclass
class ToolResult:
    """Result from a tool execution"""
    
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class Tool:
    """Base class for trading tools"""
    
    def __init__(self, name: str, tool_type: ToolType, description: str):
        self.name = name
        self.tool_type = tool_type
        self.description = description
        self._use_count = 0
        self._last_used: Optional[datetime] = None
    
    async def execute(self, *args, **kwargs) -> ToolResult:
        """Execute the tool - to be implemented by subclasses"""
        raise NotImplementedError
    
    def _record_use(self):
        """Record tool usage"""
        self._use_count += 1
        self._last_used = datetime.now()


class TechnicalIndicatorTool(Tool):
    """Tool for calculating technical indicators"""
    
    def __init__(self):
        super().__init__(
            name="technical_indicators",
            tool_type=ToolType.ANALYSIS,
            description="Calculate technical indicators from price data"
        )
    
    async def execute(
        self, 
        prices: List[float], 
        indicators: List[str] = None
    ) -> ToolResult:
        """
        Calculate specified technical indicators
        
        Args:
            prices: List of closing prices
            indicators: List of indicators to calculate
            
        Returns:
            ToolResult with calculated indicators
        """
        start_time = time.time()
        self._record_use()
        
        if not prices or len(prices) < 2:
            return ToolResult(
                success=False,
                data=None,
                error="Insufficient price data"
            )
        
        indicators = indicators or ["sma", "ema", "rsi", "macd"]
        results = {}
        
        try:
            # Simple Moving Averages
            if "sma" in indicators:
                results["sma_20"] = self._calculate_sma(prices, 20)
                results["sma_50"] = self._calculate_sma(prices, 50)
            
            # Exponential Moving Averages
            if "ema" in indicators:
                results["ema_12"] = self._calculate_ema(prices, 12)
                results["ema_26"] = self._calculate_ema(prices, 26)
            
            # RSI
            if "rsi" in indicators:
                results["rsi"] = self._calculate_rsi(prices)
            
            # MACD
            if "macd" in indicators:
                macd_result = self._calculate_macd(prices)
                results["macd"] = macd_result["macd"]
                results["macd_signal"] = macd_result["signal"]
                results["macd_histogram"] = macd_result["histogram"]
            
            # Bollinger Bands
            if "bollinger" in indicators:
                bb = self._calculate_bollinger_bands(prices)
                results["bb_upper"] = bb["upper"]
                results["bb_middle"] = bb["middle"]
                results["bb_lower"] = bb["lower"]
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                data=results,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def _calculate_sma(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period
        
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(
        self, 
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict:
        """Calculate MACD, Signal, and Histogram"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        if ema_fast is None or ema_slow is None:
            return {"macd": None, "signal": None, "histogram": None}
        
        macd = ema_fast - ema_slow
        
        # Simplified signal calculation
        signal_line = macd * 0.8  # Approximate
        
        return {
            "macd": macd,
            "signal": signal_line,
            "histogram": macd - signal_line
        }
    
    def _calculate_bollinger_bands(
        self, 
        prices: List[float], 
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {"upper": None, "middle": None, "lower": None}
        
        middle = sum(prices[-period:]) / period
        variance = sum((p - middle) ** 2 for p in prices[-period:]) / period
        std = math.sqrt(variance)
        
        return {
            "upper": middle + (std * std_dev),
            "middle": middle,
            "lower": middle - (std * std_dev)
        }


class PositionSizerTool(Tool):
    """Tool for calculating position sizes"""
    
    def __init__(self):
        super().__init__(
            name="position_sizer",
            tool_type=ToolType.CALCULATION,
            description="Calculate optimal position size based on risk parameters"
        )
    
    async def execute(
        self,
        capital: float,
        risk_percent: float,
        entry_price: float,
        stop_loss_price: float,
        method: str = "fixed_risk"
    ) -> ToolResult:
        """
        Calculate position size
        
        Args:
            capital: Total trading capital
            risk_percent: Risk per trade as percentage (e.g., 2.0 for 2%)
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            method: Sizing method (fixed_risk, kelly, volatility)
            
        Returns:
            ToolResult with position sizing details
        """
        start_time = time.time()
        self._record_use()
        
        try:
            risk_amount = capital * (risk_percent / 100)
            price_risk = abs(entry_price - stop_loss_price)
            
            if price_risk == 0:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Stop loss must be different from entry price"
                )
            
            if method == "fixed_risk":
                # Fixed risk per trade
                quantity = risk_amount / price_risk
                position_value = quantity * entry_price
                
            elif method == "kelly":
                # Kelly Criterion (simplified, assumes 55% win rate, 1:1 R:R)
                win_rate = 0.55
                win_loss_ratio = 1.0
                kelly_fraction = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
                kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25%
                
                quantity = (capital * kelly_fraction) / entry_price
                position_value = quantity * entry_price
                
            elif method == "volatility":
                # Volatility-adjusted position sizing
                # Assume 2% daily volatility target
                volatility_target = 0.02
                quantity = (capital * volatility_target) / (entry_price * 0.02)  # Simplified
                position_value = quantity * entry_price
            else:
                quantity = risk_amount / price_risk
                position_value = quantity * entry_price
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                data={
                    "quantity": round(quantity, 8),
                    "position_value": round(position_value, 2),
                    "risk_amount": round(risk_amount, 2),
                    "risk_per_share": round(price_risk, 4),
                    "method": method,
                    "capital_used_percent": round((position_value / capital) * 100, 2)
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class StopLossCalculatorTool(Tool):
    """Tool for calculating stop loss levels"""
    
    def __init__(self):
        super().__init__(
            name="stop_loss_calculator",
            tool_type=ToolType.RISK,
            description="Calculate optimal stop loss levels"
        )
    
    async def execute(
        self,
        entry_price: float,
        method: str = "percentage",
        atr: float = None,
        support_level: float = None,
        risk_percent: float = 2.0
    ) -> ToolResult:
        """
        Calculate stop loss price
        
        Args:
            entry_price: Entry price
            method: Method for stop loss (percentage, atr, support)
            atr: Average True Range (for ATR method)
            support_level: Support level (for support method)
            risk_percent: Risk percentage (for percentage method)
            
        Returns:
            ToolResult with stop loss calculations
        """
        start_time = time.time()
        self._record_use()
        
        try:
            results = {
                "entry_price": entry_price,
                "method": method
            }
            
            if method == "percentage":
                # Simple percentage-based stop
                stop_loss = entry_price * (1 - risk_percent / 100)
                results["stop_loss_price"] = round(stop_loss, 4)
                results["risk_percent"] = risk_percent
                
            elif method == "atr" and atr:
                # ATR-based stop (2x ATR below entry for longs)
                stop_loss = entry_price - (2 * atr)
                results["stop_loss_price"] = round(stop_loss, 4)
                results["atr_used"] = atr
                results["atr_multiplier"] = 2
                
            elif method == "support" and support_level:
                # Support-based stop (slightly below support)
                stop_loss = support_level * 0.99  # 1% below support
                results["stop_loss_price"] = round(stop_loss, 4)
                results["support_level"] = support_level
                
            else:
                # Default to 2% below entry
                stop_loss = entry_price * 0.98
                results["stop_loss_price"] = round(stop_loss, 4)
                results["fallback"] = True
            
            # Calculate risk amount
            results["risk_amount"] = round(entry_price - results["stop_loss_price"], 4)
            results["risk_percent_actual"] = round(
                (results["risk_amount"] / entry_price) * 100, 2
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                data=results,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )


class MarketScannerTool(Tool):
    """Tool for scanning markets for opportunities"""
    
    def __init__(self):
        super().__init__(
            name="market_scanner",
            tool_type=ToolType.DATA,
            description="Scan markets for trading opportunities"
        )
    
    async def execute(
        self,
        symbols: List[str],
        criteria: Dict = None
    ) -> ToolResult:
        """
        Scan multiple symbols for opportunities
        
        Args:
            symbols: List of symbols to scan
            criteria: Scan criteria (rsi_oversold, volume_spike, etc.)
            
        Returns:
            ToolResult with scan results
        """
        start_time = time.time()
        self._record_use()
        
        criteria = criteria or {
            "rsi_oversold": True,
            "rsi_overbought": True,
            "volume_spike": True,
            "price_above_sma": True
        }
        
        results = []
        
        # This would normally fetch real market data
        # For now, return a structured result
        for symbol in symbols:
            result = {
                "symbol": symbol,
                "signals": [],
                "score": 0.0,
                "recommendation": "hold"
            }
            results.append(result)
        
        execution_time = (time.time() - start_time) * 1000
        
        return ToolResult(
            success=True,
            data={
                "scan_results": results,
                "symbols_scanned": len(symbols),
                "criteria_used": criteria
            },
            execution_time_ms=execution_time
        )


class RiskAssessmentTool(Tool):
    """Tool for assessing trade and portfolio risk"""
    
    def __init__(self):
        super().__init__(
            name="risk_assessment",
            tool_type=ToolType.RISK,
            description="Assess risk for trades and portfolio"
        )
    
    async def execute(
        self,
        positions: List[Dict],
        capital: float,
        market_conditions: Dict = None
    ) -> ToolResult:
        """
        Assess current portfolio risk
        
        Args:
            positions: List of current positions
            capital: Total capital
            market_conditions: Current market conditions
            
        Returns:
            ToolResult with risk assessment
        """
        start_time = time.time()
        self._record_use()
        
        try:
            total_exposure = sum(p.get("value", 0) for p in positions)
            exposure_percent = (total_exposure / capital) * 100 if capital > 0 else 0
            
            # Calculate portfolio volatility (simplified)
            position_values = [p.get("value", 0) for p in positions]
            if len(position_values) > 1:
                portfolio_volatility = statistics.stdev(position_values) / capital if capital > 0 else 0
            else:
                portfolio_volatility = 0
            
            # Calculate correlation risk (simplified)
            unique_assets = len(set(p.get("symbol", "") for p in positions))
            correlation_risk = "low" if unique_assets >= 5 else "medium" if unique_assets >= 3 else "high"
            
            # Calculate drawdown risk
            max_position = max(position_values) if position_values else 0
            concentration_risk = (max_position / capital) * 100 if capital > 0 else 0
            
            # Overall risk score (0-100)
            risk_score = min(100, 
                exposure_percent * 0.4 + 
                portfolio_volatility * 100 * 0.3 +
                concentration_risk * 0.3
            )
            
            # Risk level
            if risk_score < 30:
                risk_level = "low"
            elif risk_score < 60:
                risk_level = "moderate"
            else:
                risk_level = "high"
            
            execution_time = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                data={
                    "total_exposure": round(total_exposure, 2),
                    "exposure_percent": round(exposure_percent, 2),
                    "portfolio_volatility": round(portfolio_volatility, 4),
                    "correlation_risk": correlation_risk,
                    "concentration_risk": round(concentration_risk, 2),
                    "risk_score": round(risk_score, 2),
                    "risk_level": risk_level,
                    "position_count": len(positions),
                    "unique_assets": unique_assets,
                    "recommendations": self._generate_risk_recommendations(
                        exposure_percent, concentration_risk, correlation_risk
                    )
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def _generate_risk_recommendations(
        self, 
        exposure: float, 
        concentration: float,
        correlation: str
    ) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if exposure > 70:
            recommendations.append("Consider reducing total exposure below 70%")
        
        if concentration > 25:
            recommendations.append("Reduce largest position concentration")
        
        if correlation == "high":
            recommendations.append("Diversify into more uncorrelated assets")
        
        return recommendations


class PatternRecognitionTool(Tool):
    """Tool for recognizing chart patterns"""
    
    def __init__(self):
        super().__init__(
            name="pattern_recognition",
            tool_type=ToolType.ANALYSIS,
            description="Recognize chart patterns from price data"
        )
    
    async def execute(
        self,
        prices: List[float],
        volumes: List[float] = None
    ) -> ToolResult:
        """
        Recognize patterns in price data
        
        Args:
            prices: List of closing prices
            volumes: Optional list of volumes
            
        Returns:
            ToolResult with detected patterns
        """
        start_time = time.time()
        self._record_use()
        
        if len(prices) < 20:
            return ToolResult(
                success=False,
                data=None,
                error="Need at least 20 price points for pattern recognition"
            )
        
        patterns = []
        
        # Double Bottom detection (simplified)
        if self._detect_double_bottom(prices):
            patterns.append({
                "pattern": "double_bottom",
                "confidence": 0.7,
                "implication": "bullish",
                "description": "Potential reversal pattern detected"
            })
        
        # Double Top detection (simplified)
        if self._detect_double_top(prices):
            patterns.append({
                "pattern": "double_top",
                "confidence": 0.7,
                "implication": "bearish",
                "description": "Potential reversal pattern detected"
            })
        
        # Breakout detection
        if self._detect_breakout(prices, volumes):
            patterns.append({
                "pattern": "breakout",
                "confidence": 0.65,
                "implication": "continuation",
                "description": "Price breaking resistance/support"
            })
        
        # Trend detection
        trend = self._detect_trend(prices)
        if trend != "sideways":
            patterns.append({
                "pattern": f"{trend}_trend",
                "confidence": 0.75,
                "implication": trend,
                "description": f"Strong {trend} trend detected"
            })
        
        execution_time = (time.time() - start_time) * 1000
        
        return ToolResult(
            success=True,
            data={
                "patterns": patterns,
                "pattern_count": len(patterns),
                "analysis_period": f"{len(prices)} candles"
            },
            execution_time_ms=execution_time
        )
    
    def _detect_double_bottom(self, prices: List[float]) -> bool:
        """Simplified double bottom detection"""
        if len(prices) < 20:
            return False
        
        recent = prices[-20:]
        min1_idx = recent.index(min(recent[:10]))
        min2_idx = 10 + recent[10:].index(min(recent[10:]))
        
        # Two similar lows with a peak in between
        if abs(recent[min1_idx] - recent[min2_idx]) / recent[min1_idx] < 0.02:
            if min1_idx < min2_idx:
                return True
        
        return False
    
    def _detect_double_top(self, prices: List[float]) -> bool:
        """Simplified double top detection"""
        if len(prices) < 20:
            return False
        
        recent = prices[-20:]
        max1_idx = recent.index(max(recent[:10]))
        max2_idx = 10 + recent[10:].index(max(recent[10:]))
        
        # Two similar highs with a valley in between
        if abs(recent[max1_idx] - recent[max2_idx]) / recent[max1_idx] < 0.02:
            if max1_idx < max2_idx:
                return True
        
        return False
    
    def _detect_breakout(self, prices: List[float], volumes: List[float]) -> bool:
        """Simplified breakout detection"""
        if len(prices) < 20:
            return False
        
        recent_range = max(prices[-20:-5]) - min(prices[-20:-5])
        current_price = prices[-1]
        recent_high = max(prices[-20:-5])
        
        # Price breaking above recent range
        if current_price > recent_high * 1.02:
            return True
        
        return False
    
    def _detect_trend(self, prices: List[float]) -> str:
        """Detect overall trend direction"""
        if len(prices) < 10:
            return "sideways"
        
        sma_5 = sum(prices[-5:]) / 5
        sma_10 = sum(prices[-10:]) / 10
        
        if sma_5 > sma_10 * 1.02:
            return "bullish"
        elif sma_5 < sma_10 * 0.98:
            return "bearish"
        
        return "sideways"


class ToolKit:
    """
    Central collection of trading tools for OMNICUS
    
    The ToolKit provides all the practical instruments OMNICUS needs
    to analyze markets, calculate positions, manage risk, and execute trades.
    
    Features:
    - Technical analysis tools
    - Position sizing calculators
    - Risk assessment tools
    - Pattern recognition
    - Market scanning
    """
    
    def __init__(self):
        """Initialize the toolkit with all available tools"""
        self._tools: Dict[str, Tool] = {}
        self._tools_by_type: Dict[ToolType, List[str]] = {
            t: [] for t in ToolType
        }
        
        # Register all built-in tools
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register all built-in trading tools"""
        self.register_tool(TechnicalIndicatorTool())
        self.register_tool(PositionSizerTool())
        self.register_tool(StopLossCalculatorTool())
        self.register_tool(MarketScannerTool())
        self.register_tool(RiskAssessmentTool())
        self.register_tool(PatternRecognitionTool())
    
    def register_tool(self, tool: Tool) -> bool:
        """
        Register a new tool
        
        Args:
            tool: Tool to register
            
        Returns:
            True if registered successfully
        """
        if tool.name in self._tools:
            return False
        
        self._tools[tool.name] = tool
        self._tools_by_type[tool.tool_type].append(tool.name)
        
        return True
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name
        
        Args:
            name: Tool name
            
        Returns:
            The tool or None
        """
        return self._tools.get(name)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[Tool]:
        """
        Get all tools of a specific type
        
        Args:
            tool_type: Type of tools to get
            
        Returns:
            List of tools
        """
        return [self._tools[name] for name in self._tools_by_type[tool_type]]
    
    async def use_tool(self, name: str, *args, **kwargs) -> ToolResult:
        """
        Use a tool by name
        
        Args:
            name: Tool name
            *args: Tool arguments
            **kwargs: Tool keyword arguments
            
        Returns:
            ToolResult from execution
        """
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' not found"
            )
        
        return await tool.execute(*args, **kwargs)
    
    def list_tools(self) -> List[Dict]:
        """
        List all available tools
        
        Returns:
            List of tool information
        """
        return [
            {
                "name": tool.name,
                "type": tool.tool_type.value,
                "description": tool.description,
                "use_count": tool._use_count
            }
            for tool in self._tools.values()
        ]
    
    def get_toolkit_stats(self) -> Dict:
        """
        Get toolkit statistics
        
        Returns:
            Dictionary with stats
        """
        total_uses = sum(t._use_count for t in self._tools.values())
        
        return {
            "total_tools": len(self._tools),
            "total_uses": total_uses,
            "tools_by_type": {
                t.value: len(tools) 
                for t, tools in self._tools_by_type.items()
            },
            "most_used": sorted(
                self._tools.values(),
                key=lambda t: t._use_count,
                reverse=True
            )[0].name if self._tools else None
        }


# Default toolkit instance
toolkit = ToolKit()
