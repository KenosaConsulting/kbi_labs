# Procurement API Integration Setup Guide

This document provides setup instructions for the new procurement APIs integrated into KBI Labs.

## 🚀 New Procurement APIs Implemented

### 1. GSA CALC API Integration
**File**: `gsa_calc_integration.py`
- **Purpose**: Labor rate pricing data from GSA schedules
- **Authentication**: ❌ No API key required
- **Rate Limits**: Conservative 1 second delay between requests
- **Data**: Competitive labor rates, vendor pricing, market analysis

### 2. FPDS (Federal Procurement Data System) Integration
**File**: `fpds_integration.py`
- **Purpose**: Historical federal contract performance data
- **Authentication**: ❌ No API key required
- **Rate Limits**: 2 second delay for government systems
- **Data**: Contract history, performance scores, agency analysis

### 3. Enhanced SAM.gov Opportunities API
**File**: `sam_opportunities_integration.py`
- **Purpose**: Real-time contract opportunities and vendor matching
- **Authentication**: ✅ **SAM.gov API key required**
- **Rate Limits**: 1 second delay
- **Data**: Contract opportunities, small business set-asides, opportunity matching

### 4. Unified Procurement Enrichment Pipeline
**File**: `unified_procurement_enrichment.py`
- **Purpose**: Orchestrates all procurement APIs for comprehensive enrichment
- **Features**: Batch processing, comprehensive scoring, intelligence reports

## 🔑 Required API Keys

### SAM.gov API Key (Required for Enhanced Features)

**What you need it for:**
- SAM.gov Opportunities API
- Enhanced SAM.gov entity data (already partially implemented)

**How to get it:**
1. Visit: https://sam.gov/web/sam/api-key
2. Create a SAM.gov account (free)
3. Request API access
4. Generate your API key

**Setup:**
```bash
# Option 1: Environment variable (recommended)
export SAM_GOV_API_KEY="your-api-key-here"

# Option 2: Pass directly to scripts
python sam_opportunities_integration.py --api-key "your-api-key-here"
```

**API Key Features:**
- ✅ Real-time contract opportunities
- ✅ Opportunity matching by NAICS/keywords
- ✅ Small business set-aside filtering
- ✅ Enhanced entity registration data
- ✅ Agency-specific opportunity searches

## 📦 Installation & Dependencies

### Install Additional Dependencies
```bash
# The new integrations use existing dependencies from requirements.txt
# No additional packages needed beyond what's already in KBI Labs

# Verify you have:
pip install aiohttp pandas asyncio logging pathlib
```

### Redis Setup (Optional - for SAM.gov caching)
```bash
# Install Redis for enhanced caching (optional)
# Ubuntu/Debian:
sudo apt install redis-server

# macOS:
brew install redis

# Start Redis
redis-server
```

## 🚀 Quick Start Usage

### 1. Test Individual APIs

```bash
# Test GSA CALC API (no key required)
cd /path/to/KBILabs-main
python gsa_calc_integration.py --mode search --query "Software Engineer"

# Test FPDS API (no key required)  
python fpds_integration.py --mode vendor --query "Acme Corporation"

# Test SAM Opportunities (requires API key)
python sam_opportunities_integration.py --api-key "YOUR_KEY" --mode smallbiz
```

### 2. Run Comprehensive Enrichment

```bash
# Process a CSV file with company data
python unified_procurement_enrichment.py \
  --input companies.csv \
  --output enriched_companies.csv \
  --sam-api-key "YOUR_SAM_KEY" \
  --batch-size 5 \
  --reports

# Without SAM.gov API key (limited features)
python unified_procurement_enrichment.py \
  --input companies.csv \
  --output enriched_companies.csv \
  --batch-size 5
```

### 3. Generate Intelligence Reports

```bash
# Generate market intelligence reports
python unified_procurement_enrichment.py \
  --input companies.csv \
  --reports \
  --reports-dir intelligence_reports
```

## 📊 Data Schema Extensions

The new procurement integrations add these fields to your company data:

### GSA CALC Fields
- `gsa_calc_found`: Boolean - Found in GSA schedules
- `gsa_schedule_rates`: Integer - Number of rate records
- `gsa_avg_rate`: Float - Average hourly rate
- `gsa_min_rate`: Float - Minimum rate
- `gsa_max_rate`: Float - Maximum rate
- `gsa_contract_vehicles`: List - GSA contract vehicles
- `gsa_competitive_position`: String - Competitive assessment

