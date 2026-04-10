#!/usr/bin/env python3
"""
OMNICUS Ultimate Trading Server
Combines all trading features with dashboard
"""
import os
import sys
import json
import asyncio
from datetime import datetime
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder='dashboards')
CORS(app)

# Trading state
trading_state = {
    'capital': 10000.0,
    'profit': 0.0,
    'trades': 0,
    'wins': 0,
    'losses': 0,
    'mode': 'paper',
    'status': 'ready',
    'positions': [],
    'signals': []
}

@app.route('/')
def index():
    return send_from_directory('dashboards', 'omnicus_ultimate.html')

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'online',
        'mode': trading_state['mode'],
        'capital': trading_state['capital'],
        'profit': trading_state['profit'],
        'trades': trading_state['trades'],
        'win_rate': (trading_state['wins'] / trading_state['trades'] * 100) if trading_state['trades'] > 0 else 0,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/signals')
def api_signals():
    return jsonify({
        'signals': [
            {'symbol': 'BTCUSDT', 'action': 'HOLD', 'confidence': 0.75, 'price': 50000},
            {'symbol': 'ETHUSDT', 'action': 'LONG', 'confidence': 0.82, 'price': 3000},
            {'symbol': 'SOLUSDT', 'action': 'HOLD', 'confidence': 0.68, 'price': 100}
        ]
    })

@app.route('/api/market/scan')
def api_market_scan():
    return jsonify({
        'scan_results': [
            {'symbol': 'BTCUSDT', 'price': 50000, 'change_24h': 2.5, 'volume': '1.2B', 'signal': 'BULLISH'},
            {'symbol': 'ETHUSDT', 'price': 3000, 'change_24h': 3.2, 'volume': '800M', 'signal': 'BULLISH'},
            {'symbol': 'SOLUSDT', 'price': 100, 'change_24h': -1.5, 'volume': '500M', 'signal': 'NEUTRAL'},
            {'symbol': 'DOGEUSDT', 'price': 0.12, 'change_24h': 8.5, 'volume': '300M', 'signal': 'PUMP'},
            {'symbol': 'XRPUSDT', 'price': 0.52, 'change_24h': 1.2, 'volume': '200M', 'signal': 'BULLISH'}
        ]
    })

@app.route('/api/trading/start', methods=['POST'])
def start_trading():
    trading_state['status'] = 'trading'
    return jsonify({'status': 'started', 'message': 'Trading started!'})

@app.route('/api/trading/stop', methods=['POST'])
def stop_trading():
    trading_state['status'] = 'stopped'
    return jsonify({'status': 'stopped', 'message': 'Trading stopped!'})

@app.route('/dashboards/<path:filename>')
def dashboard(filename):
    return send_from_directory('dashboards', filename)

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ██████╗ ███╗ ███╗██╗ ██╗██╗ ██╗                               ║
║   ██╔═══██╗████╗ ████║██║ ██║╚██╗██╔╝                            ║
║   ██║   ██║██╔████╔██║██║ ██║ ╚███╔╝                             ║
║   ██║   ██║██║╚██╔╝██║██║ ██║ ██╔██╗                             ║
║   ╚██████╔╝██║ ╚═╝ ██║╚██████╔╝██╔╝ ██╗                          ║
║   ╚═════╝ ╚═╝   ╚═╝ ╚═════╝ ╚═╝ ╚═╝                             ║
║                                                                   ║
║   💰 THE ULTIMATE PROFIT HUNTER 💰                              ║
║                                                                   ║
║   ═══════════════════════════════════════════════════════════════ ║
║                                                                   ║
║   🌐 Dashboard: http://localhost:9999                            ║
║   📊 API: http://localhost:9999/api/status                       ║
║   🎯 Trading Mode: Paper Trading                                 ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    app.run(host='0.0.0.0', port=9999, debug=False)
