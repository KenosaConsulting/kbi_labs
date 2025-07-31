#!/usr/bin/env python3
"""
SEC EDGAR API Integration for KBI Labs
Provides comprehensive financial intelligence and compliance monitoring
"""

import aiohttp
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SECCompanyInfo:
    cik: str
    name: str
    ticker: Optional[str]
    exchange: Optional[str]
    sic: Optional[str]
    business_address: Optional[Dict]
    
@dataclass
class SECFiling:
    accession_number: str
    filing_date: str
    report_date: str
    form: str
    file_number: str
    items: Optional[str]
    size: int
    is_xbrl: bool
    is_inline_xbrl: bool

class SECEdgarAPI:
    """
    SEC EDGAR API client for financial intelligence
    
    Features:
    - Company registration & filing data
    - Financial statements (10-K, 10-Q, 8-K)
    - Risk factor analysis
    - Insider trading activity
    - Real-time filing alerts
    """
    
    def __init__(self, user_agent: str = "KBI Labs Business Intelligence Platform admin@kbilabs.com"):
        self.base_url = "https://data.sec.gov"
        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        }
        self.rate_limit = 10  # requests per second (SEC limit)
        self.session = None
        
    async def __aenter__(self):
        # Create SSL context that works with SEC.gov
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _normalize_cik(self, cik: str) -> str:
        """Normalize CIK to 10-digit format with leading zeros"""
        # Remove any non-numeric characters
        cik_clean = re.sub(r'[^\d]', '', str(cik))
        # Pad with leading zeros to 10 digits
        return cik_clean.zfill(10)
    
    async def _rate_limited_request(self, url: str) -> Dict:
        """Make rate-limited request to SEC API"""
        if not self.session:
            raise RuntimeError("SEC API session not initialized. Use 'async with' context.")
            
        try:
            # SEC allows 10 requests/second, so we add small delay
            await asyncio.sleep(0.1)
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limited - wait and retry
                    logger.warning("SEC API rate limited, waiting...")
                    await asyncio.sleep(1)
                    return await self._rate_limited_request(url)
                else:
                    response.raise_for_status()
                    
        except Exception as e:
            logger.error(f"SEC API request failed for {url}: {e}")
            raise
    
    async def get_company_info(self, cik: str) -> Optional[SECCompanyInfo]:
        """Get basic company information by CIK"""
        cik_normalized = self._normalize_cik(cik)
        url = f"{self.base_url}/submissions/CIK{cik_normalized}.json"
        
        try:
            data = await self._rate_limited_request(url)
            
            return SECCompanyInfo(
                cik=cik_normalized,
                name=data.get('name', ''),
                ticker=data.get('tickers', [None])[0] if data.get('tickers') else None,
                exchange=data.get('exchanges', [None])[0] if data.get('exchanges') else None,
                sic=data.get('sic', ''),
                business_address=data.get('addresses', {}).get('business')
            )
            
        except Exception as e:
            logger.error(f"Failed to get company info for CIK {cik}: {e}")
            return None
    
    async def get_company_filings(self, cik: str, form_type: Optional[str] = None, 
                                limit: int = 100) -> List[SECFiling]:
        """Get company filings with optional form type filter"""
        cik_normalized = self._normalize_cik(cik)
        url = f"{self.base_url}/submissions/CIK{cik_normalized}.json"
        
        try:
            data = await self._rate_limited_request(url)
            filings_data = data.get('filings', {}).get('recent', {})
            
            filings = []
            forms = filings_data.get('form', [])
            accession_numbers = filings_data.get('accessionNumber', [])
            filing_dates = filings_data.get('filingDate', [])
            report_dates = filings_data.get('reportDate', [])
            
            for i in range(min(len(forms), limit)):
                form = forms[i]
                
                # Filter by form type if specified
                if form_type and form.upper() != form_type.upper():
                    continue
                    
                filing = SECFiling(
                    accession_number=accession_numbers[i],
                    filing_date=filing_dates[i],
                    report_date=report_dates[i],
                    form=form,
                    file_number=filings_data.get('fileNumber', [''])[i],
                    items=filings_data.get('items', [''])[i],
                    size=filings_data.get('size', [0])[i],
                    is_xbrl=bool(filings_data.get('isXBRL', [0])[i]),
                    is_inline_xbrl=bool(filings_data.get('isInlineXBRL', [0])[i])
                )
                filings.append(filing)
                
            return filings[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get filings for CIK {cik}: {e}")
            return []
    
    async def get_company_facts(self, cik: str) -> Dict[str, Any]:
        """Get company financial facts (key metrics from XBRL filings)"""
        cik_normalized = self._normalize_cik(cik)
        url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik_normalized}.json"
        
        try:
            data = await self._rate_limited_request(url)
            return data
            
        except Exception as e:
            logger.error(f"Failed to get company facts for CIK {cik}: {e}")
            return {}
    
    async def get_financial_metrics(self, cik: str) -> Dict[str, Any]:
        """Extract key financial metrics from company facts"""
        facts = await self.get_company_facts(cik)
        
        if not facts:
            return {}
            
        # Extract US-GAAP metrics
        us_gaap = facts.get('facts', {}).get('us-gaap', {})
        
        # Key financial metrics to extract
        key_metrics = {
            'Revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax'],
            'Assets': ['Assets'],
            'Liabilities': ['Liabilities'],
            'Equity': ['StockholdersEquity'],
            'NetIncome': ['NetIncomeLoss'],
            'CashAndCashEquivalents': ['CashAndCashEquivalentsAtCarryingValue'],
            'TotalDebt': ['DebtCurrent', 'DebtNoncurrent']
        }
        
        extracted_metrics = {}
        
        for metric_name, possible_fields in key_metrics.items():
            for field in possible_fields:
                if field in us_gaap:
                    # Get most recent annual data (10-K)
                    units_data = us_gaap[field].get('units', {})
                    if 'USD' in units_data:
                        annual_data = [
                            item for item in units_data['USD'] 
                            if item.get('form') == '10-K'
                        ]
                        if annual_data:
                            # Sort by end date, get most recent
                            annual_data.sort(key=lambda x: x.get('end', ''), reverse=True)
                            extracted_metrics[metric_name] = {
                                'value': annual_data[0].get('val'),
                                'end_date': annual_data[0].get('end'),
                                'filed_date': annual_data[0].get('filed'),
                                'form': annual_data[0].get('form')
                            }
                            break
        
        return extracted_metrics
    
    async def search_by_ticker(self, ticker: str) -> Optional[SECCompanyInfo]:
        """Search for company by stock ticker"""
        # SEC doesn't have direct ticker search, but we can use company-tickers.json
        url = f"{self.base_url}/files/company_tickers.json"
        
        try:
            data = await self._rate_limited_request(url)
            
            # Search through the ticker data
            for company_data in data.values():
                if company_data.get('ticker', '').upper() == ticker.upper():
                    cik = str(company_data.get('cik_str', '')).zfill(10)
                    return await self.get_company_info(cik)
                    
            return None
            
        except Exception as e:
            logger.error(f"Failed to search by ticker {ticker}: {e}")
            return None
    
    async def get_risk_factors(self, cik: str) -> List[str]:
        """Extract risk factors from most recent 10-K filing"""
        # Get recent 10-K filing
        filings = await self.get_company_filings(cik, form_type='10-K', limit=1)
        
        if not filings:
            return []
            
        # For now, return placeholder - full implementation would parse HTML filing
        # This would require additional HTML/XML parsing logic
        return [
            "Implementation note: Risk factor extraction requires HTML parsing of filing documents",
            f"Most recent 10-K filing: {filings[0].accession_number} dated {filings[0].filing_date}",
            "Risk factors would be extracted from Item 1A of the 10-K filing"
        ]
    
    async def get_insider_activity(self, cik: str) -> List[Dict]:
        """Get insider trading activity (Form 4 filings)"""
        filings = await self.get_company_filings(cik, form_type='4', limit=20)
        
        insider_activity = []
        for filing in filings:
            insider_activity.append({
                'filing_date': filing.filing_date,
                'accession_number': filing.accession_number,
                'form': filing.form,
                'file_number': filing.file_number,
                'note': 'Full insider transaction details require HTML parsing of Form 4'
            })
            
        return insider_activity

