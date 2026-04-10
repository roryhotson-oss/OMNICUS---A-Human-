import os
import logging

try:
    import ollama
    LOCAL_AI_AVAILABLE = True
except ImportError:
    LOCAL_AI_AVAILABLE = False
    ollama = None

logger = logging.getLogger("OMNICUS.LocalAI")

class LocalAIBrain:
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.available = LOCAL_AI_AVAILABLE
        if self.available:
            logger.info(f"✅ Local AI connected: {model}")

    async def generate_reasoning(self, market_data: dict, signal: dict) -> str:
        if not self.available:
            return f"Signal: {signal.get('action', 'HOLD')}"
        try:
            prompt = f"Analyze: {market_data.get('symbol')} at {market_data.get('price')}. Action?"
            response = ollama.chat(model=self.model, messages=[{'role': 'user', 'content': prompt}])
            return response['message']['content']
        except Exception as e:
            return f"Error: {e}"

local_ai = LocalAIBrain()
