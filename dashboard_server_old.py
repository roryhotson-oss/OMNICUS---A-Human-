#!/usr/bin/env python3
"""
OMNICUS Universal Dashboard Server
==================================
Serves omnicus_universal.html and provides real-time API for Hybrid Trading.
"""
import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# FastAPI imports (Replaces Flask)
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OMNICUS.Server")

app = FastAPI(title="OMNICUS Universal", version="2.0.0")

# Enable CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Global State ---
class OmniState:
    def __init__(self):
        self.mode = "learning"  # learning, paper, real
        self.running = False
        self.capital = 1000.0
        self.initial_capital = 1000.0
        self.trades = []
        self.signals = []
        self.soul_level = 1
        self.wallet_connected = False
        self.websocket_clients: List[WebSocket] = []

    def get_profit(self):
        return self.capital - self.initial_capital

    def get_progress(self):
        if self.initial_capital == 0: return 0
        return min(100.0, max(0.0, ((self.capital - self.initial_capital) / self.initial_capital) * 100))

state = OmniState()

# --- API Endpoints ---

@app.on_event("startup")
async def startup():
    logger.info("🚀 OMNICUS Core Initialized")
    # In full version: Initialize HybridAI, Binance, Alpaca, Telegram here

@app.on_event("shutdown")
async def shutdown():
    state.running = False
    logger.info("🛑 OMNICUS Stopped")

@app.get("/")
async def serve_dashboard():
    """Serve the ACTUAL HTML file from dashboards folder"""
    dashboard_path = project_root / "dashboards" / "omnicus_universal.html"
    if dashboard_path.exists():
        return FileResponse(str(dashboard_path))
    return HTMLResponse("<h1>Dashboard missing</h1><p>Ensure dashboards/omnicus_universal.html exists</p>", status_code=404)

@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    state.websocket_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in state.websocket_clients:
            state.websocket_clients.remove(websocket)

async def broadcast(data: dict):
    msg = json.dumps(data)
    disconnected = []
    for client in state.websocket_clients:
        try:
            await client.send_text(msg)
        except:
            disconnected.append(client)
    for client in disconnected:
        if client in state.websocket_clients:
            state.websocket_clients.remove(client)

@app.get("/api/status")
async def get_status():
    return {
        "mode": state.mode,
        "running": state.running,
        "capital": round(state.capital, 2),
        "profit": round(state.get_profit(), 2),
        "profit_percent": round((state.get_profit()/state.initial_capital)*100 if state.initial_capital else 0, 2),
        "progress": round(state.get_progress(), 2),
        "trades_count": len(state.trades),
        "soul_level": state.soul_level,
        "wallet_connected": state.wallet_connected
    }

@app.post("/api/start")
async def start_trading(req: Request):
    data = await req.json()
    state.mode = data.get("mode", "paper")
    state.initial_capital = data.get("capital", 1000)
    state.capital = state.initial_capital
    state.running = True
    logger.info(f"🚀 Trading Started: {state.mode.upper()} | Capital: ${state.initial_capital}")
    await broadcast({"type": "status", "running": True, "mode": state.mode})
    return {"status": "started", "mode": state.mode}

@app.post("/api/stop")
async def stop_trading():
    state.running = False
    logger.info("🛑 Trading Stopped")
    await broadcast({"type": "status", "running": False})
    return {"status": "stopped"}

@app.post("/api/connect-wallet")
async def connect_wallet(req: Request):
    data = await req.json()
    state.wallet_connected = True
    logger.info(f"🔗 Wallet Connected: {data.get('type', 'Unknown')}")
    await broadcast({"type": "wallet", "connected": True, "type": data.get('type')})
    return {"status": "connected", "type": data.get('type')}

@app.get("/api/trades")
async def get_trades():
    return {"trades": list(reversed(state.trades[-50:]))}

@app.get("/api/signals")
async def get_signals():
    return {"signals": state.signals}

# Debug endpoint to simulate a win and test the "Soul" reward system
@app.post("/api/debug/simulate-win")
async def simulate_win():
    if not state.running:
        return {"error": "Not running"}
    profit = 50.0
    state.capital += profit
    state.trades.append({"symbol": "BTCUSDT", "pnl": profit, "time": datetime.now().isoformat()})
    
    # Trigger Soul Reward
    state.soul_level += 1
    await broadcast({
        "type": "trade", 
        "pnl": profit, 
        "capital": state.capital, 
        "soul_level": state.soul_level,
        "message": "Profit made! Soul evolved! 🎁"
    })
    return {"status": "simulated win", "new_capital": state.capital}

def main():
    print("\n" + "="*50)
    print("🤖 OMNICUS UNIVERSAL DASHBOARD")
    print("="*50)
    print("🌐 URL: http://0.0.0.0:9999")
    print("📡 WS: ws://0.0.0.0:9999/ws/updates")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=9999, log_level="info")

if __name__ == "__main__":
    main()
