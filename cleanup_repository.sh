#!/bin/bash
# KBI Labs Repository Cleanup Script
# Generated automatically - review before running

set -e

echo "🧹 Starting KBI Labs repository cleanup..."

# Create backup directory
mkdir -p .cleanup_backup/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".cleanup_backup/$(date +%Y%m%d_%H%M%S)"

echo "📦 Backup directory: $BACKUP_DIR"


# Backup Files
echo "Cleaning up 28 backup_files..."
# docker-compose.yml.backup.20250731_012309
mkdir -p "$BACKUP_DIR/$(dirname 'docker-compose.yml.backup.20250731_012309')"
cp 'docker-compose.yml.backup.20250731_012309' "$BACKUP_DIR/docker-compose.yml.backup.20250731_012309" 2>/dev/null || true
rm 'docker-compose.yml.backup.20250731_012309'

# docker-compose.yml.backup
mkdir -p "$BACKUP_DIR/$(dirname 'docker-compose.yml.backup')"
cp 'docker-compose.yml.backup' "$BACKUP_DIR/docker-compose.yml.backup" 2>/dev/null || true
rm 'docker-compose.yml.backup'

# smb_intelligence.py.backup
mkdir -p "$BACKUP_DIR/$(dirname 'smb_intelligence.py.backup')"
cp 'smb_intelligence.py.backup' "$BACKUP_DIR/smb_intelligence.py.backup" 2>/dev/null || true
rm 'smb_intelligence.py.backup'

# scripts/backup_production.sh
mkdir -p "$BACKUP_DIR/$(dirname 'scripts/backup_production.sh')"
cp 'scripts/backup_production.sh' "$BACKUP_DIR/scripts/backup_production.sh" 2>/dev/null || true
rm 'scripts/backup_production.sh'

# ai_insights/ai_insights_api_new_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/ai_insights_api_new_backup.py')"
cp 'ai_insights/ai_insights_api_new_backup.py' "$BACKUP_DIR/ai_insights/ai_insights_api_new_backup.py" 2>/dev/null || true
rm 'ai_insights/ai_insights_api_new_backup.py'

# ai_insights/ai_insights_api_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/ai_insights_api_backup.py')"
cp 'ai_insights/ai_insights_api_backup.py' "$BACKUP_DIR/ai_insights/ai_insights_api_backup.py" 2>/dev/null || true
rm 'ai_insights/ai_insights_api_backup.py'

# kbi_dashboard/portfolio_backup.html
mkdir -p "$BACKUP_DIR/$(dirname 'kbi_dashboard/portfolio_backup.html')"
cp 'kbi_dashboard/portfolio_backup.html' "$BACKUP_DIR/kbi_dashboard/portfolio_backup.html" 2>/dev/null || true
rm 'kbi_dashboard/portfolio_backup.html'

# kbi_dashboard/company-details-backup.html
mkdir -p "$BACKUP_DIR/$(dirname 'kbi_dashboard/company-details-backup.html')"
cp 'kbi_dashboard/company-details-backup.html' "$BACKUP_DIR/kbi_dashboard/company-details-backup.html" 2>/dev/null || true
rm 'kbi_dashboard/company-details-backup.html'

# kbi_dashboard/index.html.backup
mkdir -p "$BACKUP_DIR/$(dirname 'kbi_dashboard/index.html.backup')"
cp 'kbi_dashboard/index.html.backup' "$BACKUP_DIR/kbi_dashboard/index.html.backup" 2>/dev/null || true
rm 'kbi_dashboard/index.html.backup'

# src/main.py.backup
mkdir -p "$BACKUP_DIR/$(dirname 'src/main.py.backup')"
cp 'src/main.py.backup' "$BACKUP_DIR/src/main.py.backup" 2>/dev/null || true
rm 'src/main.py.backup'

# src/database/connection.py.postgres_backup
mkdir -p "$BACKUP_DIR/$(dirname 'src/database/connection.py.postgres_backup')"
cp 'src/database/connection.py.postgres_backup' "$BACKUP_DIR/src/database/connection.py.postgres_backup" 2>/dev/null || true
rm 'src/database/connection.py.postgres_backup'

# src/api/combined_server_v2_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/combined_server_v2_backup.py')"
cp 'src/api/combined_server_v2_backup.py' "$BACKUP_DIR/src/api/combined_server_v2_backup.py" 2>/dev/null || true
rm 'src/api/combined_server_v2_backup.py'

# src/api/main.py.backup
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/main.py.backup')"
cp 'src/api/main.py.backup' "$BACKUP_DIR/src/api/main.py.backup" 2>/dev/null || true
rm 'src/api/main.py.backup'

# src/api/api_server_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/api_server_backup.py')"
cp 'src/api/api_server_backup.py' "$BACKUP_DIR/src/api/api_server_backup.py" 2>/dev/null || true
rm 'src/api/api_server_backup.py'

