# KBI Labs Procurement Intelligence Platform - Setup Guide

## Overview

The KBI Labs Procurement Intelligence Platform is a comprehensive AI-powered senior analyst system that provides automated procurement intelligence, opportunity analysis, and strategic guidance for small businesses in government contracting.

## Architecture Summary

### Core Components

1. **Multi-Source Data Ingestion** (`src/integrations/procurement/`)
   - 70+ government data sources (SAM.gov, USASpending, FPDS-NG, etc.)
   - Automated scrapers with rate limiting and error handling
   - Redis caching for performance optimization

2. **AI Analysis Engine** (`src/ai_analysis/`)
   - Opportunity assessment and scoring
   - Competitive intelligence analysis
   - Strategic recommendations generation
   - Document analysis and processing

3. **Living Library System** (Database schema in `procurement_intelligence_schema.sql`)
   - Knowledge base with procurement guides and best practices
   - Proposal templates and examples
   - Competitive intelligence repository
   - Historical analysis and patterns

4. **API Integration** (`src/api/routers/procurement_intelligence.py`)
   - RESTful endpoints for all functionality
   - Batch processing capabilities
   - Real-time analysis and reporting

## Installation and Setup

### Prerequisites

1. **Existing KBI Labs Environment**
   - PostgreSQL database
   - Redis server
   - MongoDB (optional for document storage)
   - Docker environment

2. **API Keys Required**
   ```bash
   # Add to .env file
   OPENAI_API_KEY=your_openai_api_key_here
   SAM_GOV_API_KEY=your_sam_gov_api_key_here  # Optional but recommended
   ```

### Database Setup

1. **Run the procurement intelligence schema**:
   ```bash
   psql -h localhost -U your_username -d your_database -f procurement_intelligence_schema.sql
   ```

2. **Verify tables created**:
   ```sql
   \dt *procurement*
   \dt *intelligence*
   \dt *knowledge*
   ```

### Service Integration

1. **Update main API router** (`src/api/main.py` or `kbi_api/app.py`):
   ```python
   from src.api.routers.procurement_intelligence import router as procurement_router
   
   app.include_router(procurement_router)
   ```

2. **Install additional dependencies**:
   ```bash
   pip install beautifulsoup4 httpx openai
   ```

### Configuration

1. **Environment Variables** (add to `.env`):
   ```bash
   # Procurement Intelligence Configuration
   PROCUREMENT_CACHE_TTL=21600
   MAX_CONCURRENT_ANALYSES=5
   ENABLE_DEEP_ANALYSIS=true
   
   # Data Source Configuration
   SAM_GOV_API_KEY=your_key_here
   DATA_REFRESH_INTERVAL_HOURS=6
   ```

2. **Redis Configuration**:
   - Ensure Redis is running on localhost:6379
   - No additional configuration needed

## API Endpoints

### Core Intelligence Endpoints

1. **Analyze Procurement Opportunity**
   ```
   POST /api/v3/procurement-intelligence/analyze
   ```
   Generate comprehensive intelligence analysis for a company and opportunity.

2. **Search Opportunities**
   ```
   GET /api/v3/procurement-intelligence/opportunities/search
   ```
   Find relevant procurement opportunities based on company profile.

3. **Get Contract History**
   ```
   GET /api/v3/procurement-intelligence/companies/{uei}/contracts
   ```
   Retrieve comprehensive contract history for a company.

4. **Market Intelligence**
   ```
   GET /api/v3/procurement-intelligence/market-intelligence
   ```
   Get market trends, forecasts, and competitive analysis.

5. **Batch Analysis**
   ```
   POST /api/v3/procurement-intelligence/batch-analyze
   ```
   Analyze multiple opportunities in parallel.

### Data Management Endpoints

6. **Data Sources Status**
   ```
   GET /api/v3/procurement-intelligence/data-sources/status
   ```
   Check status of all data ingestion sources.

7. **Refresh Data Sources**
   ```
   POST /api/v3/procurement-intelligence/data-sources/refresh
   ```
   Trigger manual refresh of all data sources.

## Usage Examples

### 1. Analyze Single Opportunity

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v3/procurement-intelligence/analyze",
    json={
        "company_uei": "ABC123DEF456",
        "opportunity_id": "NOTICE_12345",
        "analysis_depth": "standard"
    }
)

intelligence_report = response.json()
print(f"Win Probability: {intelligence_report['win_probability']}")
print(f"Recommended Actions: {intelligence_report['recommended_actions']}")
```

### 2. Search for Opportunities

```python
response = requests.get(
    "http://localhost:8000/api/v3/procurement-intelligence/opportunities/search",
    params={
        "company_uei": "ABC123DEF456",
        "agency": "Department of Defense",
        "naics": "541512",
        "max_results": 20
    }
)

