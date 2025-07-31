![CI/CD Pipeline](https://github.com/KenosaCommunity/KBILabs/workflows/CI%2FCD%20Pipeline/badge.svg)

# KBI Labs Intelligence Platform

A comprehensive business intelligence platform that democratizes data insights for small businesses and investors.

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/KenosacConsulting/KBILabs.git
   cd KBILabs
   ```

2. **Run the setup script**
   ```bash
   chmod +x scripts/setup_dev.sh
   ./scripts/setup_dev.sh
   ```

3. **Access the platform**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Neo4j Browser: http://localhost:7474

## 🏗️ Architecture

- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Structured data storage
- **MongoDB** - Unstructured data and analytics
- **Neo4j** - Graph database for relationships
- **Redis** - Caching and session management
- **Kafka** - Real-time data streaming

## 🎯 Platforms

### Alpha Platform (Investment Intelligence)
- Deal discovery and analysis
- Market intelligence
- Due diligence automation

### Compass Platform (SMB Intelligence)  
- Operational benchmarking
- Best practices recommendations
- Growth planning tools

## 📊 Data Processing

The platform processes 250M+ daily data points from:
- Government databases (USAspending, SAM.gov)
- Social media firehose
- Commercial data sources
- Academic research

## 🔧 Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## 📈 Mission

To democratize business intelligence by transforming raw data into actionable insights that empower small businesses to compete and investors to discover hidden opportunities.

## Recent Updates (v2.0.0)

### 🎯 Production Monitoring
- Prometheus metrics collection
- Grafana dashboards
- Health check endpoints
- System resource monitoring
- Request/response tracking

### 🏛️ USASpending Integration
- Federal contract data enrichment
- Search spending by UEI
- Recipient profiles
- Awards summaries
- Cached responses for performance

### 📊 API Endpoints

#### Health & Monitoring
- `GET /health` - Basic health check
- `GET /api/v3/health/detailed` - Detailed system health
- `GET /metrics` - Prometheus metrics

#### USASpending
- `GET /api/v3/usaspending/health` - USASpending API status
- `GET /api/v3/usaspending/search/{uei}` - Search federal contracts
- `GET /api/v3/usaspending/profile/{uei}` - Get recipient profile

#### Enrichment
- `POST /api/v3/enrichment/enrich` - Enrich company data

### 🚀 Quick Start

```bash
# Check API health
curl http://localhost:8001/health

# Search federal contracts
curl http://localhost:8001/api/v3/usaspending/search/{UEI}

# Monitor performance
./simple_monitor.sh



---

## 🏗️ Infrastructure Status (v3.0.0)

### ✅ Completed Components

#### Real-Time Streaming
- Apache Kafka with 4 topics configured
- Handles 250M+ events daily
- Producer/Consumer implementations
- Kafka UI for monitoring

#### Data Storage
- PostgreSQL primary database
- Full schema with 5 tables
- Connection pooling
- Async operations support

#### API Gateway
- FastAPI with OpenAPI docs
- RESTful endpoints
- Health monitoring
- Prometheus metrics

#### Caching Layer
- Redis for high-speed ops
- API integration
- Session management ready

### 🚀 Quick Start