# src/api/dashboard_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/dashboard_backup.py')"
cp 'src/api/dashboard_backup.py' "$BACKUP_DIR/src/api/dashboard_backup.py" 2>/dev/null || true
rm 'src/api/dashboard_backup.py'

# src/services/complete_pipeline_no_sam_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/services/complete_pipeline_no_sam_backup.py')"
cp 'src/services/complete_pipeline_no_sam_backup.py' "$BACKUP_DIR/src/services/complete_pipeline_no_sam_backup.py" 2>/dev/null || true
rm 'src/services/complete_pipeline_no_sam_backup.py'

# kbi_dashboard/src/services/api_backup.js
mkdir -p "$BACKUP_DIR/$(dirname 'kbi_dashboard/src/services/api_backup.js')"
cp 'kbi_dashboard/src/services/api_backup.js' "$BACKUP_DIR/kbi_dashboard/src/services/api_backup.js" 2>/dev/null || true
rm 'kbi_dashboard/src/services/api_backup.js'

# docker-compose.yml.backup
mkdir -p "$BACKUP_DIR/$(dirname 'docker-compose.yml.backup')"
cp 'docker-compose.yml.backup' "$BACKUP_DIR/docker-compose.yml.backup" 2>/dev/null || true
rm 'docker-compose.yml.backup'

# smb_intelligence.py.backup
mkdir -p "$BACKUP_DIR/$(dirname 'smb_intelligence.py.backup')"
cp 'smb_intelligence.py.backup' "$BACKUP_DIR/smb_intelligence.py.backup" 2>/dev/null || true
rm 'smb_intelligence.py.backup'

# kbi_dashboard/index.html.backup
mkdir -p "$BACKUP_DIR/$(dirname 'kbi_dashboard/index.html.backup')"
cp 'kbi_dashboard/index.html.backup' "$BACKUP_DIR/kbi_dashboard/index.html.backup" 2>/dev/null || true
rm 'kbi_dashboard/index.html.backup'

# src/main.py.backup
mkdir -p "$BACKUP_DIR/$(dirname 'src/main.py.backup')"
cp 'src/main.py.backup' "$BACKUP_DIR/src/main.py.backup" 2>/dev/null || true
rm 'src/main.py.backup'

# src/api/main.py.backup
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/main.py.backup')"
cp 'src/api/main.py.backup' "$BACKUP_DIR/src/api/main.py.backup" 2>/dev/null || true
rm 'src/api/main.py.backup'

# ai_insights/ai_insights_api_new_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/ai_insights_api_new_backup.py')"
cp 'ai_insights/ai_insights_api_new_backup.py' "$BACKUP_DIR/ai_insights/ai_insights_api_new_backup.py" 2>/dev/null || true
rm 'ai_insights/ai_insights_api_new_backup.py'

# ai_insights/ai_insights_api_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/ai_insights_api_backup.py')"
cp 'ai_insights/ai_insights_api_backup.py' "$BACKUP_DIR/ai_insights/ai_insights_api_backup.py" 2>/dev/null || true
rm 'ai_insights/ai_insights_api_backup.py'

# src/api/combined_server_v2_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/combined_server_v2_backup.py')"
cp 'src/api/combined_server_v2_backup.py' "$BACKUP_DIR/src/api/combined_server_v2_backup.py" 2>/dev/null || true
rm 'src/api/combined_server_v2_backup.py'

# src/api/api_server_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/api_server_backup.py')"
cp 'src/api/api_server_backup.py' "$BACKUP_DIR/src/api/api_server_backup.py" 2>/dev/null || true
rm 'src/api/api_server_backup.py'

# src/api/dashboard_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/dashboard_backup.py')"
cp 'src/api/dashboard_backup.py' "$BACKUP_DIR/src/api/dashboard_backup.py" 2>/dev/null || true
rm 'src/api/dashboard_backup.py'

# src/services/complete_pipeline_no_sam_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/services/complete_pipeline_no_sam_backup.py')"
cp 'src/services/complete_pipeline_no_sam_backup.py' "$BACKUP_DIR/src/services/complete_pipeline_no_sam_backup.py" 2>/dev/null || true
rm 'src/services/complete_pipeline_no_sam_backup.py'


# Broken Files
echo "Cleaning up 2 broken_files..."
# docker-compose.yml.broken
mkdir -p "$BACKUP_DIR/$(dirname 'docker-compose.yml.broken')"
cp 'docker-compose.yml.broken' "$BACKUP_DIR/docker-compose.yml.broken" 2>/dev/null || true
rm 'docker-compose.yml.broken'

# kbi_dashboard/company-details-broken.html
mkdir -p "$BACKUP_DIR/$(dirname 'kbi_dashboard/company-details-broken.html')"
cp 'kbi_dashboard/company-details-broken.html' "$BACKUP_DIR/kbi_dashboard/company-details-broken.html" 2>/dev/null || true
rm 'kbi_dashboard/company-details-broken.html'


