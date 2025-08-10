#!/usr/bin/env python3
"""
Application Metrics and Monitoring
Prometheus metrics collection and custom monitoring
"""

import time
import logging
import functools
from typing import Dict, Any, Optional, Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse
import psutil
import asyncio

logger = logging.getLogger(__name__)

# Prometheus Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

database_connections = Gauge(
    'database_connections',
    'Number of database connections'
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total', 
    'Total cache misses',
    ['cache_type']
)

auth_login_attempts_total = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['status']
)

auth_login_failures_total = Counter(
    'auth_login_failures_total',
    'Total failed login attempts'
)

rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['endpoint']
)

enrichment_jobs_total = Counter(
    'enrichment_jobs_total',
    'Total enrichment jobs',
    ['status']
)

enrichment_jobs_failed_total = Counter(
    'enrichment_jobs_failed_total',
    'Total failed enrichment jobs'
)

enrichment_job_duration_seconds = Histogram(
    'enrichment_job_duration_seconds',
    'Enrichment job duration in seconds',
    ['job_type']
)

# System Metrics
system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_percent',
    'System memory usage percentage'
)

system_disk_usage = Gauge(
    'system_disk_usage_percent',
    'System disk usage percentage'
)

class MetricsCollector:
    """Centralized metrics collection and management"""
    
    def __init__(self):
        self.start_time = time.time()
        self.active_requests = 0
        self.system_metrics_task = None
    
    async def start_background_tasks(self):
        """Start background metrics collection tasks"""
        self.system_metrics_task = asyncio.create_task(self.collect_system_metrics())
    
    async def stop_background_tasks(self):
        """Stop background metrics collection tasks"""
        if self.system_metrics_task:
            self.system_metrics_task.cancel()
            try:
                await self.system_metrics_task
            except asyncio.CancelledError:
                pass
    
    async def collect_system_metrics(self):
        """Collect system metrics periodically"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                system_cpu_usage.set(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                system_memory_usage.set(memory.percent)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                system_disk_usage.set(disk_percent)
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(30)
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        cache_hits_total.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        cache_misses_total.labels(cache_type=cache_type).inc()
    
    def record_login_attempt(self, success: bool):
        """Record login attempt"""
        status = "success" if success else "failure"
        auth_login_attempts_total.labels(status=status).inc()
        
        if not success:
            auth_login_failures_total.inc()
    
    def record_rate_limit_exceeded(self, endpoint: str):
        """Record rate limit exceeded event"""
        rate_limit_exceeded_total.labels(endpoint=endpoint).inc()
    
    def record_enrichment_job(self, status: str, duration: Optional[float] = None, job_type: str = "standard"):
        """Record enrichment job metrics"""
        enrichment_jobs_total.labels(status=status).inc()
        
        if status == "failed":
            enrichment_jobs_failed_total.inc()
        
        if duration is not None:
            enrichment_job_duration_seconds.labels(job_type=job_type).observe(duration)
    
    def increment_active_connections(self):
        """Increment active connections counter"""
        self.active_requests += 1
        active_connections.set(self.active_requests)
    
    def decrement_active_connections(self):
        """Decrement active connections counter"""
        self.active_requests = max(0, self.active_requests - 1)
        active_connections.set(self.active_requests)
    
    def set_database_connections(self, count: int):
        """Set database connections gauge"""
        database_connections.set(count)
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific metrics"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "active_requests": self.active_requests,
            "total_requests": sum([
                series.get() for series in http_requests_total._metrics.values()
            ]),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "login_success_rate": self._calculate_login_success_rate()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate overall cache hit rate"""
        try:
            total_hits = sum([series.get() for series in cache_hits_total._metrics.values()])
            total_misses = sum([series.get() for series in cache_misses_total._metrics.values()])
            
            total_requests = total_hits + total_misses
            return (total_hits / total_requests) * 100 if total_requests > 0 else 0.0
        except:
            return 0.0
    
    def _calculate_login_success_rate(self) -> float:
        """Calculate login success rate"""
        try:
            total_attempts = sum([
                series.get() for series in auth_login_attempts_total._metrics.values()
            ])
            failures = auth_login_failures_total._value.get()
            successes = total_attempts - failures
            
            return (successes / total_attempts) * 100 if total_attempts > 0 else 0.0
        except:
            return 0.0

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Middleware for automatic request metrics collection
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect HTTP request metrics"""
    start_time = time.time()
    
    # Increment active connections
    metrics_collector.increment_active_connections()
    
    try:
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        endpoint = request.url.path
        method = request.method
        status = response.status_code
        
        metrics_collector.record_http_request(method, endpoint, status, duration)
        
        return response
    
    except Exception as e:
        # Record error metrics
        duration = time.time() - start_time
        endpoint = request.url.path
        method = request.method
        
        metrics_collector.record_http_request(method, endpoint, 500, duration)
        raise
    
    finally:
        # Decrement active connections
        metrics_collector.decrement_active_connections()

# Metrics endpoint
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Decorator for monitoring function execution
def monitor_execution(metric_name: str = None, labels: Dict[str, str] = None):
    """Decorator to monitor function execution time and success rate"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Record success
                duration = time.time() - start_time
                
                if metric_name and metric_name in globals():
                    metric = globals()[metric_name]
                    if hasattr(metric, 'observe'):
                        if labels:
                            metric.labels(**labels).observe(duration)
                        else:
                            metric.observe(duration)
                
                return result
                
            except Exception as e:
                # Record failure
                duration = time.time() - start_time
                logger.error(f"Function {func.__name__} failed after {duration:.2f}s: {e}")
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Record success
                duration = time.time() - start_time
                
                if metric_name and metric_name in globals():
                    metric = globals()[metric_name]
                    if hasattr(metric, 'observe'):
                        if labels:
                            metric.labels(**labels).observe(duration)
                        else:
                            metric.observe(duration)
                
                return result
                
            except Exception as e:
                # Record failure
                duration = time.time() - start_time
                logger.error(f"Function {func.__name__} failed after {duration:.2f}s: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

# Health check metrics
async def enhanced_health_check() -> Dict[str, Any]:
    """Enhanced health check with detailed metrics"""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - metrics_collector.start_time,
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
            },
            "application": metrics_collector.get_application_metrics(),
            "services": {
                "database": "unknown",
                "cache": "unknown",
                "external_apis": "unknown"
            }
        }
        
        return health_data
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }