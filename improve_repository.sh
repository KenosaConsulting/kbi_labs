#!/bin/bash
# KBI Labs Repository Restructuring Script
# Run this in your current KBILabs directory

echo "🚀 Starting KBI Labs repository improvements..."

# 1. Create better folder structure within existing repo
mkdir -p src/{api,services,models,utils,config}
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts/{deployment,data,maintenance}
mkdir -p docs/{api,architecture,deployment}
mkdir -p .github/workflows

# 2. Create production-ready Docker setup
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/kbi_prod
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=kbi_prod
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
EOF

# 3. Create production Dockerfile
cat > Dockerfile.prod << 'EOF'
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Security: Create non-root user
RUN useradd -m -u 1000 kbiuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/kbiuser/.local

# Copy application code
COPY --chown=kbiuser:kbiuser . .

USER kbiuser

# Add Python packages to PATH
ENV PATH=/home/kbiuser/.local/bin:$PATH

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
EOF

# 4. Create Nginx configuration for load balancing
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream kbi_backend {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        server_name api.kbilabs.com;

        location / {
            proxy_pass http://kbi_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check endpoint
        location /nginx-health {
            access_log off;
            return 200 "healthy\n";
        }
    }
}
EOF

# 5. Create GitHub Actions CI/CD workflow
cat > .github/workflows/ci-cd.yml << 'EOF'
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:testpass@localhost/test_db
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile.prod
        push: true
        tags: |
          kbilabs/api:latest
          kbilabs/api:${{ github.sha }}
        cache-from: type=registry,ref=kbilabs/api:buildcache
        cache-to: type=registry,ref=kbilabs/api:buildcache,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.PROD_HOST }}
        username: ${{ secrets.PROD_USER }}
        key: ${{ secrets.PROD_SSH_KEY }}
        script: |
          cd /opt/kbilabs
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d --remove-orphans
          docker system prune -af
EOF

# 6. Create environment configuration
cat > src/config/settings.py << 'EOF'
from pydantic import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "KBI Labs Intelligence Platform"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/kbi_dev")
    database_pool_size: int = 20
    database_max_overflow: int = 40
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_ttl: int = 3600  # 1 hour default cache
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "development-secret-key")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External APIs
    sam_gov_api_key: str = os.getenv("SAM_GOV_API_KEY", "")
    usaspending_api_key: str = os.getenv("USASPENDING_API_KEY", "")
    
    # Rate Limiting
    rate_limit_per_hour: int = 1000
    rate_limit_burst: int = 100
    
    # Monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    log_level: str = "DEBUG" if debug else "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()
EOF

# 7. Create database migration system
cat > scripts/create_migration.py << 'EOF'
#!/usr/bin/env python3
"""
Database migration creator for KBI Labs
"""
import os
import sys
from datetime import datetime

def create_migration(name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"migrations/{timestamp}_{name}.sql"
    
    os.makedirs("migrations", exist_ok=True)
    
    template = f"""-- Migration: {name}
-- Created: {datetime.now().isoformat()}

-- UP
BEGIN;

-- Your migration SQL here

COMMIT;

-- DOWN
BEGIN;

-- Your rollback SQL here

COMMIT;
"""
    
    with open(filename, 'w') as f:
        f.write(template)
    
    print(f"Created migration: {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_migration.py <migration_name>")
        sys.exit(1)
    
    create_migration(sys.argv[1])
EOF

# 8. Create test structure
cat > tests/conftest.py << 'EOF'
import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db) -> Generator:
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
EOF

# 9. Create monitoring setup
cat > scripts/setup_monitoring.sh << 'EOF'
#!/bin/bash
# Setup Prometheus and Grafana monitoring

docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

echo "Monitoring stack deployed:"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000 (admin/admin)"
EOF

# 10. Create backup script
cat > scripts/backup_production.sh << 'EOF'
#!/bin/bash
# Production backup script

BACKUP_DIR="/backups/kbi-labs/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec postgres pg_dump -U user kbi_prod | gzip > $BACKUP_DIR/postgres_backup.sql.gz

# Backup Redis
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb $BACKUP_DIR/redis_backup.rdb

# Backup application logs
tar -czf $BACKUP_DIR/logs_backup.tar.gz /var/log/kbilabs/

# Upload to S3
aws s3 sync $BACKUP_DIR s3://kbi-labs-backups/$(date +%Y%m%d_%H%M%S)/

# Clean up old backups (keep last 30 days)
find /backups/kbi-labs -mtime +30 -type d -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR"
EOF

# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/*.py

echo "✅ Repository structure improved!"
echo ""
echo "Next steps:"
echo "1. Move your existing code into the new src/ structure"
echo "2. Update imports to match new structure"
echo "3. Create requirements.txt with versions"
echo "4. Set up environment variables in .env"
echo "5. Run: docker-compose -f docker-compose.prod.yml up"
