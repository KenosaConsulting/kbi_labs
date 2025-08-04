"""
SSL Configuration for Government APIs
Handles certificate issues with government websites
"""

import ssl
import aiohttp
import certifi
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GovernmentSSLConfig:
    """SSL configuration optimized for government APIs"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.development_mode = self.environment in ["development", "dev", "local"]
        
        # Create SSL contexts for different scenarios
        self.ssl_contexts = self._create_ssl_contexts()
        self.connectors = {}  # Initialize empty, create on demand
        
        logger.info(f"Government SSL Config initialized - Environment: {self.environment}")
    
    def _create_ssl_contexts(self) -> dict:
        """Create SSL contexts for different scenarios"""
        contexts = {}
        
        # 1. Strict SSL context (production default)
        try:
            strict_context = ssl.create_default_context(cafile=certifi.where())
            strict_context.check_hostname = True
            strict_context.verify_mode = ssl.CERT_REQUIRED
            contexts['strict'] = strict_context
            logger.info("✅ Strict SSL context created")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create strict SSL context: {e}")
        
        # 2. Relaxed SSL context (for problematic government sites)
        try:
            relaxed_context = ssl.create_default_context(cafile=certifi.where())
            relaxed_context.check_hostname = False
            relaxed_context.verify_mode = ssl.CERT_REQUIRED
            contexts['relaxed'] = relaxed_context
            logger.info("✅ Relaxed SSL context created")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create relaxed SSL context: {e}")
        
        # 3. Development context (bypass verification)
        if self.development_mode:
            try:
                dev_context = ssl.create_default_context()
                dev_context.check_hostname = False
                dev_context.verify_mode = ssl.CERT_NONE
                contexts['development'] = dev_context
                logger.info("🔓 Development SSL context created (verification disabled)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create development SSL context: {e}")
        
        return contexts
    
    def _create_connectors(self) -> dict:
        """Create aiohttp connectors with appropriate SSL settings"""
        connectors = {}
        
        for name, ssl_context in self.ssl_contexts.items():
            try:
                connector = aiohttp.TCPConnector(
                    ssl=ssl_context,
                    limit=100,  # Connection pool limit
                    limit_per_host=30,  # Per-host limit
                    ttl_dns_cache=300,  # DNS cache TTL
                    use_dns_cache=True,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True
                )
                connectors[name] = connector
                logger.info(f"✅ {name.title()} connector created")
            except Exception as e:
                logger.warning(f"⚠️ Failed to create {name} connector: {e}")
        
        return connectors
    
    def _get_or_create_connector(self, ssl_mode: str) -> Optional[aiohttp.TCPConnector]:
        """Get existing connector or create new one on demand"""
        # Check if we already have this connector
        if ssl_mode in self.connectors:
            return self.connectors[ssl_mode]
        
        # Get the SSL context
        ssl_context = self.ssl_contexts.get(ssl_mode)
        if not ssl_context:
            return None
        
        # Create the connector
        try:
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=100,  # Connection pool limit
                limit_per_host=30,  # Per-host limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.connectors[ssl_mode] = connector
            logger.info(f"✅ {ssl_mode.title()} connector created on demand")
            return connector
        except Exception as e:
            logger.warning(f"⚠️ Failed to create {ssl_mode} connector: {e}")
            return None
    
    def get_session(self, ssl_mode: str = "auto") -> aiohttp.ClientSession:
        """Get aiohttp session with appropriate SSL configuration"""
        
        # Auto-select SSL mode based on environment
        if ssl_mode == "auto":
            if self.development_mode:
                ssl_mode = "development"
            else:
                ssl_mode = "relaxed"  # Government sites often have certificate issues
        
        # Get or create appropriate connector
        connector = self._get_or_create_connector(ssl_mode)
        if not connector:
            logger.warning(f"SSL mode '{ssl_mode}' not available, trying fallback modes")
            # Try fallback modes
            for fallback in ["relaxed", "development", "strict"]:
                if fallback != ssl_mode:
                    connector = self._get_or_create_connector(fallback)
                    if connector:
                        ssl_mode = fallback
                        break
        
        if not connector:
            raise RuntimeError("No SSL connectors available")
        
        # Create session with timeout and headers
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        headers = {
            'User-Agent': 'KBI-Labs-Platform/3.0.0 (Government-Data-Integration)',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            raise_for_status=False  # Handle status codes manually
        )
        
        logger.debug(f"Created session with SSL mode: {ssl_mode}")
        return session
    
    async def test_connection(self, url: str, ssl_mode: str = "auto") -> dict:
        """Test connection to a government API endpoint"""
        session = self.get_session(ssl_mode)
        
        try:
            async with session.get(url) as response:
                return {
                    "url": url,
                    "ssl_mode": ssl_mode,
                    "status": response.status,
                    "success": 200 <= response.status < 400,
                    "headers": dict(response.headers),
                    "ssl_info": {
                        "cipher": getattr(response.connection.transport, 'get_extra_info', lambda x: None)('cipher'),
                        "peercert": getattr(response.connection.transport, 'get_extra_info', lambda x: None)('peercert')
                    }
                }
        except Exception as e:
            return {
                "url": url,
                "ssl_mode": ssl_mode,
                "status": None,
                "success": False,
                "error": str(e)
            }
        finally:
            await session.close()
    
    async def close_all(self):
        """Close all connectors"""
        for name, connector in self.connectors.items():
            try:
                await connector.close()
                logger.debug(f"Closed {name} connector")
            except Exception as e:
                logger.warning(f"Error closing {name} connector: {e}")
        self.connectors.clear()

# Global SSL configuration instance
ssl_config = GovernmentSSLConfig()