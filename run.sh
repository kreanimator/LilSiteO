#!/bin/bash

# LilSite-o startup script
# This script starts the FastAPI backend and UI server, then opens the browser

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}LilSite-o Startup Script${NC}"
echo "================================"

# Check if .env exists, create from example if not
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from env_example...${NC}"
    if [ -f env_example ]; then
        cp env_example .env
        echo -e "${GREEN}.env file created${NC}"
    else
        echo -e "${YELLOW}env_example not found, using defaults${NC}"
    fi
fi

# Check if vLLM server is running
echo -e "\n${YELLOW}Checking vLLM server...${NC}"
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ vLLM server is running on port 8000${NC}"
else
    echo -e "${RED}✗ vLLM server is not running on port 8000${NC}"
    echo -e "${YELLOW}Please start vLLM server first:${NC}"
    echo "  LLM_MODEL=\"Qwen/Qwen2.5-Coder-7B-Instruct\" services/agent/run_llm.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d .venv ]; then
    echo -e "\n${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies if needed
echo -e "\n${YELLOW}Checking dependencies...${NC}"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    cd services/agent
    pip install -r requirements.txt > /dev/null 2>&1
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies are installed${NC}"
fi

# Create runtime directories
echo -e "\n${YELLOW}Setting up runtime directories...${NC}"
mkdir -p runtime/runs runtime/published runtime/logs
echo -e "${GREEN}✓ Runtime directories ready${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID $UI_PID 2>/dev/null || true
    wait $BACKEND_PID $UI_PID 2>/dev/null || true
    echo -e "${GREEN}Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI backend
echo -e "\n${YELLOW}Starting FastAPI backend on port 9000...${NC}"
cd services/agent/app
uvicorn main:app --host 0.0.0.0 --port 9000 > /tmp/lilsite_backend.log 2>&1 &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# Wait for backend to start
sleep 2
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    cat /tmp/lilsite_backend.log
    exit 1
fi

# Start UI server
echo -e "\n${YELLOW}Starting UI server on port 3000...${NC}"
cd ui
python3 -m http.server 3000 > /tmp/lilsite_ui.log 2>&1 &
UI_PID=$!
cd "$SCRIPT_DIR"

# Wait for UI to start
sleep 1
if kill -0 $UI_PID 2>/dev/null; then
    echo -e "${GREEN}✓ UI server started (PID: $UI_PID)${NC}"
else
    echo -e "${RED}✗ UI server failed to start${NC}"
    cat /tmp/lilsite_ui.log
    cleanup
    exit 1
fi

# Wait a bit more for servers to be ready
sleep 1

# Check if servers are responding
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is responding${NC}"
else
    echo -e "${YELLOW}⚠ Backend might not be ready yet${NC}"
fi

# Open browser
echo -e "\n${GREEN}Opening browser...${NC}"
if command -v open > /dev/null; then
    # macOS
    open http://localhost:3000
elif command -v xdg-open > /dev/null; then
    # Linux
    xdg-open http://localhost:3000
elif command -v start > /dev/null; then
    # Windows (Git Bash)
    start http://localhost:3000
else
    echo -e "${YELLOW}Please open http://localhost:3000 in your browser${NC}"
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}LilSite-o is running!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Backend:  http://localhost:9000"
echo -e "UI:       http://localhost:3000"
echo -e "vLLM:     http://localhost:8000"
echo -e "\n${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Wait for user interrupt
wait
