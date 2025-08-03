#!/bin/bash
# KBI Labs Force Deployment Script

echo "🚀 KBI Labs Force Deployment Starting..."

# Kill any existing applications on port 8000
echo "Stopping existing applications..."
sudo pkill -f "uvicorn" || true
sudo pkill -f "python.*8000" || true
sudo pkill -f "gunicorn" || true
sudo fuser -k 8000/tcp || true
sleep 5

# Navigate to project directory
cd /home/ubuntu/kbi_labs || { echo "Directory not found"; exit 1; }

# Pull latest changes
echo "Pulling latest code..."
git fetch origin
git reset --hard origin/main
git pull origin main

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install --user -r requirements-production.txt || python3 -m pip install --user -r requirements.txt

# Set environment variables
export DATABASE_URL="sqlite:///./kbi_production.db"
export PYTHONPATH="/home/ubuntu/kbi_labs:$PYTHONPATH"

# Create log directory
mkdir -p logs

# Start our specific FastAPI application
echo "Starting KBI Labs FastAPI application..."
nohup python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > logs/kbi_fastapi.log 2>&1 &

# Wait for startup
sleep 15

# Test our specific endpoints
echo "Testing deployment..."
if curl -f http://localhost:8000/health; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    cat logs/kbi_fastapi.log
    exit 1
fi

if curl -f http://localhost:8000/api/ai/status; then
    echo "✅ AI services operational"
else
    echo "⚠️ AI services not ready yet"
fi

echo "🎉 KBI Labs FastAPI deployment complete!"
