#!/bin/bash

echo "=== KBI Labs USASpending Integration Summary ==="
echo "Date: $(date)"
echo ""

# API Status
echo "1. API Health:"
curl -s http://localhost:8001/health | jq -r '"\(.status) - \(.service) v\(.version)"'
echo ""

# USASpending Status
echo "2. USASpending Integration:"
curl -s http://localhost:8001/api/v3/usaspending/health | jq -r '"\(.status) - \(.service)"'
echo ""

# Metrics
echo "3. USASpending API Calls:"
TOTAL_CALLS=$(curl -s http://localhost:8001/metrics | grep -E "usaspending_requests_total" | grep -v "#" | awk '{sum += $2} END {print sum}')
AVG_DURATION=$(curl -s http://localhost:8001/metrics | grep -E "usaspending_request_duration_seconds_sum" | grep -v "#" | awk '{sum += $2; count++} END {if(count>0) print sum/count; else print 0}')

echo "   Total Calls: $TOTAL_CALLS"
echo "   Average Duration: ${AVG_DURATION}s"
echo ""

# System Impact
echo "4. System Resources:"
echo "   CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "   Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo ""

echo "✅ Integration Complete!"