# Utility functions for CIK lookup
async def find_company_cik(company_name: str) -> Optional[str]:
    """Find CIK by company name (fuzzy search)"""
    async with SECEdgarAPI() as sec_api:
        url = f"{sec_api.base_url}/files/company_tickers.json"
        
        try:
            data = await sec_api._rate_limited_request(url)
            
            # Fuzzy search through company names
            company_name_lower = company_name.lower()
            best_match = None
            best_score = 0
            
            for company_data in data.values():
                name = company_data.get('title', '').lower()
                # Simple fuzzy matching - count common words
                common_words = len(set(company_name_lower.split()) & set(name.split()))
                if common_words > best_score:
                    best_score = common_words
                    best_match = str(company_data.get('cik_str', '')).zfill(10)
            
            return best_match if best_score > 0 else None
            
        except Exception as e:
            logger.error(f"Failed to find CIK for company {company_name}: {e}")
            return None

# Example usage and testing
async def test_sec_edgar_api():
    """Test SEC EDGAR API functionality"""
    async with SECEdgarAPI() as sec_api:
        # Test with Apple Inc. (CIK: 0000320193)
        print("🔍 Testing SEC EDGAR API with Apple Inc...")
        
        # Get company info
        company_info = await sec_api.get_company_info("320193")
        if company_info:
            print(f"✅ Company: {company_info.name}")
            print(f"   Ticker: {company_info.ticker}")
            print(f"   Exchange: {company_info.exchange}")
        
        # Get recent filings
        filings = await sec_api.get_company_filings("320193", limit=5)
        print(f"✅ Found {len(filings)} recent filings")
        for filing in filings[:3]:
            print(f"   {filing.form} filed {filing.filing_date}")
        
        # Get financial metrics
        metrics = await sec_api.get_financial_metrics("320193")
        print(f"✅ Extracted {len(metrics)} financial metrics")
        for metric, data in list(metrics.items())[:3]:
            if data:
                print(f"   {metric}: ${data['value']:,.0f} ({data['end_date']})")

if __name__ == "__main__":
    asyncio.run(test_sec_edgar_api())