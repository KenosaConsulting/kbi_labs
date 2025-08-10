# Obsolete Files Cleanup Report
**Files to be removed as they are now replaced by consolidated main_server.py**

## Obsolete Server Files (Replaced by main_server.py)

### Root Level
- `unified_api_middleware.py` - Replaced by backend/auth/middleware.py
- `streamlined_procurement_analyst.py` - Functionality integrated into main_server.py
- `setup_enrichment_system.py` - Replaced by proper environment configuration

### src/api/ - Multiple redundant API servers
- `api_server.py`
- `api_server_v2.py`
- `auth_api.py`
- `combined_server.py`
- `combined_server_v2.py`
- `combined_server_v2_fixed.py`
- `enhanced_api.py`
- `integrated_api_server.py`
- `kbi_api_complete.py`
- `kbi_api_debug.py`
- `kbi_api_enhanced.py`
- `kbi_api_final.py`
- `kbi_api_final_working.py`
- `kbi_api_fixed.py`
- `kbi_api_simple.py`
- `kbi_api_simple_working.py`
- `kbi_api_v2.py`
- `kbi_api_v2_fixed.py`
- `kbi_api_with_details.py`
- `kbi_api_with_market.py`
- `kbi_api_with_market_intel.py`
- `kbi_api_working.py`
- `kbi_api_working_complete.py`
- `web_interface.py`
- `web_interface_fixed.py`
- `working_dashboard.py`

### Old Auth Files (Replaced by backend/auth/)
- `src/auth/foundation.py`
- `src/auth_sqlite.py`
- `src/api/auth.py`
- `src/api/middleware/auth_middleware.py`
- `src/api/middleware/create_auth_sqlite.py`
- `src/api/middleware/create_auth_system.py`
- `src/api/middleware/simple_auth.py`

### Duplicate Test Files
- `tests/unit/test_setup.py` - Functionality covered by new comprehensive tests
- Some redundant test files in tests/unit/

## Files to Keep
- `main_server.py` - Primary consolidated server
- `backend/auth/` - New authentication system
- `backend/cache/` - New caching system  
- `backend/monitoring/` - New monitoring system
- `tests/test_*.py` - New comprehensive test suite
- `Dockerfile` & `docker-compose.yml` - Updated containerization
- All configuration files (.env.*, pyproject.toml, etc.)