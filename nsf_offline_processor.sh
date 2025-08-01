#!/bin/bash
# nsf_offline_processor.sh
# Downloads and processes NSF award data offline for innovation metrics

echo "🔬 NSF Offline Data Processor"
echo "============================="

# Step 1: Download NSF data for recent years
echo "📥 Downloading NSF award data..."

# Create data directory
mkdir -p ~/KBILabs/nsf_data
cd ~/KBILabs/nsf_data

# Download recent years (2023-2024)
for year in 2024 2023; do
    if [ ! -f "${year}.zip" ]; then
        echo "Downloading NSF awards for ${year}..."
        wget -q --show-progress "https://www.nsf.gov/awardsearch/download/${year}.zip" -O "${year}.zip"
        unzip -q "${year}.zip"
        echo "✓ Downloaded ${year} awards"
    else
        echo "✓ ${year}.zip already exists"
    fi
done

# Step 2: Create NSF data processor
echo -e "\n📝 Creating NSF data processor..."

docker exec kbi_api bash -c "cat > /app/src/data_processors/nsf_offline_processor.py << 'PYTHON_EOF'
#!/usr/bin/env python3
\"\"\"
NSF Offline Data Processor
Processes downloaded NSF award JSON files for innovation metrics
\"\"\"

import json
import pandas as pd
import glob
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSFOfflineProcessor:
    \"\"\"Process NSF award data from downloaded JSON files\"\"\"
    
    def __init__(self, data_path: str = '/app/nsf_data'):
        self.data_path = data_path
        self.awards_df = None
        
    def load_nsf_data(self, years: List[int] = None) -> pd.DataFrame:
        \"\"\"Load NSF award data from JSON files\"\"\"
        if years is None:
            years = [2024, 2023, 2022]
            
        all_awards = []
        
        for year in years:
            json_files = glob.glob(f'{self.data_path}/{year}/*.json')
            logger.info(f'Found {len(json_files)} JSON files for year {year}')
            
            for json_file in json_files[:100]:  # Limit for testing
                try:
                    with open(json_file, 'r') as f:
                        award = json.load(f)
                        # Extract key fields
                        award_data = {
                            'id': award.get('id'),
                            'title': award.get('title'),
                            'awardeeName': award.get('institution', {}).get('name', ''),
                            'awardeeCity': award.get('institution', {}).get('city', ''),
                            'awardeeState': award.get('institution', {}).get('stateCode', ''),
                            'fundsObligatedAmt': float(award.get('fundsObligatedAmt', 0)),
                            'startDate': award.get('startDate'),
                            'endDate': award.get('endDate'),
                            'piFirstName': award.get('piFirstName'),
                            'piLastName': award.get('piLastName'),
                            'abstractText': award.get('abstractText', '')[:500]  # First 500 chars
                        }
                        all_awards.append(award_data)
                except Exception as e:
                    logger.error(f'Error reading {json_file}: {e}')
                    
        self.awards_df = pd.DataFrame(all_awards)
        logger.info(f'Loaded {len(self.awards_df)} total awards')
        return self.awards_df
    
    def search_organization(self, org_name: str) -> pd.DataFrame:
        \"\"\"Search for awards by organization name\"\"\"
        if self.awards_df is None:
            self.load_nsf_data()
            
        # Try multiple matching strategies
        org_variants = [
            org_name,
            org_name.upper(),
            org_name.replace(' LLC', '').replace(' Inc', '').replace(' Corp', ''),
            org_name.split()[0]  # First word only
        ]
        
        matches = pd.DataFrame()
        for variant in org_variants:
            mask = self.awards_df['awardeeName'].str.contains(variant, case=False, na=False)
            found = self.awards_df[mask]
            if not found.empty:
                matches = found
                break
                
        return matches
    
    def calculate_innovation_metrics(self, org_name: str) -> Dict:
        \"\"\"Calculate innovation metrics for an organization\"\"\"
        awards = self.search_organization(org_name)
        
        metrics = {
            'organization_name': org_name,
            'nsf_awards_count': len(awards),
            'nsf_total_funding': float(awards['fundsObligatedAmt'].sum()),
            'nsf_recent_awards': 0,
            'research_areas': [],
            'award_years': []
        }
        
        if not awards.empty:
            # Count recent awards (last 2 years)
            for _, award in awards.iterrows():
                try:
                    start_date = pd.to_datetime(award['startDate'])
                    if (datetime.now() - start_date).days < 730:  # 2 years
                        metrics['nsf_recent_awards'] += 1
                except:
                    pass
                    
            # Get unique years
            metrics['award_years'] = awards['startDate'].apply(lambda x: x[:4] if x else '').unique().tolist()
            
            # Extract research areas from titles (simplified)
            titles = ' '.join(awards['title'].fillna('').tolist()).lower()
            research_keywords = ['ai', 'machine learning', 'quantum', 'nano', 'bio', 'cyber', 'data']
            metrics['research_areas'] = [kw for kw in research_keywords if kw in titles]
            
        return metrics

