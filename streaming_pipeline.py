#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Real-time Streaming Pipeline for KBI Labs
Processes 250M+ daily data points using Kafka streams
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import hashlib
from collections import defaultdict
import time

from kafka import KafkaProducer, KafkaConsumer
from kafka.structs import ConsumerRecord
import redis
import asyncpg
from prometheus_client import Counter, Histogram, Gauge
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
MESSAGES_PROCESSED = Counter('pipeline_messages_processed_total', 'Total messages processed', ['pipeline', 'status'])
PROCESSING_TIME = Histogram('pipeline_processing_seconds', 'Time spent processing messages', ['pipeline'])
PIPELINE_LAG = Gauge('pipeline_lag_seconds', 'Pipeline processing lag', ['pipeline'])
ENRICHMENT_CACHE_HITS = Counter('enrichment_cache_hits_total', 'Cache hits for enrichment data')
ENRICHMENT_CACHE_MISSES = Counter('enrichment_cache_misses_total', 'Cache misses for enrichment data')


@dataclass
class StreamConfig:
    """Configuration for streaming pipeline"""
    kafka_brokers: str = 'localhost:9092'
    redis_url: str = 'redis://localhost:6379'
    postgres_url: str = 'postgresql://kbi_user:kbi_secure_pass_2024@localhost:5432/kbi_labs'
    batch_size: int = 1000
    batch_timeout_seconds: int = 30
    cache_ttl_seconds: int = 3600
    enable_deduplication: bool = True
    dedup_window_seconds: int = 300


