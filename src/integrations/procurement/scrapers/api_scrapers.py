"""
API-based Procurement Scrapers

Specialized scrapers for government APIs (SAM.gov, USASpending, FPDS-NG).
Extends existing KBI Labs SAM.gov integration patterns.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

from .base_scraper import BaseProcurementScraper

logger = logging.getLogger(__name__)

class SAMGovScraper(BaseProcurementScraper):
    """Scraper for SAM.gov API - extends existing KBI patterns"""
    
    def __init__(self, source):
        super().__init__(source)
        self._health_check_endpoint = "/sam/v1/registrations"
        
        # SAM.gov specific configuration
        self.api_version = "v3"
        self.endpoints = {
            'registrations': f"/sam/{self.api_version}/registrations",
            'opportunities': f"/sam/{self.api_version}/opportunities",
            'exclusions': f"/sam/{self.api_version}/exclusions"
        }
    
    async def _fetch_source_data(self) -> List[Dict[str, Any]]:
        """Fetch data from SAM.gov API"""
        all_data = []
        
        try:
            # Fetch entity registrations
            registrations = await self._fetch_registrations()
            all_data.extend(registrations)
            
            # Fetch opportunities if configured
            if self.extraction_config.get('include_opportunities', True):
                opportunities = await self._fetch_opportunities()
                all_data.extend(opportunities)
            
            return all_data
            
        except Exception as e:
            logger.error(f"Error fetching SAM.gov data: {e}")
            return []
    
    async def _fetch_registrations(self) -> List[Dict[str, Any]]:
        """Fetch entity registrations from SAM.gov"""
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'page': 1,
            'size': 100
        }
        
        # Add date filters if configured
        if 'date_range_days' in self.extraction_config:
            days_back = self.extraction_config['date_range_days']
            start_date = datetime.utcnow() - timedelta(days=days_back)
            params['modifiedFrom'] = start_date.strftime('%Y-%m-%d')
        
        registrations = []
        
        try:
            response = await self._make_request('GET', self.endpoints['registrations'], params=params)
            
            if response and 'entityData' in response:
                for entity in response['entityData']:
                    registration = {
                        'uei': entity.get('entityRegistration', {}).get('ueiSAM'),
                        'legal_business_name': entity.get('entityRegistration', {}).get('legalBusinessName'),
                        'dba_name': entity.get('entityRegistration', {}).get('dbaName'),
                        'cage_code': entity.get('entityRegistration', {}).get('cageCode'),
                        'registration_status': entity.get('entityRegistration', {}).get('registrationStatus'),
                        'registration_date': entity.get('entityRegistration', {}).get('registrationDate'),
                        'expiration_date': entity.get('entityRegistration', {}).get('expirationDate'),
                        'naics_codes': self._extract_naics_codes(entity),
                        'business_types': self._extract_business_types(entity),
                        'address': self._extract_address(entity),
                        'sam_data_type': 'registration'
                    }
                    registrations.append(registration)
            
            return registrations
            
        except Exception as e:
            logger.error(f"Error fetching SAM.gov registrations: {e}")
            return []
    
    async def _fetch_opportunities(self) -> List[Dict[str, Any]]:
        """Fetch procurement opportunities from SAM.gov"""
        params = {
            'api_key': self.api_key,
            'format': 'json',
            'page': 1,
            'size': 100,
            'postedFrom': (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
        }
        
        opportunities = []
        
        try:
            response = await self._make_request('GET', self.endpoints['opportunities'], params=params)
            
            if response and 'opportunitiesData' in response:
                for opp in response['opportunitiesData']:
                    opportunity = {
                        'notice_id': opp.get('noticeId'),
                        'title': opp.get('title'),
                        'department': opp.get('department'),
                        'sub_agency': opp.get('subAgency'),
                        'office': opp.get('office'),
                        'posted_date': opp.get('postedDate'),
                        'response_deadline': opp.get('responseDeadLine'),
                        'naics_code': opp.get('naicsCode'),
                        'set_aside': opp.get('typeOfSetAside'),
                        'description': opp.get('description', {}).get('description'),
                        'award_number': opp.get('awardNumber'),
                        'award_date': opp.get('awardDate'),
                        'awarded_amount': opp.get('awardedAmount'),
                        'sam_data_type': 'opportunity'
                    }
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error fetching SAM.gov opportunities: {e}")
            return []
    
    async def get_company_contracts(self, uei: str) -> List[Dict[str, Any]]:
        """Get contracts for a specific company from SAM.gov"""
        params = {
            'api_key': self.api_key,
            'ueiSAM': uei,
            'format': 'json'
        }
        
        try:
            response = await self._make_request('GET', self.endpoints['registrations'], params=params)
            
            if response and 'entityData' in response:
                # SAM.gov doesn't directly provide contract history
                # This would need to be supplemented with FPDS-NG data
                entity = response['entityData'][0] if response['entityData'] else {}
                return [{
                    'uei': uei,
                    'source': 'sam_gov',
                    'registration_status': entity.get('entityRegistration', {}).get('registrationStatus'),
                    'cage_code': entity.get('entityRegistration', {}).get('cageCode')
                }]
            
        except Exception as e:
            logger.error(f"Error fetching company data from SAM.gov: {e}")
        
        return []
    
    def _extract_naics_codes(self, entity: Dict) -> List[str]:
        """Extract NAICS codes from entity data"""
        naics_codes = []
        
        naics_data = entity.get('coreData', {}).get('businessTypes', {}).get('naicsLimitedSB', [])
        for naics in naics_data:
            if naics.get('naicsCode'):
                naics_codes.append(naics['naicsCode'])
        
        return naics_codes
    
    def _extract_business_types(self, entity: Dict) -> List[str]:
        """Extract business type certifications"""
        business_types = []
        
        core_data = entity.get('coreData', {})
        business_type_data = core_data.get('businessTypes', {})
        
        # Check various certification types
        certifications = [
            'sbaBusinessTypeString',
            'businessTypeString', 
            'organizationStructureString'
        ]
        
        for cert_type in certifications:
            if cert_type in business_type_data:
                cert_value = business_type_data[cert_type]
                if isinstance(cert_value, list):
                    business_types.extend(cert_value)
                elif cert_value:
                    business_types.append(cert_value)
        
        return list(set(business_types))  # Remove duplicates
    
    def _extract_address(self, entity: Dict) -> Dict[str, str]:
        """Extract address information"""
        address_data = entity.get('coreData', {}).get('physicalAddress', {})
        
        return {
            'address_line_1': address_data.get('addressLine1', ''),
            'address_line_2': address_data.get('addressLine2', ''),
            'city': address_data.get('city', ''),
            'state': address_data.get('stateOrProvinceCode', ''),
            'zip_code': address_data.get('zipCode', ''),
            'country': address_data.get('countryCode', '')
        }

class USASpendingScraper(BaseProcurementScraper):
    """Scraper for USASpending.gov API"""
    
    def __init__(self, source):
        super().__init__(source)
        self._health_check_endpoint = "/api/v2/awards/count/"
        
        self.endpoints = {
            'awards': "/api/v2/search/spending_by_award/",
            'transactions': "/api/v2/search/spending_by_transaction/",
            'recipients': "/api/v2/recipient/",
            'agencies': "/api/v2/references/agency/"
        }
    
    async def _fetch_source_data(self) -> List[Dict[str, Any]]:
        """Fetch contract data from USASpending.gov"""
        contracts = []
        
        try:
            # Build search filters
            filters = self._build_search_filters()
            
            # Search for contracts
            search_payload = {
                "filters": filters,
                "fields": [
                    "Award ID",
                    "Recipient Name", 
                    "Award Amount",
                    "Award Date",
                    "Period of Performance Start Date",
                    "Period of Performance Current End Date",
                    "Awarding Agency",
                    "Funding Agency",
                    "Award Type",
                    "def_codes"
                ],
                "page": 1,
                "limit": 100,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            response = await self._make_request('POST', self.endpoints['awards'], json=search_payload)
            
            if response and 'results' in response:
                for award in response['results']:
                    contract = {
                        'award_id': award.get('Award ID'),
                        'recipient_name': award.get('Recipient Name'),
                        'award_amount': self._parse_amount(award.get('Award Amount')),
                        'award_date': award.get('Award Date'),
                        'start_date': award.get('Period of Performance Start Date'),
                        'end_date': award.get('Period of Performance Current End Date'),
                        'awarding_agency': award.get('Awarding Agency'),
                        'funding_agency': award.get('Funding Agency'),
                        'award_type': award.get('Award Type'),
                        'naics_code': award.get('def_codes', [{}])[0].get('naics') if award.get('def_codes') else None,
                        'usaspending_data_type': 'contract'
                    }
                    contracts.append(contract)
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error fetching USASpending data: {e}")
            return []
    
    def _build_search_filters(self) -> Dict:
        """Build search filters for USASpending API"""
        filters = {
            "award_type_codes": ["A", "B", "C", "D"],  # Contract types
            "time_period": [
                {
                    "start_date": (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d'),
                    "end_date": datetime.utcnow().strftime('%Y-%m-%d')
                }
            ]
        }
        
        # Add additional filters from configuration
        config_filters = self.extraction_config.get('filters', {})
        filters.update(config_filters)
        
        return filters
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse amount string to float"""
        if not amount_str:
            return None
        
        try:
            # Remove currency symbols and commas
            clean_amount = str(amount_str).replace('$', '').replace(',', '')
            return float(clean_amount)
        except (ValueError, TypeError):
            return None
    
    async def get_company_contracts(self, uei: str) -> List[Dict[str, Any]]:
        """Get contracts for specific company from USASpending"""
        filters = {
            "recipient_search_text": [uei],
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [
                {
                    "start_date": (datetime.utcnow() - timedelta(days=1825)).strftime('%Y-%m-%d'),  # 5 years
                    "end_date": datetime.utcnow().strftime('%Y-%m-%d')
                }
            ]
        }
        
        search_payload = {
            "filters": filters,
            "fields": [
                "Award ID",
                "Award Amount", 
                "Award Date",
                "Awarding Agency",
                "Award Type"
            ],
            "page": 1,
            "limit": 100
        }
        
        try:
            response = await self._make_request('POST', self.endpoints['awards'], json=search_payload)
            
            contracts = []
            if response and 'results' in response:
                for award in response['results']:
                    contract = {
                        'award_id': award.get('Award ID'),
                        'award_amount': self._parse_amount(award.get('Award Amount')),
                        'award_date': award.get('Award Date'),
                        'awarding_agency': award.get('Awarding Agency'),
                        'award_type': award.get('Award Type'),
                        'source': 'usaspending'
                    }
                    contracts.append(contract)
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error fetching company contracts from USASpending: {e}")
            return []

