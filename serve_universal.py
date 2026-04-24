#!/usr/bin/env python3
"""
OMNICUS UNIVERSAL BRIDGE
Serves the specific 'omnicus_universal.html' dashboard and connects it to the Orchestrator.
"""
import os
import sys
import asyncio
import logging
from flask import Flask, render_template, jsonify, request, send_from_directory

# Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DASHBOARD_PATH = os.path.join(BASE_DIR, 'downloads') # Adjusted to your likely folder
DASHBOARD_FILE = 'omnicus_universal.html'

# Import the Brain
try:
    from omnicus_orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    CORE_AVAILABLE = True
    print("✅ Connected to OMNICUS Core (Orchestrator)")
except Exception as e:
    print(f"⚠️ Core not available: {e}")
    CORE_AVAILABLE = False
    orchestrator = None

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 1. Serve the specific HTML file you liked
@app.route('/')
def index():
    # Looks for the file in the 'downloads' folder or root
    if os.path.exists(os.path.join(DASHBOARD_PATH, DASHBOARD_FILE)):
        return send_from_directory(DASHBOARD_PATH, DASHBOARD_FILE)
    elif os.path.exists(os.path.join(BASE_DIR, DASHBOARD_FILE)):
        return send_from_directory(BASE_DIR, DASHBOARD_FILE)
    else:
        return f"<h1>Dashboard file '{DASHBOARD_FILE}' not found in {DASHBOARD_PATH}</h1><p>Ensure the file exists.</p>"

# 2. The API Bridge (Connects HTML to Python)
@app.route('/api/status')
def api_status():
    if not CORE_AVAILABLE:
        return jsonify({"capital": 0, "profit": 0, "mode": "OFFLINE"})
    return jsonify(orchestrator.get_status())

@app.route('/api/chat', methods=['POST'])
def api_chat():
    if not CORE_AVAILABLE:
        return jsonify({"response": "System Offline."})
    
    data = request.json
    user_msg = data.get('message', '')
    
    # Pass message to Orchestrator to handle logic (Buy, Sell, Chat)
    # The orchestrator parses natural language vs commands
    response_text = orchestrator.handle_command('chat', user_msg.split())
    return jsonify({"response": response_text})

@app.route('/api/command', methods=['POST'])
def api_command():
    if not CORE_AVAILABLE:
        return jsonify({"status": "offline"})
    
    cmd = request.json.get('command', '')
    # Trigger actions in Orchestrator
    if cmd == 'start':
        asyncio.run(orchestrator.start_trading('paper'))
    elif cmd == 'stop':
        asyncio.run(orchestrator.stop_trading())
    elif cmd == 'live':
        asyncio.run(orchestrator.start_trading('live'))
        
    return jsonify({"status": "executed"})

if __name__ == '__main__':
    print(f"🚀 SERVING DASHBOARD: {DASHBOARD_FILE}")
    print(f"🌐 OPEN IN BROWSER: http://127.0.0.1:5001")
    print("💬 Type commands like 'Buy BTC 100' or 'Status'")
    app.run(host='127.0.0.1', port=5001, debug=True)
