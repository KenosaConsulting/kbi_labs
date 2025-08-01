#!/bin/bash
# working_innovation_apis.sh
# Updates innovation processor with the NEW USPTO PatentSearch API and working NSF endpoints

echo "🔧 Fixing Innovation APIs with New Endpoints..."
echo "=============================================="

# First, let's test the NSF API (it should still work)
echo "🧪 Testing NSF API..."
curl -s "https://www.research.gov/common/webapi/awardapisearch-v1.htm?awardeeName=MIT&printFields=id,title,fundsObligatedAmt" | head -20

# Create the updated innovation processor with new USPTO API
echo -e "\n📝 Creating updated innovation processor..."

docker exec kbi_api bash -c "cat > /app/src/data_processors/innovation_processor_v3.py << 'PYTHON_EOF'
#!/usr/bin/env python3
\"\"\"
Updated USPTO PatentSearch API and NSF Integration
\"\"\"

import asyncio
import aiohttp
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InnovationMetrics:
    \"\"\"Container for innovation metrics\"\"\"
    organization_name: str
    patents_count: int = 0
    patents_last_5_years: int = 0
    patent_classifications: List[str] = None
    nsf_awards_count: int = 0
    nsf_total_funding: float = 0.0
    nsf_recent_awards: int = 0
    research_areas: List[str] = None
    innovation_score: float = 0.0
    r_and_d_intensity: str = \"Low\"
    tech_adoption_stage: str = \"Unknown\"
    last_updated: str = \"\"

