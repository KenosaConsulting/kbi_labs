#!/usr/bin/env python3
"""
Organizational Chart Scraping System
Government Agency Structure Intelligence

This system scrapes and processes organizational charts from government agency websites
to build detailed organizational intelligence for opportunity shaping and stakeholder mapping.
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
import re
import ssl
import certifi
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse, quote
import time
import hashlib

logger = logging.getLogger(__name__)

class OrganizationalLevel(Enum):
    DEPARTMENT = "Department"
    AGENCY = "Agency" 
    BUREAU = "Bureau"
    OFFICE = "Office"
    DIVISION = "Division"
    BRANCH = "Branch"
    SECTION = "Section"

class PersonnelType(Enum):
    POLITICAL_APPOINTEE = "Political Appointee"
    SENIOR_EXECUTIVE = "Senior Executive Service"
    GENERAL_SCHEDULE = "General Schedule"
    WAGE_GRADE = "Wage Grade"
    CONTRACTOR = "Contractor"
    UNKNOWN = "Unknown"

@dataclass
class OrganizationalUnit:
    """Represents an organizational unit within government structure"""
    
    # Basic Information
    unit_id: str
    unit_name: str
    unit_type: OrganizationalLevel
    parent_unit: Optional[str] = None
    
    # Hierarchy Information
    level: int = 0
    reporting_chain: List[str] = None
    subordinate_units: List[str] = None
    
    # Leadership Information
    leader_name: Optional[str] = None
    leader_title: Optional[str] = None
    deputy_name: Optional[str] = None
    deputy_title: Optional[str] = None
    
    # Contact Information
    office_location: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    
    # Mission and Function
    mission_statement: Optional[str] = None
    key_functions: List[str] = None
    areas_of_responsibility: List[str] = None
    
    # Metadata
    data_source: str = ""
    last_updated: datetime = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.reporting_chain is None:
            self.reporting_chain = []
        if self.subordinate_units is None:
            self.subordinate_units = []
        if self.key_functions is None:
            self.key_functions = []
        if self.areas_of_responsibility is None:
            self.areas_of_responsibility = []
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class OrganizationalPerson:
    """Represents a person in the organizational chart"""
    
    # Basic Information
    full_name: str
    title: str
    unit_id: str
    unit_name: str
    
    # Position Information
    personnel_type: PersonnelType
    grade_level: Optional[str] = None
    tenure_start: Optional[datetime] = None
    
    # Contact Information
    email: Optional[str] = None
    phone: Optional[str] = None
    office_location: Optional[str] = None
    
    # Professional Information
    background: Optional[str] = None
    previous_positions: List[str] = None
    education: Optional[str] = None
    
    # Organizational Context
    direct_supervisor: Optional[str] = None
    direct_reports: List[str] = None
    
    # Metadata
    data_source: str = ""
    last_updated: datetime = None
    confidence_score: float = 0.0
    
    def __post_init__(self):
        if self.previous_positions is None:
            self.previous_positions = []
        if self.direct_reports is None:
            self.direct_reports = []
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class OrganizationalChart:
    """Complete organizational chart for an agency"""
    
    agency_code: str
    agency_name: str
    chart_date: datetime
    
    # Organizational Structure
    organizational_units: List[OrganizationalUnit]
    personnel: List[OrganizationalPerson]
    
    # Hierarchy Mapping
    hierarchy_tree: Dict[str, Any]
    reporting_relationships: Dict[str, str]  # person -> supervisor
    
    # Analysis Data
    total_units: int
    total_personnel: int
    organizational_depth: int
    span_of_control_analysis: Dict[str, Any]
    
    # Quality Metrics
    data_completeness: float
    scraping_success_rate: float
    last_full_update: datetime

class OrganizationalChartScraper:
    """
    Advanced organizational chart scraping system
    Extracts organizational structure from government agency websites
    """
    
    def __init__(self):
        self.agency_website_mapping = {
            '9700': {  # Department of Defense
                'base_url': 'https://www.defense.gov',
                'org_paths': [
                    '/Our-Story/Leadership',
                    '/Our-Story/Organization',
                    '/About/Leadership',
                    '/organization-chart'
                ],
                'leadership_selectors': [
                    '.leadership-bio',
                    '.leader-profile',
                    '.official-bio'
                ]
            },
            '7000': {  # Department of Homeland Security
                'base_url': 'https://www.dhs.gov',
                'org_paths': [
                    '/about/leadership',
                    '/organization',
                    '/leadership-and-organizational-chart'
                ],
                'leadership_selectors': [
                    '.biography',
                    '.leader-bio',
                    '.leadership-profile'
                ]
            },
            '7500': {  # Department of Health and Human Services
                'base_url': 'https://www.hhs.gov',
                'org_paths': [
                    '/about/leadership',
                    '/about/organization',
                    '/agencies-and-offices'
                ],
                'leadership_selectors': [
                    '.leader-bio',
                    '.official-bio'
                ]
            },
            '1400': {  # Department of the Interior
                'base_url': 'https://www.doi.gov',
                'org_paths': [
                    '/whoweare/leadership',
                    '/bureaus',
                    '/organization-chart'
                ],
                'leadership_selectors': [
                    '.leader-profile',
                    '.biography'
                ]
            },
            '4700': {  # General Services Administration
                'base_url': 'https://www.gsa.gov',
                'org_paths': [
                    '/about-us/organization',
                    '/leadership',
                    '/about-us/mission-and-background'
                ],
                'leadership_selectors': [
                    '.leader-bio',
                    '.biography'
                ]
            },
            '3600': {  # Department of Veterans Affairs
                'base_url': 'https://www.va.gov',
                'org_paths': [
                    '/opa/bios',
                    '/about_va/vaorganization.asp',
                    '/leadership'
                ],
                'leadership_selectors': [
                    '.leader-bio',
                    '.va-biography'
                ]
            }
        }
        
        # Scraping components
        self.html_parser = HTMLStructureParser()
        self.personnel_extractor = PersonnelExtractor()
        self.hierarchy_builder = HierarchyBuilder()
        self.data_validator = OrganizationalDataValidator()
        
        # Session management
        self.session = None
        self.request_delays = {}
    
    async def initialize(self):
        """Initialize the organizational chart scraper"""
        
        # Create SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create aiohttp session with realistic browser headers
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        logger.info("Organizational chart scraper initialized")
    
    async def scrape_agency_organizational_chart(
        self, 
        agency_code: str,
        scraping_depth: str = "comprehensive"  # basic, detailed, comprehensive
    ) -> OrganizationalChart:
        """
        Scrape comprehensive organizational chart for agency
        
        Args:
            agency_code: Federal agency code
            scraping_depth: Level of detail to scrape
            
        Returns:
            Complete organizational chart with structure and personnel
        """
        
        logger.info(f"Scraping organizational chart for agency {agency_code}")
        
        if agency_code not in self.agency_website_mapping:
            logger.warning(f"No website mapping for agency {agency_code}")
            return self._create_empty_org_chart(agency_code)
        
        try:
            agency_config = self.agency_website_mapping[agency_code]
            
            # 1. Scrape organizational structure pages
            organizational_units = await self._scrape_organizational_structure(
                agency_code, agency_config, scraping_depth
            )
            
            # 2. Scrape leadership and personnel information
            personnel = await self._scrape_personnel_information(
                agency_code, agency_config, scraping_depth
            )
            
            # 3. Build hierarchy relationships
            hierarchy_data = await self._build_organizational_hierarchy(
                organizational_units, personnel
            )
            
            # 4. Validate and enhance data
            validated_org_chart = await self._validate_and_enhance_org_chart(
                agency_code, organizational_units, personnel, hierarchy_data
            )
            
            logger.info(f"Organizational chart complete: {len(organizational_units)} units, {len(personnel)} personnel")
            return validated_org_chart
            
        except Exception as e:
            logger.error(f"Error scraping organizational chart: {str(e)}")
            return self._create_empty_org_chart(agency_code)
    
    async def _scrape_organizational_structure(
        self, 
        agency_code: str, 
        agency_config: Dict[str, Any],
        scraping_depth: str
    ) -> List[OrganizationalUnit]:
        """Scrape organizational structure from agency website"""
        
        organizational_units = []
        base_url = agency_config['base_url']
        org_paths = agency_config['org_paths']
        
        for org_path in org_paths:
            await self._respect_rate_limit(base_url)
            
            try:
                full_url = urljoin(base_url, org_path)
                logger.info(f"Scraping organizational structure from: {full_url}")
                
                async with self.session.get(full_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Parse organizational structure from HTML
                        units = await self._parse_organizational_structure(
                            html_content, full_url, agency_code
                        )
                        organizational_units.extend(units)
                        
                        # If comprehensive scraping, follow links to sub-organization pages
                        if scraping_depth == "comprehensive":
                            sub_units = await self._scrape_sub_organizational_pages(
                                html_content, base_url, agency_code
                            )
                            organizational_units.extend(sub_units)
                    else:
                        logger.warning(f"Failed to access {full_url}: HTTP {response.status}")
                        
            except Exception as e:
                logger.error(f"Error scraping {org_path}: {str(e)}")
                continue
        
        # Deduplicate units
        unique_units = self._deduplicate_organizational_units(organizational_units)
        
        return unique_units
    
    async def _scrape_personnel_information(
        self, 
        agency_code: str, 
        agency_config: Dict[str, Any],
        scraping_depth: str
    ) -> List[OrganizationalPerson]:
        """Scrape personnel information from leadership pages"""
        
        personnel = []
        base_url = agency_config['base_url']
        org_paths = agency_config['org_paths']
        leadership_selectors = agency_config['leadership_selectors']
        
        for org_path in org_paths:
            await self._respect_rate_limit(base_url)
            
            try:
                full_url = urljoin(base_url, org_path)
                
                async with self.session.get(full_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Parse personnel information from HTML
                        page_personnel = await self._parse_personnel_information(
                            html_content, full_url, agency_code, leadership_selectors
                        )
                        personnel.extend(page_personnel)
                        
                        # If detailed or comprehensive, scrape individual bio pages
                        if scraping_depth in ["detailed", "comprehensive"]:
                            bio_personnel = await self._scrape_individual_bio_pages(
                                html_content, base_url, agency_code
                            )
                            personnel.extend(bio_personnel)
                    
            except Exception as e:
                logger.error(f"Error scraping personnel from {org_path}: {str(e)}")
                continue
        
        # Deduplicate personnel
        unique_personnel = self._deduplicate_personnel(personnel)
        
        return unique_personnel
    
    async def _parse_organizational_structure(
        self, 
        html_content: str, 
        source_url: str, 
        agency_code: str
    ) -> List[OrganizationalUnit]:
        """Parse organizational structure from HTML content"""
        
        units = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Common organizational structure patterns
        org_patterns = [
            # Hierarchical lists
            {'selector': 'ul.org-chart li', 'type': 'hierarchical_list'},
            {'selector': '.organization-unit', 'type': 'unit_blocks'},
            {'selector': '.org-unit', 'type': 'unit_blocks'},
            {'selector': '.department', 'type': 'department_blocks'},
            {'selector': '.bureau', 'type': 'bureau_blocks'},
            {'selector': '.office', 'type': 'office_blocks'},
            
            # Table-based organization charts
            {'selector': 'table.org-chart tr', 'type': 'table_rows'},
            {'selector': '.org-table tr', 'type': 'table_rows'},
            
            # Card-based layouts
            {'selector': '.org-card', 'type': 'org_cards'},
            {'selector': '.unit-card', 'type': 'org_cards'},
            
            # Link-based navigation
            {'selector': 'a[href*="bureau"]', 'type': 'bureau_links'},
            {'selector': 'a[href*="office"]', 'type': 'office_links'},
            {'selector': 'a[href*="division"]', 'type': 'division_links'}
        ]
        
        for pattern in org_patterns:
            elements = soup.select(pattern['selector'])
            
            for i, element in enumerate(elements):
                try:
                    unit = self._extract_organizational_unit(
                        element, pattern['type'], i, source_url, agency_code
                    )
                    if unit:
                        units.append(unit)
                except Exception as e:
                    logger.debug(f"Error extracting unit from element: {str(e)}")
                    continue
        
        return units
    
    def _extract_organizational_unit(
        self, 
        element: Tag, 
        pattern_type: str, 
        index: int, 
        source_url: str, 
        agency_code: str
    ) -> Optional[OrganizationalUnit]:
        """Extract organizational unit information from HTML element"""
        
        try:
            # Extract unit name
            unit_name = self._extract_unit_name(element)
            if not unit_name:
                return None
            
            # Generate unit ID
            unit_id = f"{agency_code}_{hashlib.md5(unit_name.encode()).hexdigest()[:8]}"
            
            # Determine organizational level
            unit_type = self._determine_organizational_level(unit_name, element)
            
            # Extract leader information
            leader_info = self._extract_leader_information(element)
            
            # Extract contact information
            contact_info = self._extract_contact_information(element)
            
            # Extract mission/function information
            function_info = self._extract_function_information(element)
            
            unit = OrganizationalUnit(
                unit_id=unit_id,
                unit_name=unit_name,
                unit_type=unit_type,
                leader_name=leader_info.get('name'),
                leader_title=leader_info.get('title'),
                deputy_name=leader_info.get('deputy_name'),
                deputy_title=leader_info.get('deputy_title'),
                office_location=contact_info.get('location'),
                phone=contact_info.get('phone'),
                email=contact_info.get('email'),
                website_url=contact_info.get('website'),
                mission_statement=function_info.get('mission'),
                key_functions=function_info.get('functions', []),
                areas_of_responsibility=function_info.get('responsibilities', []),
                data_source=source_url,
                confidence_score=0.7  # Base confidence for web scraping
            )
            
            return unit
            
        except Exception as e:
            logger.debug(f"Error extracting organizational unit: {str(e)}")
            return None
    
    def _extract_unit_name(self, element: Tag) -> Optional[str]:
        """Extract unit name from HTML element"""
        
        # Try various selectors for unit names
        name_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '.unit-name', '.org-name', '.department-name',
            '.title', '.name', 'strong', 'b',
            'a'
        ]
        
        for selector in name_selectors:
            name_element = element.select_one(selector)
            if name_element and name_element.get_text(strip=True):
                name = name_element.get_text(strip=True)
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                name = re.sub(r'^[-•\s]+|[-•\s]+$', '', name)
                if len(name) > 3 and len(name) < 200:  # Reasonable name length
                    return name
        
        # If no specific selector works, try the element text directly
        text = element.get_text(strip=True)
        if text and len(text) > 3 and len(text) < 200:
            text = re.sub(r'\s+', ' ', text)
            return text
        
        return None
    
    def _determine_organizational_level(self, unit_name: str, element: Tag) -> OrganizationalLevel:
        """Determine organizational level from unit name and context"""
        
        name_lower = unit_name.lower()
        
        # Keywords that indicate organizational level
        level_keywords = {
            OrganizationalLevel.DEPARTMENT: ['department', 'dept'],
            OrganizationalLevel.AGENCY: ['agency', 'administration', 'service'],
            OrganizationalLevel.BUREAU: ['bureau', 'bureau of'],
            OrganizationalLevel.OFFICE: ['office', 'office of'],
            OrganizationalLevel.DIVISION: ['division', 'directorate'],
            OrganizationalLevel.BRANCH: ['branch', 'unit'],
            OrganizationalLevel.SECTION: ['section', 'team', 'group']
        }
        
        for level, keywords in level_keywords.items():
            if any(keyword in name_lower for keyword in keywords):
                return level
        
        # Check HTML structure for clues
        if element.name in ['h1', 'h2']:
            return OrganizationalLevel.AGENCY
        elif element.name in ['h3', 'h4']:
            return OrganizationalLevel.OFFICE
        elif element.name in ['h5', 'h6']:
            return OrganizationalLevel.DIVISION
        
        # Default assumption
        return OrganizationalLevel.OFFICE
    
    def _extract_leader_information(self, element: Tag) -> Dict[str, Optional[str]]:
        """Extract leader information from HTML element"""
        
        leader_info = {
            'name': None,
            'title': None,
            'deputy_name': None,
            'deputy_title': None
        }
        
        # Look for leader information patterns
        leader_patterns = [
            {'selector': '.leader', 'name_attr': 'data-name', 'title_attr': 'data-title'},
            {'selector': '.director', 'name_attr': None, 'title_attr': None},
            {'selector': '.chief', 'name_attr': None, 'title_attr': None},
            {'selector': '.head', 'name_attr': None, 'title_attr': None}
        ]
        
        for pattern in leader_patterns:
            leader_element = element.select_one(pattern['selector'])
            if leader_element:
                # Try to extract from attributes first
                if pattern['name_attr']:
                    leader_info['name'] = leader_element.get(pattern['name_attr'])
                if pattern['title_attr']:
                    leader_info['title'] = leader_element.get(pattern['title_attr'])
                
                # If not in attributes, try text content
                if not leader_info['name']:
                    text = leader_element.get_text(strip=True)
                    if text:
                        leader_info['name'] = text
                
                break
        
        # Look for deputy information
        deputy_element = element.select_one('.deputy, .assistant, .associate')
        if deputy_element:
            leader_info['deputy_name'] = deputy_element.get_text(strip=True)
        
        return leader_info
    
    def _extract_contact_information(self, element: Tag) -> Dict[str, Optional[str]]:
        """Extract contact information from HTML element"""
        
        contact_info = {
            'location': None,
            'phone': None,
            'email': None,
            'website': None
        }
        
        # Extract phone numbers
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        text = element.get_text()
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            contact_info['phone'] = phone_matches[0]
        
        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            contact_info['email'] = email_matches[0]
        
        # Extract website URLs
        link_element = element.select_one('a[href]')
        if link_element:
            href = link_element.get('href')
            if href and href.startswith('http'):
                contact_info['website'] = href
        
        # Extract location information
        location_patterns = [
            r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr))',
            r'(Room\s+\d+[A-Z]?)',
            r'(Building\s+\d+)',
            r'([A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5})'
        ]
        
        for pattern in location_patterns:
            location_matches = re.findall(pattern, text)
            if location_matches:
                contact_info['location'] = location_matches[0]
                break
        
        return contact_info
    
    def _extract_function_information(self, element: Tag) -> Dict[str, Any]:
        """Extract mission and function information from HTML element"""
        
        function_info = {
            'mission': None,
            'functions': [],
            'responsibilities': []
        }
        
        text = element.get_text()
        
        # Look for mission statements
        mission_patterns = [
            r'mission[:\s]+([^.]+\.)',
            r'purpose[:\s]+([^.]+\.)',
            r'responsible for[:\s]+([^.]+\.)'
        ]
        
        for pattern in mission_patterns:
            mission_matches = re.findall(pattern, text, re.IGNORECASE)
            if mission_matches:
                function_info['mission'] = mission_matches[0].strip()
                break
        
        # Look for function lists
        function_elements = element.select('ul li, ol li')
        for func_elem in function_elements:
            func_text = func_elem.get_text(strip=True)
            if func_text and len(func_text) > 10:
                function_info['functions'].append(func_text)
        
        return function_info
    
    async def _parse_personnel_information(
        self, 
        html_content: str, 
        source_url: str, 
        agency_code: str,
        leadership_selectors: List[str]
    ) -> List[OrganizationalPerson]:
        """Parse personnel information from HTML content"""
        
        personnel = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try each leadership selector
        for selector in leadership_selectors:
            elements = soup.select(selector)
            
            for element in elements:
                try:
                    person = self._extract_person_information(
                        element, source_url, agency_code
                    )
                    if person:
                        personnel.append(person)
                except Exception as e:
                    logger.debug(f"Error extracting person: {str(e)}")
                    continue
        
        # Also look for general leadership patterns
        general_patterns = [
            '.biography', '.bio', '.leader-profile', '.leadership',
            '.official', '.executive', '.director', '.chief',
            '.secretary', '.administrator', '.assistant-secretary'
        ]
        
        for pattern in general_patterns:
            elements = soup.select(pattern)
            
            for element in elements:
                try:
                    person = self._extract_person_information(
                        element, source_url, agency_code
                    )
                    if person:
                        personnel.append(person)
                except Exception as e:
                    logger.debug(f"Error extracting person from general pattern: {str(e)}")
                    continue
        
        return personnel
    
    def _extract_person_information(
        self, 
        element: Tag, 
        source_url: str, 
        agency_code: str
    ) -> Optional[OrganizationalPerson]:
        """Extract person information from HTML element"""
        
        try:
            # Extract name
            name = self._extract_person_name(element)
            if not name:
                return None
            
            # Extract title
            title = self._extract_person_title(element)
            if not title:
                title = "Unknown"
            
            # Extract unit information
            unit_info = self._extract_person_unit(element)
            
            # Extract contact information
            contact_info = self._extract_contact_information(element)
            
            # Determine personnel type
            personnel_type = self._determine_personnel_type(title)
            
            person = OrganizationalPerson(
                full_name=name,
                title=title,
                unit_id=unit_info.get('unit_id', f"{agency_code}_unknown"),
                unit_name=unit_info.get('unit_name', 'Unknown Unit'),
                personnel_type=personnel_type,
                email=contact_info.get('email'),
                phone=contact_info.get('phone'),
                office_location=contact_info.get('location'),
                data_source=source_url,
                confidence_score=0.6  # Base confidence for web scraping
            )
            
            return person
            
        except Exception as e:
            logger.debug(f"Error extracting person information: {str(e)}")
            return None
    
    def _extract_person_name(self, element: Tag) -> Optional[str]:
        """Extract person name from HTML element"""
        
        # Try various selectors for names
        name_selectors = [
            '.name', '.full-name', '.person-name',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            '.title', 'strong', 'b'
        ]
        
        for selector in name_selectors:
            name_element = element.select_one(selector)
            if name_element:
                name = name_element.get_text(strip=True)
                # Basic name validation
                if self._is_valid_person_name(name):
                    return name
        
        # Try the element text directly
        text = element.get_text(strip=True)
        lines = text.split('\n')
        for line in lines[:3]:  # Check first few lines
            line = line.strip()
            if self._is_valid_person_name(line):
                return line
        
        return None
    
    def _is_valid_person_name(self, name: str) -> bool:
        """Check if a string looks like a valid person name"""
        
        if not name or len(name) < 3 or len(name) > 100:
            return False
        
        # Should contain at least one space (first + last name)
        if ' ' not in name:
            return False
        
        # Should be mostly alphabetic
        alpha_ratio = sum(c.isalpha() or c.isspace() for c in name) / len(name)
        if alpha_ratio < 0.8:
            return False
        
        # Shouldn't be all caps (likely a title/heading)
        if name.isupper() and len(name) > 10:
            return False
        
        return True
    
    def _extract_person_title(self, element: Tag) -> Optional[str]:
        """Extract person title from HTML element"""
        
        # Try various selectors for titles
        title_selectors = [
            '.title', '.position', '.job-title',
            '.role', '.designation'
        ]
        
        for selector in title_selectors:
            title_element = element.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                if title and len(title) > 3 and len(title) < 200:
                    return title
        
        # Look for title patterns in text
        text = element.get_text()
        title_patterns = [
            r'(Secretary|Administrator|Director|Chief|Assistant Secretary|Deputy Secretary)',
            r'(Under Secretary|Associate Administrator|Associate Director)',
            r'(Principal Deputy|Acting Secretary|Acting Administrator)'
        ]
        
        for pattern in title_patterns:
            title_matches = re.findall(pattern, text, re.IGNORECASE)
            if title_matches:
                return title_matches[0]
        
        return None
    
    def _extract_person_unit(self, element: Tag) -> Dict[str, str]:
        """Extract unit information for person"""
        
        unit_info = {
            'unit_id': 'unknown',
            'unit_name': 'Unknown Unit'
        }
        
        # Look for unit information in surrounding context
        text = element.get_text()
        
        # Common unit patterns
        unit_patterns = [
            r'(Office of [^,\n]+)',
            r'(Bureau of [^,\n]+)',
            r'(Department of [^,\n]+)',
            r'(Division of [^,\n]+)'
        ]
        
        for pattern in unit_patterns:
            unit_matches = re.findall(pattern, text, re.IGNORECASE)
            if unit_matches:
                unit_info['unit_name'] = unit_matches[0]
                unit_info['unit_id'] = hashlib.md5(unit_matches[0].encode()).hexdigest()[:8]
                break
        
        return unit_info
    
    def _determine_personnel_type(self, title: str) -> PersonnelType:
        """Determine personnel type from title"""
        
        title_lower = title.lower()
        
        # Political appointee indicators
        political_keywords = ['secretary', 'administrator', 'assistant secretary', 'under secretary']
        if any(keyword in title_lower for keyword in political_keywords):
            return PersonnelType.POLITICAL_APPOINTEE
        
        # Senior executive indicators
        senior_keywords = ['director', 'chief', 'deputy', 'associate director']
        if any(keyword in title_lower for keyword in senior_keywords):
            return PersonnelType.SENIOR_EXECUTIVE
        
        return PersonnelType.GENERAL_SCHEDULE
    
    def _deduplicate_organizational_units(self, units: List[OrganizationalUnit]) -> List[OrganizationalUnit]:
        """Remove duplicate organizational units"""
        
        seen_names = set()
        unique_units = []
        
        for unit in units:
            unit_key = unit.unit_name.lower().strip()
            if unit_key not in seen_names:
                seen_names.add(unit_key)
                unique_units.append(unit)
        
        return unique_units
    
    def _deduplicate_personnel(self, personnel: List[OrganizationalPerson]) -> List[OrganizationalPerson]:
        """Remove duplicate personnel records"""
        
        seen_names = set()
        unique_personnel = []
        
        for person in personnel:
            person_key = person.full_name.lower().strip()
            if person_key not in seen_names:
                seen_names.add(person_key)
                unique_personnel.append(person)
        
        return unique_personnel
    
    async def _respect_rate_limit(self, base_url: str):
        """Respect rate limits for website scraping"""
        
        domain = urlparse(base_url).netloc
        last_request = self.request_delays.get(domain, 0)
        time_since_last = time.time() - last_request
        
        # Wait at least 2 seconds between requests to same domain
        if time_since_last < 2:
            await asyncio.sleep(2 - time_since_last)
        
        self.request_delays[domain] = time.time()
    
    def _create_empty_org_chart(self, agency_code: str) -> OrganizationalChart:
        """Create empty organizational chart for agencies with no data"""
        
        return OrganizationalChart(
            agency_code=agency_code,
            agency_name=f"Agency {agency_code}",
            chart_date=datetime.now(),
            organizational_units=[],
            personnel=[],
            hierarchy_tree={},
            reporting_relationships={},
            total_units=0,
            total_personnel=0,
            organizational_depth=0,
            span_of_control_analysis={},
            data_completeness=0.0,
            scraping_success_rate=0.0,
            last_full_update=datetime.now()
        )
    
    async def close(self):
        """Close the organizational chart scraper"""
        if self.session:
            await self.session.close()
        logger.info("Organizational chart scraper closed")

class HTMLStructureParser:
    """Parser for HTML organizational structure"""
    
    def parse_hierarchy_from_html(self, html_content: str) -> Dict[str, Any]:
        """Parse organizational hierarchy from HTML structure"""
        # Implementation for HTML hierarchy parsing
        pass

class PersonnelExtractor:
    """Extractor for personnel information from web pages"""
    
    def extract_leadership_profiles(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract leadership profiles from HTML"""
        # Implementation for leadership extraction
        pass

