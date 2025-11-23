#!/bin/bash
# Research Copilot API Server Stop Script
# This script stops the running Research Copilot backend API server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
PID_FILE="$API_DIR/api.pid"

echo -e "${YELLOW}Stopping Research Copilot API Server...${NC}"

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found. Server may not be running.${NC}"
    exit 0
fi

# Read PID
PID=$(cat "$PID_FILE")

# Check if process is running
if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Process not found (PID: $PID). Removing stale PID file.${NC}"
    rm "$PID_FILE"
    exit 0
fi

# Try graceful shutdown first (SIGTERM)
echo -e "${YELLOW}Sending SIGTERM to process $PID...${NC}"
kill -TERM $PID 2>/dev/null || true

# Wait for process to exit (max 10 seconds)
echo -e "${YELLOW}Waiting for process to exit...${NC}"
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API server stopped successfully${NC}"
        rm "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# If still running, force kill (SIGKILL)
echo -e "${YELLOW}Process still running. Forcing shutdown...${NC}"
kill -KILL $PID 2>/dev/null || true
sleep 1

if ! ps -p $PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API server stopped (forced)${NC}"
    rm "$PID_FILE"
    exit 0
else
    echo -e "${RED}❌ Failed to stop API server${NC}"
    echo "You may need to manually kill the process: kill -9 $PID"
    exit 1
fi
