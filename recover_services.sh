#!/bin/bash
echo "🔧 Recovering KBI Labs services..."

# Stop everything
docker-compose down
pkill -f "api_gateway" || true

# Clean up
docker system prune -f

# Start services
docker-compose up -d

# Wait
echo "⏳ Waiting for services..."
sleep 40

# Show status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Start API
echo "🚀 Starting API..."
nohup python3 api_gateway_fixed.py > api.log 2>&1 &

sleep 5

# Test
echo "🧪 Testing services..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo "✅ Recovery complete!"
