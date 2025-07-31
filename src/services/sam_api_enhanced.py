#!/usr/bin/env python3
"""
Enhanced SAM.gov API Integration
Combines Entity and Opportunities data
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class EnhancedSAMAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "X-Api-Key": api_key,
            "Accept": "application/json"
        }
        self.entity_url = "https://api.sam.gov/entity-information/v3/entities"
        self.opp_url = "https://api.sam.gov/opportunities/v2/search"
    
    def test_api_key(self):
        """Test if API key is valid"""
        print("🔑 Testing API key...")
        
        # Try a simple search
        params = {
            "limit": 1,
            "postedFrom": datetime.now().strftime("%m/%d/%Y"),
            "postedTo": datetime.now().strftime("%m/%d/%Y"),
            "ptype": "o"
        }
        
        try:
            response = requests.get(
                self.opp_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ API key is valid!")
                return True
            else:
                print(f"❌ API key invalid: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def search_opportunities_by_state(self, state: str, limit: int = 10) -> List[Dict]:
        """Get opportunities for companies in a specific state"""
        params = {
            "limit": limit,
            "postedFrom": (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y"),
            "postedTo": datetime.now().strftime("%m/%d/%Y"),
            "state": state,
            "ptype": "o",
            "active": "true"
        }
        
        try:
            response = requests.get(
                self.opp_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                opportunities = []
                
                for opp in data.get("opportunitiesData", []):
                    deadline = opp.get("responseDeadLine", "")
                    days_left = None
                    
                    if deadline:
                        try:
                            deadline_date = datetime.strptime(deadline, "%m/%d/%Y")
                            days_left = (deadline_date - datetime.now()).days
                        except:
                            pass
                    
                    opportunities.append({
                        "id": opp.get("noticeId"),
                        "title": opp.get("title", "")[:100] + "...",
                        "agency": opp.get("fullParentPathName", "").split(".")[0],
                        "type": opp.get("type"),
                        "set_aside": opp.get("typeOfSetAsideDescription", "Open"),
                        "posted": opp.get("postedDate"),
                        "deadline": deadline,
                        "days_left": days_left,
                        "naics": opp.get("naicsCode"),
                        "url": f"https://sam.gov/opp/{opp.get('noticeId')}",
                        "value": "TBD"  # Most opportunities don't list value
                    })
                
                return opportunities
            else:
                print(f"Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_opportunity_stats(self, state: str = None) -> Dict:
        """Get statistics about available opportunities"""
        # Get more opportunities for analysis
        params = {
            "limit": 1000,
            "postedFrom": (datetime.now() - timedelta(days=7)).strftime("%m/%d/%Y"),
            "postedTo": datetime.now().strftime("%m/%d/%Y"),
            "ptype": "o",
            "active": "true"
        }
        
        if state:
            params["state"] = state
        
        try:
            response = requests.get(
                self.opp_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                opps = data.get("opportunitiesData", [])
                
                # Analyze set-asides
                set_asides = {}
                agencies = {}
                
                for opp in opps:
                    # Count set-asides
                    sa = opp.get("typeOfSetAsideDescription", "Open Competition")
                    set_asides[sa] = set_asides.get(sa, 0) + 1
                    
                    # Count agencies
                    agency = opp.get("fullParentPathName", "").split(".")[0]
                    agencies[agency] = agencies.get(agency, 0) + 1
                
                return {
                    "total_opportunities": len(opps),
                    "posted_this_week": len(opps),
                    "by_setaside": dict(sorted(set_asides.items(), key=lambda x: x[1], reverse=True)[:10]),
                    "by_agency": dict(sorted(agencies.items(), key=lambda x: x[1], reverse=True)[:10]),
                    "state": state or "All States"
                }
            else:
                return {"error": f"API returned {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}


# Test function
def test_sam_api():
    api_key = os.environ.get("SAM_GOV_API_KEY", "")
    
    if not api_key:
        print("❌ Please set SAM_GOV_API_KEY environment variable")
        print("   export SAM_GOV_API_KEY='your-actual-sam-gov-key'")
        return
    
    api = EnhancedSAMAPI(api_key)
    
    # Test the key
    if not api.test_api_key():
        return
    
    # Get opportunities for Florida
    print("\n📋 Florida Opportunities:")
    opps = api.search_opportunities_by_state("FL", limit=5)
    
    for opp in opps:
        print(f"\nTitle: {opp['title']}")
        print(f"Agency: {opp['agency']}")
        print(f"Set-Aside: {opp['set_aside']}")
        print(f"Deadline: {opp['deadline']} ({opp['days_left']} days left)")
        print(f"NAICS: {opp['naics']}")
        print(f"URL: {opp['url']}")
    
    # Get statistics
    print("\n📊 Opportunity Statistics (Past Week):")
    stats = api.get_opportunity_stats("FL")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    test_sam_api()
