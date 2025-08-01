#!/usr/bin/env python3
"""
SAM.gov Integration with Redis Caching
Enriches SMB data with live federal contracting information
"""

import requests
import json
import redis
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional
import os

class CachedSAMGovAPI:
    def __init__(self, api_key: str, cache_ttl: int = 86400):  # 24 hour cache
        self.api_key = api_key
        self.base_url = "https://api.sam.gov/entity-information/v3/entities"
        self.cache_ttl = cache_ttl
        
        # Initialize Redis cache (install with: sudo apt install redis-server)
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()
            self.cache_enabled = True
            print("✅ Redis cache connected")
        except:
            self.cache_enabled = False
            print("⚠️  Redis not available, running without cache")
    
    def get_cache_key(self, uei: str) -> str:
        """Generate cache key for UEI"""
        return f"sam_gov:entity:{uei}"
    
    def get_entity(self, uei: str, force_refresh: bool = False) -> Optional[Dict]:
        """Get entity data with caching"""
        cache_key = self.get_cache_key(uei)
        
        # Check cache first
        if self.cache_enabled and not force_refresh:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                print(f"✅ Cache hit for {uei}")
                return json.loads(cached_data)
        
        # Fetch from API
        print(f"🔄 Fetching {uei} from SAM.gov API...")
        data = self._fetch_from_api(uei)
        
        # Cache the result
        if data and self.cache_enabled:
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )
        
        return data
    
    def _fetch_from_api(self, uei: str) -> Optional[Dict]:
        """Fetch entity data from SAM.gov API"""
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json"
        }
        
        params = {
            "ueiSAM": uei,
            "includeSections": "entityRegistration,coreData,assertions,repsAndCerts,pointsOfContact"
        }
        
        try:
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("totalRecords", 0) > 0:
                    return self._parse_entity(data["entityData"][0])
            elif response.status_code == 429:
                print("⚠️  Rate limit hit")
                return None
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ API Error: {e}")
            return None
    
    def _parse_entity(self, entity: Dict) -> Dict:
        """Parse SAM.gov entity data into enriched format"""
        reg = entity.get("entityRegistration", {})
        core = entity.get("coreData", {})
        assertions = entity.get("assertions", {})
        
        # Extract all certifications
        certs = []
        cert_data = assertions.get("certifications", {}).get("fARResponses", [])
        for cert in cert_data:
            if cert.get("answer") == "Y":
                certs.append(cert.get("section"))
        
        # Get NAICS codes
        naics_list = []
        for naics in assertions.get("naicsList", []):
            naics_list.append({
                "code": naics.get("naicsCode"),
                "description": naics.get("naicsDescription"),
                "primary": naics.get("primaryIndicator") == "Y"
            })
        
        # Business size determination
        size_metrics = assertions.get("certifications", {})
        
        return {
            # Registration info
            "sam_uei": reg.get("ueiSAM"),
            "cage_code": reg.get("cageCode"),
            "registration_status": reg.get("registrationStatus"),
            "registration_date": reg.get("registrationDate"),
            "expiration_date": reg.get("expirationDate"),
            "last_update": reg.get("updateDate"),
            
            # Business details
            "legal_name": reg.get("legalBusinessName"),
            "dba_names": reg.get("dbaName", []),
            
            # Location
            "physical_address": {
                "address": core.get("physicalAddress", {}).get("addressLine1"),
                "city": core.get("physicalAddress", {}).get("city"),
                "state": core.get("physicalAddress", {}).get("stateOrProvinceCode"),
                "zip": core.get("physicalAddress", {}).get("zipCode")
            },
            
            # Business metrics
            "entity_structure": core.get("entityStructure"),
            "entity_type": core.get("entityTypeDesc"),
            "annual_revenue": size_metrics.get("annualRevenue"),
            "employee_count": size_metrics.get("employeeCount"),
            "started_year": core.get("organizationStartDate", "")[:4] if core.get("organizationStartDate") else None,
            
            # Certifications
            "sba_certifications": certs,
            "naics_codes": naics_list,
            "business_types": [
                bt for bt, value in assertions.get("businessTypes", {}).items()
                if value == "Y"
            ],
            
            # Federal readiness
            "accepts_credit_cards": assertions.get("creditCardUsage") == "Y",
            "federal_debt_delinquent": reg.get("delinquentFederalDebt") == "Y",
            "exclusion_status": reg.get("exclusionStatus"),
            
            # Contacts
            "govt_business_poc": core.get("governmentBusinessPOC", {}),
            "electronic_business_poc": core.get("electronicBusinessPOC", {}),
            
            # Enhanced intelligence
            "federal_ready_score": self._calculate_federal_readiness(entity),
            "enrichment_date": datetime.now().isoformat()
        }
    
    def _calculate_federal_readiness(self, entity: Dict) -> int:
        """Calculate federal contracting readiness score"""
        score = 0
        
        reg = entity.get("entityRegistration", {})
        assertions = entity.get("assertions", {})
        
        # Active registration (30 points)
        if reg.get("registrationStatus") == "ACTIVE":
            score += 30
        
        # Has certifications (20 points)
        certs = assertions.get("certifications", {}).get("fARResponses", [])
        if any(cert.get("answer") == "Y" for cert in certs):
            score += 20
        
        # Accepts credit cards (10 points)
        if assertions.get("creditCardUsage") == "Y":
            score += 10
        
        # No federal debt (20 points)
        if reg.get("delinquentFederalDebt") != "Y":
            score += 20
        
        # Not excluded (20 points)
        if reg.get("exclusionStatus") != "Y":
            score += 20
            
        return score

# Integration with your existing platform
def enrich_company_batch(uei_list: list, api_key: str) -> Dict:
    """Enrich multiple companies efficiently"""
    sam_api = CachedSAMGovAPI(api_key)
    enriched_data = {}
    
    for uei in uei_list:
        data = sam_api.get_entity(uei)
        if data:
            enriched_data[uei] = data
    
    return enriched_data

if __name__ == "__main__":
    # Test when you have your API key
    API_KEY = os.environ.get("SAM_GOV_API_KEY", "YOUR_KEY_HERE")
    
    if API_KEY != "YOUR_KEY_HERE":
        api = CachedSAMGovAPI(API_KEY)
        
        # Test with a UEI from your database
        test_uei = "TGQSQVAABZ37"
        result = api.get_entity(test_uei)
        
        if result:
            print(json.dumps(result, indent=2))
    else:
        print("Please set your SAM_GOV_API_KEY environment variable")