class FPDSScraper(BaseProcurementScraper):
    """Scraper for FPDS-NG (Federal Procurement Data System)"""
    
    def __init__(self, source):
        super().__init__(source)
        self.api_base = "https://www.fpds.gov/ezsearch/FEEDS/ATOM"
        
    async def _fetch_source_data(self) -> List[Dict[str, Any]]:
        """Fetch contract data from FPDS-NG XML feeds"""
        contracts = []
        
        try:
            # FPDS uses ATOM feeds - construct query parameters
            params = {
                'FEEDNAME': 'PUBLIC',
                'VERSION': '1.4',
                'q': self._build_fpds_query()
            }
            
            response = await self.client.get(self.api_base, params=params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.text)
            
            # Extract contract data from XML
            contracts = self._parse_fpds_xml(root)
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error fetching FPDS data: {e}")
            return []
    
    def _build_fpds_query(self) -> str:
        """Build FPDS query string"""
        # Default query for recent contracts
        base_query = f"LAST_MOD_DATE:[{(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')} TO {datetime.utcnow().strftime('%Y-%m-%d')}]"
        
        # Add additional filters from configuration
        if 'agency_code' in self.extraction_config:
            base_query += f" AND CONTRACTING_AGENCY_CODE:{self.extraction_config['agency_code']}"
        
        if 'naics_code' in self.extraction_config:
            base_query += f" AND NAICS_CODE:{self.extraction_config['naics_code']}"
        
        return base_query
    
    def _parse_fpds_xml(self, root) -> List[Dict[str, Any]]:
        """Parse FPDS XML response into contract records"""
        contracts = []
        
        # XML namespace handling for FPDS
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'fpds': 'https://www.fpds.gov/FPDSNG_CG_Integration_Services_3-4'
        }
        
        for entry in root.findall('.//atom:entry', namespaces):
            try:
                contract = self._extract_contract_from_entry(entry, namespaces)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Error parsing FPDS entry: {e}")
                continue
        
        return contracts
    
    def _extract_contract_from_entry(self, entry, namespaces) -> Optional[Dict[str, Any]]:
        """Extract contract data from single XML entry"""
        contract = {}
        
        try:
            # Extract basic contract information
            contract['piid'] = self._get_xml_text(entry, './/fpds:PIID', namespaces)
            contract['agency_name'] = self._get_xml_text(entry, './/fpds:CONTRACTING_AGENCY_NAME', namespaces)
            contract['vendor_name'] = self._get_xml_text(entry, './/fpds:VENDOR_NAME', namespaces)
            contract['award_amount'] = self._get_xml_float(entry, './/fpds:FEDERAL_ACTION_OBLIGATION', namespaces)
            contract['signed_date'] = self._get_xml_text(entry, './/fpds:SIGNED_DATE', namespaces)
            contract['naics_code'] = self._get_xml_text(entry, './/fpds:NAICS_CODE', namespaces)
            contract['place_of_performance_state'] = self._get_xml_text(entry, './/fpds:PLACE_OF_PERFORMANCE_STATE', namespaces)
            
            contract['fpds_data_type'] = 'contract'
            
            return contract
            
        except Exception as e:
            logger.error(f"Error extracting contract data: {e}")
            return None
    
    def _get_xml_text(self, element, xpath: str, namespaces: Dict) -> Optional[str]:
        """Safely extract text from XML element"""
        found = element.find(xpath, namespaces)
        return found.text if found is not None else None
    
    def _get_xml_float(self, element, xpath: str, namespaces: Dict) -> Optional[float]:
        """Safely extract float value from XML element"""
        text = self._get_xml_text(element, xpath, namespaces)
        if text:
            try:
                return float(text)
            except ValueError:
                return None
        return None