class DataEnrichmentPipeline:
    """Real-time data enrichment pipeline"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.redis_client = redis.from_url(config.redis_url)
        self.seen_messages = defaultdict(set)
        self.batch_buffer = defaultdict(list)
        self.last_flush_time = defaultdict(lambda: time.time())
        
    def _get_message_hash(self, message: Dict[str, Any]) -> str:
        """Generate hash for deduplication"""
        key_fields = ['uei', 'source', 'timestamp']
        key_data = {k: message.get(k) for k in key_fields if k in message}
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _is_duplicate(self, message: Dict[str, Any], source: str) -> bool:
        """Check if message is duplicate within window"""
        if not self.config.enable_deduplication:
            return False
        
        msg_hash = self._get_message_hash(message)
        current_time = time.time()
        
        # Clean old hashes
        cutoff_time = current_time - self.config.dedup_window_seconds
        self.seen_messages[source] = {
            (h, t) for h, t in self.seen_messages[source] 
            if t > cutoff_time
        }
        
        # Check for duplicate
        for h, t in self.seen_messages[source]:
            if h == msg_hash:
                return True
        
        # Add to seen messages
        self.seen_messages[source].add((msg_hash, current_time))
        return False
    
    async def enrich_company_data(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich company data with external sources"""
        uei = company.get('uei')
        
        # Check cache first
        cache_key = f"enriched:company:{uei}"
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            ENRICHMENT_CACHE_HITS.inc()
            return json.loads(cached_data)
        
        ENRICHMENT_CACHE_MISSES.inc()
        
        # Simulate enrichment from multiple sources
        enriched = company.copy()
        
        # Add enrichment data
        enriched.update({
            'enrichment_timestamp': datetime.utcnow().isoformat(),
            'data_quality_score': self._calculate_data_quality(company),
            'risk_indicators': self._calculate_risk_indicators(company),
            'growth_signals': self._detect_growth_signals(company),
            'market_position': self._analyze_market_position(company)
        })
        
        # Cache enriched data
        self.redis_client.setex(
            cache_key,
            self.config.cache_ttl_seconds,
            json.dumps(enriched)
        )
        
        return enriched
    
    def _calculate_data_quality(self, company: Dict[str, Any]) -> float:
        """Calculate data quality score"""
        required_fields = ['uei', 'organization_name', 'state', 'city']
        optional_fields = ['website', 'phone_number', 'email', 'annual_revenue']
        
        # Check required fields
        required_score = sum(1 for f in required_fields if company.get(f)) / len(required_fields)
        
        # Check optional fields
        optional_score = sum(1 for f in optional_fields if company.get(f)) / len(optional_fields)
        
        # Weighted score
        return (required_score * 0.7) + (optional_score * 0.3)
    
    def _calculate_risk_indicators(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate various risk indicators"""
        indicators = {
            'financial_risk': 'low',
            'operational_risk': 'medium',
            'compliance_risk': 'low',
            'market_risk': 'medium'
        }
        
        # Financial risk based on revenue and contracts
        revenue = company.get('annual_revenue', 0) or 0
        contracts = company.get('federal_contracts_value', 0) or 0
        
        if revenue < 1000000:
            indicators['financial_risk'] = 'high'
        elif revenue < 5000000:
            indicators['financial_risk'] = 'medium'
        
        # Compliance risk based on certifications
        if not company.get('sam_status') == 'active':
            indicators['compliance_risk'] = 'high'
        
        return indicators
    
    def _detect_growth_signals(self, company: Dict[str, Any]) -> List[str]:
        """Detect growth signals"""
        signals = []
        
        # Patent activity
        if company.get('patent_count', 0) > 5:
            signals.append('high_innovation_activity')
        
        # Federal contracts growth
        if company.get('federal_contracts_value', 0) > 1000000:
            signals.append('significant_federal_presence')
        
        # Certifications
        certs = company.get('active_sba_certifications', '')
        if any(cert in certs for cert in ['8(a)', 'WOSB', 'SDVOSB']):
            signals.append('socioeconomic_advantages')
        
        return signals
    
    def _analyze_market_position(self, company: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market position"""
        return {
            'market_segment': self._determine_market_segment(company),
            'competitive_advantage': self._assess_competitive_advantage(company),
            'growth_potential': self._calculate_growth_potential(company)
        }
    
    def _determine_market_segment(self, company: Dict[str, Any]) -> str:
        """Determine market segment based on NAICS code"""
        naics = company.get('primary_naics_code', '')
        
        if naics.startswith('54'):
            return 'professional_services'
        elif naics.startswith('33'):
            return 'manufacturing'
        elif naics.startswith('23'):
            return 'construction'
        else:
            return 'other'
    
    def _assess_competitive_advantage(self, company: Dict[str, Any]) -> List[str]:
        """Assess competitive advantages"""
        advantages = []
        
        if company.get('patent_count', 0) > 0:
            advantages.append('intellectual_property')
        
        if company.get('cage_code'):
            advantages.append('federal_contractor')
        
        if company.get('years_in_business', 0) > 10:
            advantages.append('established_presence')
        
        return advantages
    
    def _calculate_growth_potential(self, company: Dict[str, Any]) -> float:
        """Calculate growth potential score (0-100)"""
        score = 50.0  # Base score
        
        # Adjust based on various factors
        if company.get('innovation_score', 0) > 70:
            score += 10
        
        if company.get('federal_contracts_value', 0) > 0:
            score += 5
        
        growth_signals = self._detect_growth_signals(company)
        score += len(growth_signals) * 5
        
        # Cap at 100
        return min(score, 100.0)
    
    async def process_batch(self, messages: List[Dict[str, Any]], source: str) -> int:
        """Process a batch of messages"""
        start_time = time.time()
        processed_count = 0
        
        try:
            # Filter duplicates
            unique_messages = []
            for msg in messages:
                if not self._is_duplicate(msg, source):
                    unique_messages.append(msg)
            
            # Enrich data
            enriched_data = []
            for msg in unique_messages:
                enriched = await self.enrich_company_data(msg)
                enriched_data.append(enriched)
            
            # Store in database
            if enriched_data:
                await self._store_enriched_data(enriched_data)
            
            processed_count = len(enriched_data)
            MESSAGES_PROCESSED.labels(pipeline=source, status='success').inc(processed_count)
            
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            MESSAGES_PROCESSED.labels(pipeline=source, status='error').inc(len(messages))
        
        finally:
            processing_time = time.time() - start_time
            PROCESSING_TIME.labels(pipeline=source).observe(processing_time)
            
        return processed_count
    
    async def _store_enriched_data(self, data: List[Dict[str, Any]]):
        """Store enriched data in PostgreSQL"""
        conn = await asyncpg.connect(self.config.postgres_url)
        
        try:
            # Prepare insert statement
            insert_query = """
            INSERT INTO enriched_companies (
                uei, data, enrichment_timestamp, data_quality_score
            ) VALUES ($1, $2, $3, $4)
            ON CONFLICT (uei) DO UPDATE SET
                data = EXCLUDED.data,
                enrichment_timestamp = EXCLUDED.enrichment_timestamp,
                data_quality_score = EXCLUDED.data_quality_score,
                updated_at = CURRENT_TIMESTAMP
            """
            
            # Batch insert
            records = [
                (
                    d['uei'],
                    json.dumps(d),
                    datetime.fromisoformat(d['enrichment_timestamp']),
                    d['data_quality_score']
                )
                for d in data
            ]
            
            await conn.executemany(insert_query, records)
            
        finally:
            await conn.close()


class StreamProcessor:
    """Main stream processor"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self.pipeline = DataEnrichmentPipeline(config)
        self.consumers = {}
        self.producers = {}
        self.running = False
        
    def create_consumer(self, topic: str, group_id: str) -> KafkaConsumer:
        """Create Kafka consumer"""
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.config.kafka_brokers,
            auto_offset_reset='latest',
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            max_poll_records=self.config.batch_size
        )
        
        self.consumers[topic] = consumer
        return consumer
    
    def create_producer(self, topic: str) -> KafkaProducer:
        """Create Kafka producer"""
        producer = KafkaProducer(
            bootstrap_servers=self.config.kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='snappy',
            batch_size=32768
        )
        
        self.producers[topic] = producer
        return producer
    
    async def process_stream(self, 
                           input_topic: str,
                           output_topic: str,
                           processor_name: str):
        """Process messages from input topic to output topic"""
        consumer = self.create_consumer(input_topic, f'{processor_name}-group')
        producer = self.create_producer(output_topic)
        
        batch = []
        last_batch_time = time.time()
        
        while self.running:
            try:
                # Poll for messages
                messages = consumer.poll(timeout_ms=1000)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        batch.append(record.value)
                        
                        # Track lag
                        lag = (time.time() * 1000) - record.timestamp
                        PIPELINE_LAG.labels(pipeline=processor_name).set(lag / 1000)
                
                # Process batch if full or timeout
                current_time = time.time()
                should_process = (
                    len(batch) >= self.config.batch_size or
                    (current_time - last_batch_time) >= self.config.batch_timeout_seconds
                )
                
                if should_process and batch:
                    # Process batch
                    processed = await self.pipeline.process_batch(batch, processor_name)
                    
                    # Send to output topic
                    for msg in batch[:processed]:
                        producer.send(output_topic, value=msg)
                    
                    # Clear batch
                    batch = []
                    last_batch_time = current_time
                    
            except Exception as e:
                logger.error(f"Stream processing error: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start stream processing"""
        self.running = True
        
        # Define processing pipelines
        pipelines = [
            ('data-ingestion', 'company-enrichment', 'ingestion-processor'),
            ('company-enrichment', 'analytics-events', 'enrichment-processor'),
            ('analytics-events', 'ml-predictions', 'analytics-processor')
        ]
        
        # Start all pipelines
        tasks = []
        for input_topic, output_topic, processor_name in pipelines:
            task = asyncio.create_task(
                self.process_stream(input_topic, output_topic, processor_name)
            )
            tasks.append(task)
        
        logger.info(f"Started {len(pipelines)} stream processors")
        
        # Wait for all tasks
        await asyncio.gather(*tasks)
    
    def stop(self):
        """Stop stream processing"""
        self.running = False
        
        # Close consumers and producers
        for consumer in self.consumers.values():
            consumer.close()
        
        for producer in self.producers.values():
            producer.close()
        
        logger.info("Stream processors stopped")


class RealTimeScoring:
    """Real-time scoring engine"""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379'):
        self.redis_client = redis.from_url(redis_url)
        self.scoring_models = {}
        
    def score_company(self, company: Dict[str, Any]) -> Dict[str, float]:
        """Calculate real-time scores for a company"""
        scores = {
            'pe_investment_score': self._calculate_pe_score(company),
            'innovation_score': self._calculate_innovation_score(company),
            'growth_potential_score': self._calculate_growth_score(company),
            'risk_score': self._calculate_risk_score(company),
            'market_position_score': self._calculate_market_position_score(company)
        }
        
        # Cache scores
        cache_key = f"scores:{company['uei']}"
        self.redis_client.setex(cache_key, 3600, json.dumps(scores))
        
        return scores
    
    def _calculate_pe_score(self, company: Dict[str, Any]) -> float:
        """Calculate PE investment score"""
        score = 50.0
        
        # Revenue factor
        revenue = company.get('annual_revenue', 0) or 0
        if revenue > 10000000:
            score += 20
        elif revenue > 5000000:
            score += 10
        
        # Growth signals
        if company.get('growth_signals'):
            score += len(company['growth_signals']) * 5
        
        # Innovation
        if company.get('patent_count', 0) > 0:
            score += 10
        
        return min(score, 100.0)
    
    def _calculate_innovation_score(self, company: Dict[str, Any]) -> float:
        """Calculate innovation score"""
        base_score = 30.0
        
        # Patents
        patents = company.get('patent_count', 0)
        if patents > 0:
            base_score += min(patents * 5, 30)
        
        # R&D indicators
        if company.get('nsf_awards_count', 0) > 0:
            base_score += 20
        
        # Industry factor
        if company.get('market_segment') == 'professional_services':
            base_score += 10
        
        return min(base_score, 100.0)
    
    def _calculate_growth_score(self, company: Dict[str, Any]) -> float:
        """Calculate growth potential score"""
        return company.get('growth_potential', 50.0)
    
    def _calculate_risk_score(self, company: Dict[str, Any]) -> float:
        """Calculate risk score (lower is better)"""
        risk_score = 30.0
        
        risk_indicators = company.get('risk_indicators', {})
        
        # Add risk based on indicators
        risk_weights = {
            'high': 20,
            'medium': 10,
            'low': 5
        }
        
        for risk_type, level in risk_indicators.items():
            risk_score += risk_weights.get(level, 0)
        
        return min(risk_score, 100.0)
    
    def _calculate_market_position_score(self, company: Dict[str, Any]) -> float:
        """Calculate market position score"""
        score = 40.0
        
        # Competitive advantages
        advantages = company.get('competitive_advantage', [])
        score += len(advantages) * 10
        
        # Market segment bonus
        if company.get('market_segment') in ['professional_services', 'manufacturing']:
            score += 10
        
        return min(score, 100.0)


async def main():
    """Main function to run streaming pipeline"""
    config = StreamConfig()
    processor = StreamProcessor(config)
    
    try:
        await processor.start()
    except KeyboardInterrupt:
        logger.info("Shutting down stream processor...")
        processor.stop()


if __name__ == "__main__":
    asyncio.run(main())
