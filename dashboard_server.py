#!/usr/bin/env python3
"""
OMNICUS Universal Dashboard Server
Serves omnicus_universal.html and provides real-time API.
"""
import os, sys, asyncio, json, logging
from datetime import datetime
from typing import List
from pathlib import Path
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("OMNICUS")

app = FastAPI(title="OMNICUS Universal")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class State:
    def __init__(self):
        self.mode = "learning"
        self.running = False
        self.capital = 1000.0
        self.initial_capital = 1000.0
        self.trades = []
        self.soul_level = 1
        self.wallet_connected = False
        self.clients: List[WebSocket] = []

    def get_profit(self): return self.capital - self.initial_capital
    def get_progress(self):
        if self.initial_capital == 0: return 0
        return min(100.0, max(0.0, ((self.capital - self.initial_capital) / self.initial_capital) * 100))

state = State()

@app.on_event("startup")
async def startup(): logger.info("🚀 OMNICUS Core Initialized")

@app.on_event("shutdown")
async def shutdown(): state.running = False; logger.info("🛑 OMNICUS Stopped")

@app.get("/")
async def serve():
    p = project_root / "dashboards" / "omnicus_universal.html"
    if p.exists(): return FileResponse(str(p))
    return "<h1>Dashboard missing</h1>"

@app.websocket("/ws/updates")
async def ws(websocket: WebSocket):
    await websocket.accept()
    state.clients.append(websocket)
    try:
        while True:
            if await websocket.receive_text() == "ping": await websocket.send_text("pong")
    except: state.clients.remove(websocket) if websocket in state.clients else None

async def broadcast(data):
    msg = json.dumps(data)
    dead = []
    for c in state.clients:
        try: await c.send_text(msg)
        except: dead.append(c)
    for c in dead: state.clients.remove(c)

@app.get("/api/status")
async def status():
    return {"mode": state.mode, "running": state.running, "capital": round(state.capital, 2),
            "profit": round(state.get_profit(), 2), "progress": round(state.get_progress(), 2),
            "soul_level": state.soul_level, "wallet_connected": state.wallet_connected}

@app.post("/api/start")
async def start(req: Request):
    d = await req.json()
    state.mode = d.get("mode", "paper")
    state.initial_capital = d.get("capital", 1000)
    state.capital = state.initial_capital
    state.running = True
    logger.info(f"🚀 Started: {state.mode.upper()}")
    await broadcast({"type": "status", "running": True})
    return {"status": "started"}

@app.post("/api/stop")
async def stop():
    state.running = False
    logger.info("🛑 Stopped")
    await broadcast({"type": "status", "running": False})
    return {"status": "stopped"}

@app.post("/api/connect-wallet")
async def connect(req: Request):
    d = await req.json()
    state.wallet_connected = True
    await broadcast({"type": "wallet", "connected": True})
    return {"status": "connected"}

@app.get("/api/trades")
async def trades(): return {"trades": list(reversed(state.trades[-50:]))}

@app.get("/api/signals")
async def signals(): return {"signals": []}

if __name__ == "__main__":
    print("\n🤖 OMNICUS UNIVERSAL DASHBOARD")
    print("🌐 http://0.0.0.0:9999\n")
    uvicorn.run(app, host="0.0.0.0", port=9999, log_level="info")

@app.post("/api/chat")
async def chat_with_omnicus(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "").lower()
        response_text = ""
        
        if "start" in message or "launch" in message:
            capital = 1000
            for word in message.split():
                if word.isdigit(): capital = int(word); break
            mode = "real" if "real" in message else ("learning" if "learning" in message else "paper")
            state.mode = mode; state.initial_capital = capital; state.capital = capital; state.running = True
            response_text = f"✅ OMNICUS Activated! Mode: {mode.upper()}, Capital: ${capital}."
            await broadcast({"type": "status", "running": True, "mode": mode, "capital": capital})
        elif "stop" in message:
            state.running = False
            response_text = "⏹️ OMNICUS Stopped."
            await broadcast({"type": "status", "running": False})
        elif "status" in message or "profit" in message:
            response_text = f"📊 Mode: {state.mode.upper()} | Capital: ${state.capital:.2f} | Profit: ${state.get_profit():.2f} | Soul: {state.soul_level}"
        else:
            response_text = "🤖 OMNICUS Ready. Say 'Start', 'Status', or 'Simulate'."
            
        return {"response": response_text, "status": "success"}
    except Exception as e:
        return {"response": f"Error: {str(e)}", "status": "error"}
CHAT_END; exec bash
