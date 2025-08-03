📚 KBI Labs API with USASpending - Quick Reference

Base URL: http://localhost:8001

Authentication: None (add before production)

Endpoints:
---------
1. Health Check
   GET /health
   Returns: {"status": "healthy", "service": "KBI Labs API", "version": "2.0.0"}

2. USASpending Search
   GET /api/v3/usaspending/search/{uei}
   GET /api/v3/usaspending/search/{uei}?fiscal_year=2024
   GET /api/v3/usaspending/search/{uei}?use_cache=false
   
   Returns: Federal contract awards and spending summary

3. Enrichment
   POST /api/v3/enrichment/enrich
   Body: {"uei": "string", "company_name": "string"}
   
   Returns: Enrichment status and available data sources

4. Metrics (Prometheus)
   GET /metrics
   
   Returns: Prometheus-formatted metrics

Example Usage:
-------------
# Search federal contracts
curl http://localhost:8001/api/v3/usaspending/search/M67WJSTEVKP3

# Enrich a company
curl -X POST http://localhost:8001/api/v3/enrichment/enrich \
  -H "Content-Type: application/json" \
  -d '{"uei": "M67WJSTEVKP3"}'

# Check health
curl http://localhost:8001/health

