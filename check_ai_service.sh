
#!/bin/bash

echo "🔍 Checking AI Insights Service..."
echo "=================================="

# Check what's running on common AI ports
echo ""
echo "📡 Checking ports:"
for port in 5000 5001 5002 8095 8096; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "✅ Port $port is in use"
        # Try to access it
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/api/health | grep -q "200"; then
            echo "   └─ AI service responding on port $port!"
        fi
    else
        echo "⚠️  Port $port is free"
    fi
done

echo ""
echo "📝 Running processes:"
ps aux | grep -E "(ai_insights|insight)" | grep -v grep

echo ""
echo "🔧 To restart AI service:"
echo "   pkill -f ai_insights_api.py"
echo "   cd ~/KBILabs/ai_insights && python3 ai_insights_api.py &"