opportunities = response.json()
print(f"Found {opportunities['total_found']} opportunities")
```

### 3. Get Market Intelligence

```python
response = requests.get(
    "http://localhost:8000/api/v3/procurement-intelligence/market-intelligence",
    params={
        "naics_codes": "541511,541512,541513",
        "agencies": "DoD,NASA,DHS",
        "time_range_days": 365
    }
)

market_intel = response.json()
print(f"Active Opportunities: {market_intel['active_opportunities']}")
```

## Data Source Configuration

### Adding New Data Sources

1. **Register in Database**:
   ```sql
   INSERT INTO procurement_data_sources (
       source_id, source_name, source_url, source_type, 
       data_format, priority, refresh_interval_hours
   ) VALUES (
       'new_source', 'New Source Name', 'https://api.example.gov/',
       'contract_data', 'json_api', 2, 24
   );
   ```

2. **Create Custom Scraper** (if needed):
   ```python
   # In src/integrations/procurement/scrapers/
   class NewSourceScraper(BaseProcurementScraper):
       async def _fetch_source_data(self):
           # Implementation specific to new source
           pass
   ```

3. **Register Scraper**:
   ```python
   # In scraper_factory.py
   self.source_scrapers['new_source'] = NewSourceScraper
   ```

### Data Source Priorities

- **Priority 1**: Critical sources (SAM.gov, USASpending, FPDS-NG)
- **Priority 2**: Important sources (Agency-specific sites, SBIR/STTR)
- **Priority 3**: Supplementary sources (Regulatory sites, reference data)

## Monitoring and Maintenance

### Health Checks

```bash
# Check API health
curl http://localhost:8000/api/v3/procurement-intelligence/data-sources/status

# Check database connectivity
psql -c "SELECT COUNT(*) FROM procurement_data_sources;"

# Check Redis connectivity
redis-cli ping
```

### Performance Monitoring

1. **Database Queries**:
   - Monitor slow queries on large tables
   - Check index usage on search operations

2. **API Response Times**:
   - Intelligence analysis: Target < 30 seconds
   - Search operations: Target < 5 seconds
   - Data refresh: Background processing

3. **Cache Hit Rates**:
   - Opportunity data: Target > 80%
   - Intelligence reports: Target > 70%

### Maintenance Tasks

1. **Daily**:
   - Automated data source refresh
   - Cache cleanup for expired entries
   - Error log review

2. **Weekly**:
   - Database maintenance (VACUUM, ANALYZE)
   - Performance metrics review
   - Data quality assessment

3. **Monthly**:
   - Add new procurement data sources
   - Update knowledge base articles
   - Review and update best practices

## Troubleshooting

### Common Issues

1. **Data Source Connection Failures**:
   - Check API keys and rate limits
   - Verify network connectivity
   - Review source-specific error logs

2. **Slow Intelligence Analysis**:
   - Check OpenAI API rate limits
   - Verify Redis caching is working
   - Review database query performance

3. **Missing Opportunities**:
   - Verify data source scrapers are active
   - Check extraction patterns for website changes
   - Review search filters and criteria

### Debug Commands

```bash
# Check data ingestion logs
psql -c "SELECT * FROM data_ingestion_logs ORDER BY started_at DESC LIMIT 10;"

# Check Redis cache status
redis-cli info memory
redis-cli keys "procurement_data:*"

# Check API logs
tail -f logs/api.log | grep "procurement-intelligence"
```

## Integration with Existing KBI Features

### Company Enrichment
- Intelligence reports automatically use existing company data
- Contract history integrates with SAM.gov enrichment
- Competitive analysis leverages existing scoring models

### ML Models
- Win probability calculation uses existing ML patterns
- Fraud detection can flag suspicious opportunities
- Success prediction models enhance recommendations

### Dashboard Integration
- Intelligence reports can be displayed in existing Streamlit dashboard
- Opportunity feeds integrate with current company views
- Market intelligence enhances existing analytics

## Next Steps

1. **Start with Core Sources**: Initialize SAM.gov, USASpending, and FedConnect
2. **Test Intelligence Analysis**: Run analysis on known companies and opportunities
3. **Populate Knowledge Base**: Add agency-specific guides and templates
4. **Scale Data Sources**: Gradually add additional government sources
5. **Enhance AI Models**: Refine recommendation algorithms based on usage

## Support and Documentation

- API Documentation: Available at `/api/v3/docs` when server is running
- Database Schema: See `procurement_intelligence_schema.sql` for full structure
- Code Documentation: Inline documentation in all source files
- Error Handling: Comprehensive logging throughout the system

This platform provides a powerful foundation for automated procurement intelligence that can significantly enhance small business success in government contracting.