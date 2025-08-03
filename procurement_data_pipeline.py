#!/usr/bin/env python3
"""
KBI Labs Procurement Data Pipeline
Real-time government data ingestion and processing for procurement intelligence
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urlencode
import json
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Configuration for a government data source"""
    id: str
    name: str
    base_url: str
    endpoints: Dict[str, str]
    rate_limit: int  # requests per minute
    auth_required: bool = False
    api_key_env: Optional[str] = None
    data_format: str = "json"  # json, xml, csv, html
    update_frequency: int = 60  # minutes
    active: bool = True

@dataclass
class ProcurementOpportunity:
    """Standardized procurement opportunity data structure"""
    source_id: str
    opportunity_id: str
    title: str
    description: str
    agency: str
    sub_agency: Optional[str]
    posted_date: datetime
    response_deadline: datetime
    estimated_value: Optional[float]
    naics_code: Optional[str]
    set_aside_type: Optional[str]
    place_of_performance: Optional[str]
    solicitation_number: str
    status: str = "active"
    raw_data: Dict[str, Any] = None
    last_updated: datetime = None

class RateLimiter:
    """Rate limiting for API calls"""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self):
        """Acquire permission to make a request"""
        now = datetime.now()
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if (now - req_time).total_seconds() < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class DataParser:
    """Parse data from different government sources"""
    
    @staticmethod
    def parse_sam_gov_opportunity(data: Dict[str, Any]) -> Optional[ProcurementOpportunity]:
        """Parse SAM.gov opportunity data"""
        try:
            return ProcurementOpportunity(
                source_id="sam_gov",
                opportunity_id=data.get('noticeId', ''),
                title=data.get('title', ''),
                description=data.get('description', ''),
                agency=data.get('fullParentPathName', ''),
                sub_agency=data.get('subtierName'),
                posted_date=datetime.fromisoformat(data.get('postedDate', '').replace('Z', '+00:00')),
                response_deadline=datetime.fromisoformat(data.get('responseDeadLine', '').replace('Z', '+00:00')),
                estimated_value=DataParser._parse_currency(data.get('awardAmount')),
                naics_code=data.get('naicsCode'),
                set_aside_type=data.get('typeOfSetAsideDescription'),
                place_of_performance=data.get('placeOfPerformance', {}).get('state', {}).get('name'),
                solicitation_number=data.get('solicitationNumber', ''),
                raw_data=data,
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error parsing SAM.gov opportunity: {e}")
            return None
    
    @staticmethod
    def parse_usaspending_contract(data: Dict[str, Any]) -> Optional[ProcurementOpportunity]:
        """Parse USASpending.gov contract data"""
        try:
            return ProcurementOpportunity(
                source_id="usaspending",
                opportunity_id=data.get('award_id', ''),
                title=data.get('description', ''),
                description=data.get('award_description', ''),
                agency=data.get('awarding_agency', {}).get('agency_name', ''),
                sub_agency=data.get('awarding_sub_agency', {}).get('agency_name'),
                posted_date=datetime.fromisoformat(data.get('period_of_performance_start_date', '')),
                response_deadline=datetime.fromisoformat(data.get('period_of_performance_current_end_date', '')),
                estimated_value=float(data.get('total_obligation', 0) or 0),
                naics_code=data.get('naics_code'),
                set_aside_type=data.get('type_of_contract_pricing_description'),
                place_of_performance=data.get('place_of_performance', {}).get('state_name'),
                solicitation_number=data.get('piid', ''),
                status="awarded",
                raw_data=data,
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error parsing USASpending contract: {e}")
            return None
    
    @staticmethod
    def parse_fpds_contract(xml_data: str) -> List[ProcurementOpportunity]:
        """Parse FPDS XML contract data"""
        opportunities = []
        try:
            root = ET.fromstring(xml_data)
            for award in root.findall('.//award'):
                opp = ProcurementOpportunity(
                    source_id="fpds",
                    opportunity_id=award.get('piid', ''),
                    title=award.findtext('.//descriptionOfContractRequirement', ''),
                    description=award.findtext('.//descriptionOfContractRequirement', ''),
                    agency=award.findtext('.//contractingAgencyName', ''),
                    sub_agency=award.findtext('.//contractingOfficeName'),
                    posted_date=datetime.strptime(award.get('signedDate', ''), '%Y-%m-%d'),
                    response_deadline=datetime.strptime(award.get('currentCompletionDate', ''), '%Y-%m-%d'),
                    estimated_value=float(award.get('dollarObligated', 0) or 0),
                    naics_code=award.get('principalNAICSCode'),
                    set_aside_type=award.get('typeOfSetAside'),
                    place_of_performance=award.get('placeOfPerformanceStateCode'),
                    solicitation_number=award.get('piid', ''),
                    status="awarded",
                    raw_data=ET.tostring(award, encoding='unicode'),
                    last_updated=datetime.now()
                )
                opportunities.append(opp)
        except Exception as e:
            logger.error(f"Error parsing FPDS XML: {e}")
        
        return opportunities
    
    @staticmethod
    def _parse_currency(value: Any) -> Optional[float]:
        """Parse currency values from various formats"""
        if not value:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols and commas
            clean_value = re.sub(r'[$,]', '', value.strip())
            try:
                return float(clean_value)
            except ValueError:
                return None
        
        return None

class GovernmentDataCollector:
    """Collects data from government sources"""
    
    def __init__(self):
        self.data_sources = self._initialize_data_sources()
        self.rate_limiters = {
            source.id: RateLimiter(source.rate_limit) 
            for source in self.data_sources.values()
        }
        self.session = None
        
    def _initialize_data_sources(self) -> Dict[str, DataSource]:
        """Initialize government data sources configuration"""
        return {
            "sam_gov": DataSource(
                id="sam_gov",
                name="SAM.gov Opportunities",
                base_url="https://api.sam.gov",
                endpoints={
                    "opportunities": "/opportunities/v2/search",
                    "entity": "/entity-information/v3/entities"
                },
                rate_limit=100,  # requests per minute
                auth_required=True,
                api_key_env="SAM_GOV_API_KEY",
                data_format="json",
                update_frequency=30
            ),
            
            "usaspending": DataSource(
                id="usaspending",
                name="USASpending.gov",
                base_url="https://api.usaspending.gov/api",
                endpoints={
                    "awards": "/v2/search/spending_by_award",
                    "transactions": "/v2/search/spending_by_transaction"
                },
                rate_limit=200,
                auth_required=False,
                data_format="json",
                update_frequency=60
            ),
            
            "fpds": DataSource(
                id="fpds",
                name="Federal Procurement Data System",
                base_url="https://www.fpds.gov",
                endpoints={
                    "search": "/ezsearch/FEEDS/ATOM"
                },
                rate_limit=60,
                auth_required=False,
                data_format="xml",
                update_frequency=120
            ),
            
            "beta_sam": DataSource(
                id="beta_sam",
                name="Beta SAM Opportunities",
                base_url="https://beta.sam.gov",
                endpoints={
                    "opportunities": "/api/prod/opps/v3/opportunities"
                },
                rate_limit=50,
                auth_required=False,
                data_format="json",
                update_frequency=60
            )
        }
    
    async def initialize_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'KBI-Labs-Procurement-Intelligence/1.0',
                'Accept': 'application/json'
            }
        )
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def collect_sam_gov_opportunities(self, limit: int = 100) -> List[ProcurementOpportunity]:
        """Collect opportunities from SAM.gov"""
        source = self.data_sources["sam_gov"]
        rate_limiter = self.rate_limiters["sam_gov"]
        opportunities = []
        
        try:
            # Check for API key
            api_key = os.getenv(source.api_key_env)
            if not api_key:
                logger.warning(f"No API key found for {source.name}")
                return opportunities
            
            await rate_limiter.acquire()
            
            # Build search parameters
            params = {
                'limit': limit,
                'api_key': api_key,
                'postedFrom': (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y'),
                'postedTo': datetime.now().strftime('%m/%d/%Y'),
                'ptype': 'o'  # Opportunities only
            }
            
            url = f"{source.base_url}{source.endpoints['opportunities']}"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for opp_data in data.get('opportunitiesData', []):
                        opp = DataParser.parse_sam_gov_opportunity(opp_data)
                        if opp:
                            opportunities.append(opp)
                    
                    logger.info(f"Collected {len(opportunities)} opportunities from SAM.gov")
                else:
                    logger.error(f"SAM.gov API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error collecting SAM.gov opportunities: {e}")
        
        return opportunities
    
    async def collect_usaspending_contracts(self, limit: int = 100) -> List[ProcurementOpportunity]:
        """Collect contract data from USASpending.gov"""
        source = self.data_sources["usaspending"]
        rate_limiter = self.rate_limiters["usaspending"]
        opportunities = []
        
        try:
            await rate_limiter.acquire()
            
            # Build search payload
            payload = {
                "filters": {
                    "award_type_codes": ["A", "B", "C", "D"],  # Contract types
                    "time_period": [
                        {
                            "start_date": (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                            "end_date": datetime.now().strftime('%Y-%m-%d')
                        }
                    ]
                },
                "fields": [
                    "Award ID", "Recipient Name", "Award Amount", 
                    "Award Date", "Awarding Agency", "Award Description"
                ],
                "page": 1,
                "limit": limit,
                "sort": "Award Date",
                "order": "desc"
            }
            
            url = f"{source.base_url}{source.endpoints['awards']}"
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for contract_data in data.get('results', []):
                        opp = DataParser.parse_usaspending_contract(contract_data)
                        if opp:
                            opportunities.append(opp)
                    
                    logger.info(f"Collected {len(opportunities)} contracts from USASpending.gov")
                else:
                    logger.error(f"USASpending API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error collecting USASpending contracts: {e}")
        
        return opportunities
    
    async def collect_beta_sam_opportunities(self, limit: int = 100) -> List[ProcurementOpportunity]:
        """Collect opportunities from Beta SAM.gov (publicly accessible)"""
        opportunities = []
        
        try:
            # Beta SAM.gov public endpoint (no API key required)
            url = "https://beta.sam.gov/api/prod/opps/v3/opportunities"
            params = {
                'limit': limit,
                'offset': 0,
                'postedFrom': (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y'),
                'postedTo': datetime.now().strftime('%m/%d/%Y')
            }
            
            await self.rate_limiters["beta_sam"].acquire()
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for opp_data in data.get('opportunitiesData', []):
                        # Use same parser as SAM.gov since it's the same data structure
                        opp = DataParser.parse_sam_gov_opportunity(opp_data)
                        if opp:
                            opp.source_id = "beta_sam"
                            opportunities.append(opp)
                    
                    logger.info(f"Collected {len(opportunities)} opportunities from Beta SAM.gov")
                else:
                    logger.error(f"Beta SAM.gov API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error collecting Beta SAM opportunities: {e}")
        
        return opportunities

class ProcurementDataPipeline:
    """Main data pipeline orchestrator"""
    
    def __init__(self):
        self.collector = GovernmentDataCollector()
        self.opportunities_cache = {}
        self.last_update = {}
        self.is_running = False
        
    async def start(self):
        """Start the data pipeline"""
        logger.info("Starting Procurement Data Pipeline")
        
        await self.collector.initialize_session()
        self.is_running = True
        
        # Start background collection tasks
        tasks = [
            asyncio.create_task(self._periodic_collection()),
            asyncio.create_task(self._cleanup_old_data())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down data pipeline")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the data pipeline"""
        self.is_running = False
        await self.collector.close_session()
        logger.info("Data pipeline stopped")
    
    async def _periodic_collection(self):
        """Periodically collect data from all sources"""
        while self.is_running:
            try:
                logger.info("Starting periodic data collection")
                
                # Collect from all active sources concurrently
                collection_tasks = [
                    self._collect_from_source("beta_sam"),
                    self._collect_from_source("usaspending"),
                    # self._collect_from_source("sam_gov"),  # Requires API key
                ]
                
                results = await asyncio.gather(*collection_tasks, return_exceptions=True)
                
                total_collected = 0
                for result in results:
                    if isinstance(result, list):
                        total_collected += len(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Collection error: {result}")
                
                logger.info(f"Periodic collection complete: {total_collected} opportunities total")
                
                # Wait before next collection cycle (30 minutes)
                await asyncio.sleep(1800)
                
            except Exception as e:
                logger.error(f"Error in periodic collection: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _collect_from_source(self, source_id: str) -> List[ProcurementOpportunity]:
        """Collect data from a specific source"""
        try:
            if source_id == "sam_gov":
                opportunities = await self.collector.collect_sam_gov_opportunities()
            elif source_id == "usaspending":
                opportunities = await self.collector.collect_usaspending_contracts()
            elif source_id == "beta_sam":
                opportunities = await self.collector.collect_beta_sam_opportunities()
            else:
                logger.warning(f"Unknown source: {source_id}")
                return []
            
            # Update cache
            for opp in opportunities:
                cache_key = f"{opp.source_id}_{opp.opportunity_id}"
                self.opportunities_cache[cache_key] = opp
            
            self.last_update[source_id] = datetime.now()
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error collecting from {source_id}: {e}")
            return []
    
    async def _cleanup_old_data(self):
        """Clean up old cached data"""
        while self.is_running:
            try:
                cutoff_date = datetime.now() - timedelta(days=7)
                
                # Remove old opportunities
                keys_to_remove = [
                    key for key, opp in self.opportunities_cache.items()
                    if opp.last_updated < cutoff_date
                ]
                
                for key in keys_to_remove:
                    del self.opportunities_cache[key]
                
                if keys_to_remove:
                    logger.info(f"Cleaned up {len(keys_to_remove)} old opportunities")
                
                # Wait 24 hours before next cleanup
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    def get_opportunities(self, filters: Dict[str, Any] = None) -> List[ProcurementOpportunity]:
        """Get opportunities from cache with optional filtering"""
        opportunities = list(self.opportunities_cache.values())
        
        if not filters:
            return opportunities
        
        filtered = opportunities
        
        # Apply filters
        if filters.get('agency'):
            agency_filter = filters['agency'].lower()
            filtered = [opp for opp in filtered if agency_filter in opp.agency.lower()]
        
        if filters.get('naics_code'):
            filtered = [opp for opp in filtered if opp.naics_code == filters['naics_code']]
        
        if filters.get('set_aside_type'):
            filtered = [opp for opp in filtered if opp.set_aside_type == filters['set_aside_type']]
        
        if filters.get('min_value'):
            filtered = [opp for opp in filtered if opp.estimated_value and opp.estimated_value >= filters['min_value']]
        
        if filters.get('max_value'):
            filtered = [opp for opp in filtered if opp.estimated_value and opp.estimated_value <= filters['max_value']]
        
        # Sort by posted date (newest first)
        filtered.sort(key=lambda x: x.posted_date, reverse=True)
        
        return filtered
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status information"""
        return {
            "is_running": self.is_running,
            "total_opportunities": len(self.opportunities_cache),
            "last_updates": self.last_update,
            "sources_active": len([s for s in self.collector.data_sources.values() if s.active]),
            "cache_size_mb": len(json.dumps([asdict(opp) for opp in self.opportunities_cache.values()], default=str)) / 1024 / 1024
        }

# Global pipeline instance
data_pipeline = None

async def initialize_pipeline():
    """Initialize the global data pipeline"""
    global data_pipeline
    if data_pipeline is None:
        data_pipeline = ProcurementDataPipeline()
        # Start a background task for the pipeline
        asyncio.create_task(data_pipeline.start())
    return data_pipeline

if __name__ == "__main__":
    # Run the data pipeline
    async def main():
        pipeline = ProcurementDataPipeline()
        await pipeline.start()
    
    asyncio.run(main())