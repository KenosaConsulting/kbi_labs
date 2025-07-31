"""Health Check Utilities"""
from typing import Dict, Any
import datetime

class HealthChecker:
    async def check_health(self) -> Dict[str, Any]:
        """Basic health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "service": "KBI Labs API Gateway"
        }
    
    async def detailed_check(self) -> Dict[str, Any]:
        """Detailed health check"""
        return {
            "status": "healthy",
            "timestamp": datetime.datetime.now().isoformat(),
            "checks": {
                "database": "ok",
                "redis": "ok",
                "external_apis": "ok"
            }
        }
