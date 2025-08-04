# KBI Labs Data Enrichment System - Quick Start Guide

## Current Directory
You're working in: `/Users/oogwayuzumaki/kbi_labs`

## What We've Built

### ✅ Complete Backend System
- **Database Schema**: PostgreSQL tables for data enrichment (`backend/database/migrations/001_add_data_enrichment_tables.sql`)
- **API Routes**: FastAPI endpoints (`backend/api/data_enrichment_routes.py`)
- **Data Services**: Government data pipeline integration (`backend/services/data_enrichment_service.py`)
- **Pipeline Components**: Budget, personnel, organizational data collectors

### ✅ Complete Frontend System
- **Main Component**: Agency Intelligence Mapper (`frontend/components/AgencyIntelligenceMapper.jsx`)
- **Progress Modal**: Real-time job progress (`frontend/components/EnrichmentProgressModal.jsx`)
- **Data Visualization**: Comprehensive data display (`frontend/components/AgencyDataVisualization.jsx`)
- **Quality Indicators**: Data quality metrics (`frontend/components/DataQualityIndicator.jsx`)
- **WebSocket Hook**: Real-time updates (`frontend/hooks/useEnrichmentWebSocket.js`)
- **API Service**: Complete API client (`frontend/services/enrichmentApi.js`)
- **Utilities**: Formatters and helpers (`frontend/utils/formatters.js`)

## Prerequisites to Install

### 1. PostgreSQL
**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**macOS (Postgres.app):**
- Download from https://postgresapp.com/
- Install and start the app

### 2. Docker (Alternative to PostgreSQL)
- Download Docker Desktop from https://docker.com/products/docker-desktop
- Install and start Docker

### 3. Node.js (for frontend testing)
```bash
brew install node
```

## Setup Steps

### Step 1: Set up Python Environment
```bash
cd /Users/oogwayuzumaki/kbi_labs

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn asyncpg python-dotenv aiohttp pandas requests websockets python-multipart
```

### Step 2: Set up Database

**Option A: Using PostgreSQL directly**
```bash
# Create database and user
psql postgres
CREATE DATABASE kbi_labs_enrichment;
CREATE USER kbi_user WITH PASSWORD 'kbi_password';
GRANT ALL PRIVILEGES ON DATABASE kbi_labs_enrichment TO kbi_user;
\q

# Run migrations
psql -U kbi_user -d kbi_labs_enrichment -f backend/database/migrations/001_add_data_enrichment_tables.sql
```

**Option B: Using Docker**
```bash
# Start PostgreSQL container
docker run --name kbi_postgres \
  -e POSTGRES_DB=kbi_labs_enrichment \
  -e POSTGRES_USER=kbi_user \
  -e POSTGRES_PASSWORD=kbi_password \
  -p 5432:5432 \
  -d postgres:15

# Wait a moment for startup, then run migrations
docker exec -i kbi_postgres psql -U kbi_user -d kbi_labs_enrichment < backend/database/migrations/001_add_data_enrichment_tables.sql
```

### Step 3: Configure Environment
Create `.env` file:
```bash
cat > .env << 'EOF'
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=kbi_labs_enrichment
DATABASE_USER=kbi_user
DATABASE_PASSWORD=kbi_password
DATABASE_POOL_MIN_SIZE=5
DATABASE_POOL_MAX_SIZE=20
DATABASE_COMMAND_TIMEOUT=60
ENRICHMENT_MAX_CONCURRENT_JOBS=3
ENRICHMENT_JOB_TIMEOUT_MINUTES=30
ENRICHMENT_CACHE_DEFAULT_HOURS=168
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
DEBUG=true
EOF
```

### Step 4: Test the Backend
Create and run test server:
```bash
cat > test_server.py << 'EOF'
import uvicorn
import sys
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

from api.data_enrichment_routes import router as enrichment_router

app = FastAPI(title="KBI Labs Data Enrichment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(enrichment_router)

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("test_server:app", host="0.0.0.0", port=8000, reload=True)
EOF

# Run the server
python test_server.py
```

### Step 5: Test the System

**Backend API Tests:**
```bash
# In another terminal window
# Test health endpoint
curl http://localhost:8000/health

# Test supported agencies
curl http://localhost:8000/api/data-enrichment/agencies

# Test enrichment request
curl -X POST http://localhost:8000/api/data-enrichment/enrich \
  -H "Content-Type: application/json" \
  -d '{
    "agency_code": "9700",
    "agency_name": "Department of Defense",
    "data_types": ["budget", "personnel"],
    "enrichment_depth": "basic"
  }'
```

**Frontend Testing:**
1. Open `frontend/components/AgencyIntelligenceMapper.jsx` in your preferred React development environment
2. Or create a simple HTML test page to interact with the API

## System Architecture

### Backend Structure
```
backend/
├── api/
│   └── data_enrichment_routes.py      # FastAPI routes
├── services/
│   └── data_enrichment_service.py     # Core business logic
├── data_enrichment/
│   ├── government_data_pipeline.py    # Main data pipeline
│   ├── budget_extraction_pipeline.py  # Budget data collector
│   ├── personnel_data_collector.py    # Personnel data collector
│   ├── organizational_chart_scraper.py # Org structure collector
│   └── data_validation_system.py      # Data quality validation
└── database/
    ├── connection.py                   # Database connection management
    └── migrations/
        └── 001_add_data_enrichment_tables.sql # Database schema
```

### Frontend Structure
```
frontend/
├── components/
│   ├── AgencyIntelligenceMapper.jsx   # Main component
│   ├── EnrichmentProgressModal.jsx    # Progress tracking
│   ├── DataQualityIndicator.jsx       # Quality metrics
│   └── AgencyDataVisualization.jsx    # Data display
├── hooks/
│   └── useEnrichmentWebSocket.js       # Real-time updates
├── services/
│   └── enrichmentApi.js                # API client
└── utils/
    └── formatters.js                   # Data formatting utilities
```

## Key Features

### 1. **Real-time Data Enrichment**
- Asynchronous job processing
- WebSocket progress updates
- Quality scoring and validation

### 2. **Government Data Sources**
- USASpending.gov API integration
- Treasury API connections  
- Personnel directory scraping
- Organizational chart extraction

### 3. **Intelligent Caching**
- Configurable expiration policies
- Quality-based cache invalidation
- Access tracking and metrics

### 4. **Agency Intelligence Mapping**
- Budget analysis and line items
- Key personnel identification
- Organizational structure mapping
- Contract and procurement data

## Troubleshooting

### Database Connection Issues
```bash
# Test database connection
psql -U kbi_user -d kbi_labs_enrichment -c "SELECT version();"

# Or with Docker
docker exec kbi_postgres psql -U kbi_user -d kbi_labs_enrichment -c "SELECT version();"
```

### API Server Issues
```bash
# Check if port 8000 is available
lsof -i :8000

# View server logs
python test_server.py  # Check console output
```

### Missing Dependencies
```bash
# Reinstall Python packages
pip install -r requirements.txt

# Or install individually
pip install fastapi uvicorn asyncpg python-dotenv
```

## Next Steps

1. **Install Prerequisites** (PostgreSQL/Docker, Node.js)
2. **Run Setup Steps** above
3. **Test Basic Functionality** with curl commands
4. **Integrate with Frontend** using React or simple HTML
5. **Configure Real Government APIs** for production use

The system is fully built and ready to run once you have the prerequisites installed!