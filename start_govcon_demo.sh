#!/bin/bash

# KBI Labs Government Contractor Dashboard Demo Startup Script
echo "🏛️  Starting KBI Labs Government Contractor Dashboard Demo"
echo "========================================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "src/api/main.py" ]; then
    echo -e "${RED}❌ Please run this script from the KBILabs-main 2 directory${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Pre-flight checks...${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is required but not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found${NC}"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is required but not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm found${NC}"

echo -e "${BLUE}🔧 Installing dependencies...${NC}"

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt > /dev/null 2>&1
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  No requirements.txt found, skipping Python deps${NC}"
fi

# Install Node dependencies
if [ -d "kbi_dashboard" ]; then
    cd kbi_dashboard
    if [ -f "package.json" ]; then
        npm install > /dev/null 2>&1
        echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠️  No package.json found in kbi_dashboard${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠️  kbi_dashboard directory not found${NC}"
fi

echo -e "${BLUE}🚀 Starting services...${NC}"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Kill existing processes on ports if needed
if check_port 8001; then
    echo -e "${YELLOW}⚠️  Port 8001 is in use, attempting to free it...${NC}"
    pkill -f "uvicorn.*8001" 2>/dev/null || true
    sleep 2
fi

if check_port 3000; then
    echo -e "${YELLOW}⚠️  Port 3000 is in use, attempting to free it...${NC}"
    pkill -f "npm.*start" 2>/dev/null || true
    sleep 2
fi

# Start API server in background
echo -e "${BLUE}📡 Starting API server on port 8001...${NC}"
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --reload > api.log 2>&1 &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Check if API started successfully
if check_port 8001; then
    echo -e "${GREEN}✅ API server started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start API server${NC}"
    echo "Check api.log for details"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Start frontend server in background  
echo -e "${BLUE}🌐 Starting frontend server on port 3000...${NC}"
cd kbi_dashboard
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 5

# Check if frontend started successfully
if check_port 3000; then
    echo -e "${GREEN}✅ Frontend server started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start frontend server${NC}"
    echo "Check frontend.log for details"
    kill $API_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}🎉 Government Contractor Dashboard is now running!${NC}"
echo ""
echo -e "${BLUE}📍 Access Points:${NC}"
echo "   🌐 Dashboard: http://localhost:3000/government-contractor"
echo "   📚 API Docs:  http://localhost:8001/api/docs"
echo "   ❤️  Health:   http://localhost:8001/health"
echo ""
echo -e "${BLUE}🧪 Test the features:${NC}"
echo "   ./test_govcon_features.py"
echo ""
echo -e "${BLUE}📝 Features to test:${NC}"
echo "   ✓ CMMC 2.0 Compliance Dashboard"
echo "   ✓ DFARS Compliance Status"
echo "   ✓ FedRAMP Requirements"
echo "   ✓ NAICS Code Analysis"
echo "   ✓ Contract Pipeline Metrics"
echo "   ✓ Performance Analytics"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Save PIDs for cleanup
echo "$API_PID" > .api_pid
echo "$FRONTEND_PID" > .frontend_pid

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}🛑 Stopping services...${NC}"
    
    if [ -f .api_pid ]; then
        API_PID=$(cat .api_pid)
        kill $API_PID 2>/dev/null || true
        rm .api_pid
    fi
    
    if [ -f .frontend_pid ]; then
        FRONTEND_PID=$(cat .frontend_pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend_pid
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn.*8001" 2>/dev/null || true
    pkill -f "npm.*start" 2>/dev/null || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup INT TERM EXIT

# Keep script running and show logs
echo -e "${BLUE}📊 Monitoring services (Ctrl+C to stop)...${NC}"
echo ""

# Monitor both services
while true; do
    if ! check_port 8001; then
        echo -e "${RED}❌ API server stopped unexpectedly${NC}"
        break
    fi
    
    if ! check_port 3000; then
        echo -e "${RED}❌ Frontend server stopped unexpectedly${NC}"
        break
    fi
    
    sleep 10
done

cleanup