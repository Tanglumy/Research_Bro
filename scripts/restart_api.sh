#!/bin/bash
# Research Copilot API Server Restart Script
# This script restarts the Research Copilot backend API server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Restarting Research Copilot API Server${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Stop the server
echo -e "${YELLOW}Step 1/2: Stopping server...${NC}"
"$SCRIPT_DIR/stop_api.sh"

echo ""
echo -e "${YELLOW}Step 2/2: Starting server...${NC}"
sleep 1

# Start the server
"$SCRIPT_DIR/start_api.sh"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Server restarted successfully${NC}"
echo -e "${GREEN}========================================${NC}"
