#!/bin/bash

# KBI Labs Data Scaling Script
# This script helps scale the data enrichment to all 64,000+ companies

cd ~/KBILabs

echo "🚀 KBI Labs Data Scaling System"
echo "================================"

# 1. First, fix the AI insights
echo "1️⃣ Fixing AI Insights Enhancement..."
cd ai_insights

# Kill any existing AI processes
pkill -f "ai_insights_api.py" 2>/dev/null

# Apply the enhanced context update
python3 ~/update_context.py

# Restart the AI insights API
echo "   Starting enhanced AI insights API..."
python3 ai_insights_api.py &
sleep 3

echo "   ✅ AI Insights enhanced and restarted"

# 2. Check enrichment status
echo -e "\n2️⃣ Checking Enrichment Status..."
cd ~/KBILabs

# Get current database stats
python3 -c "
import psycopg2
from db_config import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Get total companies
cur.execute('SELECT COUNT(*) FROM companies')
total = cur.fetchone()[0]

# Get enriched companies
cur.execute('SELECT COUNT(*) FROM enriched_companies')
enriched = cur.fetchone()[0]

print(f'   Total companies: {total:,}')
print(f'   Enriched companies: {enriched:,}')
print(f'   Remaining: {total - enriched:,}')
print(f'   Progress: {(enriched/total)*100:.1f}%')

conn.close()
"

# 3. Resume enrichment pipeline
echo -e "\n3️⃣ Resuming Enrichment Pipeline..."
echo "   Options:"
echo "   [1] Test mode - Process next 100 companies"
echo "   [2] Full mode - Process all remaining companies"
echo "   [3] Check API rate limits and status"
echo "   [4] Add new enrichment sources"

read -p "   Select option (1-4): " choice

case $choice in
    1)
        echo "   Starting test enrichment (100 companies)..."
        cd enrichment_pipeline
        screen -dmS enrichment_test bash -c "python3 fixed_pipeline_final_working.py <<< '1'"
        echo "   ✅ Test enrichment started in screen session 'enrichment_test'"
        echo "   Run 'screen -r enrichment_test' to monitor progress"
        ;;
    
    2)
        echo "   Starting full enrichment (all remaining companies)..."
        cd enrichment_pipeline
        
        # Create a monitoring script
        cat > monitor_enrichment.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "🔄 KBI Labs Enrichment Progress Monitor"
    echo "======================================"
    
    # Get current stats from database
    python3 -c "
import psycopg2
from db_config import get_db_connection
import datetime

conn = get_db_connection()
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM companies')
total = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM enriched_companies')
enriched = cur.fetchone()[0]

# Get recent enrichment rate
cur.execute('''
    SELECT COUNT(*) 
    FROM enriched_companies 
    WHERE created_at > NOW() - INTERVAL '10 minutes'
''')
recent = cur.fetchone()[0]

rate = recent * 6  # per hour

remaining = total - enriched
if rate > 0:
    eta_hours = remaining / rate
    eta = datetime.datetime.now() + datetime.timedelta(hours=eta_hours)
    eta_str = eta.strftime('%Y-%m-%d %H:%M')
else:
    eta_str = 'Calculating...'

print(f'Total Companies: {total:,}')
print(f'Enriched: {enriched:,} ({(enriched/total)*100:.1f}%)')
print(f'Remaining: {remaining:,}')
print(f'Rate: {rate:,}/hour')
print(f'ETA: {eta_str}')

conn.close()
"
    
    echo ""
    echo "Press Ctrl+C to exit monitor"
    sleep 10
done
