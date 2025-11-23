#!/bin/bash
# Research Copilot API Server Status Script
# This script checks the status of the Research Copilot backend API server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")]/.." && pwd)"
PID_FILE="$API_DIR/api.pid"
API_PORT="8000"
LOG_DIR="$API_DIR/logs"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Research Copilot API Server Status${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}❌ Server Status: STOPPED${NC}"
    echo "  No PID file found"
    echo ""
    echo -e "${YELLOW}To start the server: ./scripts/start_api.sh${NC}"
    exit 1
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${RED}❌ Server Status: STOPPED${NC}"
    echo "  PID $PID not found (stale PID file)"
    echo ""
    echo -e "${YELLOW}To start the server: ./scripts/start_api.sh${NC}"
    rm "$PID_FILE"
    exit 1
fi

# Server is running - get process info
echo -e "${GREEN}✅ Server Status: RUNNING${NC}"
echo ""
echo -e "${BLUE}Process Information:${NC}"
echo "  PID: $PID"
echo "  User: $(ps -p $PID -o user=)"
echo "  CPU: $(ps -p $PID -o %cpu=)%"
echo "  Memory: $(ps -p $PID -o %mem=)%"
echo "  Started: $(ps -p $PID -o lstart=)"
echo "  Command: $(ps -p $PID -o command=)"
echo ""

# Check API endpoint
echo -e "${BLUE}API Endpoints:${NC}"
echo "  Base URL: http://localhost:$API_PORT"
echo "  API Docs: http://localhost:$API_PORT/docs"
echo "  Health Check: http://localhost:$API_PORT/health"
echo ""

# Try to hit health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"
if command -v curl > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:$API_PORT/health 2>/dev/null || echo "error")
    HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Health check: OK${NC}"
        HEALTH_DATA=$(echo "$HEALTH_RESPONSE" | head -n -1)
        echo "$HEALTH_DATA" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_DATA"
    else
        echo -e "${RED}❌ Health check: FAILED (HTTP $HTTP_CODE)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  curl not found, skipping health check${NC}"
fi

echo ""

# Check logs
if [ -f "$LOG_DIR/api.log" ]; then
    echo -e "${BLUE}Recent Logs (last 10 lines):${NC}"
    tail -n 10 "$LOG_DIR/api.log"
    echo ""
    echo -e "${YELLOW}View full logs: tail -f $LOG_DIR/api.log${NC}"
fi

echo ""
echo -e "${BLUE}Management Commands:${NC}"
echo "  Stop server: ./scripts/stop_api.sh"
echo "  Restart server: ./scripts/restart_api.sh"
echo "  View logs: tail -f $LOG_DIR/api.log"
echo -e "${GREEN}========================================${NC}"
