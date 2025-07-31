#!/usr/bin/env python3
"""
Direct fix for USPTO and NSF APIs - creates the fixed processor directly
"""

import subprocess
import os

# Create the fixed innovation processor
fixed_processor_code = '''#!/usr/bin/env python3
"""
Fixed USPTO and NSF API Integration for KBI Labs
"""

import asyncio
import aiohttp
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
from urllib.parse import quote
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InnovationMetrics:
    """Container for combined innovation metrics"""
    organization_name: str
    patents_count: int = 0
    patents_last_5_years: int = 0
    patent_classifications: List[str] = None
    nsf_awards_count: int = 0
    nsf_total_funding: float = 0.0
    nsf_recent_awards: int = 0
    research_areas: List[str] = None
    innovation_score: float = 0.0
    r_and_d_intensity: str = "Low"
    tech_adoption_stage: str = "Unknown"
    last_updated: str = ""

class InnovationAPIProcessor:
    """Fixed USPTO and NSF API processor"""
    
    def __init__(self):
        # Updated USPTO PatentsView API endpoint
        self.uspto_base_url = "https://api.patentsview.org/patents/query"
        # NSF API with JSON output
        self.nsf_base_url = "https://www.research.gov/common/webapi/awardapisearch-v1.htm"
        self.session = None
        self.rate_limit_delay = 0.5  # 500ms between requests
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_uspto_patents(self, organization_name: str) -> List[Dict]:
        """Search USPTO for patents using the working PatentsView API"""
        try:
            # Clean organization name
            clean_name = organization_name.replace("LLC", "").replace("INC", "").replace("CORP", "").strip()
            
            # PatentsView API query format
            query_data = {
                "q": {
                    "assignee_organization": {
                        "_contains": clean_name
                    }
                },
                "f": [
                    "patent_number",
                    "patent_title",
                    "patent_date",
                    "assignee_organization",
                    "cpc_category"
                ],
                "o": {
                    "page": 1,
                    "per_page": 25
                },
                "s": [{
                    "patent_date": "desc"
                }]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            async with self.session.post(
                self.uspto_base_url,
                json=query_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    patents = data.get("patents", [])
                    logger.info(f"Found {len(patents)} patents for {organization_name}")
                    return patents
                else:
                    logger.warning(f"USPTO API error {response.status} for {organization_name}")
                    return []
                    
        except Exception as e:
            logger.error(f"USPTO search error for {organization_name}: {str(e)}")
            return []
    
    async def search_nsf_awards(self, organization_name: str) -> List[Dict]:
        """Search NSF for research awards using JSON output"""
        try:
            # NSF API with JSON output format
            params = {
                "awardeeName": organization_name,
                "printFields": "id,title,fundsObligatedAmt,date,piFirstName,piLastName,awardeeName",
                "outputFormat": "json"  # Request JSON instead of XML
            }
            
            async with self.session.get(self.nsf_base_url, params=params) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'json' in content_type:
                        data = await response.json()
                        awards = data.get("response", {}).get("award", [])
                        if not isinstance(awards, list):
                            awards = [awards] if awards else []
                        logger.info(f"Found {len(awards)} NSF awards for {organization_name}")
                        return awards
                    else:
                        # Fallback to XML parsing if JSON not available
                        text = await response.text()
                        return self._parse_nsf_xml_safely(text)
                else:
                    logger.warning(f"NSF API error {response.status} for {organization_name}")
                    return []
                    
        except Exception as e:
            logger.error(f"NSF search error for {organization_name}: {str(e)}")
            return []
    
    def _parse_nsf_xml_safely(self, xml_text: str) -> List[Dict]:
        """Safely parse NSF XML response"""
        awards = []
        try:
            # Clean XML text
            xml_text = xml_text.strip()
            if not xml_text.startswith('<?xml'):
                return awards
                
            root = ET.fromstring(xml_text)
            
            # Handle different XML structures
            award_elements = root.findall('.//award')
            if not award_elements:
                award_elements = root.findall('award')
            
            for award in award_elements:
                award_dict = {}
                for child in award:
                    if child.text:
                        award_dict[child.tag] = child.text.strip()
                if award_dict:
                    awards.append(award_dict)
                    
        except Exception as e:
            logger.debug(f"XML parsing failed (may be using JSON): {str(e)}")
        
        return awards
    
    def calculate_innovation_score(self, metrics: InnovationMetrics) -> float:
        """Calculate composite innovation score (0-100)"""
        score = 0.0
        
        # Patent activity score (40 points)
        if metrics.patents_count > 0:
            score += min(20, metrics.patents_count * 2)
            score += min(20, metrics.patents_last_5_years * 4)
        
        # R&D funding score (40 points)
        if metrics.nsf_awards_count > 0:
            score += min(20, metrics.nsf_awards_count * 5)
            score += min(20, metrics.nsf_total_funding / 100000)
        
        # Diversity score (20 points)
        tech_diversity = len(set(metrics.patent_classifications or []))
        score += min(20, tech_diversity * 5)
        
        return round(min(100, score), 1)
    
    def determine_r_and_d_intensity(self, metrics: InnovationMetrics) -> str:
        """Classify R&D intensity based on metrics"""
        if metrics.nsf_total_funding > 1000000 or metrics.patents_last_5_years > 10:
            return "High"
        elif metrics.nsf_total_funding > 100000 or metrics.patents_last_5_years > 3:
            return "Medium"
        elif metrics.nsf_awards_count > 0 or metrics.patents_count > 0:
            return "Low"
        else:
            return "None"
    
    def determine_tech_adoption_stage(self, metrics: InnovationMetrics) -> str:
        """Classify technology adoption stage"""
        if metrics.patents_last_5_years > 5 and metrics.nsf_recent_awards > 2:
            return "Innovator"
        elif metrics.patents_last_5_years > 2 or metrics.nsf_recent_awards > 0:
            return "Early Adopter"
        elif metrics.patents_count > 0:
            return "Early Majority"
        else:
            return "Late Majority"
    
    async def process_organization(self, org_name: str) -> InnovationMetrics:
        """Process a single organization through both APIs"""
        logger.info(f"Processing innovation data for: {org_name}")
        
        # Initialize metrics
        metrics = InnovationMetrics(
            organization_name=org_name,
            patent_classifications=[],
            research_areas=[]
        )
        
        # Fetch data from both APIs concurrently
        patents_task = self.search_uspto_patents(org_name)
        awards_task = self.search_nsf_awards(org_name)
        
        patents, awards = await asyncio.gather(patents_task, awards_task)
        
        # Process USPTO data
        if patents:
            metrics.patents_count = len(patents)
            five_years_ago = datetime.now() - timedelta(days=5*365)
            
            for patent in patents:
                # Count recent patents
                patent_date = patent.get("patent_date", "")
                if patent_date:
                    try:
                        pdate = datetime.strptime(patent_date, "%Y-%m-%d")
                        if pdate > five_years_ago:
                            metrics.patents_last_5_years += 1
                    except:
                        pass
                
                # Collect classifications
                cpcs = patent.get("cpc_category", [])
                if isinstance(cpcs, list):
                    for cpc in cpcs:
                        if cpc not in metrics.patent_classifications:
                            metrics.patent_classifications.append(cpc)
        
        # Process NSF data
        if awards:
            metrics.nsf_awards_count = len(awards)
            two_years_ago = datetime.now() - timedelta(days=2*365)
            
            for award in awards:
                # Sum funding
                funding = award.get("fundsObligatedAmt", 0)
                try:
                    metrics.nsf_total_funding += float(funding)
                except:
                    pass
                
                # Count recent awards
                award_date = award.get("date", "")
                if award_date:
                    try:
                        # Handle different date formats
                        for fmt in ["%m/%d/%Y", "%Y-%m-%d"]:
                            try:
                                adate = datetime.strptime(award_date, fmt)
                                if adate > two_years_ago:
                                    metrics.nsf_recent_awards += 1
                                break
                            except:
                                continue
                    except:
                        pass
        
        # Calculate derivative metrics
        metrics.innovation_score = self.calculate_innovation_score(metrics)
        metrics.r_and_d_intensity = self.determine_r_and_d_intensity(metrics)
        metrics.tech_adoption_stage = self.determine_tech_adoption_stage(metrics)
        metrics.last_updated = datetime.now().isoformat()
        
        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)
        
        return metrics
    
    async def process_batch(self, organizations: List[str], batch_size: int = 10) -> pd.DataFrame:
        """Process multiple organizations in batches"""
        all_results = []
        
        for i in range(0, len(organizations), batch_size):
            batch = organizations[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} of {len(organizations)//batch_size + 1}")
            
            # Process batch concurrently
            tasks = [self.process_organization(org) for org in batch]
            results = await asyncio.gather(*tasks)
            
            all_results.extend(results)
            
            # Longer delay between batches
            await asyncio.sleep(1.0)
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'organization_name': m.organization_name,
                'patents_count': m.patents_count,
                'patents_last_5_years': m.patents_last_5_years,
                'patent_classifications': ','.join(m.patent_classifications[:5]) if m.patent_classifications else '',
                'nsf_awards_count': m.nsf_awards_count,
                'nsf_total_funding': m.nsf_total_funding,
                'nsf_recent_awards': m.nsf_recent_awards,
                'innovation_score': m.innovation_score,
                'r_and_d_intensity': m.r_and_d_intensity,
                'tech_adoption_stage': m.tech_adoption_stage,
                'last_updated': m.last_updated
            }
            for m in all_results
        ])
        
        return df

# Import the utility functions
try:
    from src.data_processors.innovation_processor_utils import load_all_dsbs_data
except:
    # If utils not available, use direct loading
    def load_all_dsbs_data():
        import glob
        files = glob.glob('/app/data/*DSBS*.csv')
        if files:
            return pd.read_csv(files[0])
        raise FileNotFoundError("No DSBS files found")

async def enrich_dsbs_with_innovation(dsbs_file: str, output_file: str, sample_size: Optional[int] = None):
    """Main function to enrich DSBS data with innovation metrics"""
    logger.info("Starting innovation enrichment process...")
    
    # Load DSBS data
    logger.info(f"Loading DSBS data from {dsbs_file}")
    if dsbs_file == "auto":
        dsbs_df = load_all_dsbs_data()
    else:
        dsbs_df = pd.read_csv(dsbs_file)
    
    # Sample if requested
    if sample_size:
        dsbs_df = dsbs_df.sample(n=min(sample_size, len(dsbs_df)))
        logger.info(f"Processing sample of {len(dsbs_df)} organizations")
    
    # Get unique organization names
    org_names = dsbs_df['Organization Name'].dropna().unique().tolist()
    logger.info(f"Found {len(org_names)} unique organizations")
    
    # Process through APIs
    async with InnovationAPIProcessor() as processor:
        innovation_df = await processor.process_batch(org_names)
    
    # Merge with original data
    logger.info("Merging innovation data with DSBS data...")
    enriched_df = dsbs_df.merge(
        innovation_df,
        left_on='Organization Name',
        right_on='organization_name',
        how='left'
    )
    
    # Fill missing values
    enriched_df['innovation_score'] = enriched_df['innovation_score'].fillna(0)
    enriched_df['r_and_d_intensity'] = enriched_df['r_and_d_intensity'].fillna('None')
    enriched_df['tech_adoption_stage'] = enriched_df['tech_adoption_stage'].fillna('Unknown')
    
    # Save results
    logger.info(f"Saving enriched data to {output_file}")
    enriched_df.to_csv(output_file, index=False)
    
    # Print summary statistics
    print("\\n=== Innovation Enrichment Summary ===")
    print(f"Total organizations processed: {len(org_names)}")
    print(f"Organizations with patents: {(enriched_df['patents_count'] > 0).sum()}")
    print(f"Organizations with NSF awards: {(enriched_df['nsf_awards_count'] > 0).sum()}")
    print(f"Average innovation score: {enriched_df['innovation_score'].mean():.1f}")
    print("\\nR&D Intensity Distribution:")
    print(enriched_df['r_and_d_intensity'].value_counts())
    print("\\nTech Adoption Stage Distribution:")
    print(enriched_df['tech_adoption_stage'].value_counts())
    
    return enriched_df

# Test function
async def test_known_innovators():
    """Test with companies known to have patents and NSF awards"""
    test_companies = [
        "Massachusetts Institute of Technology",
        "Stanford University", 
        "IBM",
        "Microsoft",
        "General Electric"
    ]
    
    async with InnovationAPIProcessor() as processor:
        for company in test_companies:
            print(f"\\n{'='*60}")
            print(f"Testing: {company}")
            print('='*60)
            
            metrics = await processor.process_organization(company)
            
            print(f"Patents: {metrics.patents_count} (Recent: {metrics.patents_last_5_years})")
            print(f"NSF Awards: {metrics.nsf_awards_count} (Total: ${metrics.nsf_total_funding:,.0f})")
            print(f"Innovation Score: {metrics.innovation_score}")
            print(f"R&D Intensity: {metrics.r_and_d_intensity}")
            print(f"Tech Stage: {metrics.tech_adoption_stage}")
            
            if metrics.patent_classifications:
                print(f"Tech Areas: {', '.join(metrics.patent_classifications[:5])}")

if __name__ == "__main__":
    asyncio.run(test_known_innovators())
'''

# Write the fixed processor to a temporary file
with open('/tmp/innovation_processor_fixed.py', 'w') as f:
    f.write(fixed_processor_code)

# Copy it to the container
print("📝 Creating fixed innovation processor...")
subprocess.run(['docker', 'cp', '/tmp/innovation_processor_fixed.py', 'kbi_api:/app/src/data_processors/innovation_processor.py'])

# Test with known companies
print("\n🧪 Testing with known innovative companies...")
test_cmd = '''
docker exec kbi_api python -c "
import asyncio
from src.data_processors.innovation_processor import test_known_innovators
asyncio.run(test_known_innovators())
"
'''
subprocess.run(test_cmd, shell=True)

print("\n✅ Innovation processor updated! Now you can:")
print("1. Test API health: check_api_health")
print("2. Process DSBS companies: process_dsbs_innovation 100")
print("3. Test specific company: quick_innovation_search 'MICROSOFT'")
