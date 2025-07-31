#!/bin/bash

echo "🔄 Refreshing KBI Labs Platform..."

# Check and restart services if needed
if ! pgrep -f "combined_server_v2.py" > /dev/null; then
    echo "Starting combined server..."
    cd ~/KBILabs
    python3 combined_server_v2.py &
    sleep 3
fi

if ! pgrep -f "enhanced_insights_api_fixed.py" > /dev/null; then
    echo "Starting AI insights API..."
    cd ~/KBILabs/ai_insights
    python3 enhanced_insights_api_fixed.py &
    sleep 3
fi

echo "✅ All services running!"
echo ""
echo "📊 Access your platform at:"
echo "   http://3.143.232.123:8090"
echo ""
echo "💼 Portfolio Analysis at:"
echo "   http://3.143.232.123:8090/portfolio.html"
