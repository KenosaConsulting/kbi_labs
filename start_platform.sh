#!/bin/bash

echo "🚀 Starting KBI Labs Platform..."
echo "================================"

cd ~/KBILabs

# Check if services are already running
if pgrep -f "combined_server_v2.py" > /dev/null; then
    echo "⚠️  Main server already running"
else
    echo "Starting main server..."
    python3 combined_server_v2.py &
    sleep 3
fi

# Start AI insights if exists
if [ -f "ai_insights/ai_insights_api.py" ]; then
    if pgrep -f "ai_insights_api.py" > /dev/null; then
        echo "⚠️  AI insights already running"
    else
        echo "Starting AI insights..."
        cd ai_insights
        python3 ai_insights_api.py &
        cd ..
        sleep 3
    fi
fi

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Platform URLs:"
echo "   Dashboard: http://localhost:8090"
echo "   Portfolio: http://localhost:8090/portfolio.html"
echo "   API Docs: http://localhost:8090/api/health"
echo ""
echo "📝 Next steps:"
echo "   1. Run: python3 health_check.py"
echo "   2. Run: python3 load_companies_fixed.py"
echo "   3. Visit dashboard in browser"
