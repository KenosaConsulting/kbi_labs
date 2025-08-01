"""
Web Scraping Procurement Scrapers

Specialized scrapers for HTML-based government websites.
Handles dynamic content, pagination, and site-specific extraction patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import re
from bs4 import BeautifulSoup
import httpx

from .base_scraper import BaseProcurementScraper

logger = logging.getLogger(__name__)

class FedConnectScraper(BaseProcurementScraper):
    """Scraper for FedConnect procurement opportunities"""
    
    def __init__(self, source):
        super().__init__(source)
        self.search_url = f"{self.base_url}/FedConnect"
        
    async def _fetch_source_data(self) -> List[Dict[str, Any]]:
        """Fetch opportunities from FedConnect"""
        opportunities = []
        
        try:
            # FedConnect requires session handling
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # Get main search page
                search_params = {
                    'mode': 'list',
                    'tab': 'list',
                    'searchtype': 'basic'
                }
                
                response = await client.get(self.search_url, params=search_params)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract opportunity listings
                opportunity_rows = soup.find_all('tr', class_='lst-row')
                
                for row in opportunity_rows:
                    try:
                        opportunity = self._extract_fedconnect_opportunity(row)
                        if opportunity:
                            opportunities.append(opportunity)
                    except Exception as e:
                        logger.error(f"Error extracting FedConnect opportunity: {e}")
                        continue
                
                # Handle pagination if needed
                next_page = soup.find('a', string='Next')
                if next_page and len(opportunities) < 100:  # Limit total results
                    additional_opps = await self._fetch_fedconnect_page(
                        client, 
                        next_page.get('href')
                    )
                    opportunities.extend(additional_opps)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error fetching FedConnect data: {e}")
            return []
    
    def _extract_fedconnect_opportunity(self, row) -> Optional[Dict[str, Any]]:
        """Extract opportunity data from FedConnect table row"""
        try:
            cells = row.find_all('td')
            if len(cells) < 6:
                return None
            
            # Extract basic information
            title_cell = cells[0]
            title_link = title_cell.find('a')
            title = title_link.text.strip() if title_link else title_cell.text.strip()
            
            agency = cells[1].text.strip()
            posted_date_str = cells[2].text.strip()
            response_date_str = cells[3].text.strip()
            
            # Parse dates
            posted_date = self._parse_fedconnect_date(posted_date_str)
            response_deadline = self._parse_fedconnect_date(response_date_str)
            
            # Extract notice ID from link if available
            notice_id = None
            if title_link:
                href = title_link.get('href', '')
                notice_match = re.search(r'id=([^&]+)', href)
                if notice_match:
                    notice_id = notice_match.group(1)
            
            opportunity = {
                'notice_id': notice_id or f"fedconnect_{hash(title + agency + posted_date_str)}",
                'title': title,
                'department': agency,
                'posted_date': posted_date,
                'response_deadline': response_deadline,
                'source_url': f"{self.base_url}{title_link.get('href')}" if title_link else None,
                'fedconnect_data_type': 'opportunity'
            }
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error extracting FedConnect opportunity: {e}")
            return None
    
    def _parse_fedconnect_date(self, date_str: str) -> Optional[str]:
        """Parse FedConnect date format"""
        try:
            # FedConnect typically uses MM/DD/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except Exception:
            pass
        
        return None
    
    async def _fetch_fedconnect_page(self, client: httpx.AsyncClient, page_url: str) -> List[Dict[str, Any]]:
        """Fetch additional page of FedConnect results"""
        opportunities = []
        
        try:
            response = await client.get(f"{self.base_url}{page_url}")
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            opportunity_rows = soup.find_all('tr', class_='lst-row')
            
            for row in opportunity_rows:
                try:
                    opportunity = self._extract_fedconnect_opportunity(row)
                    if opportunity:
                        opportunities.append(opportunity)
                except Exception as e:
                    logger.error(f"Error extracting FedConnect opportunity from page: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching FedConnect page: {e}")
        
        return opportunities

class AgencyScraper(BaseProcurementScraper):
    """Generic scraper for agency-specific procurement websites"""
    
    def __init__(self, source):
        super().__init__(source)
        
        # Configure extraction patterns based on source
        self.extraction_patterns = self._get_extraction_patterns()
    
    def _get_extraction_patterns(self) -> Dict[str, Any]:
        """Get extraction patterns based on source configuration"""
        patterns = self.extraction_config.get('patterns', {})
        
        # Default patterns for common elements
        default_patterns = {
            'opportunity_links': 'a[href*="opportunity"], a[href*="solicitation"], a[href*="rfp"]',
            'title_selector': 'h1, h2, .title, .opportunity-title',
            'date_selector': '.date, .posted-date, .deadline',
            'description_selector': '.description, .summary, .overview',
            'agency_selector': '.agency, .office, .contracting-office'
        }
        
        return {**default_patterns, **patterns}
    
    async def _fetch_source_data(self) -> List[Dict[str, Any]]:
        """Fetch data from agency website"""
        opportunities = []
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                # Get main page
                response = await client.get(self.base_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract opportunities based on patterns
                if 'opportunity_links' in self.extraction_patterns:
                    opportunity_links = soup.select(self.extraction_patterns['opportunity_links'])
                    
                    # Process each opportunity link
                    for link in opportunity_links[:20]:  # Limit to prevent overwhelming
                        try:
                            opp_url = self._resolve_url(link.get('href'))
                            if opp_url:
                                opportunity = await self._extract_opportunity_details(client, opp_url, link)
                                if opportunity:
                                    opportunities.append(opportunity)
                        except Exception as e:
                            logger.error(f"Error processing opportunity link: {e}")
                            continue
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                
                else:
                    # Fall back to parsing current page for opportunities
                    page_opportunities = self._extract_opportunities_from_page(soup)
                    opportunities.extend(page_opportunities)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error fetching agency data: {e}")
            return []
    
    async def _extract_opportunity_details(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        link_element
    ) -> Optional[Dict[str, Any]]:
        """Extract detailed opportunity information"""
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract details using configured patterns
            title = self._extract_text_by_selector(soup, self.extraction_patterns.get('title_selector'))
            description = self._extract_text_by_selector(soup, self.extraction_patterns.get('description_selector'))
            agency = self._extract_text_by_selector(soup, self.extraction_patterns.get('agency_selector'))
            
            # Extract dates
            dates = self._extract_dates_from_page(soup)
            
            opportunity = {
                'notice_id': f"agency_{hash(url)}",
                'title': title or link_element.text.strip(),
                'description': description,
                'department': agency or self.source.name,
                'posted_date': dates.get('posted_date'),
                'response_deadline': dates.get('deadline'),
                'source_url': url,
                'agency_data_type': 'opportunity'
            }
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error extracting opportunity details from {url}: {e}")
            return None
    
    def _extract_opportunities_from_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract opportunities directly from current page"""
        opportunities = []
        
        try:
            # Look for common opportunity listing patterns
            opportunity_containers = soup.find_all(['div', 'tr', 'li'], class_=re.compile(r'opportunity|solicitation|rfp|contract'))
            
            for container in opportunity_containers:
                try:
                    title = self._extract_text_by_selector(container, 'h1, h2, h3, .title, a')
                    if title and len(title) > 10:  # Basic validation
                        opportunity = {
                            'notice_id': f"page_{hash(title)}",
                            'title': title,
                            'department': self.source.name,
                            'extracted_from': 'page_listing',
                            'agency_data_type': 'opportunity'
                        }
                        opportunities.append(opportunity)
                except Exception as e:
                    logger.error(f"Error extracting opportunity from container: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting opportunities from page: {e}")
        
        return opportunities
    
    def _extract_text_by_selector(self, soup, selector: str) -> Optional[str]:
        """Extract text using CSS selector"""
        if not selector:
            return None
        
        try:
            element = soup.select_one(selector)
            return element.text.strip() if element else None
        except Exception:
            return None
    
    def _extract_dates_from_page(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        """Extract dates from page content"""
        dates = {'posted_date': None, 'deadline': None}
        
        try:
            # Look for date patterns in text
            text_content = soup.get_text()
            
            # Common date patterns
            date_patterns = [
                r'Posted:\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'Deadline:\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'Due:\s*(\d{1,2}/\d{1,2}/\d{4})',
                r'Response Due:\s*(\d{1,2}/\d{1,2}/\d{4})'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    date_str = matches[0]
                    formatted_date = self._parse_date_string(date_str)
                    
                    if 'posted' in pattern.lower():
                        dates['posted_date'] = formatted_date
                    elif any(word in pattern.lower() for word in ['deadline', 'due']):
                        dates['deadline'] = formatted_date
        
        except Exception as e:
            logger.error(f"Error extracting dates: {e}")
        
        return dates
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date string formats to ISO format"""
        try:
            # Handle MM/DD/YYYY format
            if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                parts = date_str.split('/')
                month, day, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Add more date format handling as needed
            
        except Exception:
            pass
        
        return None
    
    def _resolve_url(self, href: str) -> Optional[str]:
        """Resolve relative URLs to absolute URLs"""
        if not href:
            return None
        
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"{self.base_url.rstrip('/')}{href}"
        else:
            return f"{self.base_url.rstrip('/')}/{href}"

class DARPAScraper(AgencyScraper):
    """Specialized scraper for DARPA opportunities"""
    
    def __init__(self, source):
        super().__init__(source)
        
        # DARPA-specific extraction patterns
        self.extraction_patterns.update({
            'opportunity_links': 'a[href*="baa"], a[href*="broad-agency-announcement"]',
            'title_selector': '.baa-title, h1',
            'program_selector': '.program-name, .program-title',
            'solicitation_number_selector': '.solicitation-number, .baa-number'
        })
    
    async def _extract_opportunity_details(
        self, 
        client: httpx.AsyncClient, 
        url: str, 
        link_element
    ) -> Optional[Dict[str, Any]]:
        """Extract DARPA-specific opportunity details"""
        opportunity = await super()._extract_opportunity_details(client, url, link_element)
        
        if opportunity:
            try:
                response = await client.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract DARPA-specific fields
                program_name = self._extract_text_by_selector(soup, self.extraction_patterns.get('program_selector'))
                solicitation_number = self._extract_text_by_selector(soup, self.extraction_patterns.get('solicitation_number_selector'))
                
                opportunity.update({
                    'program_name': program_name,
                    'solicitation_number': solicitation_number,
                    'agency_specific_type': 'darpa_baa'
                })
                
            except Exception as e:
                logger.error(f"Error extracting DARPA-specific details: {e}")
        
        return opportunity