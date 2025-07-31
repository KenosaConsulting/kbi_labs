#!/bin/bash

echo "🗂️ Organizing KBI Labs files into new structure..."

# Move main API files to src/api/
echo "Moving API files..."
mv kbi_api*.py src/api/ 2>/dev/null
mv api_server*.py src/api/ 2>/dev/null
mv combined_server*.py src/api/ 2>/dev/null
mv auth_api.py src/api/ 2>/dev/null
mv enhanced_api.py src/api/ 2>/dev/null
mv integrated_api_server.py src/api/ 2>/dev/null

# Move service/processing files to src/services/
echo "Moving service files..."
mv *enrichment*.py src/services/ 2>/dev/null
mv *_integration.py src/services/ 2>/dev/null
mv *_processor.py src/services/ 2>/dev/null
mv *_processing.py src/services/ 2>/dev/null
mv create_production_db*.py src/services/ 2>/dev/null
mv load_companies*.py src/services/ 2>/dev/null
mv process_*.py src/services/ 2>/dev/null
mv rescore_*.py src/services/ 2>/dev/null
mv update_scoring*.py src/services/ 2>/dev/null
mv implement_scoring.py src/services/ 2>/dev/null
mv complete_pipeline*.py src/services/ 2>/dev/null
mv fixed_pipeline*.py src/services/ 2>/dev/null
mv master_enrichment*.py src/services/ 2>/dev/null

# Move model-related files to src/models/
echo "Moving model files..."
mv database.py src/models/ 2>/dev/null
mv create_tables.py src/models/ 2>/dev/null

# Move utility files to src/utils/
echo "Moving utility files..."
mv check_*.py src/utils/ 2>/dev/null
mv fix_*.py src/utils/ 2>/dev/null
mv analyze_*.py src/utils/ 2>/dev/null
mv view_*.py src/utils/ 2>/dev/null
mv warm_cache.py src/utils/ 2>/dev/null
mv transfer_companies.py src/utils/ 2>/dev/null

# Move data processing scripts to scripts/data/
echo "Moving data scripts..."
mv generate_innovation_report.py scripts/data/ 2>/dev/null
mv fragmentation_summary.py scripts/data/ 2>/dev/null
mv platform_summary.py scripts/data/ 2>/dev/null
mv create_summary_report.py scripts/data/ 2>/dev/null
mv company_stats.py scripts/data/ 2>/dev/null

# Move web interface files
echo "Moving web interface files..."
mv web_interface*.py src/api/ 2>/dev/null
mv dashboard*.py src/api/ 2>/dev/null

# Move auth-related files
echo "Moving auth files..."
mv auth_middleware.py src/api/middleware/ 2>/dev/null || mkdir -p src/api/middleware && mv auth_middleware.py src/api/middleware/ 2>/dev/null
mv simple_auth.py src/api/middleware/ 2>/dev/null
mv create_auth*.py src/api/middleware/ 2>/dev/null

# Move specialized services
echo "Moving specialized services..."
mv opportunities_api.py src/api/ 2>/dev/null
mv sam_*.py src/services/ 2>/dev/null
mv patent_*.py src/services/ 2>/dev/null

# Move test setup files
echo "Moving setup files..."
mv setup_enrichment.py scripts/deployment/ 2>/dev/null
mv run_enrichment.py scripts/deployment/ 2>/dev/null
mv main.py scripts/deployment/ 2>/dev/null

# List remaining Python files in root
echo ""
echo "📋 Remaining Python files in root directory:"
ls -la *.py 2>/dev/null || echo "None - all files organized!"

# Create a mapping file for reference
echo ""
echo "📝 Creating file mapping reference..."
cat > file_organization_map.txt << 'MAPPING'
FILE ORGANIZATION MAP
====================

src/api/
  - All kbi_api*.py files (main API endpoints)
  - api_server*.py files
  - combined_server*.py files
  - web_interface*.py files
  - dashboard*.py files
  - opportunities_api.py
  
src/api/middleware/
  - auth_middleware.py
  - simple_auth.py
  - create_auth*.py files

src/services/
  - All enrichment files
  - All integration files (sam_*, patent_*, etc.)
  - All processing files
  - Database creation files
  - Pipeline files
  - Scoring files

src/models/
  - database.py
  - create_tables.py

src/utils/
  - All check_*.py files
  - All fix_*.py files
  - Utility scripts
  - Cache warming

scripts/data/
  - Report generation scripts
  - Analysis scripts
  - Summary scripts

scripts/deployment/
  - Setup scripts
  - Main entry points
MAPPING

echo ""
echo "✅ File organization complete!"
echo "📖 Check file_organization_map.txt for reference"
