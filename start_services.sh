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
