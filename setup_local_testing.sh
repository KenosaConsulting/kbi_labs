#!/bin/bash
# KBI Labs Local Testing Setup with Real API Keys

echo "🚀 Setting up KBI Labs local testing environment..."

# Set environment variables for this session
export CENSUS_API_KEY="70e4e3355e1b7b1a42622ba9201157bd1b105629"
export REGULATIONS_API_KEY="eOaulCdds6asIkvxR54otUJIC6badoeSynDJN68w"
export CONGRESS_API_KEY="Lt9hyLPZ5yBFUreIFDHvrMljeplEviWoHkAshNq9"
export GOVINFO_API_KEY="2y76olvQevGbWUkoWgFNAJSa1KBabOFU1FBrhWsF"
export GSA_API_KEY="MbeF6wFg5auoS4v2uy0ua3Dc1hfo5RV68uXbVAwY"
export SAM_API_KEY="Ec4gRnGckZjZmwbCtTiCyCsELua6nREcoyysaXqk"
export FEDERAL_REGISTER_BASE_URL="https://www.federalregister.gov/api/v1"

# Additional configuration
export ENVIRONMENT="local_testing"
export DEBUG="true"
export LOG_LEVEL="INFO"

echo "✅ Environment variables set!"

# Test API connection
echo "🧪 Testing API endpoints..."

# Start API in background if not running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "🚀 Starting API server..."
    python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
    API_PID=$!
    echo "API PID: $API_PID"
    sleep 5
else
    echo "✅ API already running"
fi

# Test endpoints
echo "Testing health endpoint..."
curl -s http://localhost:8000/health | jq .

echo "Testing AI status..."
curl -s http://localhost:8000/api/ai/status | jq .

echo "Testing government intelligence..."
curl -s http://localhost:8000/api/government-intelligence/procurement-opportunities | jq '.data | keys'

echo ""
echo "🎉 Local testing setup complete!"
echo "🌐 Dashboard available at: http://localhost:8081/smb_dashboard_fast.html"
echo "🔧 API available at: http://localhost:8000"
echo ""
echo "Next: Run the AWS deployment setup!"