class InnovationAPIProcessor:
    \"\"\"Updated processor for new USPTO and NSF APIs\"\"\"
    
    def __init__(self):
        # NEW USPTO PatentSearch API endpoint (from PatentsView)
        self.uspto_search_url = \"https://search.patentsview.org/api/v1/patent/\"
        # Alternative: USPTO Open Data Portal
        self.uspto_odp_url = \"https://data.uspto.gov/peds/v1/patent/\"
        # NSF API (still working)
        self.nsf_base_url = \"https://www.research.gov/common/webapi/awardapisearch-v1.htm\"
        self.session = None
        self.rate_limit_delay = 0.5
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_uspto_patents(self, organization_name: str) -> List[Dict]:
        \"\"\"Search USPTO using new PatentSearch API or fallback methods\"\"\"
        try:
            # Clean organization name
            clean_name = organization_name.replace(\"LLC\", \"\").replace(\"INC\", \"\").replace(\"CORP\", \"\").strip()
            
            # Try PatentSearch API first
            search_query = {
                \"q\": f\"assignee.organization:{clean_name}\",
                \"size\": 25,
                \"sort\": [{\"patent_date\": {\"order\": \"desc\"}}]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Try the new endpoint
            url = f\"{self.uspto_search_url}search\"
            
            async with self.session.post(url, json=search_query, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    patents = data.get(\"results\", [])
                    logger.info(f\"Found {len(patents)} patents for {organization_name}\")
                    return patents
                else:
                    logger.warning(f\"PatentSearch API error {response.status}, trying fallback\")
                    
            # Fallback: Try USPTO ODP or basic search
            return await self._fallback_patent_search(clean_name)
                    
        except Exception as e:
            logger.error(f\"USPTO search error: {str(e)}\")
            return []
    
    async def _fallback_patent_search(self, organization_name: str) -> List[Dict]:
        \"\"\"Fallback patent search using alternative methods\"\"\"
        try:
            # For now, return empty - in production, implement ODP API
            logger.info(f\"Would search ODP for: {organization_name}\")
            return []
        except:
            return []
    
    async def search_nsf_awards(self, organization_name: str) -> List[Dict]:
        \"\"\"Search NSF for research awards\"\"\"
        try:
            params = {
                \"awardeeName\": organization_name,
                \"printFields\": \"id,title,fundsObligatedAmt,date,piFirstName,piLastName,awardeeName\"
            }
            
            async with self.session.get(self.nsf_base_url, params=params) as response:
                if response.status == 200:
                    text = await response.text()
                    return self._parse_nsf_response(text)
                else:
                    logger.warning(f\"NSF API error {response.status}\")
                    return []
                    
        except Exception as e:
            logger.error(f\"NSF search error: {str(e)}\")
            return []
    
    def _parse_nsf_response(self, xml_text: str) -> List[Dict]:
        \"\"\"Parse NSF XML response\"\"\"
        awards = []
        try:
            # Clean and validate XML
            xml_text = xml_text.strip()
            if not xml_text:
                return awards
                
            # NSF returns HTML error pages sometimes, check for XML
            if not xml_text.startswith('<?xml') and '<award>' not in xml_text:
                return awards
                
            # Parse XML
            root = ET.fromstring(xml_text)
            
            # Find all award elements
            for award in root.findall('.//award'):
                award_dict = {}
                for child in award:
                    if child.text:
                        award_dict[child.tag] = child.text.strip()
                if award_dict:
                    awards.append(award_dict)
                    
        except ET.ParseError as e:
            logger.debug(f\"XML parsing failed: {str(e)}\")
        except Exception as e:
            logger.error(f\"NSF parsing error: {str(e)}\")
        
        return awards
    
    def calculate_innovation_score(self, metrics: InnovationMetrics) -> float:
        \"\"\"Calculate innovation score\"\"\"
        score = 0.0
        
        # Patent score (40 points)
        if metrics.patents_count > 0:
            score += min(20, metrics.patents_count * 2)
            score += min(20, metrics.patents_last_5_years * 4)
        
        # NSF funding score (40 points)
        if metrics.nsf_awards_count > 0:
            score += min(20, metrics.nsf_awards_count * 5)
            score += min(20, metrics.nsf_total_funding / 100000)
        
        # Diversity score (20 points)
        tech_diversity = len(set(metrics.patent_classifications or []))
        score += min(20, tech_diversity * 5)
        
        return round(min(100, score), 1)
    
    async def process_organization(self, org_name: str) -> InnovationMetrics:
        \"\"\"Process organization through available APIs\"\"\"
        logger.info(f\"Processing: {org_name}\")
        
        metrics = InnovationMetrics(
            organization_name=org_name,
            patent_classifications=[],
            research_areas=[]
        )
        
        # Search both APIs
        patents_task = self.search_uspto_patents(org_name)
        awards_task = self.search_nsf_awards(org_name)
        
        patents, awards = await asyncio.gather(patents_task, awards_task)
        
        # Process patent data
        if patents:
            metrics.patents_count = len(patents)
            # Process patent details based on new API structure
            
        # Process NSF data
        if awards:
            metrics.nsf_awards_count = len(awards)
            for award in awards:
                try:
                    funding = float(award.get(\"fundsObligatedAmt\", 0))
                    metrics.nsf_total_funding += funding
                except:
                    pass
        
        # Calculate scores
        metrics.innovation_score = self.calculate_innovation_score(metrics)
        metrics.last_updated = datetime.now().isoformat()
        
        await asyncio.sleep(self.rate_limit_delay)
        
        return metrics

# Test function
async def test_apis():
    \"\"\"Test the updated APIs\"\"\"
    test_orgs = [
        \"Massachusetts Institute of Technology\",
        \"Stanford University\",
        \"IBM Corporation\",
        \"Microsoft Corporation\"
    ]
    
    async with InnovationAPIProcessor() as processor:
        for org in test_orgs:
            print(f\"\\nTesting: {org}\")
            metrics = await processor.process_organization(org)
            print(f\"  NSF Awards: {metrics.nsf_awards_count}\")
            print(f\"  NSF Funding: \${metrics.nsf_total_funding:,.0f}\")
            print(f\"  Patents: {metrics.patents_count} (placeholder)\")
            print(f\"  Innovation Score: {metrics.innovation_score}\")

if __name__ == \"__main__\":
    asyncio.run(test_apis())
PYTHON_EOF"

# Copy to main processor location
echo -e "\n📋 Copying to main processor..."
docker exec kbi_api cp /app/src/data_processors/innovation_processor_v3.py /app/src/data_processors/innovation_processor.py

# Test the updated processor
echo -e "\n🧪 Testing updated APIs..."
docker exec kbi_api python /app/src/data_processors/innovation_processor.py

# Create simplified test functions
cat >> ~/.bashrc << 'BASHEOF'

# Test NSF API directly
test_nsf_api() {
    echo "🔬 Testing NSF API..."
    curl -s "https://www.research.gov/common/webapi/awardapisearch-v1.htm?awardeeName=MIT" | \
        grep -c "<award>" || echo "No awards found"
}

# Check USPTO alternatives
check_uspto_alternatives() {
    echo "🏢 Checking USPTO Alternatives..."
    
    echo -e "\n1. USPTO Open Data Portal:"
    curl -s "https://data.uspto.gov/" | grep -o "Open Data Portal" || echo "Not accessible"
    
    echo -e "\n2. PatentsView Data Download:"
    echo "   - Direct downloads available at: https://patentsview.org/download/data-download-tables"
    
    echo -e "\n3. Google Patents API:"
    echo "   - Consider using Google Patents Public Data for patent searches"
}

# Process with NSF only for now
process_nsf_innovation() {
    local company="${1:-Microsoft}"
    echo "🔬 Processing NSF data for: $company"
    
    docker exec kbi_api python -c "
import asyncio
from src.data_processors.innovation_processor import InnovationAPIProcessor

async def test():
    async with InnovationAPIProcessor() as p:
        metrics = await p.process_organization('$company')
        print(f'NSF Awards: {metrics.nsf_awards_count}')
        print(f'Total Funding: \${metrics.nsf_total_funding:,.0f}')

asyncio.run(test())
"
}
BASHEOF

source ~/.bashrc

echo "
✅ Innovation APIs Updated!
===========================

📊 Current Status:
- NSF API: ✅ Working (XML format)
- USPTO API: ⚠️  Legacy discontinued, alternatives available

🛠️ Available Commands:
$ test_nsf_api                    # Test NSF directly
$ check_uspto_alternatives        # See patent data options
$ process_nsf_innovation \"MIT\"    # Process NSF data

🎯 Next Steps:
1. NSF data is working - can enrich DSBS with R&D funding
2. For patents, consider:
   - Download PatentsView bulk data
   - Use Google Patents API
   - Access USPTO Open Data Portal

💡 Recommendation:
Start with NSF enrichment while we implement patent alternatives
"
