#!/bin/bash
echo "🚀 Starting KBI Labs Infrastructure"
echo "==================================="

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install it first."
    exit 1
fi

# Stop and remove existing containers
echo "🧹 Cleaning up old containers..."
docker-compose down 2>/dev/null || true

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting 30 seconds for services to start..."
sleep 30

# Show what's running
echo "📊 Running services:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Initialize PostgreSQL
echo -e "\n🔧 Initializing PostgreSQL..."
docker exec kbi_postgres psql -U postgres -c "CREATE USER kbi_user WITH PASSWORD 'kbi_secure_pass_2024';" 2>/dev/null || true
docker exec kbi_postgres psql -U postgres -c "CREATE DATABASE kbi_labs OWNER kbi_user;" 2>/dev/null || true
docker exec kbi_postgres psql -U postgres -c "GRANT ALL ON DATABASE kbi_labs TO kbi_user;" 2>/dev/null || true

# Test connection
if docker exec kbi_postgres psql -U kbi_user -d kbi_labs -c "SELECT 1" &>/dev/null; then
    echo "✅ PostgreSQL is ready!"
else
    echo "❌ PostgreSQL connection failed"
fi

# Initialize Kafka topics
echo -e "\n🔧 Creating Kafka topics..."
sleep 10

for topic in company-enrichment data-ingestion analytics-events ml-predictions; do
    docker exec kbi_kafka kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic $topic \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists 2>/dev/null || true
done

# List topics
echo -e "\n📋 Kafka topics:"
docker exec kbi_kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null || echo "Kafka not ready yet"

echo -e "\n✅ Infrastructure setup complete!"
echo -e "\n📍 Services available at:"
echo "  • Redis: localhost:6379"
echo "  • PostgreSQL: localhost:5432 (user: kbi_user, password: kbi_secure_pass_2024)"
echo "  • Kafka: localhost:9092"
echo "  • Kafka UI: http://localhost:8080"
echo -e "\nRun 'python3 test_current_setup.py' to verify everything is working."
