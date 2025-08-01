#!/bin/bash
# Start all KBI Labs services

echo "Starting KBI Labs services..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
cd ai_insights
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Copy .env.example to .env and add your OpenAI API key"
    cp .env.example .env
fi

# Start the main API
echo "Starting Main API on port 5000..."
cd ../kbi_api
python3 app.py &
MAIN_API_PID=$!
echo "Main API PID: $MAIN_API_PID"

# Start the AI insights API
echo "Starting AI Insights API on port 5001..."
cd ../ai_insights
python3 ai_insights_api.py &
AI_API_PID=$!
echo "AI API PID: $AI_API_PID"

# Start the web server
echo "Starting web server on port 8090..."
cd ../kbi_dashboard
python3 -m http.server 8090 &
WEB_PID=$!
echo "Web server PID: $WEB_PID"

echo ""
echo "All services started!"
echo "Dashboard: http://localhost:8090"
echo "Main API: http://localhost:5000"
echo "AI Insights API: http://localhost:5001"
echo ""
echo "To stop all services, run: pkill -f 'python3'"

# Keep script running
wait