### FPDS Fields
- `fpds_found`: Boolean - Found in FPDS
- `fpds_total_contracts`: Integer - Historical contract count
- `fpds_total_value`: Float - Total contract value
- `fpds_avg_contract_value`: Float - Average contract size
- `fpds_performance_score`: Integer - Performance score (0-100)
- `fpds_primary_agencies`: List - Top contracting agencies

### SAM.gov Opportunities Fields
- `sam_opportunities_found`: Boolean - Found matching opportunities
- `sam_total_matches`: Integer - Number of opportunities
- `sam_high_score_matches`: Integer - High-scoring matches (80+)
- `sam_urgent_matches`: Integer - Urgent opportunities (<14 days)
- `sam_avg_match_score`: Float - Average opportunity match score
- `sam_top_opportunities`: List - Top 5 opportunities with details

### Unified Intelligence Fields
- `procurement_intelligence_score`: Integer - Overall score (0-100)
- `enrichment_summary`: Dict - Detailed enrichment metadata

## 🎯 Procurement Intelligence Scoring

The unified system calculates a comprehensive procurement readiness score (0-100):

- **SAM.gov Registration (25 points)**: Active registration status
- **Historical Performance (25 points)**: FPDS contract history and performance
- **GSA Schedule Presence (20 points)**: Number of GSA rate records
- **Opportunity Matching (15 points)**: Quality of opportunity matches
- **Federal Readiness (15 points)**: Certifications and compliance factors

## 📈 Business Intelligence Features

### 1. Competitive Analysis
- Compare labor rates across GSA schedules
- Identify market positioning opportunities
- Benchmark against competitors

### 2. Opportunity Intelligence
- Real-time contract opportunity matching
- Small business set-aside identification
- Response deadline management

### 3. Performance Analytics
- Historical contracting performance
- Agency relationship analysis
- Contract value trend analysis

### 4. Market Intelligence Reports
- GSA labor rate market analysis
- Small business opportunity landscapes
- Agency spending pattern analysis

## 🔧 Integration with Existing KBI Labs

### Add to Existing Workflows

```python
# Example: Integrate with existing company processing
from unified_procurement_enrichment import UnifiedProcurementEnrichment

async def enrich_company_with_procurement(company_data):
    async with UnifiedProcurementEnrichment(sam_api_key="YOUR_KEY") as enricher:
        return await enricher.enrich_company_comprehensive(company_data)
```

### Database Integration

The new fields can be added to your existing PostgreSQL schema:

```sql
-- Add new procurement intelligence columns
ALTER TABLE companies ADD COLUMN procurement_intelligence_score INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN gsa_calc_found BOOLEAN DEFAULT FALSE;
ALTER TABLE companies ADD COLUMN fpds_found BOOLEAN DEFAULT FALSE;
ALTER TABLE companies ADD COLUMN sam_opportunities_found BOOLEAN DEFAULT FALSE;
-- ... (add other fields as needed)
```

## 🚨 Rate Limiting & Best Practices

### API Rate Limits
- **GSA CALC**: No documented limits - using 1 second delays
- **FPDS**: Government system - using 2 second delays  
- **SAM.gov**: Enforced rate limits - using 1 second delays with retry logic

### Best Practices
1. **Batch Processing**: Use batch sizes of 5-10 companies
2. **Error Handling**: All APIs include comprehensive error handling
3. **Caching**: SAM.gov data is cached with Redis when available
4. **Monitoring**: Detailed logging for all API interactions
5. **Graceful Degradation**: System works with partial API availability

## 🐛 Troubleshooting

### Common Issues

1. **SAM.gov API Key Issues**
   ```bash
   # Test your API key
   curl -H "X-Api-Key: YOUR_KEY" "https://api.sam.gov/opportunities/v2/search?limit=1"
   ```

2. **Rate Limiting**
   - Reduce batch size if hitting rate limits
   - Increase delays between requests if needed

3. **No Data Found**
   - Companies may not have procurement history
   - Try different search terms (company name vs UEI vs DUNS)

4. **Memory Issues with Large Batches**
   - Reduce batch size to 3-5 companies
   - Process data in smaller chunks

## 📞 Support

For issues with the procurement integrations:
1. Check logs for specific error messages
2. Verify API keys are correctly set
3. Test individual APIs before running unified pipeline
4. Ensure proper CSV format for input data

The procurement intelligence system significantly enhances KBI Labs' ability to provide comprehensive federal contracting insights and opportunity identification for your clients.