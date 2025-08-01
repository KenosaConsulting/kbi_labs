#!/bin/bash
echo "🔧 Final Infrastructure Fix for KBI Labs"
echo "========================================"

# Fix PostgreSQL
echo -e "\n1️⃣ Fixing PostgreSQL..."
docker exec kbi_postgres psql -U postgres << 'EOSQL'
DROP USER IF EXISTS kbi_user CASCADE;
CREATE USER kbi_user WITH PASSWORD 'kbi_secure_pass_2024' CREATEDB;
DROP DATABASE IF EXISTS kbi_labs;
CREATE DATABASE kbi_labs OWNER kbi_user;
\c kbi_labs
GRANT ALL ON SCHEMA public TO kbi_user;
ALTER DEFAULT PRIVILEGES FOR USER kbi_user IN SCHEMA public GRANT ALL ON TABLES TO kbi_user;
ALTER DEFAULT PRIVILEGES FOR USER kbi_user IN SCHEMA public GRANT ALL ON SEQUENCES TO kbi_user;
EOSQL

# Test PostgreSQL
echo -e "\n   Testing PostgreSQL connection..."
PGPASSWORD=kbi_secure_pass_2024 psql -h localhost -U kbi_user -d kbi_labs -c "SELECT 'SUCCESS' as status;" || echo "FAILED"

# Create tables
echo -e "\n   Creating tables..."
if [ -f create_kbi_tables.sql ]; then
    PGPASSWORD=kbi_secure_pass_2024 psql -h localhost -U kbi_user -d kbi_labs < create_kbi_tables.sql
else
    echo "   Warning: create_kbi_tables.sql not found"
fi

# Fix Kafka topics
echo -e "\n2️⃣ Creating Kafka topics..."
topics=("company-enrichment" "data-ingestion" "analytics-events" "ml-predictions")
for topic in "${topics[@]}"; do
    echo "   Creating topic: $topic"
    docker exec kbi_kafka kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic "$topic" \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists 2>/dev/null || echo "   Topic $topic already exists"
done

# List all topics
echo -e "\n   All Kafka topics:"
docker exec kbi_kafka kafka-topics --list --bootstrap-server localhost:9092

echo -e "\n✅ Infrastructure fix complete!"
