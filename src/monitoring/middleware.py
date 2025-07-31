from fastapi import Request
import time
from .metrics import http_requests_total, http_request_duration_seconds, active_connections

class MonitoringMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            active_connections.inc()
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    duration = time.time() - start_time
                    status_code = message["status"]
                    
                    # Record metrics
                    http_requests_total.labels(
                        method=scope["method"],
                        endpoint=scope["path"],
                        status=status_code
                    ).inc()
                    
                    http_request_duration_seconds.labels(
                        method=scope["method"],
                        endpoint=scope["path"]
                    ).observe(duration)
                    
                await send(message)
            
            try:
                await self.app(scope, receive, send_wrapper)
            finally:
                active_connections.dec()
        else:
            await self.app(scope, receive, send)
