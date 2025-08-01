#!/bin/bash
# Complete Infrastructure Setup Script for KBI Labs
# This script sets up Kafka, PostgreSQL, and all services

echo "🚀 KBI Labs Complete Infrastructure Setup"
echo "========================================"
echo ""

# Step 1: Create the fix_kafka_and_db.sh script
echo "📝 Creating infrastructure fix script..."
cat > fix_kafka_and_db.sh << 'EOF'
#!/bin/bash
# Fix Kafka and Database Configuration Script

echo "🔧 KBI Labs Infrastructure Fix - Day 1"
echo "====================================="
echo ""

# Backup current docker-compose
echo "📦 Backing up current docker-compose.yml..."
if [ -f docker-compose.yml ]; then
    cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)
fi

# Create fixed docker-compose with Kafka enabled
echo "🚀 Creating fixed docker-compose.yml with Kafka enabled..."
cat > docker-compose.yml << 'INNER_EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: kbi_postgres
    environment:
      POSTGRES_DB: kbi_labs
      POSTGRES_USER: kbi_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-kbi_secure_pass_2024}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - kbi_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kbi_user -d kbi_labs"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:7.0
    container_name: kbi_mongodb
    environment:
      MONGO_INITDB_ROOT_USERNAME: kbi_user
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-kbi_secure_pass_2024}
      MONGO_INITDB_DATABASE: kbi_labs
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - kbi_network
    restart: unless-stopped

  neo4j:
    image: neo4j:5.11
    container_name: kbi_neo4j
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD:-kbi_secure_pass_2024}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_dbms_memory_pagecache_size: 1G
      NEO4J_dbms_memory_heap_max__size: 2G
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
    networks:
      - kbi_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: kbi_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    networks:
      - kbi_network
    restart: unless-stopped

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: kbi_zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
      - zookeeper_logs:/var/lib/zookeeper/log
    networks:
      - kbi_network
    restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: kbi_kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_LOG_SEGMENT_BYTES: 1073741824
      KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS: 300000
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - kbi_network
    restart: unless-stopped

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kbi_kafka_ui
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: kbi_cluster
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
      KAFKA_CLUSTERS_0_ZOOKEEPER: zookeeper:2181
    networks:
      - kbi_network
    restart: unless-stopped

volumes:
  postgres_data:
  mongo_data:
  neo4j_data:
  redis_data:
  kafka_data:
  zookeeper_data:
  zookeeper_logs:

networks:
  kbi_network:
    driver: bridge
INNER_EOF

echo "✅ Docker Compose file created"
EOF

# Make the script executable
chmod +x fix_kafka_and_db.sh

# Step 2: Create PostgreSQL initialization script
echo "📄 Creating PostgreSQL initialization script..."
mkdir -p scripts
cat > scripts/init_db.sql << 'EOF'
-- KBI Labs PostgreSQL Initialization Script

-- Create schemas
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS ml_features;

-- Create main companies table
CREATE TABLE IF NOT EXISTS public.companies (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) UNIQUE NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    dba_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    country VARCHAR(100) DEFAULT 'USA',
    
    -- Financial metrics
    annual_revenue DECIMAL(15,2),
    federal_contracts_value DECIMAL(15,2),
    grants_received DECIMAL(15,2),
    
    -- Scores
    pe_investment_score FLOAT,
    business_health_grade VARCHAR(2),
    innovation_score FLOAT,
    growth_potential_score FLOAT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_enriched_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_companies_state ON companies(state);
CREATE INDEX IF NOT EXISTS idx_companies_pe_score ON companies(pe_investment_score);
CREATE INDEX IF NOT EXISTS idx_companies_health_grade ON companies(business_health_grade);

-- Create enrichment tracking table
CREATE TABLE IF NOT EXISTS public.enrichment_history (
    id SERIAL PRIMARY KEY,
    uei VARCHAR(12) NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    data JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (uei) REFERENCES companies(uei)
);

CREATE INDEX IF NOT EXISTS idx_enrichment_uei_source ON enrichment_history(uei, source);
CREATE INDEX IF NOT EXISTS idx_enrichment_created_at ON enrichment_history(created_at);

-- Create enriched companies table for streaming pipeline
CREATE TABLE IF NOT EXISTS public.enriched_companies (
    uei VARCHAR(12) PRIMARY KEY,
    data JSONB NOT NULL,
    enrichment_timestamp TIMESTAMP NOT NULL,
    data_quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO kbi_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO kbi_user;
GRANT ALL ON SCHEMA analytics TO kbi_user;
GRANT ALL ON SCHEMA staging TO kbi_user;
GRANT ALL ON SCHEMA ml_features TO kbi_user;
EOF

# Step 3: Create Kafka initialization script
echo "📨 Creating Kafka topic initialization script..."
cat > scripts/init_kafka_topics.sh << 'EOF'
#!/bin/bash
# Initialize Kafka topics for KBI Labs

echo "Creating Kafka topics..."

# Wait for Kafka to be ready
sleep 10

# Create topics
docker exec kbi_kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic company-enrichment \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

docker exec kbi_kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic data-ingestion \
  --partitions 5 \
  --replication-factor 1 \
  --if-not-exists

docker exec kbi_kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic analytics-events \
  --partitions 3 \
  --replication-factor 1 \
  --if-not-exists

docker exec kbi_kafka kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic ml-predictions \
  --partitions 2 \
  --replication-factor 1 \
  --if-not-exists

echo "Kafka topics created successfully!"

# List all topics
docker exec kbi_kafka kafka-topics --list --bootstrap-server localhost:9092
EOF

chmod +x scripts/init_kafka_topics.sh

# Step 4: Fix imports in Python files
echo "🐍 Fixing Python imports..."

# Fix kafka_infrastructure.py
sed -i '1s/^/#!\/usr\/bin\/env python3\n/' kafka_infrastructure.py 2>/dev/null || true

# Fix database_manager.py  
sed -i '1s/^/#!\/usr\/bin\/env python3\n/' database_manager.py 2>/dev/null || true

# Fix streaming_pipeline.py
sed -i '1s/^/#!\/usr\/bin\/env python3\n/' streaming_pipeline.py 2>/dev/null || true

# Fix api_gateway.py - need to add json import
sed -i '/import logging/a import json' api_gateway.py 2>/dev/null || true

# Step 5: Create test scripts
echo "🧪 Creating test scripts..."

cat > test_infrastructure.py << 'EOF'
#!/usr/bin/env python3
"""Test infrastructure components"""
import asyncio
import sys

async def test_kafka():
    """Test Kafka connectivity"""
    print("Testing Kafka...")
    try:
        from kafka_infrastructure import KafkaInfrastructure
        kafka = KafkaInfrastructure()
        if kafka.initialize():
            health = kafka.health_check()
            print(f"✅ Kafka is healthy: {health['status']}")
            return True
    except Exception as e:
        print(f"❌ Kafka test failed: {e}")
        return False

async def test_database():
    """Test PostgreSQL connectivity"""
    print("\nTesting PostgreSQL...")
    try:
        from database_manager import db_manager
        await db_manager.initialize()
        health = await db_manager.health_check()
        print(f"✅ PostgreSQL is healthy: {health['status']}")
        await db_manager.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False

async def test_redis():
    """Test Redis connectivity"""
    print("\nTesting Redis...")
    try:
        import redis
        r = redis.from_url('redis://localhost:6379')
        r.ping()
        print("✅ Redis is healthy")
        return True
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔧 KBI Labs Infrastructure Tests")
    print("================================\n")
    
    # Run tests
    kafka_ok = await test_kafka()
    db_ok = await test_database()
    redis_ok = await test_redis()
    
    print("\n📊 Test Summary:")
    print(f"  Kafka: {'✅ Passed' if kafka_ok else '❌ Failed'}")
    print(f"  PostgreSQL: {'✅ Passed' if db_ok else '❌ Failed'}")
    print(f"  Redis: {'✅ Passed' if redis_ok else '❌ Failed'}")
    
    if all([kafka_ok, db_ok, redis_ok]):
        print("\n🎉 All tests passed! Infrastructure is ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the services.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
EOF

# Step 6: Create environment file
echo "🔐 Creating environment configuration..."
cat > .env << 'EOF'
# KBI Labs Environment Configuration

# Database Passwords
POSTGRES_PASSWORD=kbi_secure_pass_2024
MONGO_PASSWORD=kbi_secure_pass_2024
NEO4J_PASSWORD=kbi_secure_pass_2024

# Database URLs
DATABASE_URL=postgresql://kbi_user:kbi_secure_pass_2024@localhost:5432/kbi_labs
REDIS_URL=redis://localhost:6379
KAFKA_BROKER=localhost:9092

# API Keys (add your real keys here)
SAM_GOV_API_KEY=your_sam_gov_key_here
USASPENDING_API_KEY=public_api_no_key_needed
USPTO_API_KEY=your_uspto_key_here
NSF_API_KEY=your_nsf_key_here

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
EOF

# Step 7: Create startup script
echo "🚀 Creating startup script..."
cat > start_services.sh << 'EOF'
#!/bin/bash
# Start all KBI Labs services

echo "🚀 Starting KBI Labs Services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Run the infrastructure fix
./fix_kafka_and_db.sh

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose down

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 30

# Initialize Kafka topics
echo "📨 Initializing Kafka topics..."
./scripts/init_kafka_topics.sh

# Run tests
echo "🧪 Running infrastructure tests..."
python3 test_infrastructure.py

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Available services:"
echo "  • API Gateway: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/api/docs"
echo "  • Kafka UI: http://localhost:8080"
echo "  • PostgreSQL: localhost:5432"
echo "  • MongoDB: localhost:27017"
echo "  • Neo4j: http://localhost:7474"
echo "  • Redis: localhost:6379"
echo ""
echo "To start the API Gateway:"
echo "  python3 api_gateway.py"
EOF

chmod +x start_services.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Run: ./start_services.sh"
echo "2. Wait for all services to start"
echo "3. Run: python3 api_gateway.py"
echo "4. Visit: http://localhost:8000/api/docs"