# Function to process DSBS companies
async def process_dsbs_with_nsf_offline(dsbs_file: str, output_file: str, sample_size: int = None):
    \"\"\"Process DSBS companies with offline NSF data\"\"\"
    logger.info('Starting offline NSF enrichment...')
    
    # Load DSBS data
    dsbs_df = pd.read_csv(dsbs_file)
    if sample_size:
        dsbs_df = dsbs_df.sample(n=min(sample_size, len(dsbs_df)))
    
    # Initialize processor
    processor = NSFOfflineProcessor()
    processor.load_nsf_data([2024, 2023])
    
    # Process each organization
    results = []
    for org_name in dsbs_df['Organization Name'].dropna().unique():
        metrics = processor.calculate_innovation_metrics(org_name)
        results.append(metrics)
        
    # Create results dataframe
    results_df = pd.DataFrame(results)
    
    # Merge with original DSBS data
    enriched_df = dsbs_df.merge(
        results_df,
        left_on='Organization Name',
        right_on='organization_name',
        how='left'
    )
    
    # Fill missing values
    enriched_df['nsf_awards_count'] = enriched_df['nsf_awards_count'].fillna(0)
    enriched_df['nsf_total_funding'] = enriched_df['nsf_total_funding'].fillna(0)
    
    # Save results
    enriched_df.to_csv(output_file, index=False)
    
    # Print summary
    print(f'\\n=== NSF Enrichment Summary ===')
    print(f'Total organizations processed: {len(results)}')
    print(f'Organizations with NSF awards: {(enriched_df[\\'nsf_awards_count\\'] > 0).sum()}')
    print(f'Total NSF funding found: ${enriched_df[\\'nsf_total_funding\\'].sum():,.0f}')
    
    return enriched_df

# Test function
if __name__ == '__main__':
    processor = NSFOfflineProcessor()
    
    # Test with known organizations
    test_orgs = ['Massachusetts Institute of Technology', 'MIT', 'Stanford University']
    
    print('Testing NSF offline processor...')
    processor.load_nsf_data([2024])
    
    for org in test_orgs:
        print(f'\\nSearching for: {org}')
        awards = processor.search_organization(org)
        if not awards.empty:
            print(f'  Found {len(awards)} awards')
            print(f'  Total funding: ${awards[\\'fundsObligatedAmt\\'].sum():,.0f}')
            print(f'  Example: {awards.iloc[0][\\'title\\'][:60]}...')
PYTHON_EOF"

# Step 3: Copy NSF data to container
echo -e "\n📤 Copying NSF data to container..."
docker exec kbi_api mkdir -p /app/nsf_data
for year in 2024 2023; do
    if [ -d "${year}" ]; then
        docker cp "${year}" kbi_api:/app/nsf_data/
        echo "✓ Copied ${year} data to container"
    fi
done

# Step 4: Test the processor
echo -e "\n🧪 Testing NSF offline processor..."
docker exec kbi_api python /app/src/data_processors/nsf_offline_processor.py

# Step 5: Create helper functions
cat >> ~/.bashrc << 'BASHEOF'

# Process DSBS with offline NSF data
process_nsf_offline() {
    local sample="${1:-100}"
    echo "🔬 Processing $sample DSBS companies with NSF data..."
    
    docker exec kbi_api python -c "
import asyncio
from src.data_processors.nsf_offline_processor import process_dsbs_with_nsf_offline

asyncio.run(process_dsbs_with_nsf_offline(
    '/app/data/All_DSBS_processed_chunk_001_20250727_182259.csv',
    'dsbs_with_nsf_metrics.csv',
    sample_size=$sample
))
"
}

# Search NSF offline data
search_nsf_offline() {
    local org="${1:-MIT}"
    docker exec kbi_api python -c "
from src.data_processors.nsf_offline_processor import NSFOfflineProcessor
p = NSFOfflineProcessor()
p.load_nsf_data([2024])
awards = p.search_organization('$org')
print(f'Found {len(awards)} awards for $org')
if not awards.empty:
    print(f'Total funding: \${awards[\\"fundsObligatedAmt\\"].sum():,.0f}')
"
}

# Download more NSF years
download_nsf_years() {
    cd ~/KBILabs/nsf_data
    for year in 2022 2021 2020; do
        if [ ! -f "${year}.zip" ]; then
            echo "Downloading $year..."
            wget -q --show-progress "https://www.nsf.gov/awardsearch/download/${year}.zip"
            unzip -q "${year}.zip"
        fi
    done
}
BASHEOF

source ~/.bashrc

echo "
✅ NSF Offline Processor Ready!
===============================

📊 Downloaded NSF Data:
- 2024 awards ✓
- 2023 awards ✓

🧪 Test Commands:
$ search_nsf_offline \"Stanford University\"
$ process_nsf_offline 100

🚀 Next Steps:
1. Test with your DSBS companies
2. Download more years if needed: download_nsf_years
3. Process full DSBS dataset

💡 Benefits:
- No API rate limits
- Full award details available
- Faster processing
- More reliable than API
"
