from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from fastapi import Response
import time
import psutil

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# Enrichment metrics
enrichment_requests_total = Counter(
    'enrichment_requests_total',
    'Total enrichment requests',
    ['source', 'status']
)

enrichment_duration_seconds = Histogram(
    'enrichment_duration_seconds',
    'Enrichment request duration',
    ['source']
)

# System metrics
cpu_usage_percent = Gauge('cpu_usage_percent', 'CPU usage percentage')
memory_usage_percent = Gauge('memory_usage_percent', 'Memory usage percentage')
active_connections = Gauge('active_connections', 'Number of active connections')

# Database metrics
db_connections_active = Gauge('db_connections_active', 'Active database connections')
db_query_duration_seconds = Histogram('db_query_duration_seconds', 'Database query duration')

def update_system_metrics():
    """Update system metrics"""
    cpu_usage_percent.set(psutil.cpu_percent())
    memory_usage_percent.set(psutil.virtual_memory().percent)

async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    update_system_metrics()
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
