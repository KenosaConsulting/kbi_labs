#!/usr/bin/env python3
"""Simple Kafka test"""
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient
import json
import time

def test_kafka():
    try:
        # Test admin connection
        admin = KafkaAdminClient(
            bootstrap_servers='localhost:9092',
            client_id='test-client'
        )
        
        # List topics
        topics = admin.list_topics()
        print(f"✅ Connected to Kafka. Found {len(topics)} topics:")
        for topic in topics:
            if not topic.startswith('_'):
                print(f"   - {topic}")
        
        # Test producer
        producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        test_message = {
            'test': True,
            'timestamp': time.time(),
            'message': 'Hello KBI Labs!'
        }
        
        producer.send('data-ingestion', value=test_message)
        producer.flush()
        print("\n✅ Successfully sent test message")
        
        # Test consumer
        consumer = KafkaConsumer(
            'data-ingestion',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=5000
        )
        
        print("\n📨 Waiting for messages...")
        message_count = 0
        for message in consumer:
            print(f"   Received: {message.value}")
            message_count += 1
            
        consumer.close()
        
        print(f"\n✅ Kafka test complete! Received {message_count} messages")
        return True
        
    except Exception as e:
        print(f"❌ Kafka test failed: {e}")
        return False

if __name__ == "__main__":
    test_kafka()
