#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Kafka Infrastructure Implementation for KBI Labs
Handles all Kafka-related operations for the predictive analytics pipeline
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError
from kafka.structs import TopicPartition
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaTopics(Enum):
    """Kafka topic definitions"""
    COMPANY_ENRICHMENT = "company-enrichment"
    DATA_INGESTION = "data-ingestion"
    ANALYTICS_EVENTS = "analytics-events"
    ML_PREDICTIONS = "ml-predictions"
    REAL_TIME_SCORING = "real-time-scoring"
    AUDIT_TRAIL = "audit-trail"


@dataclass
class EnrichmentRequest:
    """Data class for enrichment requests"""
    uei: str
    company_name: str
    request_id: str = None
    enrichment_sources: List[str] = None
    priority: str = "normal"
    metadata: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.enrichment_sources:
            self.enrichment_sources = ["sam_gov", "usaspending", "patents", "nsf"]


@dataclass
class AnalyticsEvent:
    """Data class for analytics events"""
    event_type: str
    entity_id: str
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class KafkaInfrastructure:
    """Main Kafka infrastructure class"""
    
    def __init__(self, 
                 bootstrap_servers: str = 'localhost:9092',
                 redis_url: str = 'redis://localhost:6379'):
        self.bootstrap_servers = bootstrap_servers
        self.redis_client = redis.from_url(redis_url)
        self.admin_client = None
        self.producers = {}
        self.consumers = {}
        
    def initialize(self):
        """Initialize Kafka infrastructure"""
        try:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='kbi-admin'
            )
            self._create_topics()
            self._initialize_producers()
            logger.info("Kafka infrastructure initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Kafka: {e}")
            return False
    
    def _create_topics(self):
        """Create all required Kafka topics"""
        topics = [
            NewTopic(
                name=KafkaTopics.COMPANY_ENRICHMENT.value,
                num_partitions=3,
                replication_factor=1,
                config={
                    'retention.ms': '604800000',  # 7 days
                    'compression.type': 'snappy'
                }
            ),
            NewTopic(
                name=KafkaTopics.DATA_INGESTION.value,
                num_partitions=5,
                replication_factor=1,
                config={
                    'retention.ms': '259200000',  # 3 days
                    'compression.type': 'lz4'
                }
            ),
            NewTopic(
                name=KafkaTopics.ANALYTICS_EVENTS.value,
                num_partitions=3,
                replication_factor=1,
                config={
                    'retention.ms': '2592000000',  # 30 days
                    'compression.type': 'snappy'
                }
            ),
            NewTopic(
                name=KafkaTopics.ML_PREDICTIONS.value,
                num_partitions=2,
                replication_factor=1,
                config={
                    'retention.ms': '1209600000',  # 14 days
                    'compression.type': 'snappy'
                }
            ),
            NewTopic(
                name=KafkaTopics.REAL_TIME_SCORING.value,
                num_partitions=4,
                replication_factor=1,
                config={
                    'retention.ms': '86400000',  # 1 day
                    'compression.type': 'lz4'
                }
            ),
            NewTopic(
                name=KafkaTopics.AUDIT_TRAIL.value,
                num_partitions=1,
                replication_factor=1,
                config={
                    'retention.ms': '7776000000',  # 90 days
                    'compression.type': 'gzip',
                    'cleanup.policy': 'compact'
                }
            )
        ]
        
        try:
            self.admin_client.create_topics(topics, validate_only=False)
            logger.info(f"Created {len(topics)} Kafka topics")
        except TopicAlreadyExistsError:
            logger.info("Topics already exist")
        except Exception as e:
            logger.error(f"Error creating topics: {e}")
    
    def _initialize_producers(self):
        """Initialize Kafka producers with optimized settings"""
        producer_config = {
            'bootstrap_servers': self.bootstrap_servers,
            'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            'compression_type': 'snappy',
            'acks': 'all',
            'retries': 3,
            'max_in_flight_requests_per_connection': 5,
            'linger_ms': 10,
            'batch_size': 32768  # 32KB
        }
        
        # Create specialized producers
        self.producers['default'] = KafkaProducer(**producer_config)
        
        # High-throughput producer for data ingestion
        high_throughput_config = producer_config.copy()
        high_throughput_config.update({
            'linger_ms': 100,
            'batch_size': 131072,  # 128KB
            'compression_type': 'lz4'
        })
        self.producers['high_throughput'] = KafkaProducer(**high_throughput_config)
        
        # Low-latency producer for real-time scoring
        low_latency_config = producer_config.copy()
        low_latency_config.update({
            'linger_ms': 0,
            'batch_size': 16384  # 16KB
        })
        self.producers['low_latency'] = KafkaProducer(**low_latency_config)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def send_enrichment_request(self, request: EnrichmentRequest) -> bool:
        """Send enrichment request to Kafka"""
        try:
            producer = self.producers['default']
            future = producer.send(
                KafkaTopics.COMPANY_ENRICHMENT.value,
                key=request.uei,
                value=asdict(request)
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            # Cache request status
            self.redis_client.setex(
                f"enrichment:status:{request.request_id}",
                3600,  # 1 hour TTL
                json.dumps({
                    'status': 'queued',
                    'partition': record_metadata.partition,
                    'offset': record_metadata.offset,
                    'timestamp': datetime.utcnow().isoformat()
                })
            )
            
            logger.info(f"Sent enrichment request {request.request_id} for {request.uei}")
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send enrichment request: {e}")
            return False
    
    def send_analytics_event(self, event: AnalyticsEvent) -> bool:
        """Send analytics event to Kafka"""
        try:
            producer = self.producers['default']
            producer.send(
                KafkaTopics.ANALYTICS_EVENTS.value,
                key=event.entity_id,
                value=asdict(event)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send analytics event: {e}")
            return False
    
    def send_batch_data(self, topic: str, data: List[Dict[str, Any]], 
                       key_field: str = None) -> int:
        """Send batch data to Kafka"""
        producer = self.producers['high_throughput']
        sent_count = 0
        
        for record in data:
            try:
                key = record.get(key_field) if key_field else None
                producer.send(topic, key=key, value=record)
                sent_count += 1
            except Exception as e:
                logger.error(f"Error sending batch record: {e}")
        
        # Flush to ensure all messages are sent
        producer.flush()
        logger.info(f"Sent {sent_count}/{len(data)} records to {topic}")
        return sent_count
    
    def create_consumer(self, 
                       topics: List[str],
                       group_id: str,
                       auto_offset_reset: str = 'latest') -> KafkaConsumer:
        """Create a Kafka consumer with optimized settings"""
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
            max_poll_records=500,
            fetch_min_bytes=1024,
            fetch_max_wait_ms=500
        )
        
        self.consumers[group_id] = consumer
        return consumer
    
    async def process_enrichment_requests(self, 
                                        processor_func: Callable,
                                        batch_size: int = 10):
        """Process enrichment requests from Kafka"""
        consumer = self.create_consumer(
            [KafkaTopics.COMPANY_ENRICHMENT.value],
            'enrichment-processors'
        )
        
        batch = []
        
        try:
            for message in consumer:
                batch.append(message.value)
                
                if len(batch) >= batch_size:
                    # Process batch
                    await self._process_batch(batch, processor_func)
                    batch = []
                    
                # Update processing status
                request_id = message.value.get('request_id')
                if request_id:
                    self.redis_client.setex(
                        f"enrichment:status:{request_id}",
                        3600,
                        json.dumps({
                            'status': 'processing',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                    )
        except Exception as e:
            logger.error(f"Error in enrichment processor: {e}")
        finally:
            # Process remaining batch
            if batch:
                await self._process_batch(batch, processor_func)
            consumer.close()
    
    async def _process_batch(self, batch: List[Dict], processor_func: Callable):
        """Process a batch of messages"""
        try:
            results = await processor_func(batch)
            
            # Send results to ML predictions topic
            producer = self.producers['default']
            for result in results:
                producer.send(
                    KafkaTopics.ML_PREDICTIONS.value,
                    key=result.get('uei'),
                    value=result
                )
            
            logger.info(f"Processed batch of {len(batch)} messages")
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
    
    def get_topic_stats(self) -> Dict[str, Any]:
        """Get statistics for all Kafka topics"""
        stats = {}
        
        try:
            metadata = self.admin_client._client.cluster
            
            for topic in KafkaTopics:
                topic_name = topic.value
                if topic_name in metadata.topics():
                    partitions = metadata.partitions_for_topic(topic_name)
                    stats[topic_name] = {
                        'partitions': len(partitions) if partitions else 0,
                        'status': 'active'
                    }
                else:
                    stats[topic_name] = {
                        'partitions': 0,
                        'status': 'not_found'
                    }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting topic stats: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Kafka infrastructure"""
        health = {
            'status': 'unknown',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {}
        }
        
        try:
            # Check admin client
            metadata = self.admin_client._client.cluster
            brokers = metadata.brokers()
            
            health['details']['brokers'] = len(brokers)
            health['details']['topics'] = self.get_topic_stats()
            
            # Check Redis connection
            self.redis_client.ping()
            health['details']['redis'] = 'connected'
            
            # Overall status
            health['status'] = 'healthy' if len(brokers) > 0 else 'unhealthy'
            
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health
    
    def close(self):
        """Close all connections"""
        for producer in self.producers.values():
            producer.close()
        
        for consumer in self.consumers.values():
            consumer.close()
        
        logger.info("Kafka infrastructure closed")


# Example usage functions
async def example_enrichment_processor(batch: List[Dict]) -> List[Dict]:
    """Example processor function for enrichment requests"""
    results = []
    
    for request in batch:
        # Simulate enrichment processing
        enriched_data = {
            'uei': request['uei'],
            'company_name': request['company_name'],
            'enrichment_complete': True,
            'sam_gov_status': 'active',
            'federal_contracts': 5,
            'patent_count': 3,
            'enriched_at': datetime.utcnow().isoformat()
        }
        results.append(enriched_data)
    
    return results


def setup_kafka_monitoring():
    """Set up Kafka monitoring with Prometheus metrics"""
    from prometheus_client import Counter, Histogram, Gauge
    
    # Define metrics
    kafka_messages_sent = Counter(
        'kafka_messages_sent_total',
        'Total Kafka messages sent',
        ['topic']
    )
    
    kafka_messages_received = Counter(
        'kafka_messages_received_total',
        'Total Kafka messages received',
        ['topic', 'consumer_group']
    )
    
    kafka_processing_time = Histogram(
        'kafka_message_processing_seconds',
        'Time spent processing Kafka messages',
        ['topic', 'consumer_group']
    )
    
    kafka_lag = Gauge(
        'kafka_consumer_lag',
        'Kafka consumer lag',
        ['topic', 'partition', 'consumer_group']
    )
    
    return {
        'messages_sent': kafka_messages_sent,
        'messages_received': kafka_messages_received,
        'processing_time': kafka_processing_time,
        'consumer_lag': kafka_lag
    }


if __name__ == "__main__":
    # Initialize infrastructure
    kafka_infra = KafkaInfrastructure()
    
    if kafka_infra.initialize():
        # Run health check
        health = kafka_infra.health_check()
        print(json.dumps(health, indent=2))
        
        # Example: Send enrichment request
        request = EnrichmentRequest(
            uei="TEST123456789",
            company_name="Test Corp Alpha",
            priority="high"
        )
        
        if kafka_infra.send_enrichment_request(request):
            print(f"✅ Sent enrichment request: {request.request_id}")
        
        # Example: Send analytics event
        event = AnalyticsEvent(
            event_type="company_viewed",
            entity_id="TEST123456789",
            data={"source": "api", "endpoint": "/companies/TEST123456789"}
        )
        
        if kafka_infra.send_analytics_event(event):
            print("✅ Sent analytics event")
        
        # Clean up
        kafka_infra.close()
