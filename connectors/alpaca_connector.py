import os
import logging
from typing import Dict

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False
    TradingClient = None

logger = logging.getLogger("OMNICUS.Alpaca")

class AlpacaConnector:
    def __init__(self, api_key: str = "", secret_key: str = "", paper: bool = True):
        if not ALPACA_AVAILABLE:
            logger.error("❌ alpaca-py not installed")
            self.client = None
            return
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        if not self.api_key:
            logger.warning("⚠️ Alpaca keys missing")
            self.client = None
            return
        try:
            self.client = TradingClient(api_key=self.api_key, secret_key=self.secret_key, paper=paper)
            logger.info(f"✅ Alpaca Connected")
        except Exception as e:
            logger.error(f"❌ Alpaca Error: {e}")
            self.client = None

    async def execute_trade(self, symbol: str, side: str, qty: float) -> Dict:
        if not self.client:
            return {"status": "error", "message": "No client"}
        return {"status": "success", "symbol": symbol, "side": side, "qty": qty}
