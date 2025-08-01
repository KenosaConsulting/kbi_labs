#!/usr/bin/env python3
"""
Federal Contract Opportunities API
Shows active contracts SMBs can bid on
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class OpportunitiesAPI:
    def __init__(self):
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        # This API might work without a key for basic searches
        self.headers = {
            "Accept": "application/json"
        }
    
    def search_opportunities(self, 
                           keywords: str = None,
                           naics_code: str = None,
                           state: str = None,
                           set_aside: str = None,  # "SBA", "8(a)", "WOSB", etc.
                           days_posted: int = 30,
                           limit: int = 100) -> List[Dict]:
        """Search for contract opportunities"""
        
        # Build query parameters
        params = {
            "limit": limit,
            "postedFrom": (datetime.now() - timedelta(days=days_posted)).strftime("%m/%d/%Y"),
            "postedTo": datetime.now().strftime("%m/%d/%Y"),
            "ptype": "o",  # Opportunities
            "active": "true"
        }
        
        if keywords:
            params["keywords"] = keywords
        if naics_code:
            params["naics"] = naics_code
        if state:
            params["state"] = state
        if set_aside:
            params["typeOfSetAsideDescription"] = set_aside
            
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_opportunities(data)
            else:
                print(f"Error {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            print(f"API Error: {e}")
            return []
    
    def _parse_opportunities(self, data: Dict) -> List[Dict]:
        """Parse opportunity data into useful format"""
        opportunities = []
        
        for opp in data.get("opportunitiesData", []):
            # Calculate days until due
            response_deadline = opp.get("responseDeadLine", "")
            days_remaining = None
            if response_deadline:
                try:
                    deadline = datetime.strptime(response_deadline, "%m/%d/%Y")
                    days_remaining = (deadline - datetime.now()).days
                except:
                    pass
            
            opportunities.append({
                "notice_id": opp.get("noticeId"),
                "title": opp.get("title"),
                "agency": opp.get("fullParentPathName", "").split(".")[0],
                "sub_agency": opp.get("fullParentPathName", ""),
                
                # Key details
                "type": opp.get("type"),
                "set_aside": opp.get("typeOfSetAsideDescription"),
                "naics_code": opp.get("naicsCode"),
                "naics_description": opp.get("naicsDescription"),
                
                # Location
                "state": opp.get("state"),
                "city": opp.get("city"),
                
                # Dates
                "posted_date": opp.get("postedDate"),
                "response_deadline": response_deadline,
                "days_remaining": days_remaining,
                
                # Contract details
                "classification_code": opp.get("classificationCode"),
                "solicitation_number": opp.get("solicitationNumber"),
                
                # URL to full details
                "url": f"https://sam.gov/opp/{opp.get('noticeId')}",
                
                # Intelligence flags
                "is_small_business_setaside": opp.get("typeOfSetAside") in ["SBA", "SBP"],
                "is_8a_setaside": "8(a)" in str(opp.get("typeOfSetAsideDescription", "")),
                "is_women_owned": "WOSB" in str(opp.get("typeOfSetAsideDescription", "")),
                "is_veteran_owned": "VOSB" in str(opp.get("typeOfSetAsideDescription", ""))
            })
        
        return opportunities
    
    def get_opportunities_by_company(self, naics_codes: List[str], state: str = None) -> Dict:
        """Get opportunities matching a company's profile"""
        all_opportunities = []
        
        # Search by each NAICS code
        for naics in naics_codes[:3]:  # Limit to top 3 to avoid too many requests
            opps = self.search_opportunities(
                naics_code=naics,
                state=state,
                limit=20
            )
            all_opportunities.extend(opps)
        
        # Remove duplicates
        seen = set()
        unique_opps = []
        for opp in all_opportunities:
            if opp["notice_id"] not in seen:
                seen.add(opp["notice_id"])
                unique_opps.append(opp)
        
        # Sort by days remaining
        unique_opps.sort(key=lambda x: x.get("days_remaining", 999))
        
        return {
            "total_opportunities": len(unique_opps),
            "opportunities": unique_opps[:10],  # Top 10 most urgent
            "by_setaside": self._group_by_setaside(unique_opps)
        }
    
    def _group_by_setaside(self, opportunities: List[Dict]) -> Dict:
        """Group opportunities by set-aside type"""
        groups = {
            "small_business": 0,
            "8a": 0,
            "women_owned": 0,
            "veteran_owned": 0,
            "unrestricted": 0
        }
        
        for opp in opportunities:
            if opp.get("is_8a_setaside"):
                groups["8a"] += 1
            elif opp.get("is_women_owned"):
                groups["women_owned"] += 1
            elif opp.get("is_veteran_owned"):
                groups["veteran_owned"] += 1
            elif opp.get("is_small_business_setaside"):
                groups["small_business"] += 1
            else:
                groups["unrestricted"] += 1
                
        return groups


# Test without API key first
if __name__ == "__main__":
    api = OpportunitiesAPI()
    
    print("🔍 Testing Opportunities API (no key required)...")
    
    # Search for IT opportunities in Florida
    opportunities = api.search_opportunities(
        keywords="information technology",
        state="FL",
        set_aside="SBA",
        days_posted=7,
        limit=5
    )
    
    print(f"\n📋 Found {len(opportunities)} opportunities:\n")
    
    for opp in opportunities:
        print(f"Title: {opp['title']}")
        print(f"Agency: {opp['agency']}")
        print(f"Set-Aside: {opp['set_aside']}")
        print(f"Deadline: {opp['response_deadline']} ({opp['days_remaining']} days)")
        print(f"URL: {opp['url']}")
        print("-" * 50)
