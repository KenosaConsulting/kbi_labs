#!/bin/bash
# KBI Labs Context-Aware Intelligence Platform Setup
# This script sets up the complete DSBS processing pipeline with context-aware API

set -e  # Exit on error

echo "🚀 KBI Labs Intelligence Platform Setup"
echo "======================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Must run from KBILabs project root directory"
    exit 1
fi

# Step 1: Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p data/dsbs_raw
mkdir -p data/dsbs_processed
mkdir -p src/data_processors
mkdir -p src/api/v2
mkdir -p logs
mkdir -p scripts

# Step 2: Save the processor script
echo "💾 Creating DSBS processor with context awareness..."
cat > src/data_processors/dsbs_processor.py << 'EOF'
# [Insert the full dsbs_processor.py content from the first artifact]
EOF

# Step 3: Save the API endpoints
echo "🌐 Creating context-aware API endpoints..."
cat > src/api/v2/intelligence.py << 'EOF'
# [Insert the full intelligence.py content from the second artifact]
EOF

# Step 4: Update main.py to include new routes
echo "🔧 Updating main application..."
cat > src/main_update.py << 'EOF'
# Add this to your existing main.py

from src.api.v2.intelligence import router as intelligence_router

# Add to your FastAPI app
app.include_router(intelligence_router)

# Add startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Initializing KBI Labs Intelligence Platform...")
    
    # Test database connections
    try:
        # Test PostgreSQL
        from sqlalchemy import create_engine
        engine = create_engine(os.getenv('DATABASE_URL'))
        engine.connect()
        logger.info("✅ PostgreSQL connected")
        
        # Test MongoDB
        from pymongo import MongoClient
        mongo = MongoClient(os.getenv('MONGODB_URL'))
        mongo.server_info()
        logger.info("✅ MongoDB connected")
        
        # Test Redis
        import redis
        r = redis.from_url(os.getenv('REDIS_URL'))
        r.ping()
        logger.info("✅ Redis connected")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
EOF

# Step 5: Install additional Python packages
echo "📦 Installing additional dependencies..."
docker exec -it kbi_api pip install \
    pandas==2.0.3 \
    openpyxl==3.1.2 \
    numpy==1.24.3 \
    redis==4.6.0 \
    pymongo==4.4.1 \
    cachetools==5.3.1 \
    pyjwt==2.8.0

# Step 6: Create data upload script
echo "📤 Creating data upload helper..."
cat > scripts/upload_dsbs_data.sh << 'EOF'
#!/bin/bash
# Helper script to upload DSBS CSV files

echo "📤 DSBS Data Upload Helper"
echo "========================"

