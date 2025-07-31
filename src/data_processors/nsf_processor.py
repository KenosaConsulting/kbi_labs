#!/usr/bin/env python3
"""
NSF Award Data Processor
Matches DSBS companies with NSF awards
"""

import json
import pandas as pd
import glob
import logging
from typing import Dict, List
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSFProcessor:
    def __init__(self):
        self.awards = []
        
    def load_awards(self, path="/app/nsf_data"):
        """Load NSF awards from JSON files"""
        json_files = glob.glob(f"{path}/**/*.json", recursive=True)
        logger.info(f"Found {len(json_files)} JSON files")
        
        for i, file in enumerate(json_files):
            if i % 1000 == 0:
                logger.info(f"Loaded {i} files...")
            try:
                with open(file, "r") as f:
                    award = json.load(f)
                    # Extract institution info
                    institutions = award.get("institutions", [])
                    if institutions:
                        inst = institutions[0]
                        award["institution_name"] = inst.get("name", "")
                        award["institution_city"] = inst.get("city", "")
                        award["institution_state"] = inst.get("stateCode", "")
                    self.awards.append(award)
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
                
        logger.info(f"Loaded {len(self.awards)} awards total")
        return len(self.awards)
    
    def search_by_organization(self, org_name):
        """Search awards by organization name"""
        matches = []
        
        # Clean organization name
        clean_name = org_name.upper().replace("LLC", "").replace("INC", "").replace("CORP", "").strip()
        
        for award in self.awards:
            inst_name = award.get("institution_name", "").upper()
            
            # Try different matching strategies
            if clean_name in inst_name or inst_name in clean_name:
                # Get PI info
                pi_list = award.get("pi", [])
                pi_name = ""
                if pi_list and isinstance(pi_list, list) and len(pi_list) > 0:
                    pi = pi_list[0]
                    first_name = pi.get("pi_first_name", "")
                    last_name = pi.get("pi_last_name", "")
                    pi_name = f"{first_name} {last_name}".strip()
                
                matches.append({
                    "id": award.get("awd_id"),
                    "title": award.get("awd_titl_txt", "")[:100],
                    "amount": award.get("awd_amount", 0),
                    "start_date": award.get("awd_eff_date"),
                    "institution": award.get("institution_name"),
                    "pi_name": pi_name
                })
                
        return matches
    
    def calculate_metrics(self, org_name):
        """Calculate innovation metrics for organization"""
        matches = self.search_by_organization(org_name)
        
        total_funding = sum(m["amount"] for m in matches)
        
        # Count recent awards
        recent = 0
        for m in matches:
            if m["start_date"] and ("2024" in m["start_date"] or "2023" in m["start_date"]):
                recent += 1
        
        return {
            "organization": org_name,
            "nsf_awards_count": len(matches),
            "nsf_total_funding": total_funding,
            "recent_awards": recent,
            "awards": matches[:5]  # First 5 awards
        }

# Test
if __name__ == "__main__":
    processor = NSFProcessor()
    print("Loading NSF awards...")
    processor.load_awards()
    
    # Test with known institutions
    for org in ["Massachusetts Institute of Technology", "Stanford University", "MIT"]:
        metrics = processor.calculate_metrics(org)
        print(f"\n{org}:")
        print(f"  Awards: {metrics['nsf_awards_count']}")
        print(f"  Total funding: ${metrics['nsf_total_funding']:,.0f}")
        if metrics["awards"]:
            print(f"  Example: {metrics['awards'][0]['title']}")