# Old Files
echo "Cleaning up 3 old_files..."
# kbi_dashboard/portfolio_old.html
mkdir -p "$BACKUP_DIR/$(dirname 'kbi_dashboard/portfolio_old.html')"
cp 'kbi_dashboard/portfolio_old.html' "$BACKUP_DIR/kbi_dashboard/portfolio_old.html" 2>/dev/null || true
rm 'kbi_dashboard/portfolio_old.html'

# src/services/smb_intelligence_old.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/services/smb_intelligence_old.py')"
cp 'src/services/smb_intelligence_old.py' "$BACKUP_DIR/src/services/smb_intelligence_old.py" 2>/dev/null || true
rm 'src/services/smb_intelligence_old.py'

# src/services/smb_intelligence_old.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/services/smb_intelligence_old.py')"
cp 'src/services/smb_intelligence_old.py' "$BACKUP_DIR/src/services/smb_intelligence_old.py" 2>/dev/null || true
rm 'src/services/smb_intelligence_old.py'


# Duplicate Apis
echo "Cleaning up 2 duplicate_apis..."
# ai_insights/ai_insights_api.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/ai_insights_api.py')"
cp 'ai_insights/ai_insights_api.py' "$BACKUP_DIR/ai_insights/ai_insights_api.py" 2>/dev/null || true
rm 'ai_insights/ai_insights_api.py'

# src/api/api_server_backup.py
mkdir -p "$BACKUP_DIR/$(dirname 'src/api/api_server_backup.py')"
cp 'src/api/api_server_backup.py' "$BACKUP_DIR/src/api/api_server_backup.py" 2>/dev/null || true
rm 'src/api/api_server_backup.py'


# Test Files
echo "Cleaning up 13 test_files..."
# test_postgres_fix.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_postgres_fix.py')"
cp 'test_postgres_fix.py' "$BACKUP_DIR/test_postgres_fix.py" 2>/dev/null || true
rm 'test_postgres_fix.py'

# test_kafka_simple.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_kafka_simple.py')"
cp 'test_kafka_simple.py' "$BACKUP_DIR/test_kafka_simple.py" 2>/dev/null || true
rm 'test_kafka_simple.py'

# test_api_integration.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_api_integration.py')"
cp 'test_api_integration.py' "$BACKUP_DIR/test_api_integration.py" 2>/dev/null || true
rm 'test_api_integration.py'

# test_db_connection.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_db_connection.py')"
cp 'test_db_connection.py' "$BACKUP_DIR/test_db_connection.py" 2>/dev/null || true
rm 'test_db_connection.py'

# test_infrastructure.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_infrastructure.py')"
cp 'test_infrastructure.py' "$BACKUP_DIR/test_infrastructure.py" 2>/dev/null || true
rm 'test_infrastructure.py'

# test_current_setup.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_current_setup.py')"
cp 'test_current_setup.py' "$BACKUP_DIR/test_current_setup.py" 2>/dev/null || true
rm 'test_current_setup.py'

# test_usaspending.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_usaspending.py')"
cp 'test_usaspending.py' "$BACKUP_DIR/test_usaspending.py" 2>/dev/null || true
rm 'test_usaspending.py'

# test_complete_infrastructure.py
mkdir -p "$BACKUP_DIR/$(dirname 'test_complete_infrastructure.py')"
cp 'test_complete_infrastructure.py' "$BACKUP_DIR/test_complete_infrastructure.py" 2>/dev/null || true
rm 'test_complete_infrastructure.py'

# ai_insights/test_openai.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/test_openai.py')"
cp 'ai_insights/test_openai.py' "$BACKUP_DIR/ai_insights/test_openai.py" 2>/dev/null || true
rm 'ai_insights/test_openai.py'

# ai_insights/test_openai_simple.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/test_openai_simple.py')"
cp 'ai_insights/test_openai_simple.py' "$BACKUP_DIR/ai_insights/test_openai_simple.py" 2>/dev/null || true
rm 'ai_insights/test_openai_simple.py'

# final_test.py
mkdir -p "$BACKUP_DIR/$(dirname 'final_test.py')"
cp 'final_test.py' "$BACKUP_DIR/final_test.py" 2>/dev/null || true
rm 'final_test.py'

# debug_usaspending.py
mkdir -p "$BACKUP_DIR/$(dirname 'debug_usaspending.py')"
cp 'debug_usaspending.py' "$BACKUP_DIR/debug_usaspending.py" 2>/dev/null || true
rm 'debug_usaspending.py'

# ai_insights/debug_ai.py
mkdir -p "$BACKUP_DIR/$(dirname 'ai_insights/debug_ai.py')"
cp 'ai_insights/debug_ai.py' "$BACKUP_DIR/ai_insights/debug_ai.py" 2>/dev/null || true
rm 'ai_insights/debug_ai.py'


echo "✅ Cleanup completed!"
echo "📦 Backup created in: $BACKUP_DIR"
echo "🗑️  To permanently delete backups: rm -rf .cleanup_backup"