if [ $# -eq 0 ]; then
    echo "Usage: ./upload_dsbs_data.sh path/to/csv/files/*.csv"
    exit 1
fi

# Upload each file
for file in "$@"; do
    if [ -f "$file" ]; then
        echo "Uploading $file..."
        docker cp "$file" kbi_api:/app/data/dsbs_raw/
        echo "✅ Uploaded $(basename "$file")"
    else
        echo "❌ File not found: $file"
    fi
done

echo "✅ Upload complete!"
EOF

chmod +x scripts/upload_dsbs_data.sh

# Step 7: Create processing script
echo "⚙️ Creating processing runner..."
cat > scripts/run_dsbs_processing.sh << 'EOF'
#!/bin/bash
# Run DSBS processing pipeline

echo "🔄 Running DSBS Processing Pipeline"
echo "=================================="

# Run inside container
docker exec -it kbi_api python -m src.data_processors.dsbs_processor

echo "✅ Processing complete!"
EOF

chmod +x scripts/run_dsbs_processing.sh

# Step 8: Create JWT token generator for testing
echo "🔐 Creating JWT token generator..."
cat > scripts/generate_test_tokens.py << 'EOF'
#!/usr/bin/env python3
"""Generate test JWT tokens for different user contexts"""

import jwt
from datetime import datetime, timedelta

JWT_SECRET = "your-secret-key"  # Same as in API
JWT_ALGORITHM = "HS256"

def generate_token(user_type, subscription_tier="professional"):
    payload = {
        "sub": f"test-{user_type.lower()}-user",
        "aud": "alpha" if user_type == "PE_FIRM" else "compass",
        "context": {
            "user_type": user_type,
            "firm_id": "test-firm-123",
            "permissions": ["read", "analyze", "export"],
            "subscription_tier": subscription_tier,
            "preferences": {
                "default_view": "acquisition" if user_type == "PE_FIRM" else "operations",
                "risk_tolerance": "moderate"
            }
        },
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

# Generate tokens
print("🔐 Test JWT Tokens")
print("==================")
print()

pe_token = generate_token("PE_FIRM", "enterprise")
print("PE Firm Token (Enterprise):")
print(pe_token)
print()

smb_token = generate_token("SMB_OWNER", "professional")
print("SMB Owner Token (Professional):")
print(smb_token)
print()

api_token = generate_token("API_DEVELOPER", "enterprise")
print("API Developer Token:")
print(api_token)
print()

print("Usage:")
print('curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v2/companies/{uei}/intelligence')
EOF

chmod +x scripts/generate_test_tokens.py

# Step 9: Create API test script
echo "🧪 Creating API test script..."
cat > scripts/test_context_api.sh << 'EOF'
#!/bin/bash
# Test context-aware API responses

echo "🧪 Testing Context-Aware API"
echo "==========================="

# Generate tokens
echo "Generating test tokens..."
PE_TOKEN=$(docker exec kbi_api python scripts/generate_test_tokens.py | grep -A1 "PE Firm Token" | tail -1)
SMB_TOKEN=$(docker exec kbi_api python scripts/generate_test_tokens.py | grep -A1 "SMB Owner Token" | tail -1)

# Test PE context
echo ""
echo "Testing PE Firm Context:"
echo "------------------------"
curl -s -H "Authorization: Bearer $PE_TOKEN" \
     http://localhost:8000/api/v2/companies/TEST123/intelligence | \
     python -m json.tool

# Test SMB context
echo ""
echo "Testing SMB Owner Context:"
echo "--------------------------"
curl -s -H "Authorization: Bearer $SMB_TOKEN" \
     http://localhost:8000/api/v2/companies/TEST123/intelligence | \
     python -m json.tool

# Test search endpoint
echo ""
echo "Testing Search (PE Context):"
echo "----------------------------"
curl -s -H "Authorization: Bearer $PE_TOKEN" \
     "http://localhost:8000/api/v2/intelligence/search?state=FL&min_succession_risk=7" | \
     python -m json.tool
EOF

chmod +x scripts/test_context_api.sh

# Step 10: Create monitoring dashboard
echo "📊 Creating monitoring setup..."
cat > docker-compose.override.yml << 'EOF'
# Additional services for monitoring

services:
  # API metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    
  # Visualization
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
EOF

# Step 11: Create quick start guide
echo "📚 Creating quick start guide..."
cat > QUICKSTART.md << 'EOF'
# KBI Labs Context-Aware Intelligence Platform - Quick Start

## 1. Upload DSBS Data
```bash
./scripts/upload_dsbs_data.sh path/to/your/All_DSBS_processed_chunk_*.csv
```

## 2. Process Data
```bash
./scripts/run_dsbs_processing.sh
```

## 3. Generate Test Tokens
```bash
python scripts/generate_test_tokens.py
```

## 4. Test API Endpoints

### PE Firm View
```bash
curl -H "Authorization: Bearer <PE_TOKEN>" \
     http://localhost:8000/api/v2/companies/{UEI}/intelligence
```

### SMB Owner View
```bash
curl -H "Authorization: Bearer <SMB_TOKEN>" \
     http://localhost:8000/api/v2/companies/{UEI}/intelligence
```

### Search High-Risk Companies (PE Only)
```bash
curl -H "Authorization: Bearer <PE_TOKEN>" \
     "http://localhost:8000/api/v2/intelligence/search?min_succession_risk=7&state=FL"
```

## 5. Access Documentation
- API Docs: http://localhost:8000/docs
- Monitoring: http://localhost:3000 (admin/admin)

## Context-Aware Features

The API automatically adjusts responses based on user type:

- **PE Firms** see: Valuation multiples, acquisition scores, due diligence flags
- **SMB Owners** see: Health grades, peer comparisons, improvement actions
- **API Developers** see: Raw data with all calculations

## Subscription Tiers

- **Free**: 10 requests/min, basic features
- **Professional**: 50 requests/min, peer benchmarking
- **Enterprise**: 500 requests/min, all features + overrides
EOF

# Step 12: Final setup
echo "🔧 Finalizing setup..."

# Restart services to load new code
docker-compose restart api

echo ""
echo "✅ Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Upload your DSBS CSV files:"
echo "   ./scripts/upload_dsbs_data.sh /path/to/All_DSBS_processed_chunk_*.csv"
echo ""
echo "2. Run the processing pipeline:"
echo "   ./scripts/run_dsbs_processing.sh"
echo ""
echo "3. Test the API:"
echo "   ./scripts/test_context_api.sh"
echo ""
echo "4. View API documentation:"
echo "   http://your-ec2-ip:8000/docs"
echo ""
echo "📚 See QUICKSTART.md for detailed usage instructions"