class HierarchyBuilder:
    """Builder for organizational hierarchy relationships"""
    
    def build_reporting_relationships(
        self, 
        units: List[OrganizationalUnit], 
        personnel: List[OrganizationalPerson]
    ) -> Dict[str, Any]:
        """Build reporting relationships from units and personnel"""
        # Implementation for hierarchy building
        pass

class OrganizationalDataValidator:
    """Validator for organizational data quality"""
    
    def validate_organizational_data(self, org_chart: OrganizationalChart) -> OrganizationalChart:
        """Validate and enhance organizational chart data"""
        # Implementation for data validation
        pass

# Example usage
async def main():
    """Example: Scrape organizational chart for agency"""
    
    scraper = OrganizationalChartScraper()
    await scraper.initialize()
    
    try:
        # Scrape Department of Defense organizational chart
        dod_org_chart = await scraper.scrape_agency_organizational_chart(
            agency_code='9700',
            scraping_depth='comprehensive'
        )
        
        print(f"DoD Organizational Chart Results:")
        print(f"- Total organizational units: {dod_org_chart.total_units}")
        print(f"- Total personnel: {dod_org_chart.total_personnel}")
        print(f"- Organizational depth: {dod_org_chart.organizational_depth}")
        print(f"- Data completeness: {dod_org_chart.data_completeness:.1%}")
        
        # Show some sample units
        for i, unit in enumerate(dod_org_chart.organizational_units[:5]):
            print(f"- {unit.unit_name} ({unit.unit_type.value})")
            if unit.leader_name:
                print(f"  Leader: {unit.leader_name} - {unit.leader_title}")
        
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())