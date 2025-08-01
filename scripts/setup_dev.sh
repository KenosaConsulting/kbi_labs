#!/bin/bash

echo "🚀 Setting up KBI Labs development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    sudo apt update
    sudo apt install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Please log out and back in for group changes to take effect."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Installing..."
    sudo apt install -y docker-compose
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update the .env file with your actual configuration values"
fi

# Create necessary directories
mkdir -p data/uploads
mkdir -p data/exports
mkdir -p logs

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 45

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo "✅ Development environment setup complete!"
echo ""
echo "🌐 Services available at:"
echo "  • API documentation: http://localhost:8000/docs"
echo "  • API health check: http://localhost:8000/health"
echo "  • Neo4j browser: http://localhost:7474"
echo "  • Alpha platform: http://localhost:8000/api/v1/alpha/status"
echo "  • Compass platform: http://localhost:8000/api/v1/compass/status"
echo ""
echo "📊 Database connections:"
echo "  • PostgreSQL: localhost:5432"
echo "  • MongoDB: localhost:27017"
echo "  • Neo4j: localhost:7687"
echo "  • Redis: localhost:6379"
echo "  • Kafka: localhost:9092"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Access API docs at http://localhost:8000/docs"
echo "3. Start building your data pipelines!"
