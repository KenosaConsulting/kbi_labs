# 🔒 CRITICAL PRODUCTION ASSETS - DO NOT DELETE

## Core Production Files (PROTECTED)
### Frontend/Dashboard
- `/smb_dashboard_fast.html` - Main production dashboard (< 2s load)
- `/kbi_dashboard/` - React dashboard components
- `/static/` - Enhanced demo dashboards
- `/index.html` - Main entry point

### Backend/API
- `/src/main.py` - Primary unified API server (v3.0.0)
- `/src/api/` - All API routers and endpoints
- `/src/integrations/` - Government API integrations
- `/src/services/` - Business logic services

### Data Assets
- `/companies_large.json` - 1.36M lines of enriched companies (PRIMARY DATASET)
- `/companies.json` - Company sample data
- `/kbi_labs.db` - SQLite production database
- `/data/` - Data processing directories

### ML/AI Components
- `/ml_contract_predictor.py` - Contract prediction ML
- `/enhanced_ml_features.py` - Multi-source ML models
- `/src/ai_services/` - AI analysis services
- `/models/` - Trained ML models and scalers

### Infrastructure
- `/docker-compose.yml` - Production container orchestration
- `/requirements.txt` - Python dependencies
- `/Dockerfile` - Container configuration
- `/monitoring/` - Performance monitoring setup

### Configuration
- `/api_keys.env` - API keys and environment variables
- `/pytest.ini` - Test configuration
- `/nginx.conf` - Web server configuration

## Files Safe to Delete (BLOAT IDENTIFIED)
### Archive Directory (1.3MB of bloat)
- `/archive/` - ENTIRE DIRECTORY can be deleted
  - backup_files/
  - dashboards_old/
  - debug_files/
  - documentation/

### Root Directory Scattered Files (90+ files)
- All duplicate API files (api_*.py variants)
- All debug/test files in root
- Old shell scripts (.sh files not in use)
- Markdown documentation duplicates

### Duplicate API Files
- `api_server.py` (use src/main.py instead)
- `api_gateway*.py` variants
- `api_with_*.py` variants
- `working_*.py` files
- `enhanced_*.py` duplicates

Total Estimated Cleanup: 500+ files, 50% repository size reduction