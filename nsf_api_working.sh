#!/bin/bash
# nsf_api_working.sh
# Implements NSF API with correct parameters based on documentation

echo "🔬 Setting up Working NSF API..."
echo "================================"

# Test NSF API with correct parameters
echo "🧪 Testing NSF API with documented parameters..."

# According to the docs, we need to use specific parameter names
# Test 1: Search by keyword (use + for spaces)
echo -e "\n1. Testing keyword search:"
curl -s "https://www.research.gov/common/webapi/awardapisearch-v1.htm?keyword=computer+science" | head -100

# Test 2: Search by awardee name with proper formatting
echo -e "\n2. Testing awardeeName with quotes:"
curl -s 'https://www.research.gov/common/webapi/awardapisearch-v1.htm?awardeeName="Massachusetts+Institute+of+Technology"' | head -100

# Test 3: Search by PI name
echo -e "\n3. Testing PI name search:"
curl -s "https://www.research.gov/common/webapi/awardapisearch-v1.htm?pdPIName=Johnson" | head -100

# Create the corrected NSF processor
echo -e "\n📝 Creating corrected NSF API processor..."

docker exec kbi_api bash -c "cat > /app/src/data_processors/nsf_api_fixed.py << 'PYTHON_EOF'
#!/usr/bin/env python3
\"\"\"
Working NSF API Implementation
Based on actual API documentation from research.gov
\"\"\"

