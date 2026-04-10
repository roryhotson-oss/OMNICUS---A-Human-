#!/usr/bin/env python3
"""
OMNICUS Trading Switch - Mode Controller
Controls trading mode switching for the OMNICUS system
"""

import os
from enum import Enum
from typing import Optional


class TradingSwitchMode(Enum):
    """Available trading switch modes"""
    SIMULATION = "simulation"
    PAPER = "paper"
    REAL = "real"
    TESTNET = "testnet"


class TradingSwitch:
    """
    Trading mode switch controller.
    Allows dynamic switching between trading modes.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "omnicus_config.py"
        self._current_mode = os.getenv("TRADING_MODE", "SIMULATION").upper()
        
        # Validate mode
        valid_modes = [m.value.upper() for m in TradingSwitchMode]
        if self._current_mode not in valid_modes:
            print(f"⚠️ Invalid TRADING_MODE '{self._current_mode}', defaulting to SIMULATION")
            self._current_mode = "SIMULATION"
    
    def get_current_mode(self) -> str:
        """Get the current trading mode"""
        return self._current_mode
    
    def set_mode(self, mode: str) -> bool:
        """
        Set the trading mode.
        
        Args:
            mode: One of 'simulation', 'paper', 'real', 'testnet'
            
        Returns:
            True if mode was set successfully
        """
        mode_upper = mode.upper()
        valid_modes = [m.value.upper() for m in TradingSwitchMode]
        
        if mode_upper in valid_modes:
            self._current_mode = mode_upper
            print(f"✅ Trading mode set to: {mode_upper}")
            return True
        else:
            print(f"❌ Invalid mode '{mode}'. Valid modes: {valid_modes}")
            return False
    
    def is_simulation(self) -> bool:
        """Check if running in simulation mode"""
        return self._current_mode in ("SIMULATION", "PAPER")
    
    def is_real_trading(self) -> bool:
        """Check if real trading is enabled"""
        return self._current_mode == "REAL"
    
    def is_testnet(self) -> bool:
        """Check if running on testnet"""
        return self._current_mode == "TESTNET"
    
    def get_status(self) -> dict:
        """Get full switch status"""
        return {
            "current_mode": self._current_mode,
            "is_simulation": self.is_simulation(),
            "is_real_trading": self.is_real_trading(),
            "is_testnet": self.is_testnet(),
            "can_trade": self.is_real_trading() or self.is_testnet(),
            "paper_trading": self.is_simulation()
        }


# Global trading switch instance
trading_switch = TradingSwitch()


if __name__ == "__main__":
    # Test the switch
    print("OMNICUS Trading Switch Test")
    print("=" * 40)
    print(f"Current Mode: {trading_switch.get_current_mode()}")
    print(f"Status: {trading_switch.get_status()}")
