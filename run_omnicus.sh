#!/bin/bash
# ==================================================
# OMNICUS ULTIMATE - Launcher Script
# "Double the money. Period."
# ==================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="/home/master/Documents/OMNICUS-Ultimate-Project"
cd "$PROJECT_ROOT"

# Banner
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${GREEN}██████╗ ███╗   ███╗██╗   ██╗██╗      █████╗         ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${GREEN}██╔═══██╗████╗ ████║██║   ██║██║     ██╔══██╗        ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${GREEN}██║   ██║██╔████╔██║██║   ██║██║     ███████║        ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${GREEN}██║   ██║██║╚██╔╝██║██║   ██║██║     ██╔══██║        ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${GREEN}╚██████╔╝██║ ╚═╝ ██║╚██████╔╝███████╗██║  ██║        ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${GREEN}╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝        ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${YELLOW}🤖 THE ULTIMATE PROFIT HUNTER 💰                  ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}   ${PURPLE}Hybrid Trading: Paper + Real                      ${CYAN}║${NC}"
echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Check/install dependencies
echo -e "${BLUE}📦 Checking dependencies...${NC}"
pip install -q -r requirements.txt 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Installing dependencies...${NC}"
    pip install -r requirements.txt
}

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your API keys before running in real mode${NC}"
fi

# Parse command line arguments
MODE="${1:-dashboard}"
PORT="${2:-5000}"

case "$MODE" in
    dashboard|dash|d)
        echo -e "${GREEN}🚀 Starting OMNICUS Dashboard...${NC}"
        echo -e "${CYAN}📊 Access at: http://localhost:${PORT}${NC}"
        echo ""
        python dashboard_server.py --port $PORT
        ;;
    
    paper|p)
        echo -e "${GREEN}🎮 Starting PAPER TRADING mode...${NC}"
        echo -e "${CYAN}💰 Virtual capital only - learning mode${NC}"
        echo ""
        export TRADING_MODE=paper
        python main.py --mode paper
        ;;
    
    live|l|real|r)
        echo -e "${RED}⚠️  Starting LIVE TRADING mode...${NC}"
        echo -e "${RED}💰 REAL MONEY AT RISK${NC}"
        echo ""
        if [ -z "$BINANCE_API_KEY" ]; then
            echo -e "${RED}❌ Error: API keys not configured. Set them in .env first.${NC}"
            exit 1
        fi
        export TRADING_MODE=live
        python main.py --mode live
        ;;
    
    hybrid|h)
        echo -e "${PURPLE}🔥 Starting HYBRID TRADING mode...${NC}"
        echo -e "${CYAN}📚 Paper trades for learning${NC}"
        echo -e "${GREEN}💰 Real trades when confidence > 85%${NC}"
        echo ""
        export TRADING_MODE=hybrid
        python main.py --mode hybrid
        ;;
    
    test|t)
        echo -e "${BLUE}🧪 Running tests...${NC}"
        python -m pytest tests/test_omnicus.py -v
        ;;
    
    status|s)
        echo -e "${BLUE}📊 OMNICUS Status:${NC}"
        echo ""
        echo -e "  Mode: ${YELLOW}$(grep TRADING_MODE .env | cut -d'=' -f2)${NC}"
        echo -e "  Starting Capital: ${GREEN}$(grep STARTING_CAPITAL .env | cut -d'=' -f2)${NC}"
        echo -e "  Binance Testnet: ${CYAN}$(grep BINANCE_TESTNET .env | cut -d'=' -f2)${NC}"
        echo -e "  Dashboard Port: ${PURPLE}$(grep DASHBOARD_PORT .env | cut -d'=' -f2)${NC}"
        echo ""
        if [ -f "logs/omnicus.log" ]; then
            echo -e "  Last 10 log lines:"
            tail -10 logs/omnicus.log | sed 's/^/    /'
        fi
        ;;
    
    logs)
        if [ -f "logs/omnicus.log" ]; then
            tail -f logs/omnicus.log
        else
            echo -e "${YELLOW}⚠️  No log file found${NC}"
        fi
        ;;
    
    reset)
        echo -e "${YELLOW}🔄 Resetting OMNICUS...${NC}"
        rm -rf logs/*.log data/*.db __pycache__ */__pycache__
        echo -e "${GREEN}✅ Reset complete${NC}"
        ;;
    
    help|*)
        echo -e "${BLUE}Usage: ./run_omnicus.sh [mode] [port]${NC}"
        echo ""
        echo -e "Modes:"
        echo -e "  ${GREEN}dashboard${NC}   Start web dashboard only (default)"
        echo -e "  ${GREEN}paper${NC}       Paper trading mode (learning)"
        echo -e "  ${GREEN}live${NC}        Live trading with real money"
        echo -e "  ${GREEN}hybrid${NC}      Hybrid: paper + real when confident"
        echo -e "  ${GREEN}test${NC}        Run test suite"
        echo -e "  ${GREEN}status${NC}      Show current status"
        echo -e "  ${GREEN}logs${NC}        Tail log file"
        echo -e "  ${GREEN}reset${NC}       Clear logs and cache"
        echo -e "  ${GREEN}help${NC}        Show this help"
        echo ""
        ;;
esac

echo ""
