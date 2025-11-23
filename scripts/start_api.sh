#!/bin/bash
# Research Copilot API Server Startup Script
# This script starts the Research Copilot backend API server with production settings

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="0.0.0.0"
API_PORT="8000"
LOG_DIR="$API_DIR/logs"
PID_FILE="$API_DIR/api.pid"
LOG_LEVEL="info"  # Options: debug, info, warning, error

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Research Copilot API Server${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if API is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  API server is already running (PID: $PID)${NC}"
        echo "Use ./scripts/stop_api.sh to stop it first."
        exit 1
    else
        echo -e "${YELLOW}Removing stale PID file...${NC}"
        rm "$PID_FILE"
    fi
fi

# Check Python environment
if [ ! -d "$API_DIR/spoon-env" ]; then
    echo -e "${RED}❌ Virtual environment not found at $API_DIR/spoon-env${NC}"
    echo "Please run: python -m venv spoon-env && source spoon-env/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Create logs directory
mkdir -p "$LOG_DIR"

# Check environment variables
echo -e "${YELLOW}Checking environment variables...${NC}"
if [ ! -f "$API_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from template...${NC}"
    cat > "$API_DIR/.env" << EOF
# LLM Provider API Keys (at least one required)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
GEMINI_API_KEY=

# Research Tools (optional)
BITQUERY_API_KEY=
CHAINBASE_API_KEY=

# Server Configuration
API_HOST=$API_HOST
API_PORT=$API_PORT
LOG_LEVEL=$LOG_LEVEL
EOF
    echo -e "${YELLOW}⚠️  Please edit .env file and add your API keys before starting the server.${NC}"
    echo "Location: $API_DIR/.env"
    exit 1
fi

# Source environment variables
set -a
source "$API_DIR/.env"
set +a

# Check if at least one LLM provider is configured
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$DEEPSEEK_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ No LLM provider API key configured${NC}"
    echo "Please set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, GEMINI_API_KEY"
    echo "Edit $API_DIR/.env to add your API keys."
    exit 1
fi

echo -e "${GREEN}✅ Environment configured${NC}"
if [ -n "$OPENAI_API_KEY" ]; then echo "  - OpenAI: Configured"; fi
if [ -n "$ANTHROPIC_API_KEY" ]; then echo "  - Anthropic: Configured"; fi
if [ -n "$DEEPSEEK_API_KEY" ]; then echo "  - DeepSeek: Configured"; fi
if [ -n "$GEMINI_API_KEY" ]; then echo "  - Gemini: Configured"; fi
echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$API_DIR/spoon-env/bin/activate"

# Install/update dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
if [ -f "$API_DIR/requirements.txt" ]; then
    pip install -q -r "$API_DIR/requirements.txt" 2>&1 | grep -v "Requirement already satisfied" || true
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# Change to API directory
cd "$API_DIR"

# Start the API server
echo -e "${GREEN}🚀 Starting API server...${NC}"
echo "  Host: $API_HOST"
echo "  Port: $API_PORT"
echo "  Log Level: $LOG_LEVEL"
echo "  Logs: $LOG_DIR/api.log"
echo ""

nohup python research_copilot/api.py \
    --host "$API_HOST" \
    --port "$API_PORT" \
    --log-level "$LOG_LEVEL" \
    > "$LOG_DIR/api.log" 2>&1 &

API_PID=$!
echo $API_PID > "$PID_FILE"

# Wait a bit and check if process is still running
sleep 2
if ps -p $API_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API server started successfully!${NC}"
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Server Information${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "  PID: $API_PID"
    echo "  URL: http://localhost:$API_PORT"
    echo "  API Docs: http://localhost:$API_PORT/docs"
    echo "  Health Check: http://localhost:$API_PORT/health"
    echo ""
    echo -e "${YELLOW}Management Commands:${NC}"
    echo "  View logs: tail -f $LOG_DIR/api.log"
    echo "  Stop server: ./scripts/stop_api.sh"
    echo "  Restart server: ./scripts/restart_api.sh"
    echo "  Check status: ./scripts/status_api.sh"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}❌ Failed to start API server${NC}"
    echo "Check logs at: $LOG_DIR/api.log"
    rm "$PID_FILE"
    exit 1
fi
