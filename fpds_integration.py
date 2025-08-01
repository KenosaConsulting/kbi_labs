#!/usr/bin/env python3
"""
FPDS (Federal Procurement Data System) Integration
No authentication required - Public SOAP/XML web services
"""

import asyncio
import aiohttp
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import xml.etree.ElementTree as ET
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FPDSProcessor:
    """
    Integrates FPDS API for comprehensive federal procurement data
    Provides historical contract performance and procurement analytics
    """
    
    def __init__(self, base_url: str = "https://www.fpds.gov/ezsearch/FEEDS/ATOM"):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 2.0  # Conservative delay for government systems
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'KBI-Labs-FPDS-Integration/1.0',
                'Accept': 'application/atom+xml, application/xml, text/xml'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def search_contracts_by_duns(self, duns: str, days_back: int = 365) -> Optional[Dict[str, Any]]:
        """
        Search contracts by DUNS number
        FPDS uses DUNS as primary identifier (legacy before UEI)
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'VENDORDUNS': duns,
            'LAST_MOD_DATE': f"[{start_date.strftime('%Y/%m/%d')},{end_date.strftime('%Y/%m/%d')}]",
            'sortBy': '-dollarsobligated',
            'max': '100'
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    return self._parse_fpds_xml(xml_content, duns)
                else:
                    logger.debug(f"FPDS API status {response.status} for DUNS: {duns}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching FPDS data for DUNS {duns}: {e}")
            return None

    async def search_contracts_by_vendor_name(self, vendor_name: str, days_back: int = 365) -> Optional[Dict[str, Any]]:
        """
        Search contracts by vendor name
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'VENDOR_NAME': vendor_name,
            'LAST_MOD_DATE': f"[{start_date.strftime('%Y/%m/%d')},{end_date.strftime('%Y/%m/%d')}]",
            'sortBy': '-dollarsobligated',
            'max': '100'
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    return self._parse_fpds_xml(xml_content, vendor_name)
                else:
                    logger.debug(f"FPDS API status {response.status} for vendor: {vendor_name}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching FPDS data for vendor {vendor_name}: {e}")
            return None

    async def get_agency_spending_analysis(self, agency_code: str, days_back: int = 365) -> Optional[Dict[str, Any]]:
        """
        Analyze spending patterns by agency
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'CONTRACTING_AGENCY_CODE': agency_code,
            'LAST_MOD_DATE': f"[{start_date.strftime('%Y/%m/%d')},{end_date.strftime('%Y/%m/%d')}]",
            'sortBy': '-dollarsobligated',
            'max': '500'
        }
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    return self._parse_agency_spending(xml_content, agency_code)
                else:
                    logger.debug(f"FPDS API status {response.status} for agency: {agency_code}")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching agency spending for {agency_code}: {e}")
            return None

    async def search_small_business_contracts(self, naics_code: str = None, days_back: int = 365) -> Optional[Dict[str, Any]]:
        """
        Search for small business set-aside contracts
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'SMALL_BUSINESS_COMPETITIVENESS_DEMONSTRATION_PROGRAM': 'Y',
            'LAST_MOD_DATE': f"[{start_date.strftime('%Y/%m/%d')},{end_date.strftime('%Y/%m/%d')}]",
            'sortBy': '-dollarsobligated',
            'max': '200'
        }
        
        if naics_code:
            params['PRINCIPAL_NAICS_CODE'] = naics_code
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    xml_content = await response.text()
                    return self._parse_small_business_contracts(xml_content)
                else:
                    logger.debug(f"FPDS API status {response.status} for small business search")
                    return None
                    
        except Exception as e:
            logger.debug(f"Error fetching small business contracts: {e}")
            return None

    def _parse_fpds_xml(self, xml_content: str, search_term: str) -> Dict[str, Any]:
        """
        Parse FPDS XML response and extract contract data
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Handle different XML namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'fpds': 'https://www.fpds.gov/FPDS'
            }
            
            contracts = []
            total_value = 0
            
            # Find all entry elements
            entries = root.findall('.//atom:entry', namespaces)
            
            for entry in entries:
                contract_data = self._extract_contract_data(entry, namespaces)
                if contract_data:
                    contracts.append(contract_data)
                    # Add to total value
                    value = contract_data.get('dollars_obligated', 0)
                    if isinstance(value, (int, float)):
                        total_value += value
            
            # Calculate analytics
            analysis = self._calculate_contract_analytics(contracts)
            
            return {
                'search_term': search_term,
                'total_contracts': len(contracts),
                'total_value': total_value,
                'contracts': contracts,
                'analytics': analysis,
                'searched_at': datetime.now().isoformat()
            }
            
        except ET.ParseError as e:
            logger.error(f"Error parsing FPDS XML: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing FPDS data: {e}")
            return None

    def _extract_contract_data(self, entry: ET.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Extract individual contract data from XML entry
        """
        try:
            contract = {}
            
            # Basic contract info
            contract['title'] = self._get_xml_text(entry, './/atom:title', namespaces)
            contract['updated'] = self._get_xml_text(entry, './/atom:updated', namespaces)
            contract['link'] = self._get_xml_attr(entry, './/atom:link', 'href', namespaces)
            
            # Contract details from content
            content = entry.find('.//atom:content', namespaces)
            if content is not None:
                # Extract key procurement fields
                contract['piid'] = self._get_xml_text(content, './/fpds:PIID', namespaces)
                contract['modification_number'] = self._get_xml_text(content, './/fpds:MODIFICATION_NUMBER', namespaces)
                contract['agency_name'] = self._get_xml_text(content, './/fpds:CONTRACTING_AGENCY_NAME', namespaces)
                contract['vendor_name'] = self._get_xml_text(content, './/fpds:VENDOR_NAME', namespaces)
                contract['vendor_duns'] = self._get_xml_text(content, './/fpds:VENDOR_DUNS_NUMBER', namespaces)
                
                # Financial data
                dollars_obligated = self._get_xml_text(content, './/fpds:DOLLARS_OBLIGATED', namespaces)
                contract['dollars_obligated'] = float(dollars_obligated) if dollars_obligated else 0
                
                base_value = self._get_xml_text(content, './/fpds:BASE_AND_EXERCISED_OPTIONS_VALUE', namespaces)
                contract['base_and_options_value'] = float(base_value) if base_value else 0
                
                # Contract characteristics
                contract['contract_type'] = self._get_xml_text(content, './/fpds:TYPE_OF_CONTRACT', namespaces)
                contract['naics_code'] = self._get_xml_text(content, './/fpds:PRINCIPAL_NAICS_CODE', namespaces)
                contract['naics_description'] = self._get_xml_text(content, './/fpds:NAICS_DESCRIPTION', namespaces)
                contract['product_service_code'] = self._get_xml_text(content, './/fpds:PRODUCT_OR_SERVICE_CODE', namespaces)
                
                # Dates
                contract['effective_date'] = self._get_xml_text(content, './/fpds:EFFECTIVE_DATE', namespaces)
                contract['signed_date'] = self._get_xml_text(content, './/fpds:SIGNED_DATE', namespaces)
                
                # Small business indicators
                contract['small_business'] = self._get_xml_text(content, './/fpds:SMALL_BUSINESS_COMPETITIVENESS_DEMONSTRATION_PROGRAM', namespaces)
                contract['woman_owned_small_business'] = self._get_xml_text(content, './/fpds:WOMEN_OWNED_SMALL_BUSINESS', namespaces)
                contract['veteran_owned_small_business'] = self._get_xml_text(content, './/fpds:VETERAN_OWNED_SMALL_BUSINESS', namespaces)
                
            return contract
            
        except Exception as e:
            logger.debug(f"Error extracting contract data: {e}")
            return None

    def _get_xml_text(self, element: ET.Element, xpath: str, namespaces: Dict[str, str]) -> Optional[str]:
        """Helper to safely get XML text content"""
        try:
            found = element.find(xpath, namespaces)
            return found.text if found is not None else None
        except:
            return None

    def _get_xml_attr(self, element: ET.Element, xpath: str, attr: str, namespaces: Dict[str, str]) -> Optional[str]:
        """Helper to safely get XML attribute"""
        try:
            found = element.find(xpath, namespaces)
            return found.get(attr) if found is not None else None
        except:
            return None

    def _calculate_contract_analytics(self, contracts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate procurement analytics from contract data
        """
        if not contracts:
            return {}
        
        # Financial analytics
        values = [c.get('dollars_obligated', 0) for c in contracts if c.get('dollars_obligated')]
        total_value = sum(values)
        
        analytics = {
            'contract_count': len(contracts),
            'total_value': total_value,
            'average_value': total_value / len(values) if values else 0,
            'median_value': sorted(values)[len(values) // 2] if values else 0
        }
        
        # Agency breakdown
        agencies = {}
        for contract in contracts:
            agency = contract.get('agency_name', 'Unknown')
            if agency not in agencies:
                agencies[agency] = {'count': 0, 'value': 0}
            agencies[agency]['count'] += 1
            agencies[agency]['value'] += contract.get('dollars_obligated', 0)
        
        analytics['top_agencies'] = sorted(
            agencies.items(), 
            key=lambda x: x[1]['value'], 
            reverse=True
        )[:5]
        
        # NAICS breakdown
        naics = {}
        for contract in contracts:
            code = contract.get('naics_code', 'Unknown')
            desc = contract.get('naics_description', 'Unknown')
            key = f"{code}: {desc}"
            if key not in naics:
                naics[key] = {'count': 0, 'value': 0}
            naics[key]['count'] += 1
            naics[key]['value'] += contract.get('dollars_obligated', 0)
        
        analytics['top_naics'] = sorted(
            naics.items(),
            key=lambda x: x[1]['value'],
            reverse=True
        )[:5]
        
        # Small business analysis
        small_biz_contracts = [c for c in contracts if c.get('small_business') == 'Y']
        analytics['small_business_percentage'] = (len(small_biz_contracts) / len(contracts)) * 100 if contracts else 0
        analytics['small_business_value'] = sum(c.get('dollars_obligated', 0) for c in small_biz_contracts)
        
        return analytics

    def _parse_agency_spending(self, xml_content: str, agency_code: str) -> Dict[str, Any]:
        """
        Parse agency-specific spending data
        """
        base_data = self._parse_fpds_xml(xml_content, f"Agency-{agency_code}")
        if base_data:
            # Add agency-specific analytics
            contracts = base_data.get('contracts', [])
            
            # Vendor concentration analysis
            vendors = {}
            for contract in contracts:
                vendor = contract.get('vendor_name', 'Unknown')
                if vendor not in vendors:
                    vendors[vendor] = {'count': 0, 'value': 0}
                vendors[vendor]['count'] += 1
                vendors[vendor]['value'] += contract.get('dollars_obligated', 0)
            
            base_data['analytics']['top_vendors'] = sorted(
                vendors.items(),
                key=lambda x: x[1]['value'],
                reverse=True 
            )[:10]
            
            # Competition analysis
            competed = len([c for c in contracts if 'competed' in str(c.get('title', '')).lower()])
            base_data['analytics']['competition_rate'] = (competed / len(contracts)) * 100 if contracts else 0
        
        return base_data

    def _parse_small_business_contracts(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse small business set-aside contracts
        """
        base_data = self._parse_fpds_xml(xml_content, "Small-Business-Setasides")
        if base_data:
            contracts = base_data.get('contracts', [])
            
            # Set-aside type analysis
            setaside_types = {
                'Total Small Business': 0,
                'Women-Owned Small Business': 0,
                'Veteran-Owned Small Business': 0,
                'Service-Disabled Veteran-Owned': 0,
                'HUBZone': 0,
                '8(a) Program': 0
            }
            
            for contract in contracts:
                if contract.get('small_business') == 'Y':
                    setaside_types['Total Small Business'] += contract.get('dollars_obligated', 0)
                if contract.get('woman_owned_small_business') == 'Y':
                    setaside_types['Women-Owned Small Business'] += contract.get('dollars_obligated', 0)
                if contract.get('veteran_owned_small_business') == 'Y':
                    setaside_types['Veteran-Owned Small Business'] += contract.get('dollars_obligated', 0)
            
            base_data['analytics']['setaside_breakdown'] = setaside_types
        
        return base_data

    async def enrich_company_with_fpds_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich company data with FPDS historical performance data
        """
        company_name = company_data.get('Organization Name', '')
        duns = company_data.get('DUNS Number', '')
        
        enhanced_data = company_data.copy()
        
        if not company_name and not duns:
            return enhanced_data
        
        logger.info(f"Enriching {company_name} with FPDS historical data")
        
        # Try DUNS first if available, then company name
        fpds_data = None
        if duns:
            fpds_data = await self.search_contracts_by_duns(str(duns))
        
        if not fpds_data and company_name:
            fpds_data = await self.search_contracts_by_vendor_name(company_name)
        
        if fpds_data and fpds_data.get('contracts'):
            enhanced_data['fpds_found'] = True
            enhanced_data['fpds_total_contracts'] = fpds_data.get('total_contracts', 0)
            enhanced_data['fpds_total_value'] = fpds_data.get('total_value', 0)
            
            analytics = fpds_data.get('analytics', {})
            enhanced_data['fpds_avg_contract_value'] = analytics.get('average_value', 0)
            enhanced_data['fpds_small_business_pct'] = analytics.get('small_business_percentage', 0)
            
            # Top agencies
            top_agencies = analytics.get('top_agencies', [])
            enhanced_data['fpds_primary_agencies'] = [agency[0] for agency in top_agencies[:3]]
            
            # Performance indicators
            enhanced_data['fpds_performance_score'] = self._calculate_performance_score(fpds_data)
            
            logger.info(f"✅ Found {enhanced_data['fpds_total_contracts']} FPDS contracts worth ${enhanced_data['fpds_total_value']:,.2f}")
        else:
            enhanced_data['fpds_found'] = False
            enhanced_data['fpds_total_contracts'] = 0
            enhanced_data['fpds_total_value'] = 0
            enhanced_data['fpds_performance_score'] = 0
        
        return enhanced_data

    def _calculate_performance_score(self, fpds_data: Dict[str, Any]) -> int:
        """
        Calculate a performance score based on FPDS data
        """
        score = 0
        contracts = fpds_data.get('contracts', [])
        analytics = fpds_data.get('analytics', {})
        
        # Volume bonus (up to 30 points)
        contract_count = len(contracts)
        if contract_count >= 50:
            score += 30
        elif contract_count >= 20:
            score += 20
        elif contract_count >= 5:
            score += 10
        
        # Value bonus (up to 25 points)
        total_value = fpds_data.get('total_value', 0)
        if total_value >= 10000000:  # $10M+
            score += 25
        elif total_value >= 1000000:  # $1M+
            score += 15
        elif total_value >= 100000:  # $100K+
            score += 10
        
        # Diversity bonus (up to 15 points)
        agencies = analytics.get('top_agencies', [])
        if len(agencies) >= 3:
            score += 15
        elif len(agencies) >= 2:
            score += 10
        
        # Recent activity bonus (up to 15 points)
        recent_contracts = [
            c for c in contracts 
            if c.get('signed_date') and 
            datetime.fromisoformat(c['signed_date'].replace('Z', '+00:00')).year >= datetime.now().year - 2
        ]
        if len(recent_contracts) >= 5:
            score += 15
        elif len(recent_contracts) >= 2:
            score += 10
        
        # Small business participation (up to 15 points)
        sb_pct = analytics.get('small_business_percentage', 0)
        if sb_pct >= 75:
            score += 15
        elif sb_pct >= 50:
            score += 10
        elif sb_pct >= 25:
            score += 5
        
        return min(score, 100)  # Cap at 100

# CLI interface
async def main():
    """
    Main execution function for FPDS integration
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='FPDS Integration for Federal Procurement Data')
    parser.add_argument('--mode', choices=['vendor', 'duns', 'agency', 'smallbiz'], default='vendor',
                       help='Search mode')
    parser.add_argument('--query', '-q', required=True, help='Search query')
    parser.add_argument('--days', '-d', type=int, default=365, help='Days back to search')
    parser.add_argument('--output', '-o', help='Output JSON file')
    
    args = parser.parse_args()
    
    async with FPDSProcessor() as processor:
        result = None
        
        if args.mode == 'vendor':
            result = await processor.search_contracts_by_vendor_name(args.query, args.days)
        elif args.mode == 'duns':
            result = await processor.search_contracts_by_duns(args.query, args.days)
        elif args.mode == 'agency':
            result = await processor.get_agency_spending_analysis(args.query, args.days)
        elif args.mode == 'smallbiz':
            result = await processor.search_small_business_contracts(args.query, args.days)
        
        if result:
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"Results saved to: {args.output}")
            else:
                print(json.dumps(result, indent=2, default=str))
        else:
            print(f"No data found for query: {args.query}")

if __name__ == "__main__":
    asyncio.run(main())