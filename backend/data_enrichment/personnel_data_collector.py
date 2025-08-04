#!/usr/bin/env python3
"""
Personnel Data Collection System
Real-time Government Personnel Intelligence Gathering

This system collects detailed personnel data from multiple government sources
to build comprehensive contact and decision-maker databases for opportunity shaping.
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import ssl
import certifi
from bs4 import BeautifulSoup
import time
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class PersonnelRecord:
    """Structured personnel record from government sources"""
    
    # Basic Information
    full_name: str
    title: str
    agency: str
    office: str
    department: str
    
    # Contact Information
    email: Optional[str] = None
    phone: Optional[str] = None
    office_address: Optional[str] = None
    
    # Employment Details
    grade_level: Optional[str] = None  # GS-15, SES, etc.
    pay_plan: Optional[str] = None     # GS, WG, etc.
    series: Optional[str] = None       # Job series code
    tenure: Optional[str] = None       # Years in position
    
    # Organizational Context
    supervisor: Optional[str] = None
    subordinates: List[str] = None
    organizational_code: Optional[str] = None
    
    # Intelligence Metadata
    data_sources: List[str] = None
    last_updated: datetime = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.subordinates is None:
            self.subordinates = []
        if self.data_sources is None:
            self.data_sources = []
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class ContactIntelligence:
    """Enhanced contact intelligence for personnel"""
    
    person: PersonnelRecord
    
    # Professional Background
    education: List[str]
    certifications: List[str]
    previous_positions: List[Dict[str, str]]
    expertise_areas: List[str]
    
    # Network Intelligence
    professional_network: List[str]
    industry_contacts: List[str]
    conference_participation: List[str]
    published_works: List[str]
    
    # Engagement Intelligence
    communication_style: str
    meeting_preferences: List[str]
    response_patterns: Dict[str, str]
    
    # Strategic Context
    current_priorities: List[str]
    budget_authority: Optional[float]
    procurement_involvement: List[str]
    decision_authority_level: str

class PersonnelDataCollector:
    """
    Advanced personnel data collection system for government intelligence
    Integrates multiple sources to build comprehensive personnel databases
    """
    
    def __init__(self):
        self.data_sources = {
            'fedscope': {
                'url': 'https://www.fedscope.opm.gov/api/',
                'type': 'official',
                'rate_limit': 60
            },
            'plum_book': {
                'url': 'https://www.govinfo.gov/app/collection/plumbook/',
                'type': 'political_appointees',
                'rate_limit': 30
            },
            'federal_directory': {
                'url': 'https://www.federaldirectory.com/api/',
                'type': 'commercial',
                'rate_limit': 120
            },
            'linkedin_gov': {
                'url': 'https://api.linkedin.com/v2/',
                'type': 'professional',
                'rate_limit': 100
            },
            'usaspending_officers': {
                'url': 'https://api.usaspending.gov/api/v2/',
                'type': 'contracting',
                'rate_limit': 100
            }
        }
        
        # Collection components
        self.official_collector = OfficialPersonnelCollector()
        self.network_analyzer = ProfessionalNetworkAnalyzer()
        self.contact_enricher = ContactIntelligenceEnricher()
        self.validation_engine = PersonnelValidationEngine()
        
        # Session management
        self.session = None
        self.rate_limiters = {}
    
    async def initialize(self):
        """Initialize the personnel collection system"""
        
        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=20)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'KBI-Labs-Personnel-Collector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        
        # Initialize rate limiters
        for source_name, config in self.data_sources.items():
            self.rate_limiters[source_name] = RateLimiter(config['rate_limit'])
        
        logger.info("Personnel data collector initialized")
    
    async def collect_agency_personnel(
        self, 
        agency_code: str,
        collection_depth: str = "comprehensive",  # basic, detailed, comprehensive
        focus_roles: List[str] = None
    ) -> List[PersonnelRecord]:
        """
        Collect comprehensive personnel data for agency
        
        Args:
            agency_code: Federal agency code
            collection_depth: Level of detail to collect
            focus_roles: Specific roles to focus on (PM, CO, etc.)
            
        Returns:
            List of personnel records with intelligence
        """
        
        if focus_roles is None:
            focus_roles = [
                'Program Manager', 'Contracting Officer', 'Director', 
                'Chief', 'Deputy', 'Assistant Secretary'
            ]
        
        logger.info(f"Collecting personnel data for agency {agency_code}")
        
        try:
            # 1. Official Government Sources
            official_personnel = await self._collect_official_personnel(agency_code)
            
            # 2. Contracting Officers and Procurement Personnel
            procurement_personnel = await self._collect_procurement_personnel(agency_code)
            
            # 3. Senior Leadership and Political Appointees
            leadership_personnel = await self._collect_leadership_personnel(agency_code)
            
            # 4. Technical and Program Staff
            technical_personnel = await self._collect_technical_personnel(agency_code, focus_roles)
            
            # 5. Merge and deduplicate personnel records
            all_personnel = self._merge_personnel_records([
                official_personnel, procurement_personnel, 
                leadership_personnel, technical_personnel
            ])
            
            # 6. Enrich with additional intelligence
            if collection_depth in ['detailed', 'comprehensive']:
                enriched_personnel = await self._enrich_personnel_intelligence(
                    all_personnel, collection_depth
                )
            else:
                enriched_personnel = all_personnel
            
            # 7. Validate and score personnel data
            validated_personnel = await self._validate_personnel_data(enriched_personnel)
            
            logger.info(f"Personnel collection complete: {len(validated_personnel)} records")
            return validated_personnel
            
        except Exception as e:
            logger.error(f"Error collecting agency personnel: {str(e)}")
            raise
    
    async def _collect_official_personnel(self, agency_code: str) -> List[PersonnelRecord]:
        """Collect personnel from official government sources"""
        
        personnel_records = []
        
        try:
            # 1. FedScope OPM Data
            fedscope_data = await self._fetch_fedscope_personnel(agency_code)
            personnel_records.extend(self._parse_fedscope_data(fedscope_data, agency_code))
            
            # 2. Agency Organizational Charts
            org_chart_data = await self._scrape_agency_org_charts(agency_code)
            personnel_records.extend(self._parse_org_chart_data(org_chart_data, agency_code))
            
            # 3. Agency Phone Books and Directories
            directory_data = await self._scrape_agency_directories(agency_code)
            personnel_records.extend(self._parse_directory_data(directory_data, agency_code))
            
            logger.info(f"Official personnel collection: {len(personnel_records)} records")
            return personnel_records
            
        except Exception as e:
            logger.error(f"Error collecting official personnel: {str(e)}")
            return []
    
    async def _collect_procurement_personnel(self, agency_code: str) -> List[PersonnelRecord]:
        """Collect contracting officers and procurement personnel"""
        
        procurement_records = []
        
        try:
            # 1. USASpending Contracting Officer Data
            usaspending_cos = await self._fetch_usaspending_contracting_officers(agency_code)
            procurement_records.extend(self._parse_contracting_officer_data(usaspending_cos))
            
            # 2. SAM.gov Point of Contact Data
            sam_contacts = await self._fetch_sam_contacts(agency_code)
            procurement_records.extend(self._parse_sam_contact_data(sam_contacts))
            
            # 3. Procurement Office Directories
            procurement_dirs = await self._scrape_procurement_directories(agency_code)
            procurement_records.extend(self._parse_procurement_directory_data(procurement_dirs))
            
            logger.info(f"Procurement personnel collection: {len(procurement_records)} records")
            return procurement_records
            
        except Exception as e:
            logger.error(f"Error collecting procurement personnel: {str(e)}")
            return []
    
    async def _fetch_fedscope_personnel(self, agency_code: str) -> Dict[str, Any]:
        """Fetch personnel data from FedScope"""
        
        await self.rate_limiters['fedscope'].wait()
        
        try:
            # FedScope data structure for personnel information
            fedscope_data = {
                'employees': [],
                'organizational_structure': {},
                'employment_statistics': {}
            }
            
            # In production, this would parse FedScope CSV files
            # For now, return structured data that would contain real personnel info
            
            logger.info(f"FedScope personnel data prepared for agency {agency_code}")
            return fedscope_data
            
        except Exception as e:
            logger.error(f"Error fetching FedScope personnel: {str(e)}")
            return {}
    
    async def _fetch_usaspending_contracting_officers(self, agency_code: str) -> List[Dict[str, Any]]:
        """Fetch contracting officer data from USASpending"""
        
        await self.rate_limiters['usaspending_officers'].wait()
        
        try:
            # Get current fiscal year
            current_fy = self._get_current_fiscal_year()
            
            url = f"{self.data_sources['usaspending_officers']['url']}search/spending_by_award/"
            
            payload = {
                "filters": {
                    "agencies": [{"type": "awarding", "tier": "toptier", "code": agency_code}],
                    "time_period": [{"start_date": f"{current_fy-1}-10-01", "end_date": f"{current_fy}-09-30"}]
                },
                "fields": [
                    "Award ID", "Awarding Agency", "Awarding Sub Agency",
                    "Contracting Officer", "Contract Award Type"
                ],
                "sort": "Award Amount",
                "order": "desc",
                "limit": 1000
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    contracting_officers = []
                    
                    # Extract unique contracting officers
                    for award in data.get('results', []):
                        co_name = award.get('Contracting Officer')
                        if co_name and co_name not in [co['name'] for co in contracting_officers]:
                            contracting_officers.append({
                                'name': co_name,
                                'agency': award.get('Awarding Agency'),
                                'sub_agency': award.get('Awarding Sub Agency'),
                                'source': 'usaspending'
                            })
                    
                    logger.info(f"USASpending COs: {len(contracting_officers)} officers")
                    return contracting_officers
                else:
                    logger.warning(f"USASpending CO API error {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching contracting officers: {str(e)}")
            return []
    
    def _parse_fedscope_data(self, fedscope_data: Dict[str, Any], agency_code: str) -> List[PersonnelRecord]:
        """Parse FedScope data into personnel records"""
        
        personnel_records = []
        
        for employee in fedscope_data.get('employees', []):
            record = PersonnelRecord(
                full_name=employee.get('name', 'Unknown'),
                title=employee.get('position_title', 'Unknown'),
                agency=self._get_agency_name(agency_code),
                office=employee.get('office', 'Unknown'),
                department=employee.get('department', 'Unknown'),
                grade_level=employee.get('grade', ''),
                pay_plan=employee.get('pay_plan', ''),
                series=employee.get('series', ''),
                organizational_code=employee.get('org_code', ''),
                data_sources=['fedscope'],
                confidence_score=0.9  # High confidence for official data
            )
            personnel_records.append(record)
        
        return personnel_records
    
    def _parse_contracting_officer_data(self, co_data: List[Dict[str, Any]]) -> List[PersonnelRecord]:
        """Parse contracting officer data into personnel records"""
        
        personnel_records = []
        
        for officer in co_data:
            record = PersonnelRecord(
                full_name=officer['name'],
                title='Contracting Officer',
                agency=officer.get('agency', 'Unknown'),
                office=officer.get('sub_agency', 'Unknown'),
                department=officer.get('agency', 'Unknown'),
                data_sources=['usaspending'],
                confidence_score=0.8  # Good confidence for procurement data
            )
            personnel_records.append(record)
        
        return personnel_records
    
    def _merge_personnel_records(self, record_lists: List[List[PersonnelRecord]]) -> List[PersonnelRecord]:
        """Merge and deduplicate personnel records from multiple sources"""
        
        merged_records = []
        seen_names = set()
        
        # Flatten all records
        all_records = []
        for record_list in record_lists:
            all_records.extend(record_list)
        
        # Deduplicate by name and agency
        for record in all_records:
            record_key = f"{record.full_name.lower()}_{record.agency.lower()}"
            
            if record_key not in seen_names:
                seen_names.add(record_key)
                merged_records.append(record)
            else:
                # Merge data from duplicate record
                existing_record = next(
                    r for r in merged_records 
                    if f"{r.full_name.lower()}_{r.agency.lower()}" == record_key
                )
                self._merge_duplicate_records(existing_record, record)
        
        return merged_records
    
    def _merge_duplicate_records(self, existing: PersonnelRecord, duplicate: PersonnelRecord):
        """Merge data from duplicate personnel records"""
        
        # Merge data sources
        existing.data_sources.extend(duplicate.data_sources)
        existing.data_sources = list(set(existing.data_sources))
        
        # Use more complete information
        if not existing.email and duplicate.email:
            existing.email = duplicate.email
        if not existing.phone and duplicate.phone:
            existing.phone = duplicate.phone
        if not existing.grade_level and duplicate.grade_level:
            existing.grade_level = duplicate.grade_level
        
        # Update confidence score (average of sources)
        existing.confidence_score = (existing.confidence_score + duplicate.confidence_score) / 2
        
        # Update timestamp to most recent
        if duplicate.last_updated > existing.last_updated:
            existing.last_updated = duplicate.last_updated
    
    def _get_agency_name(self, agency_code: str) -> str:
        """Convert agency code to agency name"""
        
        agency_mapping = {
            '9700': 'Department of Defense',
            '7000': 'Department of Homeland Security',
            '7500': 'Department of Health and Human Services',
            '1400': 'Department of the Interior',
            '4700': 'General Services Administration',
            '3600': 'Department of Veterans Affairs',
            '5700': 'Department of the Air Force',
            '2100': 'Department of the Army',
            '1700': 'Department of the Navy'
        }
        
        return agency_mapping.get(agency_code, f"Agency {agency_code}")
    
    def _get_current_fiscal_year(self) -> int:
        """Get current federal fiscal year"""
        today = datetime.now()
        if today.month >= 10:  # FY starts Oct 1
            return today.year + 1
        else:
            return today.year
    
    async def close(self):
        """Close the personnel collector and cleanup resources"""
        if self.session:
            await self.session.close()
        logger.info("Personnel data collector closed")

class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.request_times = []
    
    async def wait(self):
        """Wait if necessary to respect rate limits"""
        
        now = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now)

class OfficialPersonnelCollector:
    """Collector for official government personnel sources"""
    
    async def collect_fedscope_data(self, agency_code: str) -> Dict[str, Any]:
        """Collect personnel data from FedScope"""
        # Implementation for FedScope data collection
        pass

class ProfessionalNetworkAnalyzer:
    """Analyzer for professional networks and relationships"""
    
    async def analyze_professional_network(self, person: PersonnelRecord) -> Dict[str, Any]:
        """Analyze professional network for person"""
        # Implementation for network analysis
        pass

class ContactIntelligenceEnricher:
    """Enricher for contact intelligence"""
    
    async def enrich_contact_intelligence(self, person: PersonnelRecord) -> ContactIntelligence:
        """Enrich personnel record with contact intelligence"""
        # Implementation for contact enrichment
        pass

class PersonnelValidationEngine:
    """Validation engine for personnel data quality"""
    
    async def validate_personnel_record(self, record: PersonnelRecord) -> PersonnelRecord:
        """Validate and score personnel record quality"""
        # Implementation for validation
        pass

# Example usage
async def main():
    """Example: Collect personnel data for agency"""
    
    collector = PersonnelDataCollector()
    await collector.initialize()
    
    try:
        # Collect Department of Defense personnel
        dod_personnel = await collector.collect_agency_personnel(
            agency_code='9700',
            collection_depth='comprehensive',
            focus_roles=['Program Manager', 'Contracting Officer', 'Director']
        )
        
        print(f"DoD Personnel Collection Results:")
        print(f"- Total personnel records: {len(dod_personnel)}")
        print(f"- Average confidence score: {np.mean([p.confidence_score for p in dod_personnel]):.2f}")
        
        # Show some sample records
        for i, person in enumerate(dod_personnel[:5]):
            print(f"- {person.full_name}: {person.title} ({person.office})")
        
    finally:
        await collector.close()

if __name__ == "__main__":
    asyncio.run(main())