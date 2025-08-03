#!/usr/bin/env python3
"""
Force deploy the correct KBI Labs FastAPI application
This script will create a simple deployment command that forces our app to run
"""

import subprocess
import time
import requests
import sys

def create_deployment_script():
    """Create a deployment script"""
    deploy_script = """#!/bin/bash
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
"""
    
    with open('deploy_script.sh', 'w') as f:
        f.write(deploy_script)
    
    return 'deploy_script.sh'

def test_current_deployment():
    """Test what's currently running"""
    print("🔍 Testing current deployment...")
    
    try:
        response = requests.get("http://3.143.232.123:8000/", timeout=10)
        data = response.json()
        print(f"Current app: {data.get('message', data.get('title', 'Unknown'))}")
        print(f"Version: {data.get('version', 'Unknown')}")
        
        # Check if our AI endpoint exists
        try:
            ai_response = requests.get("http://3.143.232.123:8000/api/ai/status", timeout=5)
            if ai_response.status_code == 200:
                print("✅ Our FastAPI app is running!")
                return True
            else:
                print(f"❌ Wrong app running (AI endpoint: {ai_response.status_code})")
                return False
        except:
            print("❌ Our FastAPI app not running (AI endpoint not found)")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 KBI LABS DEPLOYMENT FIX")
    print("=" * 60)
    
    # Test current state
    if test_current_deployment():
        print("✅ Correct application is already running!")
        return
    
    # Create deployment script
    script_path = create_deployment_script()
    print(f"✅ Created deployment script: {script_path}")
    
    print(f"""
📋 DEPLOYMENT INSTRUCTIONS:

The issue is that a different application (API Gateway v3.0.0) is running 
instead of our KBI Labs FastAPI application with AI services.

To fix this, you need to run the deployment script on the EC2 instance:

1. SSH into your EC2 instance:
   ssh -i your-key.pem ubuntu@3.143.232.123

2. Copy the deployment script to the server:
   scp -i your-key.pem {script_path} ubuntu@3.143.232.123:/home/ubuntu/

3. Run the deployment script:
   chmod +x /home/ubuntu/{script_path}
   /home/ubuntu/{script_path}

4. Verify deployment:
   curl http://localhost:8000/api/ai/status

This will:
• Stop any conflicting applications
• Pull our latest code with AI services
• Install proper dependencies
• Start our FastAPI application specifically
• Test that AI endpoints are working

The script is designed to be safe and will show detailed logs if anything fails.
""")

if __name__ == "__main__":
    main()