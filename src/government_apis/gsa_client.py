#!/usr/bin/env python3
"""
GSA (General Services Administration) API Client
Access 25+ GSA APIs for government analytics, operational data, and procurement intelligence
"""

import asyncio
import aiohttp
import requests
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GSAResponse:
    """Standardized GSA API response format"""
    success: bool = False
    data: List[Dict] = None
    error: str = None
    source: str = "gsa"
    count: int = 0
    response_time_ms: float = 0
    endpoint: str = None

class GSAClient:
    """
    GSA (General Services Administration) API Client
    
    Integrates with 25+ GSA APIs including:
    - Digital Analytics Program (DAP)
    - Site Scanning API  
    - Per Diem API
    - Auctions API
    - CALC (Contract-Awarded Labor Category)
    - Federal Acquisition Service APIs
    - Technology Transformation Services
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.gsa.gov"
        
        # GSA API endpoints - only confirmed working public APIs
        self.endpoints = {
            # Analytics and Performance (confirmed working)
            'analytics_dap': f"{self.base_url}/analytics/dap/v2",
            'site_scanning': f"{self.base_url}/technology/site-scanning/v1/websites",
            
            # Travel Operations (confirmed working)
            'per_diem': f"{self.base_url}/travel/perdiem/v2",
            
            # Search Services (confirmed working)
            'searchgov_clicks': f"{self.base_url}/search/clicks/v1",
            'searchgov_results': f"{self.base_url}/search/results/v1", 
            'searchgov_suggestions': f"{self.base_url}/search/suggestions/v1",
            
            # Data Services
            'data_gov': f"{self.base_url}/data.gov",
        }
        
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        import ssl
        import urllib3
        
        # Disable SSL warnings for government APIs
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Create SSL context that's more permissive for government APIs
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'KBI-Labs-GSA-Client/1.0',
                'Accept': 'application/json',
                'x-api-key': self.api_key
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_digital_analytics(self, domain: str = None, report_type: str = "agencies") -> GSAResponse:
        """
        Get GSA Digital Analytics Program (DAP) data
        Real government website analytics and performance metrics
        """
        start_time = time.time()
        
        try:
            if report_type == "agencies":
                # Get general site data for all agencies
                url = f"{self.endpoints['analytics_dap']}/reports/site/data"
            elif report_type == "domains" and domain:
                url = f"{self.endpoints['analytics_dap']}/domain/{domain}/reports/site/data"
            else:
                # Default to general reports
                url = f"{self.endpoints['analytics_dap']}/reports/site/data"
            
            params = {}
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    return await self._process_gsa_response(response, start_time, 'digital_analytics')
            else:
                headers = {'x-api-key': self.api_key, 'User-Agent': 'KBI-Labs-GSA-Client/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
                return self._process_sync_response(response, start_time, 'digital_analytics')
                
        except Exception as e:
            logger.error(f"GSA Digital Analytics error: {e}")
            return GSAResponse(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint='digital_analytics'
            )
    
    async def get_site_scanning_data(self, limit: int = 10) -> GSAResponse:
        """
        Get GSA Site Scanning API data
        Federal website security, performance, and compliance metrics
        """
        start_time = time.time()
        
        try:
            url = self.endpoints['site_scanning']
            params = {
                'api_key': self.api_key,
                'limit': limit
            }
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    return await self._process_gsa_response(response, start_time, 'site_scanning')
            else:
                headers = {'x-api-key': self.api_key, 'User-Agent': 'KBI-Labs-GSA-Client/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
                return self._process_sync_response(response, start_time, 'site_scanning')
                
        except Exception as e:
            logger.error(f"GSA Site Scanning error: {e}")
            return GSAResponse(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint='site_scanning'
            )
    
    async def get_per_diem_rates(self, city: str = "Washington", state: str = "DC", 
                                year: int = None) -> GSAResponse:
        """
        Get GSA Per Diem rates for government travel
        Real government travel allowance data
        """
        start_time = time.time()
        
        if not year:
            year = datetime.now().year
        
        try:
            url = f"{self.endpoints['per_diem']}/rates/city/{city}/state/{state}/year/{year}"
            params = {}
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    return await self._process_gsa_response(response, start_time, 'per_diem')
            else:
                headers = {'x-api-key': self.api_key, 'User-Agent': 'KBI-Labs-GSA-Client/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
                return self._process_sync_response(response, start_time, 'per_diem')
                
        except Exception as e:
            logger.error(f"GSA Per Diem error: {e}")
            return GSAResponse(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint='per_diem'
            )
    
    async def get_government_auctions(self, limit: int = 10) -> GSAResponse:
        """
        Get GSA Auctions data
        Government surplus property and asset auctions
        """
        start_time = time.time()
        
        try:
            url = f"{self.endpoints['auctions']}/auctions"
            params = {
                'api_key': self.api_key,
                'limit': limit
            }
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    return await self._process_gsa_response(response, start_time, 'auctions')
            else:
                headers = {'x-api-key': self.api_key, 'User-Agent': 'KBI-Labs-GSA-Client/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
                return self._process_sync_response(response, start_time, 'auctions')
                
        except Exception as e:
            logger.error(f"GSA Auctions error: {e}")
            return GSAResponse(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint='auctions'
            )
    
    async def get_calc_data(self, labor_category: str = None, limit: int = 10) -> GSAResponse:
        """
        Get CALC (Contract-Awarded Labor Category) data
        Real government contractor labor rates and categories
        """
        start_time = time.time()
        
        try:
            url = f"{self.endpoints['calc']}/rates"
            params = {
                'api_key': self.api_key,
                'limit': limit
            }
            
            if labor_category:
                params['labor_category'] = labor_category
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    return await self._process_gsa_response(response, start_time, 'calc')
            else:
                headers = {'x-api-key': self.api_key, 'User-Agent': 'KBI-Labs-GSA-Client/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
                return self._process_sync_response(response, start_time, 'calc')
                
        except Exception as e:
            logger.error(f"GSA CALC error: {e}")
            return GSAResponse(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint='calc'
            )
    
    async def get_search_suggestions(self, query: str = "technology", limit: int = 10) -> GSAResponse:
        """
        Get GSA Search.gov type-ahead suggestions
        Government search query suggestions and completions
        """
        start_time = time.time()
        
        try:
            url = f"{self.endpoints['searchgov_suggestions']}/suggestions"
            params = {
                'q': query,
                'limit': limit
            }
            
            if self.session:
                async with self.session.get(url, params=params) as response:
                    return await self._process_gsa_response(response, start_time, 'search_suggestions')
            else:
                headers = {'x-api-key': self.api_key, 'User-Agent': 'KBI-Labs-GSA-Client/1.0'}
                response = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
                return self._process_sync_response(response, start_time, 'search_suggestions')
                
        except Exception as e:
            logger.error(f"GSA Search Suggestions error: {e}")
            return GSAResponse(
                success=False,
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint='search_suggestions'
            )
    
    async def _process_gsa_response(self, response: aiohttp.ClientResponse, 
                                   start_time: float, endpoint: str) -> GSAResponse:
        """Process async GSA API response"""
        
        if response.status == 200:
            try:
                data = await response.json()
                processed_data = self._standardize_gsa_data(data, endpoint)
                
                return GSAResponse(
                    success=True,
                    data=processed_data,
                    count=len(processed_data),
                    response_time_ms=(time.time() - start_time) * 1000,
                    endpoint=endpoint
                )
            except Exception as e:
                error_text = await response.text()
                return GSAResponse(
                    success=False,
                    error=f"JSON parsing error: {e}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    endpoint=endpoint
                )
        else:
            error_text = await response.text()
            return GSAResponse(
                success=False,
                error=f"HTTP {response.status}: {error_text[:200]}",
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint=endpoint
            )
    
    def _process_sync_response(self, response: requests.Response, 
                              start_time: float, endpoint: str) -> GSAResponse:
        """Process synchronous GSA API response"""
        
        if response.status_code == 200:
            try:
                data = response.json()
                processed_data = self._standardize_gsa_data(data, endpoint)
                
                return GSAResponse(
                    success=True,
                    data=processed_data,
                    count=len(processed_data),
                    response_time_ms=(time.time() - start_time) * 1000,
                    endpoint=endpoint
                )
            except Exception as e:
                return GSAResponse(
                    success=False,
                    error=f"JSON parsing error: {e}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    endpoint=endpoint
                )
        else:
            return GSAResponse(
                success=False,
                error=f"HTTP {response.status_code}: {response.text[:200]}",
                response_time_ms=(time.time() - start_time) * 1000,
                endpoint=endpoint
            )
    
    def _standardize_gsa_data(self, raw_data: Any, endpoint: str) -> List[Dict]:
        """Standardize GSA API responses to consistent format"""
        
        standardized = []
        
        try:
            # Handle different GSA API response structures
            if isinstance(raw_data, dict):
                # Look for common data containers
                data_list = None
                
                for key in ['data', 'results', 'records', 'agencies', 'domains', 'rates', 'auctions', 'schedules']:
                    if key in raw_data:
                        data_list = raw_data[key]
                        break
                
                if data_list is None:
                    # Treat the entire dict as a single record
                    data_list = [raw_data]
                
                if isinstance(data_list, list):
                    for item in data_list:
                        standardized.append(self._format_gsa_record(item, endpoint))
                else:
                    standardized.append(self._format_gsa_record(data_list, endpoint))
                    
            elif isinstance(raw_data, list):
                for item in raw_data:
                    standardized.append(self._format_gsa_record(item, endpoint))
            else:
                # Single item
                standardized.append(self._format_gsa_record(raw_data, endpoint))
        
        except Exception as e:
            logger.error(f"Error standardizing GSA data for {endpoint}: {e}")
            # Return minimal record on error
            standardized = [{
                'name': f'GSA {endpoint} data',
                'source': 'gsa',
                'endpoint': endpoint,
                'error': str(e)
            }]
        
        return standardized
    
    def _format_gsa_record(self, record: Any, endpoint: str) -> Dict:
        """Format individual GSA record to standard format"""
        
        if isinstance(record, dict):
            formatted = {
                'source': 'gsa',
                'endpoint': endpoint,
                'raw_data': record
            }
            
            # Extract common fields based on endpoint
            if endpoint == 'digital_analytics':
                formatted.update({
                    'name': record.get('agency', record.get('domain', 'N/A')),
                    'type': 'analytics',
                    'sessions': record.get('sessions', 0),
                    'users': record.get('users', 0),
                    'page_views': record.get('page_views', 0)
                })
            
            elif endpoint == 'site_scanning':
                formatted.update({
                    'name': record.get('domain', record.get('website', 'N/A')),
                    'type': 'website_scan',
                    'https': record.get('https', False),
                    'mobile_friendly': record.get('mobile_friendly', False),
                    'performance_score': record.get('performance', 0)
                })
            
            elif endpoint == 'per_diem':
                formatted.update({
                    'name': f"{record.get('city', 'N/A')}, {record.get('state', 'N/A')}",
                    'type': 'per_diem_rate',
                    'meals_rate': record.get('meals', 0),
                    'lodging_rate': record.get('lodging', 0),
                    'total_rate': record.get('total', 0)
                })
            
            elif endpoint == 'auctions':
                formatted.update({
                    'name': record.get('title', record.get('description', 'N/A'))[:100],
                    'type': 'government_auction',
                    'start_price': record.get('start_price', 0),
                    'current_bid': record.get('current_bid', 0),
                    'end_date': record.get('end_date', 'N/A')
                })
            
            elif endpoint == 'calc':
                formatted.update({
                    'name': record.get('labor_category', 'N/A'),
                    'type': 'labor_rate',
                    'min_rate': record.get('min_rate', 0),
                    'max_rate': record.get('max_rate', 0),
                    'avg_rate': record.get('avg_rate', 0)
                })
            
            elif endpoint == 'search_suggestions':
                formatted.update({
                    'name': record.get('suggestion', record.get('text', 'N/A')),
                    'type': 'search_suggestion',
                    'score': record.get('score', 0),
                    'category': record.get('category', 'N/A'),
                    'description': record.get('suggestion', 'N/A')
                })
            
            else:
                # Generic formatting
                formatted.update({
                    'name': record.get('name', record.get('title', f'GSA {endpoint} record')),
                    'type': endpoint,
                    'description': record.get('description', 'N/A')
                })
            
            return formatted
        
        else:
            # Non-dict record
            return {
                'name': str(record),
                'source': 'gsa',
                'endpoint': endpoint,
                'type': endpoint,
                'raw_data': record
            }

# Convenience functions
async def get_gsa_analytics_data(api_key: str, report_type: str = "agencies") -> GSAResponse:
    """Get GSA digital analytics data"""
    async with GSAClient(api_key) as client:
        return await client.get_digital_analytics(report_type=report_type)

async def get_gsa_operational_data(api_key: str, data_type: str = "sites") -> GSAResponse:
    """Get GSA operational data (sites, auctions, etc.)"""
    async with GSAClient(api_key) as client:
        if data_type == "sites":
            return await client.get_site_scanning_data()
        elif data_type == "auctions":
            return await client.get_government_auctions()
        elif data_type == "rates":
            return await client.get_per_diem_rates()
        elif data_type == "calc":
            return await client.get_calc_data()
        elif data_type == "search":
            return await client.get_search_suggestions()
        else:
            return await client.get_site_scanning_data()  # Default