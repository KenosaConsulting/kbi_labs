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
