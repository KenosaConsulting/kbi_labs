#!/usr/bin/env python3
"""
USASpending.gov API Integration for KBI Labs (Fixed)
Provides access to federal spending data
"""
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

class USASpendingAPI:
    """Client for USASpending.gov API"""
    
    BASE_URL = "https://api.usaspending.gov/api/v2"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'KBI Labs Enrichment Platform/1.0',
            'Content-Type': 'application/json'
        })
        
    def search_awards_by_recipient(self, uei: str, fiscal_year: Optional[int] = None) -> Dict:
        """
        Search for federal awards by recipient UEI using the correct endpoint
        """
        try:
            # Use the advanced search endpoint
            endpoint = f"{self.BASE_URL}/search/spending_by_award/"
            
            # Build the request payload
            payload = {
                "filters": {
                    "recipient_unique_id": uei,
                    "award_type_codes": ["A", "B", "C", "D"]  # All contract types
                },
                "fields": [
                    "Award ID",
                    "Recipient Name",
                    "Award Amount",
                    "Total Outlays",
                    "Contract Award Type",
                    "Description",
                    "Start Date",
                    "End Date",
                    "Awarding Agency",
                    "Awarding Sub Agency",
                    "Place of Performance State Code",
                    "Place of Performance Country Code",
                    "NAICS Code",
                    "NAICS Description"
                ],
                "page": 1,
                "limit": 100,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            if fiscal_year:
                payload["filters"]["time_period"] = [{
                    "start_date": f"{fiscal_year}-10-01",
                    "end_date": f"{fiscal_year + 1}-09-30"
                }]
            
            logger.info(f"Searching USASpending for UEI: {uei}")
            start_time = time.time()
            
            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            logger.info(f"USASpending API response time: {elapsed:.2f}s, Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                # If no results with UEI, try alternate search
                if not results:
                    logger.info(f"No results for UEI {uei}, trying recipient search")
                    return self.search_by_recipient_name(uei)
                
                return {
                    "success": True,
                    "results": results,
                    "total": data.get("total", 0),
                    "response_time": elapsed
                }
            else:
                logger.error(f"USASpending API error: {response.status_code}, Response: {response.text[:200]}")
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "details": response.text[:500],
                    "response_time": elapsed
                }
                
        except requests.exceptions.Timeout:
            logger.error("USASpending API timeout")
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"USASpending API error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def search_by_recipient_name(self, search_text: str) -> Dict:
        """
        Search by recipient name as fallback
        """
        try:
            endpoint = f"{self.BASE_URL}/autocomplete/funding_agency/"
            
            # First, try to find the recipient
            recipient_endpoint = f"{self.BASE_URL}/autocomplete/recipient/"
            
            payload = {
                "search_text": search_text,
                "limit": 10
            }
            
            response = self.session.post(
                recipient_endpoint,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    # Get the first matching recipient
                    recipient = results[0]
                    recipient_id = recipient.get("recipient_unique_id", recipient.get("uei"))
                    
                    if recipient_id:
                        # Now search for awards
                        return self.search_awards_by_recipient(recipient_id)
                
            return {
                "success": False,
                "error": "No matching recipients found",
                "search_text": search_text
            }
            
        except Exception as e:
            logger.error(f"Error in recipient name search: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_awards_summary(self, uei: str) -> Dict:
        """
        Get summary of all awards for a recipient
        """
        try:
            spending_data = self.search_awards_by_recipient(uei)
            
            if not spending_data.get("success", False):
                return spending_data
            
            results = spending_data.get("results", [])
            
            if not results:
                return {
                    "success": True,
                    "summary": {
                        "total_awards": 0,
                        "total_amount": 0.0,
                        "total_outlays": 0.0,
                        "message": "No federal contracts found for this UEI"
                    }
                }
            
            # Calculate summary statistics
            total_awards = len(results)
            total_amount = sum(float(r.get("Award Amount", 0) or 0) for r in results)
            total_outlays = sum(float(r.get("Total Outlays", 0) or 0) for r in results)
            
            # Group by agency
            agencies = {}
            for r in results:
                agency = r.get("Awarding Agency", "Unknown")
                if agency not in agencies:
                    agencies[agency] = {
                        "count": 0,
                        "total_amount": 0.0
                    }
                agencies[agency]["count"] += 1
                agencies[agency]["total_amount"] += float(r.get("Award Amount", 0) or 0)
            
            # Group by NAICS
            naics_codes = {}
            for r in results:
                naics = r.get("NAICS Code", "Unknown")
                naics_desc = r.get("NAICS Description", "Unknown")
                if naics not in naics_codes:
                    naics_codes[naics] = {
                        "description": naics_desc,
                        "count": 0,
                        "total_amount": 0.0
                    }
                naics_codes[naics]["count"] += 1
                naics_codes[naics]["total_amount"] += float(r.get("Award Amount", 0) or 0)
            
            return {
                "success": True,
                "summary": {
                    "total_awards": total_awards,
                    "total_amount": total_amount,
                    "total_outlays": total_outlays,
                    "agencies": agencies,
                    "naics_codes": naics_codes,
                    "recent_awards": results[:5]  # Top 5 most recent
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating awards summary: {str(e)}")
            return {"success": False, "error": str(e)}

# Cache for performance
@lru_cache(maxsize=1000)
def get_cached_spending(uei: str) -> Dict:
    """Cached version of spending lookup"""
    client = USASpendingAPI()
    return client.get_awards_summary(uei)