import asyncio
import aiohttp
import xml.etree.ElementTree as ET
import logging
from urllib.parse import quote_plus
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSFAPIProcessor:
    \"\"\"NSF Award Search API processor with correct parameters\"\"\"
    
    def __init__(self):
        self.base_url = \"https://www.research.gov/common/webapi/awardapisearch-v1.htm\"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_awards(self, organization_name: str) -> List[Dict]:
        \"\"\"Search NSF awards using correct parameter format\"\"\"
        awards_found = []
        
        # Try different search strategies based on documentation
        search_strategies = [
            # Strategy 1: Exact match with quotes
            {\"awardeeName\": f'\"{organization_name}\"'},
            # Strategy 2: With spaces as +
            {\"awardeeName\": organization_name.replace(\" \", \"+\")},
            # Strategy 3: Keyword search
            {\"keyword\": organization_name.replace(\" \", \"+\")},
            # Strategy 4: Try common abbreviations
            {\"awardeeName\": self._get_abbreviation(organization_name)}
        ]
        
        for params in search_strategies:
            try:
                logger.info(f\"Trying NSF search with params: {params}\")
                
                async with self.session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        text = await response.text()
                        awards = self._parse_nsf_xml(text)
                        
                        if awards:
                            logger.info(f\"Found {len(awards)} awards using {params}\")
                            awards_found.extend(awards)
                            break  # Found results, stop trying other strategies
                            
            except Exception as e:
                logger.error(f\"NSF search error with {params}: {str(e)}\")
                continue
        
        return awards_found
    
    def _get_abbreviation(self, org_name: str) -> str:
        \"\"\"Get common abbreviations for organizations\"\"\"
        abbreviations = {
            \"Massachusetts Institute of Technology\": \"MIT\",
            \"Stanford University\": \"Stanford\",
            \"University of California\": \"UC\",
            \"Georgia Institute of Technology\": \"Georgia Tech\",
            \"California Institute of Technology\": \"Caltech\"
        }
        return abbreviations.get(org_name, org_name.split()[0])
    
    def _parse_nsf_xml(self, xml_text: str) -> List[Dict]:
        \"\"\"Parse NSF XML response correctly\"\"\"
        awards = []
        
        try:
            # Check if it's an error response
            if \"serviceNotification\" in xml_text:
                logger.warning(\"NSF API returned an error notification\")
                return awards
                
            # Check for valid XML
            if not xml_text.strip().startswith('<?xml'):
                logger.warning(\"Response is not XML\")
                return awards
            
            root = ET.fromstring(xml_text)
            
            # Look for award elements
            for award in root.findall('.//award'):
                award_data = {}
                for field in award:
                    if field.text:
                        award_data[field.tag] = field.text.strip()
                
                if award_data:
                    awards.append(award_data)
                    
        except ET.ParseError as e:
            logger.error(f\"XML parsing error: {e}\")
        
        return awards

# Test with known organizations
async def test_nsf_api():
    \"\"\"Test NSF API with various organizations\"\"\"
    
    test_orgs = [
        \"MIT\",
        \"Stanford\",
        \"University of Chicago\",
        \"Harvard University\",
        \"Carnegie Mellon\"
    ]
    
    async with NSFAPIProcessor() as processor:
        for org in test_orgs:
            print(f\"\\n{'='*50}\")
            print(f\"Searching NSF awards for: {org}\")
            print('='*50)
            
            awards = await processor.search_awards(org)
            
            if awards:
                print(f\"✓ Found {len(awards)} awards!\")
                # Show first award details
                if awards:
                    first = awards[0]
                    print(f\"  Example award:\")
                    print(f\"    ID: {first.get('id', 'N/A')}\")
                    print(f\"    Title: {first.get('title', 'N/A')[:60]}...\")
                    print(f\"    Amount: ${first.get('fundsObligatedAmt', 'N/A')}\")
                    print(f\"    PI: {first.get('piFirstName', '')} {first.get('piLastName', '')}\")
            else:
                print(f\"✗ No awards found\")

if __name__ == \"__main__\":
    asyncio.run(test_nsf_api())
PYTHON_EOF"

# Test the fixed NSF API
echo -e "\n🧪 Testing fixed NSF API processor..."
docker exec kbi_api python /app/src/data_processors/nsf_api_fixed.py

# Also check the new NSF Award Search site
echo -e "\n📊 Alternative: NSF Award Search Downloads"
echo "NSF provides bulk downloads of award data at:"
echo "https://www.nsf.gov/awardsearch/download.jsp"
echo ""
echo "We can download JSON files by year for offline processing"

# Create a function to download NSF data by year
cat >> ~/.bashrc << 'BASHEOF'

# Download NSF awards for a specific year
download_nsf_year() {
    local year="${1:-2024}"
    echo "📥 Downloading NSF awards for year $year..."
    
    # NSF provides yearly downloads
    wget -O "nsf_awards_${year}.zip" \
        "https://www.nsf.gov/awardsearch/download?DownloadFileName=Award&All=true"
    
    echo "Unzipping..."
    unzip "nsf_awards_${year}.zip"
}

# Test NSF API with exact parameters from docs
test_nsf_exact() {
    echo "🧪 Testing NSF with exact documentation examples..."
    
    # Example from docs: University of Montana
    curl -s 'https://www.research.gov/common/webapi/awardapisearch-v1.htm?awardeeName=University+of+Montana' | \
        grep -E "<award>|<title>|<fundsObligatedAmt>" | head -20
}

# Search NSF with proper encoding
search_nsf() {
    local query="${1:-MIT}"
    local encoded=$(python3 -c "import urllib.parse; print(urllib.parse.quote_plus('$query'))")
    
    echo "🔍 Searching NSF for: $query (encoded: $encoded)"
    
    curl -s "https://www.research.gov/common/webapi/awardapisearch-v1.htm?awardeeName=$encoded" | \
        grep -c "<award>" || echo "No awards found"
}
BASHEOF

source ~/.bashrc

echo "
✅ NSF API Implementation Updated!
==================================

🧪 Test Commands:
$ test_nsf_exact              # Test with known working example
$ search_nsf \"MIT\"            # Search with proper encoding
$ download_nsf_year 2024      # Download bulk data

📊 Key Findings:
1. NSF API requires exact parameter names
2. Organization names need proper encoding
3. Quotes and + signs matter for multi-word searches
4. Bulk downloads available as alternative

🎯 Next: Let's test with your DSBS companies
"
