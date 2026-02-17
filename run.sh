#!/bin/bash

# LilSite-o startup script
# This script starts vLLM, FastAPI backend and UI server, then opens the browser

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

# Load .env if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default model if not set
LLM_MODEL="${LLM_MODEL:-deepseek-ai/DeepSeek-Coder-6.7B-Instruct}"

# Check if vLLM server is running, start it if not
echo -e "\n${YELLOW}Checking vLLM server...${NC}"
VLLM_PID=""
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    echo -e "${GREEN}✓ vLLM server is already running on port 8000${NC}"
else
    echo -e "${YELLOW}✗ vLLM server is not running, starting it...${NC}"
    
    # Check if virtual environment exists for vLLM (might be in .venv or separate)
    if [ -d .venv ]; then
        source .venv/bin/activate
    fi
    
    # Check if vllm is installed
    if ! python -c "import vllm" 2>/dev/null; then
        echo -e "${YELLOW}Installing vLLM...${NC}"
        pip install vllm > /tmp/lilsite_vllm_install.log 2>&1 || {
            echo -e "${RED}Failed to install vLLM. Check /tmp/lilsite_vllm_install.log${NC}"
            exit 1
        }
    fi
    
    # Start vLLM in background
    echo -e "${BLUE}Starting vLLM server with model: ${LLM_MODEL}${NC}"
    cd services/agent
    
    # Add trust-remote-code for DeepSeek models
    VLLM_FLAGS=""
    if [[ "$LLM_MODEL" == *"deepseek"* ]]; then
        VLLM_FLAGS="--trust-remote-code"
        echo -e "${YELLOW}Using --trust-remote-code flag for DeepSeek model${NC}"
    fi
    
    python -m vllm.entrypoints.openai.api_server \
        --host 0.0.0.0 \
        --port 8000 \
        --model "$LLM_MODEL" \
        $VLLM_FLAGS > /tmp/lilsite_vllm.log 2>&1 &
    VLLM_PID=$!
    cd "$SCRIPT_DIR"
    
    # Wait for vLLM to start (longer timeout for model download/initialization)
    echo -e "${YELLOW}Waiting for vLLM to start...${NC}"
    echo -e "${YELLOW}Note: First-time model download can take 5-10 minutes depending on your connection${NC}"
    echo -e "${YELLOW}Model initialization may take 1-2 minutes after download${NC}"
    MAX_WAIT=600  # 10 minutes for download + initialization
    WAITED=0
    LAST_STATUS=0
    
    while [ $WAITED -lt $MAX_WAIT ]; do
        # Check if process is still running
        if ! kill -0 $VLLM_PID 2>/dev/null; then
            echo -e "\n${RED}✗ vLLM process died during startup${NC}"
            echo -e "${YELLOW}Check /tmp/lilsite_vllm.log for errors:${NC}"
            tail -30 /tmp/lilsite_vllm.log
            exit 1
        fi
        
        # Check if server is responding
        if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
            echo -e "\n${GREEN}✓ vLLM server started (PID: $VLLM_PID)${NC}"
            break
        fi
        
        # Show progress every 30 seconds
        if [ $((WAITED % 30)) -eq 0 ] && [ $WAITED -gt 0 ]; then
            minutes=$((WAITED / 60))
            seconds=$((WAITED % 60))
            echo -e "\n${YELLOW}[${minutes}m ${seconds}s] Still initializing... (checking /tmp/lilsite_vllm.log for progress)${NC}"
        else
            echo -n "."
        fi
        
        sleep 2
        WAITED=$((WAITED + 2))
    done
    echo ""
    
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo -e "${RED}✗ vLLM server failed to start within ${MAX_WAIT}s (10 minutes)${NC}"
        echo -e "${YELLOW}This might be due to:${NC}"
        echo -e "  - Slow internet (model still downloading)"
        echo -e "  - Insufficient VRAM/RAM"
        echo -e "  - Model initialization error"
        echo -e "\n${YELLOW}Check /tmp/lilsite_vllm.log for details:${NC}"
        tail -50 /tmp/lilsite_vllm.log
        echo -e "\n${YELLOW}You can manually start vLLM and check the full log:${NC}"
        echo -e "  tail -f /tmp/lilsite_vllm.log"
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
    if pip install -r requirements.txt > /tmp/lilsite_deps.log 2>&1; then
        cd "$SCRIPT_DIR"
        echo -e "${GREEN}✓ Dependencies installed${NC}"
    else
        cd "$SCRIPT_DIR"
        echo -e "${RED}✗ Failed to install dependencies${NC}"
        echo -e "${YELLOW}Check /tmp/lilsite_deps.log for errors${NC}"
        tail -20 /tmp/lilsite_deps.log
        exit 1
    fi
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
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
    [ -n "$UI_PID" ] && kill $UI_PID 2>/dev/null || true
    [ -n "$VLLM_PID" ] && kill $VLLM_PID 2>/dev/null || true
    wait $BACKEND_PID $UI_PID $VLLM_PID 2>/dev/null || true
    echo -e "${GREEN}Servers stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Start FastAPI backend
echo -e "\n${YELLOW}Starting FastAPI backend on port 9000...${NC}"
cd services/agent/app
if uvicorn main:app --host 0.0.0.0 --port 9000 > /tmp/lilsite_backend.log 2>&1 &
then
    BACKEND_PID=$!
    cd "$SCRIPT_DIR"
    
    # Wait for backend to start
    sleep 3
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}✗ Backend failed to start${NC}"
        cat /tmp/lilsite_backend.log
        exit 1
    fi
else
    cd "$SCRIPT_DIR"
    echo -e "${RED}✗ Failed to start backend${NC}"
    exit 1
fi

# Start UI server
echo -e "\n${YELLOW}Starting UI server on port 3000...${NC}"
cd ui
if python3 -m http.server 3000 > /tmp/lilsite_ui.log 2>&1 &
then
    UI_PID=$!
    cd "$SCRIPT_DIR"
    
    # Wait for UI to start
    sleep 1
    if kill -0 $UI_PID 2>/dev/null; then
        echo -e "${GREEN}✓ UI server started (PID: $UI_PID)${NC}"
    else
        echo -e "${RED}✗ UI server failed to start${NC}"
        cat /tmp/lilsite_ui.log
        exit 1
    fi
else
    cd "$SCRIPT_DIR"
    echo -e "${RED}✗ Failed to start UI server${NC}"
    exit 1
fi

# Wait a bit more for servers to be ready
sleep 2

# Check if servers are responding
echo -e "\n${YELLOW}Verifying servers...${NC}"
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is responding${NC}"
else
    echo -e "${YELLOW}⚠ Backend might not be ready yet${NC}"
fi

if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ UI server is responding${NC}"
else
    echo -e "${YELLOW}⚠ UI might not be ready yet${NC}"
fi

# Open browser
echo -e "\n${GREEN}Opening browser...${NC}"
sleep 1
if command -v open > /dev/null; then
    # macOS
    open http://localhost:3000 2>/dev/null || true
elif command -v xdg-open > /dev/null; then
    # Linux
    xdg-open http://localhost:3000 2>/dev/null || true
elif command -v start > /dev/null; then
    # Windows (Git Bash)
    start http://localhost:3000 2>/dev/null || true
else
    echo -e "${YELLOW}Please open http://localhost:3000 in your browser${NC}"
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}LilSite-o is running!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Backend:  http://localhost:9000"
echo -e "UI:       http://localhost:3000"
echo -e "vLLM:     http://localhost:8000"
if [ -n "$VLLM_PID" ]; then
    echo -e "\n${YELLOW}Note: vLLM was started by this script (PID: $VLLM_PID)${NC}"
    echo -e "${YELLOW}It will be stopped when you press Ctrl+C${NC}"
fi
echo -e "\n${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Keep script running and monitor processes
while true; do
    # Check if processes are still running
    if [ -n "$BACKEND_PID" ] && ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}Backend process died!${NC}"
        tail -20 /tmp/lilsite_backend.log
        break
    fi
    if [ -n "$UI_PID" ] && ! kill -0 $UI_PID 2>/dev/null; then
        echo -e "${RED}UI server process died!${NC}"
        tail -20 /tmp/lilsite_ui.log
        break
    fi
    if [ -n "$VLLM_PID" ] && ! kill -0 $VLLM_PID 2>/dev/null; then
        echo -e "${RED}vLLM process died!${NC}"
        tail -20 /tmp/lilsite_vllm.log
        break
    fi
    sleep 5
done
